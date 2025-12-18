# Kalvium Attendance Discord Bot

A Discord bot that monitors the Kalvium attendance system and automatically pings @everyone when the "Mark Attendance" button appears.

## Features

- 🔐 **Secure Google Login**: Automatically logs into Kaivium using your Google account
- ⏰ **Schedule-Based Monitoring**: Only checks during configured class times
- 🔔 **Automatic Pings**: Sends @everyone ping when attendance opens
- ⚙️ **Configurable**: Easy to customize class schedule, timezone, and check frequency
- 📊 **Status Commands**: Check bot status and configuration from Discord

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- Discord Bot Token (from Discord Developer Portal)
- Google Account credentials
- Chrome Browser (for Selenium)

### 2. Installation

1. Clone/download this repository to `/Users/ars/Desktop/attendence`

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

4. Edit `.env` and add your credentials:
```
DISCORD_TOKEN=your_discord_bot_token
ATTENDANCE_CHANNEL_ID=your_channel_id
GOOGLE_EMAIL=your_email@gmail.com
GOOGLE_PASSWORD=your_password
```

### 3. Get Discord Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section and create a bot
4. Copy the token and add it to `.env`
5. Enable these intents: Message Content Intent
6. Go to OAuth2 → URL Generator and select:
   - Scopes: `bot`
   - Permissions: `Send Messages`, `Mention Everyone`
7. Use the generated URL to invite the bot to your server

### 4. Get Channel ID

1. Enable Developer Mode in Discord (User Settings → App Settings → Advanced → Developer Mode)
2. Right-click on the "attendance" channel and select "Copy Channel ID"
3. Add this ID to `.env`

### 5. Configure Class Schedule (Optional)

Edit `config.py` to adjust:
- Class times (currently 8:30-12:45 Mon-Sat)
- Timezone (currently Asia/Kolkata)
- Check interval (currently 10 seconds)
- Ping message format

Example:
```python
CLASS_SCHEDULE = {
    0: [  # Monday
        ('08:30', '09:30'),
        ('09:30', '10:30'),
    ],
    # ... more days
}
```

### 6. Run the Bot

```bash
python bot.py
```

The bot will:
- Log into Discord
- Wait for class times
- Start checking for the attendance button during class
- Send @everyone ping when button appears
- Rest until the next class period

## Discord Commands

- `!status` - Check current bot status and whether in class time
- `!config` - Display current configuration and class schedule
- `!test` - Send a test ping to verify Discord integration

## Troubleshooting

### Bot not detecting button
- Check if the button selector in `scraper.py` matches the actual Kalvium page
- Run `!status` to verify bot is in checking mode
- Inspect the Kalvium website to find correct element selectors

### Google login fails
- Verify credentials in `.env` are correct
- Check if 2FA is enabled on Google account (may need app password)
- Try logging in manually first to ensure account works

### Bot not sending messages
- Verify Channel ID is correct: `!status`
- Ensure bot has "Send Messages" and "Mention Everyone" permissions
- Test with `!test` command

### Permission issues
Make sure your Discord bot has these permissions in the attendance channel:
- Send Messages
- Mention Everyone
- Embed Links (for status/config commands)

## Hosting Options

### Local Machine
- Simplest setup
- Runs only while your computer is on
- Good for testing

### VPS/Cloud Server
Options:
- **AWS EC2** (free tier available)
- **DigitalOcean** (~$5/month)
- **Heroku** (free tier removed, ~$7/month)
- **Replit** (free for public projects)
- **Railway** (~$5/month)

### Docker
Create a `Dockerfile` to containerize the bot for easier deployment:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

## Security Notes

- Never commit `.env` file to version control
- Use environment variables for sensitive data
- Consider using Google App Passwords if 2FA is enabled
- Regularly rotate Discord tokens

## Notes

- The bot checks every 10 seconds (configurable in `config.py`)
- It only checks during configured class hours
- Once attendance is marked, it won't ping again for the same class
- The browser window is visible by default (for debugging); uncomment `--headless` in `scraper.py` to hide it

## Support

If you encounter issues:
1. Check the logs in the console output
2. Verify all configuration values
3. Test Discord integration with `!test` command
4. Inspect the Kaivium website to ensure selectors are correct
