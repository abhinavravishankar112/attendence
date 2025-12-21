"""
Discord bot for Kalvium attendance monitoring
Checks for attendance button and pings @everyone when it appears
"""
import discord
from discord.ext import commands, tasks
import logging
import pytz
from datetime import datetime, time
import asyncio

from config import (
    DISCORD_TOKEN, ATTENDANCE_CHANNEL_ID, GOOGLE_EMAIL, GOOGLE_PASSWORD,
    KALVIUM_URL, CHECK_INTERVAL, TIMEZONE, CLASS_SCHEDULE, PING_MESSAGE
)
from scraper import create_bot as create_scraper_bot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Global variables
scraper_bot = None
is_checking = False
attendance_marked = False
current_class_period = None


@bot.event
async def on_ready():
    """Called when the bot is ready"""
    logger.info(f'Logged in as {bot.user}')
    check_attendance.start()


def is_class_time():
    """Check if current time falls within any class period"""
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    
    # Check if it's a weekday (Monday=0, Sunday=6)
    weekday = now.weekday()
    if weekday > 5:  # Sunday and beyond
        return None
    
    current_time = now.time()
    
    if weekday not in CLASS_SCHEDULE:
        return None
    
    for start_str, end_str in CLASS_SCHEDULE[weekday]:
        start_time = datetime.strptime(start_str, '%H:%M').time()
        end_time = datetime.strptime(end_str, '%H:%M').time()
        
        if start_time <= current_time <= end_time:
            return (start_str, end_str)
    
    return None


async def send_attendance_ping():
    """Send attendance ping to Discord channel"""
    try:
        channel = bot.get_channel(ATTENDANCE_CHANNEL_ID)
        if not channel:
            logger.error(f"Channel with ID {ATTENDANCE_CHANNEL_ID} not found")
            return False
        
        await channel.send(PING_MESSAGE)
        logger.info(f"Sent attendance ping to channel {channel.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to send Discord message: {e}")
        return False


@tasks.loop(seconds=10)
async def check_attendance():
    """Main task to check for attendance button every 10 seconds"""
    global scraper_bot, is_checking, attendance_marked, current_class_period
    
    try:
        # Check if we're in class time
        class_period = is_class_time()
        
        if not class_period:
            # Not in class time
            if is_checking:
                logger.info("Class period ended, stopping attendance check")
                is_checking = False
                attendance_marked = False
                current_class_period = None
            return
        
        # We're in class time
        if not is_checking:
            logger.info(f"Starting attendance check for class {class_period[0]}-{class_period[1]}")
            is_checking = True
            attendance_marked = False
            current_class_period = class_period
        
        # Initialize scraper if not already done
        if scraper_bot is None:
            logger.info("Initializing Kalvium scraper...")
            scraper_bot = create_scraper_bot(GOOGLE_EMAIL, GOOGLE_PASSWORD, KALVIUM_URL)
            if not scraper_bot:
                logger.error("Failed to initialize scraper bot")
                return
        
        # Check for attendance button
        if not attendance_marked:
            # Refresh page before checking
            scraper_bot.refresh_page()
            
            if scraper_bot.check_attendance_button():
                logger.info("Attendance button detected!")
                if await send_attendance_ping():
                    attendance_marked = True
                    logger.info(f"Successfully pinged @everyone for class {current_class_period}")
    
    except Exception as e:
        logger.error(f"Error in check_attendance task: {e}")


@bot.command(name='status')
async def status_command(ctx):
    """Check the current status of the attendance bot"""
    class_period = is_class_time()
    
    embed = discord.Embed(title="Attendance Bot Status", color=discord.Color.blue())
    embed.add_field(name="Bot Status", value="🟢 Running", inline=False)
    embed.add_field(name="Currently in Class Time", value="✅ Yes" if is_checking else "❌ No", inline=False)
    
    if class_period:
        embed.add_field(name="Current Class", value=f"{class_period[0]} - {class_period[1]}", inline=False)
    
    embed.add_field(name="Attendance Marked", value="✅ Yes" if attendance_marked else "❌ No", inline=False)
    
    await ctx.send(embed=embed)


@bot.command(name='test')
async def test_command(ctx):
    """Test the Discord ping functionality"""
    try:
        channel = bot.get_channel(ATTENDANCE_CHANNEL_ID)
        if not channel:
            await ctx.send("❌ Attendance channel not found!")
            return
        
        await channel.send("[TEST] @everyone attendance is now live")
        await ctx.send("✅ Test message sent successfully!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")


@bot.command(name='config')
async def config_command(ctx):
    """Display current configuration"""
    embed = discord.Embed(title="Bot Configuration", color=discord.Color.green())
    embed.add_field(name="Timezone", value=TIMEZONE, inline=False)
    embed.add_field(name="Check Interval", value=f"{CHECK_INTERVAL} seconds", inline=False)
    embed.add_field(name="Kalvium URL", value=KALVIUM_URL, inline=False)
    
    schedule_text = "📅 Class Schedule:\n"
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    for day_num in range(6):
        if day_num in CLASS_SCHEDULE:
            times = CLASS_SCHEDULE[day_num]
            schedule_text += f"\n**{days[day_num]}:**\n"
            for start, end in times:
                schedule_text += f"  • {start} - {end}\n"
    
    embed.add_field(name="Schedule", value=schedule_text, inline=False)
    await ctx.send(embed=embed)


def main():
    """Main function to run the bot"""
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN not set in environment variables")
        return
    
    if not ATTENDANCE_CHANNEL_ID or ATTENDANCE_CHANNEL_ID == 0:
        logger.error("ATTENDANCE_CHANNEL_ID not set in environment variables")
        return
    
    if not GOOGLE_EMAIL or not GOOGLE_PASSWORD:
        logger.error("Google credentials (GOOGLE_EMAIL/GOOGLE_PASSWORD) not set")
        return
    
    logger.info("Starting Attendance Bot...")
    bot.run(DISCORD_TOKEN)


if __name__ == '__main__':
    main()
