import instaloader
import pandas as pd
import requests
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Google Sheets
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Load environment variables from .env file
load_dotenv()

INSTAGRAM_IDS_FILE = os.getenv("INSTAGRAM_IDS_FILE", "insta_ids.txt")
CSV_FILE = os.getenv("CSV_FILE", "insta_data.csv")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "InstagramData")

def read_insta_ids(filename):
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip()]

def get_insta_data(username):
    L = instaloader.Instaloader()
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        data = {
            "username": username,
            "full_name": profile.full_name,
            "followers": profile.followers,
            "following": profile.followees,
            "posts": profile.mediacount,
            "bio": profile.biography,
            "timestamp": datetime.now().isoformat()
        }
        return data
    except Exception as e:
        print(f"Error fetching {username}: {e}")
        return None

def save_to_csv(data, filename):
    df = pd.DataFrame(data)
    if not df.empty:
        try:
            old = pd.read_csv(filename)
            df = pd.concat([old, df], ignore_index=True)
        except FileNotFoundError:
            pass
        df.to_csv(filename, index=False)

def upload_to_gsheet(csv_file, sheet_name):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    with open(csv_file, 'r') as f:
        content = f.read()
    rows = [row.split(',') for row in content.split('\n') if row]
    sheet.clear()
    sheet.append_rows(rows)

def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, data=payload)

def main():
    insta_ids = read_insta_ids(INSTAGRAM_IDS_FILE)
    all_data = []
    for username in insta_ids:
        data = get_insta_data(username)
        if data:
            all_data.append(data)
            print(f"Fetched data for {username}")
        time.sleep(2)  # Be polite to Instagram

    save_to_csv(all_data, CSV_FILE)
    print(f"Saved data to {CSV_FILE}")

    # Optionally upload to Google Sheets
    upload = input("Upload to Google Sheets? (y/n): ").strip().lower()
    if upload == 'y':
        upload_to_gsheet(CSV_FILE, GOOGLE_SHEET_NAME)
        print("Uploaded to Google Sheets.")

    # Optionally send Telegram message
    send_msg = input("Send Telegram message? (y/n): ").strip().lower()
    if send_msg == 'y':
        send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, f"Instagram data updated at {datetime.now()}.")

if __name__ == "__main__":
    main()