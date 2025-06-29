# Instagram Public Data Scraper

This Python script fetches public data from a list of Instagram accounts, saves the data locally, updates a CSV file with a timestamp, and provides options to upload the data to Google Sheets and send a notification via Telegram.

## Features

- Reads Instagram usernames from a file
- Scrapes public profile data using `instaloader`
- Saves and appends data to a CSV file
- Optionally uploads the CSV to Google Sheets
- Optionally sends a Telegram message notification

## Requirements

- Python 3.7+
- [instaloader](https://instaloader.github.io/)
- pandas
- requests
- gspread
- oauth2client
- python-dotenv

Install dependencies:

```bash
pip install instaloader pandas requests gspread oauth2client python-dotenv
```

## Setup

1. **Clone the repository and navigate to the project folder.**

2. **Create a `.env` file in the project directory:**

    ```
    INSTAGRAM_IDS_FILE=insta_ids.txt
    CSV_FILE=insta_data.csv
    TELEGRAM_BOT_TOKEN=your_telegram_bot_token
    TELEGRAM_CHAT_ID=your_telegram_chat_id
    GOOGLE_SHEET_NAME=InstagramData
    ```

3. **Add your Instagram usernames (one per line) to `insta_ids.txt`.**

4. **(Optional) For Google Sheets upload:**
   - Create a Google Cloud service account and download `credentials.json` to the project directory.
   - Share your Google Sheet with the service account email.

## Usage

Run the script:

```bash
python insta_scraper.py
```

You will be prompted to upload to Google Sheets and/or send a Telegram message after data is fetched.

## Notes

- Only public Instagram profiles can be scraped.
- Be mindful of Instagram's rate limits.
- Your Telegram bot token and chat ID can be obtained from [BotFather](https://t.me/botfather) and [@myidbot](https://t.me/myidbot).

## License

MIT