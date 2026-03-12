import requests
import os
import time
import json
from datetime import date
from twilio.rest import Client

API_URL = os.getenv("WOD_API")

HEADERS = {
    "authorization": os.getenv("WOD_AUTH"),
    "cookie": os.getenv("WOD_COOKIE")
}

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")

FROM_PHONE = os.getenv("TWILIO_FROM")
TO_PHONE = os.getenv("YOUR_PHONE")

CHECK_INTERVAL = 300

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

def get_engine_room():

    r = requests.get(API_URL, headers=HEADERS)

    data = r.json()

    for item in data:

        if "Engine Room" in item["className"]:

            return item["description"]

    return None

while True:

    try:

        workout = get_engine_room()

        state = load_state()

        today = str(date.today())

        if workout and state.get("last_sent") != today:

            send_sms("New Engine Room workout:\n\n" + workout)

            state["last_sent"] = today

            save_state(state)

    except Exception as e:

        print("error:", e)

    time.sleep(CHECK_INTERVAL)