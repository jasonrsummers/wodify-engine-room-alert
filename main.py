import requests
import os
import time
import json
from datetime import date
from twilio.rest import Client

API_URL = os.getenv("WOD_API")

HEADERS = {
    "cookie": os.getenv("WOD_COOKIE"),
    "x-csrftoken": os.getenv("WOD_CSRF"),
    "content-type": "application/json"
}

BODY = json.loads(os.getenv("WOD_BODY"))

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


def get_workout():

    r = requests.post(API_URL, headers=HEADERS, json=BODY)

    data = r.json()

    workout = data["data"]["Response"]["ResponseWOD"]["ResponseWorkout"]

    name = workout["Name"]

    desc = workout["WorkoutComponents"]["List"][0]["Description"]

    return name, desc


while True:

    try:

        name, description = get_workout()

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
