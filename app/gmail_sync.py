import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def sync_classification_to_gmail(access_token: str, refresh_token: str, message_id: str, category: str, rating: int):
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GMAIL_CLIENT_ID"),
        client_secret=os.getenv("GMAIL_CLIENT_SECRET")
    )

    service = build('gmail', 'v1', credentials=creds)

    category_label_name = f"MailSift/{category}"
    rating_label_name = f"MailSift/{rating}-Star"

    category_label_id = ensure_gmail_label(service, category_label_name)
    rating_label_id = ensure_gmail_label(service, rating_label_name)

    service.users().messages().modify(
        userId='me',
        id=message_id,
        body={'addLabelIds': [category_label_id, rating_label_id]}
    ).execute()

def ensure_gmail_label(service, name: str) -> str:
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    for label in labels:
        if label['name'] == name:
            return label['id']

    label_object = {
        'name': name,
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'show',
        'color': {'backgroundColor': '#4a3b32', 'textColor': '#ffffff'}
    }
    created = service.users().labels().create(userId='me', body=label_object).execute()
    return created['id']
