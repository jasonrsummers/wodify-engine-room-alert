import os
import json
import requests
from datetime import date
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from twilio.rest import Client

API_URL = "https://app-clientapp.wodify.com/WodifyClient/screenservices/WodifyClient_DataFetch_WB/WOD_Flow/GetAllWorkoutData"

EMAIL = os.getenv("WODIFY_EMAIL")
PASSWORD = os.getenv("WODIFY_PASSWORD")

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
YOUR_PHONE = os.getenv("YOUR_PHONE")

STATE_FILE = "state.json"

print("script booting")

def send_sms(message):

    client = Client(TWILIO_SID, TWILIO_TOKEN)

    client.messages.create(
        body=message,
        from_=TWILIO_FROM,
        to=YOUR_PHONE
    )


def load_state():

    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {}


def save_state(state):

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def get_session_cookies():

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        page.goto("https://app.wodify.com")

        page.fill("input[type=email]", EMAIL)
        page.fill("input[type=password]", PASSWORD)

        page.click("button[type=submit]")

        page.wait_for_timeout(5000)

        cookies = page.context.cookies()

        browser.close()

        return cookies


def fetch_workout(cookies):

    session = requests.Session()

    for c in cookies:
        session.cookies.set(c["name"], c["value"])

    payload = {
        "screenData": {
            "variables": {
                "In_Request": {
                    "SelectedDate": date.today().isoformat()
                }
            }
        }
    }

    r = session.post(API_URL, json=payload)

    data = r.json()

    workout = data["data"]["Response"]["ResponseWOD"]["ResponseWorkout"]

    name = workout["Name"]

    html = workout["WorkoutComponents"]["List"][0]["Description"]

    description = BeautifulSoup(html, "html.parser").get_text("\n")

    return name, description


def main():

    cookies = get_session_cookies()

    name, description = fetch_workout(cookies)

    if "Engine Room" not in name:
        print("Engine Room not found")
        return

    state = load_state()

    today = str(date.today())

    if state.get("last_sent") == today:
        print("Already sent today")
        return

    send_sms("Engine Room workout:\n\n" + description)

    state["last_sent"] = today

    save_state(state)

    print("SMS sent")


import time

import time

if __name__ == "__main__":

    print("Engine Room watcher started")

    while True:

        print("checking for workout...")

        try:
            main()
        except Exception as e:
            print("error:", e)

        print("waiting 5 minutes...\n")

        time.sleep(300)
