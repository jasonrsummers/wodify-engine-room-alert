import os
import json
import requests
from datetime import datetime, date
from bs4 import BeautifulSoup
from twilio.rest import Client

# ---------- CONFIG ----------

LOGIN_URL = "https://app-clientapp.wodify.com/WodifyClient/screenservices/WodifyClient_DataFetch_WB/LoginFlow/Login"
WORKOUT_URL = "https://app-clientapp.wodify.com/WodifyClient/screenservices/WodifyClient_DataFetch_WB/WOD_Flow/GetAllWorkoutData"

EMAIL = os.getenv("WODIFY_EMAIL")
PASSWORD = os.getenv("WODIFY_PASSWORD")

CUSTOMER_ID = os.getenv("WOD_CUSTOMER_ID")
USER_ID = os.getenv("WOD_USER_ID")
GLOBAL_USER_ID = os.getenv("WOD_GLOBAL_USER_ID")
LOCATION_ID = os.getenv("WOD_LOCATION_ID")
PROGRAM_ID = os.getenv("WOD_PROGRAM_ID")

DEVICE_UUID = os.getenv("WOD_DEVICE_UUID")

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
YOUR_PHONE = os.getenv("YOUR_PHONE")

STATE_FILE = "state.json"


# ---------- SMS ----------

def send_sms(message):

    client = Client(TWILIO_SID, TWILIO_TOKEN)

    client.messages.create(
        body=message,
        from_=TWILIO_FROM,
        to=YOUR_PHONE
    )


# ---------- STATE ----------

def load_state():

    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {}


def save_state(state):

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# ---------- LOGIN ----------

def login(session):

    payload = {
        "screenData": {
            "variables": {
                "Email": EMAIL,
                "Password": PASSWORD
            }
        }
    }

    r = session.post(LOGIN_URL, json=payload)

    print("login status:", r.status_code)

    if r.status_code != 200:
        raise Exception("Login failed")

    return r.json()


# ---------- WORKOUT ----------

def fetch_workout(session):

    today = date.today().isoformat()

    now = datetime.utcnow().isoformat() + "Z"

    payload = {
        "screenData": {
            "variables": {
                "In_Request": {
                    "SelectedDate": today,
                    "DateTime": now,
                    "CustomerId": CUSTOMER_ID,
                    "UserId": USER_ID,
                    "GlobalUserId": GLOBAL_USER_ID,
                    "ActiveLocationId": LOCATION_ID,
                    "GymProgramId": PROGRAM_ID,
                    "IsChangeDate": False
                }
            }
        }
    }

    r = session.post(WORKOUT_URL, json=payload)

    print("workout status:", r.status_code)

    data = r.json()

    workout = data["data"]["Response"]["ResponseWOD"]["ResponseWorkout"]

    name = workout["Name"]

    html = workout["WorkoutComponents"]["List"][0]["Description"]

    description = BeautifulSoup(html, "html.parser").get_text("\n")

    return name, description


# ---------- MAIN ----------

def main():

    session = requests.Session()

    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
        "outsystems-device-uuid": DEVICE_UUID,
        "User-Agent": "OutSystemsApp"
    })

    login(session)

    name, description = fetch_workout(session)

    if "Engine Room" not in name:
        print("Engine Room not found")
        return

    state = load_state()

    today = str(date.today())

    if state.get("last_sent") == today:
        print("Already sent today")
        return

    message = "Engine Room workout:\n\n" + description

    send_sms(message)

    state["last_sent"] = today

    save_state(state)

    print("SMS sent")


if __name__ == "__main__":
    main()
