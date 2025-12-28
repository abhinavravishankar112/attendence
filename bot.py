"""
Minimal bot: logs into website, takes screenshots periodically, sends to Gemini to detect
"Mark Attendance", and pings Discord channel when detected.
"""
import os
import time
import logging
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from PIL import Image
import google.generativeai as genai

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ATTENDANCE_CHANNEL_ID = int(os.getenv('ATTENDANCE_CHANNEL_ID', '0'))
GOOGLE_EMAIL = os.getenv('GOOGLE_EMAIL')
GOOGLE_PASSWORD = os.getenv('GOOGLE_PASSWORD')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
KALVIUM_URL = os.getenv('KALVIUM_URL', 'https://kalvium.community')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '10'))
PING_MESSAGE = os.getenv('PING_MESSAGE', '@everyone attendance is now live')

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Selenium driver and state
driver = None
logged_in = False
notified = False


def setup_driver():
    try:
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-features=AutomationControlled')
        # Persist session to avoid repeated login
        profile_dir = os.path.join(os.path.dirname(__file__), '.chrome-profile')
        os.makedirs(profile_dir, exist_ok=True)
        options.add_argument(f'--user-data-dir={profile_dir}')
        options.add_argument('--profile-directory=Default')

        mac_chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.exists(mac_chrome_path):
            options.binary_location = mac_chrome_path

        d = webdriver.Chrome(options=options)
        logger.info('WebDriver initialized')
        return d
    except Exception as e:
        logger.error(f'Failed to initialize WebDriver: {e}')
        return None


def is_dashboard_loaded(d):
    try:
        wait = WebDriverWait(d, 5)
        candidates = [
            "//*[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'your kalvium apps')]",
            "//*[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'attendance hub')]",
            "//*[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'my day')]",
        ]
        for xp in candidates:
            try:
                el = wait.until(EC.presence_of_element_located((By.XPATH, xp)))
                if el:
                    return True
            except Exception:
                continue
        return False
    except Exception:
        return False


def login_with_google(d):
    global logged_in
    try:
        logger.info(f'Navigating to {KALVIUM_URL}')
        d.get(KALVIUM_URL)
        wait = WebDriverWait(d, 20)

        if 'kalvium.community' in d.current_url and is_dashboard_loaded(d):
            logger.info('Session persisted; dashboard visible')
            logged_in = True
            return True

        selectors = [
            "//button[.//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'continue with google')]]",
            "//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'continue with google')]",
            "//*[@data-provider='google']",
        ]
        btn = None
        for xp in selectors:
            try:
                btn = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                if btn:
                    break
            except Exception:
                continue
        if not btn:
            logger.error('Google login button not found')
            return False
        try:
            btn.click()
        except Exception:
            d.execute_script('arguments[0].click();', btn)

        # Possibly switched to popup
        try:
            wait.until(lambda dd: len(dd.window_handles) >= 2)
            d.switch_to.window(d.window_handles[-1])
        except Exception:
            pass

        # Email
        try:
            email_input = wait.until(EC.presence_of_element_located((By.ID, 'identifierId')))
            email_input.clear(); email_input.send_keys(GOOGLE_EMAIL)
            next_button = wait.until(EC.element_to_be_clickable((By.ID, 'identifierNext')))
            next_button.click()
        except Exception:
            logger.info('Email step skipped (already signed in?)')

        # Password
        try:
            password_input = wait.until(EC.presence_of_element_located((By.NAME, 'Passwd')))
            password_input.clear(); password_input.send_keys(GOOGLE_PASSWORD)
            password_next = wait.until(EC.element_to_be_clickable((By.ID, 'passwordNext')))
            password_next.click()
        except Exception:
            logger.info('Password step skipped or not required')

        # Wait for redirect back
        try:
            WebDriverWait(d, 90).until(lambda dd: 'kalvium.community' in dd.current_url and 'accounts.google' not in dd.current_url)
        except Exception:
            if len(d.window_handles) > 1:
                d.close(); d.switch_to.window(d.window_handles[0])

        if is_dashboard_loaded(d):
            logged_in = True
            logger.info('Login successful; dashboard visible')
            return True
        logger.error('Login flow completed but dashboard not detected')
        return False
    except Exception as e:
        logger.error(f'Login failed: {e}')
        return False


def detect_attendance_in_image(image_path: str) -> bool:
    try:
        if not GEMINI_API_KEY:
            logger.error('GEMINI_API_KEY missing')
            return False
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        img = Image.open(image_path)
        prompt = (
            "Answer ONLY YES or NO. Respond YES if a visible button/link says 'Mark Attendance' "
            "or text indicates attendance is live (like a countdown). Otherwise respond NO."
        )
        resp = model.generate_content([prompt, img])
        text = (resp.text or '').strip().upper()
        logger.info(f'Gemini response: {text}')
        if 'YES' in text and 'NO' not in text:
            return True
        if text.startswith('YES'):
            return True
        return False
    except Exception as e:
        logger.error(f'Gemini detection error: {e}')
        return False


async def send_ping():
    try:
        channel = bot.get_channel(ATTENDANCE_CHANNEL_ID)
        if not channel:
            logger.error(f'Channel {ATTENDANCE_CHANNEL_ID} not found')
            return False
        await channel.send(PING_MESSAGE)
        logger.info('Pinged attendance channel')
        return True
    except Exception as e:
        logger.error(f'Discord send failed: {e}')
        return False


@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user}')
    global driver
    driver = setup_driver()
    if not driver:
        logger.error('Driver init failed')
        return
    if not login_with_google(driver):
        logger.error('Login failed; stopping')
        return
    check_loop.start()


@tasks.loop(seconds=CHECK_INTERVAL)
async def check_loop():
    global notified
    try:
        driver.refresh()
        time.sleep(0.7)
        debug_dir = os.path.join(os.path.dirname(__file__), 'debug_output')
        os.makedirs(debug_dir, exist_ok=True)
        path = os.path.join(debug_dir, f'screenshot_{int(time.time())}.png')
        driver.save_screenshot(path)
        logger.info(f'Screenshot saved: {path}')

        detected = detect_attendance_in_image(path)
        logger.info(f'Detected attendance: {detected}')
        if detected and not notified:
            if await send_ping():
                notified = True
    except Exception as e:
        logger.error(f'Check loop error: {e}')


def main():
    if not DISCORD_TOKEN or not ATTENDANCE_CHANNEL_ID or not GOOGLE_EMAIL or not GOOGLE_PASSWORD:
        logger.error('Missing required env: DISCORD_TOKEN, ATTENDANCE_CHANNEL_ID, GOOGLE_EMAIL, GOOGLE_PASSWORD')
        return
    logger.info('Starting Attendance Bot (minimal) ...')
    bot.run(DISCORD_TOKEN)


if __name__ == '__main__':
    main()
