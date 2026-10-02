import os
import re
import json
import traceback
import base64
from pathlib import Path
from typing import Any, Dict, List
from fastapi import FastAPI, Request, Query, Body, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from google_auth_oauthlib.flow import Flow  # type: ignore
from googleapiclient.discovery import build  # type: ignore
from google.oauth2.credentials import Credentials  # type: ignore
from dotenv import load_dotenv

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR.parent / '.env')

app = FastAPI(title="MailSift Python Engine")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
USER_CREDS: Dict[str, Any] = {}

# Path for persistent JSON storage
DATA_FILE = BASE_DIR / "data.json"

# Defaults
DEFAULT_CATEGORIES = ["Work", "Personal", "Promotions", "Other"]

def load_app_data() -> tuple[List[str], Dict[str, str], Dict[str, str]]:
    """Load categories and rules from JSON file if available."""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                cats = data.get("categories", DEFAULT_CATEGORIES)
                sender_rules = data.get("sender_rules", {})
                email_overrides = data.get("email_overrides", {})
                return cats, sender_rules, email_overrides
        except Exception:
            pass
    return list(DEFAULT_CATEGORIES), {}, {}

def save_app_data():
    """Write state to data.json whenever changes occur."""
    with open(DATA_FILE, "w") as f:
        json.dump({
            "categories": CUSTOM_CATEGORIES,
            "sender_rules": SENDER_CATEGORY_RULES,
            "email_overrides": EMAIL_CATEGORY_OVERRIDES
        }, f, indent=2)

# Load state on startup
CUSTOM_CATEGORIES, SENDER_CATEGORY_RULES, EMAIL_CATEGORY_OVERRIDES = load_app_data()

def get_display_name(raw_sender: str) -> str:
    """Extract display name from 'GitHub <noreply@github.com>' -> 'GitHub'."""
    if '<' in raw_sender:
        name = raw_sender.split('<')[0].strip().strip('"\'')
        if name:
            return name
    return raw_sender.strip()

def resolve_category_for_sender(raw_sender: str, subject: str) -> str:
    """Check if any saved keyword exists inside the sender header."""
    sender_lower = raw_sender.lower()
    for rule_keyword, category in SENDER_CATEGORY_RULES.items():
        if rule_keyword.lower() in sender_lower:
            return category
    return "Work" if "work" in subject.lower() else "Other"

def get_flow() -> Any:
    redirect_uri = os.getenv("GMAIL_REDIRECT_URI", "http://127.0.0.1:8000/auth/callback")
    return Flow.from_client_config(
        {
            "web": {
                "client_id": os.getenv("GMAIL_CLIENT_ID"),
                "client_secret": os.getenv("GMAIL_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri,
        autogenerate_code_verifier=False
    )

@app.get("/login")
def login() -> Any:
    flow = get_flow()
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    return RedirectResponse(auth_url)

@app.get("/auth/callback")
def auth_callback(request: Request, code: str) -> RedirectResponse:
    try:
        flow = get_flow()
        flow.fetch_token(code=code)
        creds = flow.credentials
        USER_CREDS['token'] = creds.token
        USER_CREDS['refresh_token'] = creds.refresh_token
        return RedirectResponse("/")
    except Exception:
        err_msg = traceback.format_exc()
        return HTMLResponse(
            content=f"<div style='font-family: monospace; padding: 20px; background: #200; color: #ff8888;'>"
                    f"<h2>OAuth Callback Error:</h2><pre>{err_msg}</pre></div>",
            status_code=500
        )

def get_gmail_service():
    if 'token' not in USER_CREDS:
        return None
    creds = Credentials(
        USER_CREDS['token'],
        refresh_token=USER_CREDS.get('refresh_token'),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GMAIL_CLIENT_ID"),
        client_secret=os.getenv("GMAIL_CLIENT_SECRET")
    )
    return build('gmail', 'v1', credentials=creds)

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, category: str = Query(default="All")) -> Any:
    if 'token' not in USER_CREDS:
        return RedirectResponse("/login")

    try:
        service = get_gmail_service()
        results = service.users().messages().list(userId='me', maxResults=15).execute()
        messages = results.get('messages', [])

        emails: List[Dict[str, Any]] = []

        for msg in messages:
            msg_id = msg['id']
            detail = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            payload = detail.get('payload', {})
            headers = payload.get('headers', [])
            
            subject = "No Subject"
            sender = "Unknown Sender"
            date_str = "Unknown Date"

            for h in headers:
                name = str(h.get('name', '')).lower()
                if name == 'subject':
                    subject = str(h.get('value', 'No Subject'))
                elif name == 'from':
                    sender = str(h.get('value', 'Unknown Sender'))
                elif name == 'date':
                    date_str = str(h.get('value', 'Unknown Date'))

            snippet = str(detail.get('snippet', ''))
            display_sender = get_display_name(sender)

            if msg_id in EMAIL_CATEGORY_OVERRIDES:
                assigned_category = EMAIL_CATEGORY_OVERRIDES[msg_id]
            else:
                assigned_category = resolve_category_for_sender(sender, subject)

            emails.append({
                "id": msg_id,
                "sender": sender,
                "display_sender": display_sender,
                "subject": subject,
                "snippet": snippet,
                "category": assigned_category,
                "date_str": date_str
            })

        filtered = emails if category == "All" else [e for e in emails if e["category"] == category]

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "emails": filtered, 
                "categories": CUSTOM_CATEGORIES, 
                "selected_category": category
            }
        )

    except Exception as e:
        err_msg = traceback.format_exc()
        if hasattr(e, 'content'):
            try:
                err_msg += f"\n\nGoogle API Error Body:\n{e.content.decode('utf-8')}"
            except Exception:
                err_msg += f"\n\nGoogle API Content:\n{str(getattr(e, 'content'))}"

        return HTMLResponse(
            content=f"<div style='font-family: monospace; padding: 20px; background: #200; color: #ff8888;'>"
                    f"<h2>Dashboard Error:</h2><pre>{err_msg}</pre></div>",
            status_code=500
        )

