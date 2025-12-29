"""Minimal bot: open site, take screenshots, ask Gemini vision, send Discord message when detected."""
import os
import asyncio
import logging
import time
from datetime import datetime

import discord

from config import (
    DISCORD_TOKEN,
    ATTENDANCE_CHANNEL_ID,
    GOOGLE_EMAIL,
    GOOGLE_PASSWORD,
    KALVIUM_URL,
    CHECK_INTERVAL,
    PING_MESSAGE,
)
from simple_scraper import SimpleScraper
from gemini_vision import detect_attendance_in_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
client = discord.Client(intents=intents)


async def detection_loop(scraper: SimpleScraper, channel: discord.abc.Messageable):
    """Loop: take screenshot every CHECK_INTERVAL seconds and ask Gemini."""
    try:
        debug_dir = os.path.join(os.path.dirname(__file__), 'debug_output')
        os.makedirs(debug_dir, exist_ok=True)

        while True:
            ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            shot = os.path.join(debug_dir, f'shot_{ts}.png')
            # Refresh page and wait before taking screenshot to allow dynamic content to load
            wait_seconds = float(os.getenv('SCREENSHOT_DELAY', '2'))
            scraper.refresh_page(wait=wait_seconds)
            ok = scraper.take_screenshot(shot)
            if ok:
                logger.info(f"Screenshot saved: {shot}")
                res = detect_attendance_in_image(shot, os.getenv('GEMINI_API_KEY'), os.getenv('GEMINI_MODEL', 'gemini-1.5-flash'))
                logger.info(f"Vision result: {res}")
                if res:
                    try:
                        await channel.send(PING_MESSAGE)
                        logger.info("Sent attendance ping via Discord")
                    except Exception as e:
                        logger.error(f"Failed to send Discord message: {e}")
                    # After successful send, sleep longer to avoid spam
                    await asyncio.sleep(60)
            else:
                logger.warning("Failed to capture screenshot")

            await asyncio.sleep(CHECK_INTERVAL)
    except asyncio.CancelledError:
        logger.info('Detection loop cancelled')
    except Exception as e:
        logger.error(f'Detection loop error: {e}')


@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user}')
    # Start scraper and detection
    scraper = SimpleScraper(GOOGLE_EMAIL, GOOGLE_PASSWORD, KALVIUM_URL)
    if not scraper.setup_driver():
        logger.error('Failed to initialize WebDriver')
        return

    # best-effort login (may require manual 2FA in browser)
    scraper.login_with_google()

    channel = client.get_channel(ATTENDANCE_CHANNEL_ID)
    if channel is None:
        logger.error('Attendance channel not found')
        return

    client.loop.create_task(detection_loop(scraper, channel))


def main():
    if not DISCORD_TOKEN:
        logger.error('DISCORD_TOKEN not configured')
        return
    if not ATTENDANCE_CHANNEL_ID:
        logger.error('ATTENDANCE_CHANNEL_ID not configured')
        return
    logger.info('Starting minimal attendance bot')
    client.run(DISCORD_TOKEN)


if __name__ == '__main__':
    main()
