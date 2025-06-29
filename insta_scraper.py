import pandas as pd
import requests
import time
from datetime import datetime
import os
from dotenv import load_dotenv
import json
from bs4 import BeautifulSoup

def read_insta_ids(filename):
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip()]

def get_insta_data(username):
    url = f"https://www.instagram.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Failed to fetch {username}: HTTP {resp.status_code}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        scripts = soup.find_all("script", type="application/ld+json")
        followers = None
        name = username
        if scripts:
            data_json = json.loads(scripts[0].string)
            name = data_json.get("name", username)
            desc = data_json.get("description", "")
            if desc:
                import re
                match = re.search(r"([\d,.]+) Followers", desc)
                if match:
                    followers = match.group(1).replace(",", "")
        if not followers:
            meta = soup.find("meta", property="og:description")
            if meta:
                desc = meta.get("content", "")
                import re
                match = re.search(r"([\d,.]+) Followers", desc)
                if match:
                    followers = match.group(1).replace(",", "")
        user_data = {
            "username": username,
            "name": name,
            "followers": followers,
            "timestamp": datetime.now().isoformat()
        }
        return user_data
    except Exception as e:
        print(f"Error fetching {username}: {e}")
        return None

def save_to_csv(data, filename):
    # Load existing data if file exists, else create empty DataFrame
    try:
        old = pd.read_csv(filename)
    except FileNotFoundError:
        old = pd.DataFrame()
    
    df = pd.DataFrame(data)
    if not df.empty:
        # Ensure all columns are of type object (string) to avoid dtype issues
        old = old.astype('object') if not old.empty else old
        df = df.astype('object')
        # If old is not empty, update rows by username, else just save new
        if not old.empty and 'username' in old.columns:
            old.set_index('username', inplace=True)
            df.set_index('username', inplace=True)
            # Update or insert new rows
            old.update(df)
            for idx in df.index:
                if idx not in old.index:
                    old.loc[idx] = df.loc[idx]
            old.reset_index(inplace=True)
            old.to_csv(filename, index=False)
        else:
            df.reset_index(inplace=True)
            df.to_csv(filename, index=False)

def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, data=payload)

def main():
    load_dotenv()
    INSTAGRAM_IDS_FILE = os.getenv("INSTAGRAM_IDS_FILE", "ids.txt")
    CSV_FILE = os.getenv("CSV_FILE", "insta_data.csv")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    insta_ids = read_insta_ids(INSTAGRAM_IDS_FILE)
    all_data = []
    messages = []
    for username in insta_ids:
        data = get_insta_data(username)
        if data:
            all_data.append(data)
            msg = f"{data['name']} (@{data['username']}): {data['followers']} followers as of {data['timestamp']}"
            messages.append(msg)
            print(f"Fetched data for {username}")
        time.sleep(2)  # Be polite to Instagram

    save_to_csv(all_data, CSV_FILE)
    print(f"Saved data to {CSV_FILE}")

    # Send Telegram summary message
    if messages and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        summary = "Instagram Follower Update:\n" + "\n".join(messages)
        send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, summary)
        print("Sent Telegram message.")
    else:
        print("Telegram message not sent (missing data or credentials).")

if __name__ == "__main__":
    main()