@app.get("/api/email/{email_id}")
def get_email_details(email_id: str):
    service = get_gmail_service()
    if not service:
        raise HTTPException(status_code=401, detail="Unauthenticated")

    try:
        detail = service.users().messages().get(userId='me', id=email_id, format='full').execute()
        payload = detail.get('payload', {})
        headers = payload.get('headers', [])

        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), "No Subject")
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), "Unknown Sender")
        date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), "Unknown Date")

        body = detail.get('snippet', '')
        parts = payload.get('parts', [])
        
        if 'body' in payload and payload['body'].get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        elif parts:
            for part in parts:
                if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                    break

        return {
            "id": email_id,
            "subject": subject,
            "sender": sender,
            "display_sender": get_display_name(sender),
            "date": date_str,
            "snippet": detail.get('snippet', ''),
            "body": body,
            "category": EMAIL_CATEGORY_OVERRIDES.get(email_id, resolve_category_for_sender(sender, subject))
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/categories/add")
def add_category(payload: Dict[str, Any] = Body(...)):
    category = payload.get("category", "").strip()
    senders_input = payload.get("senders", "")
    
    if not category:
        raise HTTPException(status_code=400, detail="Category name required")

    if category not in CUSTOM_CATEGORIES:
        CUSTOM_CATEGORIES.append(category)

    if senders_input:
        raw_list = re.split(r'[,\n]+', str(senders_input))
        for raw_item in raw_list:
            clean_item = raw_item.strip()
            if clean_item:
                SENDER_CATEGORY_RULES[clean_item] = category

    save_app_data()
    return {"categories": CUSTOM_CATEGORIES, "sender_rules": SENDER_CATEGORY_RULES}

@app.post("/api/categories/delete")
def delete_category(payload: Dict[str, str] = Body(...)):
    category_to_delete = payload.get("category", "").strip()

    if not category_to_delete:
        raise HTTPException(status_code=400, detail="Category name required")

    if category_to_delete == "Other":
        raise HTTPException(status_code=400, detail="Cannot delete default 'Other' category")

    if category_to_delete in CUSTOM_CATEGORIES:
        CUSTOM_CATEGORIES.remove(category_to_delete)

    for sender, cat in list(SENDER_CATEGORY_RULES.items()):
        if cat == category_to_delete:
            SENDER_CATEGORY_RULES[sender] = "Other"

    for msg_id, cat in list(EMAIL_CATEGORY_OVERRIDES.items()):
        if cat == category_to_delete:
            EMAIL_CATEGORY_OVERRIDES[msg_id] = "Other"

    save_app_data()
    return {"status": "success", "categories": CUSTOM_CATEGORIES}

@app.post("/api/sender/rule")
def set_sender_rule(payload: Dict[str, str] = Body(...)):
    sender_name = payload.get("sender_name", "").strip()
    category = payload.get("category", "").strip()
    
    if not sender_name or not category:
        raise HTTPException(status_code=400, detail="Missing sender_name or category")

    if category not in CUSTOM_CATEGORIES:
        CUSTOM_CATEGORIES.append(category)

    SENDER_CATEGORY_RULES[sender_name] = category
    save_app_data()
    return {"status": "success", "sender": sender_name, "category": category}

@app.post("/api/email/categorize")
def categorize_email(payload: Dict[str, str] = Body(...)):
    email_id = payload.get("email_id")
    category = payload.get("category")
    
    if not email_id or not category:
        raise HTTPException(status_code=400, detail="Missing email_id or category")

    if category not in CUSTOM_CATEGORIES:
        CUSTOM_CATEGORIES.append(category)

    EMAIL_CATEGORY_OVERRIDES[email_id] = category
    save_app_data()
    return {"status": "success", "email_id": email_id, "category": category}
