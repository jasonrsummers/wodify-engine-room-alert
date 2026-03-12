import requests
import os
import time
import json
from datetime import datetime, date
from twilio.rest import Client
from bs4 import BeautifulSoup

API_URL = os.getenv("WOD_API")

HEADERS = {
    "Content-Type": "application/json; charset=UTF-8",
    "Accept": "application/json",
    "outsystems-device-uuid": os.getenv("WOD_DEVICE_UUID"),
    "x-csrftoken": os.getenv("WOD_CSRF"),
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 OutSystemsApp",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://app-clientapp.wodify.com",
    "Cookie": os.getenv("WOD_COOKIE")
}

BASE_BODY = json.loads(os.getenv("WOD_BODY"))

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
FROM_PHONE = os.getenv("TWILIO_FROM")
TO_PHONE = os.getenv("YOUR_PHONE")

CHECK_INTERVAL = 180


def send_sms(message):

    client = Client(TWILIO_SID, TWILIO_TOKEN)

    client.messages.create(
        body=message,
        from_=FROM_PHONE,
        to=TO_PHONE
    )


def load_state():

    try:
        with open("state.json") as f:
            return json.load(f)
    except:
        return {}


def save_state(state):

    with open("state.json","w") as f:
        json.dump(state,f)


def build_body():

    body = BASE_BODY

    today = date.today().isoformat()

    now = datetime.now().isoformat() + "Z"

    body["screenData"]["variables"]["In_Request"]["SelectedDate"] = today
    body["screenData"]["variables"]["In_Request"]["DateTime"] = now

    return body


def get_engine_room():

    body = build_body()

    r = requests.post(API_URL, headers=HEADERS, json=body)
    
    r = requests.post(API_URL, headers=HEADERS, json=body)
    
    print("status:", r.status_code)
    print("response preview:", r.text[:300])
    
    if r.status_code != 200:
        print("API error:", r.status_code)
        return None, None
    
    try:
        data = r.json()
    
    except Exception:
        print("Invalid JSON response:", r.text[:200])
        return None, None

    workout = data["data"]["Response"]["ResponseWOD"]["ResponseWorkout"]

    name = workout["Name"]

    html = workout["WorkoutComponents"]["List"][0]["Description"]

    description = BeautifulSoup(html, "html.parser").get_text("\n")

    return name, description


while True:

    try:

        name, description = get_engine_room()
        
        if not name:
            time.sleep(CHECK_INTERVAL)
            continue

        if "Engine Room" not in name:
            time.sleep(CHECK_INTERVAL)
            continue

        state = load_state()

        today = str(date.today())

        if state.get("last_sent") != today:

            send_sms("New Engine Room workout:\n\n" + description)

            state["last_sent"] = today

            save_state(state)

    except Exception as e:

        print("error:", e)

    time.sleep(CHECK_INTERVAL)
