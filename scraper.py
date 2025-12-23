"""
Web scraper for Kalvium attendance button detection
Uses Selenium with Google login
"""
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)


class AttendanceBot:
    def __init__(self, email, password, url):
        self.email = email
        self.password = password
        self.url = url
        self.driver = None
        self.logged_in = False

    def setup_driver(self):
        """Initialize and setup Selenium WebDriver"""
        try:
            options = Options()
            # Uncomment the line below to run in headless mode (no browser window)
            # options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--start-maximized')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-first-run')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--disable-sync')
            options.add_argument('--disable-features=AccountConsistency,SignInProfileCreation,ChromeWhatsNewUI')

            # On macOS, explicitly set Chrome binary if available
            mac_chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if os.path.exists(mac_chrome_path):
                options.binary_location = mac_chrome_path
            
            # Use Selenium Manager (built into Selenium 4.6+) to resolve driver automatically
            self.driver = webdriver.Chrome(options=options)
            logger.info("WebDriver initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            return False

    def login_with_google(self):
        """Login to Kalvium using Google account.
        Clicks "Continue with Google" and completes OAuth flow.
        """
        try:
            logger.info(f"Navigating to {self.url}")
            self.driver.get(self.url)

            wait = WebDriverWait(self.driver, 20)

            # Click the "Continue with Google" button (try multiple selectors)
            selectors = [
                # Button contains a span with text
                "//button[.//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'continue with google')]]",
                # Button text directly
                "//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'continue with google')]",
                # Role-button div
                "//div[@role='button'][.//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'continue with google')]]",
                # Anchor fallback
                "//a[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'continue with google')]",
                # Provider attribute
                "//*[@data-provider='google']",
            ]

            google_login_button = None
            last_err = None
            for xpath in selectors:
                try:
                    google_login_button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    if google_login_button:
                        break
                except Exception as e:
                    last_err = e
                    continue

            if not google_login_button:
                raise RuntimeError(f"Google login button not found; last error: {last_err}")

            try:
                google_login_button.click()
            except Exception:
                # Fallback to JS click in case of overlays
                self.driver.execute_script("arguments[0].click();", google_login_button)
            logger.info("Clicked 'Continue with Google'")

            # If a new window opens, switch to it; otherwise stay
            try:
                wait.until(lambda d: len(d.window_handles) >= 2)
                self.driver.switch_to.window(self.driver.window_handles[-1])
                logger.info("Switched to Google auth window")
            except Exception:
                logger.info("No popup detected; continuing in current window")

            # If account chooser appears, pick the provided account or use another account
            try:
                # Sometimes Google shows the account list; click "Use another account"
                use_another_xpath = "//div[text()='Use another account' or contains(text(),'another account')]"
                elems = self.driver.find_elements(By.XPATH, use_another_xpath)
                if elems:
                    elems[0].click()
                    logger.info("Selected 'Use another account'")
            except Exception:
                pass

            # Enter email
            try:
                email_input = wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
                email_input.clear()
                email_input.send_keys(self.email)
                next_button = wait.until(EC.element_to_be_clickable((By.ID, "identifierNext")))
                next_button.click()
                logger.info("Entered email")
            except Exception:
                logger.info("Email step not required (likely already signed in)")

            # Enter password
            try:
                # Google uses name='Passwd' for the password field
                password_input = wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
                password_input.clear()
                password_input.send_keys(self.password)
                password_next = wait.until(EC.element_to_be_clickable((By.ID, "passwordNext")))
                password_next.click()
                logger.info("Entered password")
            except Exception as e:
                logger.info(f"Password step not found or not required: {e}")

            # Wait until redirected back to Kalvium (not on accounts.google)
            try:
                wait.until(lambda d: "kalvium.community" in d.current_url and "accounts.google" not in d.current_url)
            except Exception:
                # If still in popup, close and switch back
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])

            # Handle Chrome's "Turn on sync?" or profile prompt if it shows up
            try:
                sync_dismiss = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//button[contains(., 'No thanks')]"
                        " | //span[contains(., 'No thanks')]"
                        " | //div[@role='button'][contains(., 'No thanks')]"
                        " | //button[contains(., 'Not now')]"
                    ))
                )
                sync_dismiss.click()
                logger.info("Dismissed Chrome sync/profile prompt")
            except Exception:
                pass

            # Prefer "Use Chrome without an account" on profile setup prompt
            try:
                without_account_btn = WebDriverWait(self.driver, 4).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//button[contains(., 'Use Chrome without an account')]"
                        " | //div[@role='button'][contains(., 'Use Chrome without an account')]"
                        " | //span[contains(., 'Use Chrome without an account')]"
                    ))
                )
                without_account_btn.click()
                logger.info("Selected 'Use Chrome without an account'")
            except Exception:
                # If the only option visible is 'Continue as ...', leave it untouched
                pass

            logger.info("Successfully completed Google login")
            self.logged_in = True
            return True

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def check_attendance_button(self):
        """Check if 'Mark Attendance' button is visible"""
        try:
            if not self.logged_in:
                return False
            
            # Look for the "Mark Attendance" button
            # Adjust selectors based on actual button attributes
            mark_attendance_buttons = self.driver.find_elements(
                By.XPATH, 
                "//button[contains(text(), 'Mark Attendance')] | //button[contains(text(), 'mark attendance')]"
            )
            
            if mark_attendance_buttons:
                # Check if any button is visible and clickable
                for button in mark_attendance_buttons:
                    if button.is_displayed():
                        logger.info("Mark Attendance button found and visible!")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking for button: {e}")
            return False

    def refresh_page(self):
        """Refresh the current page"""
        try:
            self.driver.refresh()
            logger.info("Page refreshed")
            # Give the page a moment to settle
            time.sleep(0.8)
            return True
        except Exception as e:
            logger.error(f"Failed to refresh page: {e}")
            return False

    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")

    def get_attendance_status(self):
        """Determine attendance status on the Kalvium dashboard.
        Returns one of: 'PRESENT', 'LIVE', 'NONE'.
        - PRESENT: The UI shows that the user is already marked present
        - LIVE: Attendance window is open (button or banner present)
        - NONE: No attendance indicator found
        """
        try:
            if not self.logged_in:
                return 'NONE'

            # Wait for dashboard elements to render
            wait = WebDriverWait(self.driver, 10)
            try:
                wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
            except Exception:
                pass

            # Try to wait for the "My Day" section or header
            dashboard_candidates = [
                "//*[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'my day')]",
                "//*[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'your kalvium apps')]",
            ]
            for xp in dashboard_candidates:
                try:
                    wait.until(EC.presence_of_element_located((By.XPATH, xp)))
                    break
                except Exception:
                    continue

            # Helper to find a visible element by xpath
            def find_visible(xpath):
                elems = self.driver.find_elements(By.XPATH, xpath)
                for el in elems:
                    try:
                        if el.is_displayed():
                            return el
                    except Exception:
                        continue
                return None

            # PRESENT indicators (blue dot + 'Present' or message text)
            present_xpaths = [
                "//*[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'you\'re marked as present')]",
                "//*[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'marked as present')]",
                "//span[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'present')]",
                "//div[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'present')]",
                "//*[@class and contains(translate(@class,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'present')]",
                "//*[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'yay! you\'re marked as present')]",
            ]
            for xp in present_xpaths:
                el = find_visible(xp)
                if el:
                    logger.info("Detected 'Present' status on dashboard")
                    return 'PRESENT'

            # LIVE indicators (button or banner)
            live_xpaths = [
                "//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'mark attendance')]",
                "//*[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'attendance is live')]",
            ]
            for xp in live_xpaths:
                el = find_visible(xp)
                if el:
                    logger.info("Detected attendance is LIVE")
                    return 'LIVE'

            # Fallback: plain text search across the page
            try:
                body_text = (self.driver.execute_script("return document.body.innerText") or "").lower()
                if "you're marked as present" in body_text or "yay! you're marked as present" in body_text:
                    logger.info("Detected 'Present' via text fallback")
                    return 'PRESENT'
                if "attendance is live" in body_text or "mark attendance" in body_text:
                    logger.info("Detected 'LIVE' via text fallback")
                    return 'LIVE'
            except Exception:
                pass

            return 'NONE'
        except Exception as e:
            logger.error(f"Error determining attendance status: {e}")
            return 'NONE'


def create_bot(email, password, url):
    """Factory function to create and initialize the bot"""
    bot = AttendanceBot(email, password, url)
    if bot.setup_driver():
        if bot.login_with_google():
            return bot
    return None
