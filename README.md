# 📬 MailSift — Intelligent Gmail Categorization & Priority Triage Engine (Python Edition)

MailSift is a fully-featured python web application that organizes Gmail emails automatically. It integrates directly with your personal Gmail account, automatically sorts incoming emails by AI schema parsing (Pydantic + OpenAI), allows you to set priority from 1 to 5 by yourself, and updates custom labels on the fly into your local Gmail mailbox.

---

## 🚀 Key Features

- **OAuth 2.0 Gmail Connection:** Safely authenticate with personal Google accounts 
- **Automated AI Categorization:** Instantly assigns 5 key categories via Pydantic schema validation:
  - 💼 `Work`
  - 🎓 `School`
  - 🚀 `Job Opportunities`
  - 🔑 `Verification Codes`
  - 📂 `Other`
- **Interactive 1-to-5 Star Importance Ratings:** Users can manually override AI-assigned priority stars
- **Two-Way Gmail Sync:** Updates in the web application instantly update labels inside your native Gmail mailbox (`MailSift/Work`, `MailSift/5-Star`).

---


## 💻 Tech Stack

- **Backend:** Python, FastAPI, Uvicorn, Celery, Redis
- **Database:** SQLAlchemy, SQLite, PostgreSQL, Alembic
- **Frontend:** Jinja2 Templates, Tailwind CSS, HTMX, Lucide Icons
- **Integrations:** `google-api-python-client`, `google-auth-oauthlib`, `openai`, `pydantic`

---

## 🛠 Local Setup Instructions


### 1. Setup Virtual Environment
```bash
git clone https://github.com/your-username/mail-sift-python.git
cd mail-sift-python
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Create Environment 
Create a `.env` file in the root directory:

```env
DATABASE_URL="sqlite:///./mail_sift.db"
REDIS_URL="redis://localhost:6379/0"

GMAIL_CLIENT_ID="your-google-client-id"
GMAIL_CLIENT_SECRET="your-google-client-secret"
GMAIL_REDIRECT_URI="http://localhost:8000/auth/callback"

OPENAI_API_KEY="your-openai-api-key"
```

### 4. Run Application
```bash
uvicorn app.main:app --reload
```
Open `http://localhost:8000` in your browser.

---
