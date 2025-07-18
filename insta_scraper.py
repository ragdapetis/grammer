import os
import argparse
import json
import time
import random
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def read_insta_ids(filename):
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip()]

def send_telegram_message(token, chat_id, message):
    import requests
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def save_cookies(context, cookie_path):
    cookies = context.cookies()
    with open(cookie_path, 'w') as f:
        json.dump(cookies, f)

def load_cookies(context, cookie_path):
    if os.path.exists(cookie_path):
        with open(cookie_path, 'r') as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        return True
    return False

def login_instagram(page, username, password):
    page.goto("https://www.instagram.com/accounts/login/")
    page.wait_for_selector('input[name="username"]')
    time.sleep(random.uniform(1.5, 3.5))  # Simulate human delay before typing username
    page.locator('input[name="username"]').type(username)
    time.sleep(random.uniform(1.5, 3.5))  # Simulate human delay before typing password
    page.locator('input[name="password"]').type(password)
    time.sleep(random.uniform(1.5, 3.5))  # Simulate human delay before clicking login
    page.click('button[type="submit"]')
    try:
        page.wait_for_selector('nav', timeout=15000)
        save_cookies(page.context, "insta_cookies.json")
    except PlaywrightTimeoutError:
        return False
    return True

def get_profile_stats(page, username):
    url = f"https://www.instagram.com/{username}/"
    page.goto(url)
    try:
        page.wait_for_selector('header section ul li', timeout=15000)
        stats = page.query_selector_all('header section ul li span')
        posts = stats[0].get_attribute('title') or stats[0].inner_text() if len(stats) > 0 else None
        followers = stats[1].get_attribute('title') or stats[1].inner_text() if len(stats) > 1 else None
        following = stats[2].get_attribute('title') or stats[2].inner_text() if len(stats) > 2 else None
        return posts, followers, following
    except Exception as e:
        return None, None, None

def main():
    parser = argparse.ArgumentParser(description="Instagram scraper with Playwright and Telegram notification.")
    parser.add_argument('--headless', type=str, default='false', help='Run browser in headless mode (true/false)')
    parser.add_argument('--delay', type=float, default=10.0, help='Base delay (seconds) between account visits (default: 10)')
    args = parser.parse_args()
    headless = args.headless.lower() in ["true", "1", "yes", "on"]
    base_delay = args.delay

    load_dotenv()
    INSTAGRAM_IDS_FILE = os.getenv("INSTAGRAM_IDS_FILE", "ids.txt")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    INSTA_LOGIN_USER = os.getenv("INSTA_LOGIN_USER")
    INSTA_LOGIN_PASS = os.getenv("INSTA_LOGIN_PASS")
    COOKIE_PATH = "insta_cookies.json"

    insta_ids = read_insta_ids(INSTAGRAM_IDS_FILE)
    messages = []
    error_messages = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        # Try to login using cookies first
        logged_in = False
        if load_cookies(context, COOKIE_PATH):
            page.goto("https://www.instagram.com/")
            try:
                page.wait_for_selector('nav', timeout=10000)
                logged_in = True
            except PlaywrightTimeoutError:
                logged_in = False
        if not logged_in:
            print("Manual login required. Simulating...")
            login_instagram(page, INSTA_LOGIN_USER, INSTA_LOGIN_PASS)
            # After manual login, check if successful
            try:
                page.wait_for_selector('nav', timeout=15000)
                save_cookies(context, COOKIE_PATH)
                logged_in = True
            except PlaywrightTimeoutError:
                send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, "Instagram manual login failed.")
                page.close()
                context.close()
                browser.close()
                return
        for username in insta_ids:
            print(f"Fetching stats for @{username}...")
            try:
                posts, followers, following = get_profile_stats(page, username)
                if followers is not None:
                    msg = f"(@{username}): {followers} followers, {following} following, {posts} posts"
                    messages.append(msg)
                    print(f"Fetched data for {username}")
                else:
                    error_messages.append(f"Error fetching stats for {username}")
            except Exception as e:
                error_messages.append(f"Error for {username}: {e}")
            # Randomized delay between accounts
            delay = base_delay + random.uniform(-base_delay/2, base_delay/2)
            print(f"Waiting {delay:.2f} seconds before next account...")
            time.sleep(delay)
        page.close()
        context.close()
        browser.close()
    # Send Telegram summary message
    if messages:
        summary = "Instagram Follower Update:\n" + "\n".join(messages)
        send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, summary)
        print("Sent Telegram message.")
    if error_messages:
        error_summary = "Instagram Scraper Errors:\n" + "\n".join(error_messages)
        send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, error_summary)
        print("Sent error messages to Telegram.")

if __name__ == "__main__":
    main()