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
        """Login to Kalvium using Google account"""
        try:
            logger.info(f"Navigating to {self.url}")
            self.driver.get(self.url)
            
            # Wait for and click Google login button
            # These selectors might need adjustment based on actual Kalvium page
            wait = WebDriverWait(self.driver, 10)
            
            # Look for Google login button (adjust selector if needed)
            google_login_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Google')] | //a[contains(text(), 'Google')] | //button[@data-provider='google']"))
            )
            google_login_button.click()
            logger.info("Clicked Google login button")
            
            # Wait for Google login window and switch to it
            time.sleep(1)
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # Enter email
            email_input = wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
            email_input.send_keys(self.email)
            
            next_button = self.driver.find_element(By.ID, "identifierNext")
            next_button.click()
            logger.info("Entered email")
            
            time.sleep(1)
            
            # Enter password
            password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
            password_input.send_keys(self.password)
            
            password_next = self.driver.find_element(By.ID, "passwordNext")
            password_next.click()
            logger.info("Entered password")
            
            # Wait for redirect back to Kalvium
            time.sleep(3)
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            logger.info("Successfully logged in with Google")
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
            return True
        except Exception as e:
            logger.error(f"Failed to refresh page: {e}")
            return False

    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")


def create_bot(email, password, url):
    """Factory function to create and initialize the bot"""
    bot = AttendanceBot(email, password, url)
    if bot.setup_driver():
        if bot.login_with_google():
            return bot
    return None
