# Minimal Attendance Bot

Opens Kalvium, logs in via Google, takes a screenshot every 10 seconds, sends to Gemini for vision detection, and pings the Discord channel when "Mark Attendance" appears.

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
GEMINI_API_KEY=your_gemini_api_key
# Optional:
# GEMINI_MODEL=gemini-1.5-flash
CHECK_INTERVAL=10
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

### Run

```bash
python bot.py
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

## Behavior

- Refreshes the page, captures a screenshot into `debug_output/`, and asks Gemini if attendance is live.
- Sends `@everyone` once per run when detection is positive.

## Troubleshooting

### Bot not detecting button
- Ensure `GEMINI_API_KEY` is set and has quota.
- Verify Chrome is installed.

### Google login fails
- Verify credentials in `.env`.
- If 2FA is enabled, use an App Password.

### Bot not sending messages
- Verify Channel ID is correct.
- Ensure bot has "Send Messages" and "Mention Everyone" permissions.

### Permissions
- Send Messages
- Mention Everyone

## Hosting Options

### Local Machine
- Simplest setup
- Runs only while your computer is on
- Good for testing

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

- Checks every 10 seconds by default.
- Sends one ping per run when detected.
- Browser window is visible by default.

## Support

If you encounter issues:
1. Check the logs in the console output
2. Verify all configuration values
3. Test Discord integration with `!test` command
4. Inspect the Kaivium website to ensure selectors are correct
