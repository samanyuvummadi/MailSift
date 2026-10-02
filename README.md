# 📬 MailSift — Intelligent Gmail Categorization & Priority Triage Engine (Python Edition)

MailSift is a dynamic, full-stack web application built in Python for automated Gmail organization. It connects directly to personal Gmail accounts, automatically categorizes incoming emails using AI schema parsing (Pydantic + OpenAI), enables user-controlled 1-to-5 star priority ratings, and updates custom labels in real-time within your native Gmail mailbox.

---

## 🎨 Design Theme & Palette
Designed with a cohesive **Warm Light Brown (Mocha) & Deep Navy** aesthetic:
- **Navy Primary (`#0F172A`, `#1E293B`)**: Navigation bars, headers, and primary badges.
- **Warm Light Brown (`#FAF6F0`, `#E8DFC8`, `#8C6D46`)**: Main content backgrounds, email card containers, and priority accent highlights.

---

## 🚀 Key Features

- **OAuth 2.0 Gmail Connection:** Safely authenticate with personal Google accounts (`gmail.modify` scope).
- **Automated AI Categorization:** Instant classification into five key categories via Pydantic schema validation:
  - 💼 `Work`
  - 🎓 `School`
  - 🚀 `Job Opportunities`
  - 🔑 `Verification Codes`
  - 📂 `Other`
- **Interactive 1-to-5 Star Importance Ratings:** Users can manually override AI-assigned priority stars (5 = Urgent / High Priority, 1 = Low / Marketing).
- **Two-Way Gmail Sync:** Updates in the web application instantly update labels inside your native Gmail mailbox (`MailSift/Work`, `MailSift/5-Star`).
- **Asynchronous Task Queue:** Managed with Celery & Redis for non-blocking email syncing.

---

## 🏗 System Architecture

```
[ Gmail Event ] ──► [ FastAPI Webhook ] ──► [ Celery / Redis Worker ]
                                                   │
                                ┌──────────────────┴──────────────────┐
                                ▼                                     ▼
                      [ OpenAI API Triage ]               [ SQLite / PostgreSQL ]
                                │                                     │
                                └──────────────────┬──────────────────┘
                                                   ▼
                                       [ Sync Back to Gmail API ]
```

---

## 💻 Tech Stack

- **Backend:** Python 3.11+, FastAPI, Uvicorn, Celery, Redis
- **Database:** SQLAlchemy, SQLite (default for quick dev) / PostgreSQL, Alembic
- **Frontend:** Jinja2 Templates, Tailwind CSS (via CDN), HTMX / Alpine.js for dynamic updates, Lucide Icons
- **Integrations:** `google-api-python-client`, `google-auth-oauthlib`, `openai`, `pydantic`

---

## 🛠 Local Setup Instructions

### Prerequisites
- Python >= 3.10
- Redis instance (`redis-server` or via Docker)
- Google Cloud Console Project (with Gmail API enabled & OAuth Credentials)

### 1. Clone & Setup Virtual Environment
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

### 3. Environment Variables Configuration
Create a `.env` file in the root directory:

```env
DATABASE_URL="sqlite:///./mail_sift.db"
REDIS_URL="redis://localhost:6379/0"

GMAIL_CLIENT_ID="your-google-client-id"
GMAIL_CLIENT_SECRET="your-google-client-secret"
GMAIL_REDIRECT_URI="http://localhost:8000/auth/callback"

OPENAI_API_KEY="your-openai-api-key"
```

### 4. Run Development Server
```bash
uvicorn app.main:app --reload
```
Open `http://localhost:8000` in your browser.

---

## ⚡ Technical Highlights for Reviewers
- **Data Validation:** Strict runtime validation using **Pydantic v2** models for structured OpenAI outputs.
- **Asynchronous Scalability:** Heavy Gmail API sync jobs are dispatched asynchronously to **Celery workers** to avoid slowing down HTTP request cycles.
