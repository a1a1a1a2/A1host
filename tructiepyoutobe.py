import os
from flask import Flask, jsonify
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, db
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# === CONFIGURATION ===
SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly"
]
FIREBASE_CRED_JSON = "firebase-adminsdk.json"
FIREBASE_DB_URL = "https://your-firebase-project.firebaseio.com/"
CLIENT_SECRETS_FILE = "client_secret.json"
TOKEN_FILE = "token.json"

CHANNEL_ID = "MINE"  # or use a real ID

app = Flask(__name__)

# === INITIALIZATION ===
def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CRED_JSON)
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})


def get_credentials():
    if os.path.exists(TOKEN_FILE):
        return Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
    return creds


def get_youtube_services():
    creds = get_credentials()
    youtube_analytics = build("youtubeAnalytics", "v2", credentials=creds)
    youtube = build("youtube", "v3", credentials=creds)
    return youtube_analytics, youtube


def resolve_channel_id(youtube):
    global CHANNEL_ID
    if CHANNEL_ID == "MINE":
        response = youtube.channels().list(mine=True, part="id").execute()
        CHANNEL_ID = response['items'][0]['id']


def get_report(youtube_analytics, start_date, end_date):
    return youtube_analytics.reports().query(
        ids=f"channel=={CHANNEL_ID}",
        startDate=start_date,
        endDate=end_date,
        metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained",
        dimensions="country",
        sort="-views"
    ).execute()


def filter_vietnam_data(report):
    if not report:
        return []
    headers = [h['name'] for h in report.get('columnHeaders', [])]
    return [dict(zip(headers, row)) for row in report.get('rows', []) if row[0].lower() == 'vn']


def save_to_firebase(data):
    ref = db.reference('youtube_analytics/vietnam')
    timestamp = datetime.now().isoformat()
    ref.child(timestamp).set(data)


@app.route("/run", methods=["GET"])
def run_report():
    try:
        init_firebase()
        youtube_analytics, youtube = get_youtube_services()
        resolve_channel_id(youtube)

        end_date = datetime.today()
        start_date = end_date - timedelta(days=7)

        report = get_report(
            youtube_analytics,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )

        vietnam_data = filter_vietnam_data(report)
        if vietnam_data:
            save_to_firebase(vietnam_data)
            return jsonify({"status": "success", "data": vietnam_data})
        else:
            return jsonify({"status": "no_data", "message": "Không có dữ liệu Việt Nam."})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
