"""
Configuration file for the Attendance Bot
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Discord Bot Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ATTENDANCE_CHANNEL_ID = int(os.getenv('ATTENDANCE_CHANNEL_ID', '0'))  # Replace with your channel ID

# Google Login Credentials
GOOGLE_EMAIL = os.getenv('GOOGLE_EMAIL')
GOOGLE_PASSWORD = os.getenv('GOOGLE_PASSWORD')

# Website Configuration
KALVIUM_URL = "https://kalvium.community"  # Update if different
CHECK_INTERVAL = 10  # seconds - how often to check for the button

# Timezone
TIMEZONE = 'Asia/Kolkata'  # IST

# Class Schedule (Monday=0, Sunday=6)
# Format: {day: [(start_time, end_time), ...]}
# Times in HH:MM format (24-hour)
CLASS_SCHEDULE = {
    0: [  # Monday
        ('08:30', '09:30'),
        ('09:30', '10:30'),
        ('10:45', '11:45'),
        ('11:45', '12:45'),
    ],
    1: [  # Tuesday
        ('08:30', '09:30'),
        ('09:30', '10:30'),
        ('10:45', '11:45'),
        ('11:45', '12:45'),
    ],
    2: [  # Wednesday
        ('08:30', '09:30'),
        ('09:30', '10:30'),
        ('10:45', '11:45'),
        ('11:45', '12:45'),
    ],
    3: [  # Thursday
        ('08:30', '09:30'),
        ('09:30', '10:30'),
        ('10:45', '11:45'),
        ('11:45', '12:45'),
    ],
    4: [  # Friday
        ('08:30', '09:30'),
        ('09:30', '10:30'),
        ('10:45', '11:45'),
        ('11:45', '12:45'),
    ],
    5: [  # Saturday
        ('08:30', '09:30'),
        ('09:30', '10:30'),
        ('10:45', '11:45'),
    ],
}

# Discord Message Configuration
PING_MESSAGE = "@everyone attendance is now live"
