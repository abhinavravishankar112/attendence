"""
Minimal scraper: open site, perform Google login (best-effort), take screenshots.
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


class SimpleScraper:
    def __init__(self, email: str, password: str, url: str):
        self.email = email
        self.password = password
        self.url = url
        self.driver = None
        self.logged_in = False

    def setup_driver(self) -> bool:
        try:
            options = Options()
            # keep visible by default for debugging; add --headless if desired
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            profile_dir = os.path.join(os.path.dirname(__file__), '.chrome-profile')
            os.makedirs(profile_dir, exist_ok=True)
            options.add_argument(f'--user-data-dir={profile_dir}')
            options.add_argument('--profile-directory=Default')
            mac_chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if os.path.exists(mac_chrome_path):
                options.binary_location = mac_chrome_path

            self.driver = webdriver.Chrome(options=options)
            return True
        except Exception as e:
            logger.error(f"Failed to start WebDriver: {e}")
            return False

    def login_with_google(self, timeout: int = 30) -> bool:
        """Attempt Google OAuth login. This is best-effort — persistent profile preferred."""
        if not self.driver:
            return False
        try:
            self.driver.get(self.url)
            wait = WebDriverWait(self.driver, 15)

            # If already on kalvium and looks like dashboard, assume logged in
            if 'kalvium.community' in self.driver.current_url:
                self.logged_in = True
                return True

            # Try to click common "Continue with Google" buttons (several XPaths)
            selectors = [
                "//button[.//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'continue with google')]]",
                "//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'continue with google')]",
                "//*[@data-provider='google']",
            ]
            clicked = False
            for xp in selectors:
                try:
                    el = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                    self.driver.execute_script("arguments[0].click();", el)
                    clicked = True
                    break
                except Exception:
                    continue

            # If not clicked, proceed — maybe already logged in or site uses a different flow
            # Wait a bit for Google auth to proceed (may require manual 2FA)
            time.sleep(2)

            # If a Google auth window opened, try to switch and enter credentials
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                # Try email
                try:
                    email_input = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'identifierId')))
                    email_input.clear(); email_input.send_keys(self.email)
                    nxt = self.driver.find_element(By.ID, 'identifierNext')
                    self.driver.execute_script('arguments[0].click();', nxt)
                except Exception:
                    pass
                # Try password
                try:
                    pwd = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.NAME, 'Passwd')))
                    pwd.clear(); pwd.send_keys(self.password)
                    pnext = self.driver.find_element(By.ID, 'passwordNext')
                    self.driver.execute_script('arguments[0].click();', pnext)
                except Exception:
                    pass
            except Exception:
                pass

            # Wait up to timeout for kalvium URL to appear
            end = time.time() + timeout
            while time.time() < end:
                if 'kalvium.community' in self.driver.current_url:
                    self.logged_in = True
                    return True
                time.sleep(1)

            # Not logged in automatically — still proceed; the page may be accessible without login
            return self.logged_in
        except Exception as e:
            logger.error(f"Login flow failed: {e}")
            return False

    def take_screenshot(self, dest_path: str) -> bool:
        try:
            if not self.driver:
                return False
            # small wait to let UI settle
            time.sleep(0.6)
            self.driver.save_screenshot(dest_path)
            return True
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return False

    def refresh_page(self, wait: float = 2.0) -> bool:
        """Refresh the current page and wait `wait` seconds for it to settle."""
        try:
            if not self.driver:
                return False
            self.driver.refresh()
            time.sleep(wait)
            return True
        except Exception as e:
            logger.error(f"Refresh failed: {e}")
            return False

    def close(self):
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass
