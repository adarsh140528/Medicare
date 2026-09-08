# MediVision AI — Clinical Healthcare Platform

> **Clinical Decision Support, Computer Vision Telemetry, and Telehealth Operations**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-emerald.svg)](https://flask.palletsprojects.com)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4.0-orange.svg)](https://scikit-learn.org)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-3.6--Flash-4285F4.svg)](https://ai.google.dev/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.9-red.svg)](https://opencv.org)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E.svg)](https://supabase.com)
[![Twilio](https://img.shields.io/badge/Twilio-SMS%202FA-F22F46.svg)](https://www.twilio.com)

---

## 📋 Executive Overview

**MediVision AI** is a production-grade clinical technology platform engineered for health systems, medical practices, and patient self-care operations. Built with a minimal, high-density design language inspired by Linear, Stripe, and modern clinical EHR systems, it unifies **diagnostic symptom screening**, **real-time computer vision biomarker telemetry**, **generative clinical decision support**, and **telehealth consultation management**.

---

## 🏛️ Platform Architecture

```text
                               ┌────────────────────────────────────────┐
                               │       MediVision Clinical UI           │
                               │  (Vanilla CSS System + Zero Flicker)   │
                               └──────────────────┬─────────────────────┘
                                                  │
                  ┌───────────────────────────────┴───────────────────────────────┐
                  ▼                                                               ▼
       ┌─────────────────────┐                                         ┌─────────────────────┐
       │   Patient Portal    │                                         │ Physician Workspace │
       │  (/dashboard, etc.) │                                         │ (/doctor-dashboard) │
       └──────────┬──────────┘                                         └──────────┬──────────┘
                  │                                                               │
                  └───────────────────────────────┬───────────────────────────────┘
                                                  │ REST APIs & WebSockets
                                                  ▼
                               ┌────────────────────────────────────────┐
                               │        Flask + SocketIO Engine         │
                               └───────┬──────────┬──────────┬──────────┘
                                       │          │          │
                 ┌─────────────────────┴──┐       │       ┌──┴─────────────────────┐
                 ▼                        ▼       ▼       ▼                        ▼
        ┌──────────────────┐  ┌─────────────┐ ┌───────┐ ┌──────────────────┐  ┌─────────────┐
        │  Scikit-Learn ML │  │Google Gemini│ │OpenCV │ │  Twilio SMS 2FA  │  │  Supabase   │
        │ Disease Ensemble │  │ Clinical AI │ │Vision │ │   Phone 2FA      │  │ PostgreSQL  │
        └──────────────────┘  └─────────────┘ └───────┘ └──────────────────┘  └─────────────┘
```

---

## ✨ Clinical Core Modules

| Module | Route | Technical Foundation | Clinical Function |
|---|---|---|---|
| **Clinical Symptom Assessment** | `/ai-predict` | `scikit-learn` Ensemble Classifier | Evaluates 158 clinical symptoms to compute differential condition probabilities & risk index. |
| **Clinical AI Assistant** | `/medibot` | `Google Gemini 3.6 Flash` | Live generative clinical intelligence for drug interactions, pediatric guidance, and triage Q&A. |
| **Computer Vision Telemetry** | `/vision` | `OpenCV` + `MediaPipe` | Real-time rPPG pulse rate estimation (BPM), blink rate, and ocular drowsiness indices. |
| **Patient Portal** | `/dashboard` | Flask + SocketIO + REST | Longitudinal biomarker tracking, weekly vitals log, health score gauge, and consultations. |
| **Physician Workspace** | `/doctor-dashboard` | Flask + Supabase RLS | High-density clinical queue, intake triage actions, mark paid controls, and e-prescriptions. |
| **Consultation Scheduling** | `/appointments` | Flask + Payment Gateway | Doctor directory filtered by specialty with interactive calendar slot reservations. |
| **Prescription Records** | `/prescriptions` | `ReportLab` PDF Engine | Formal digital medical prescription issuance and instant PDF export downloads. |
| **Clinical Health Summary** | `/health-report` | Printable Clinical Layout | Print-ready comprehensive medical profile, domain scores, and longitudinal logs. |
| **2FA Authentication** | `/login`, `/register` | `Twilio` SMS + JWT | Segmented Patient/Doctor role switcher with 6-digit auto-advancing OTP verification. |

---

## 📂 Repository Structure

```
Medicare-1/
├── app.py                          # Flask application factory & SocketIO setup
├── run.py                          # Local dev server launcher & model verification
├── requirements.txt                # Production Python dependencies
├── Procfile                        # Gunicorn production process file
├── render.yaml                     # Render 1-click cloud infrastructure config
├── Dockerfile                      # Production Docker container definition
├── .dockerignore                   # Build ignore rules
├── .env.example                    # Sample environment variable template
│
├── backend/
│   ├── routes/
│   │   ├── auth_routes.py          # Twilio OTP, JWT token generation & login/register
│   │   ├── ai_routes.py            # Disease prediction ML endpoint & chat routing
│   │   ├── appointment_routes.py   # Scheduling, slot availability & doctor catalog
│   │   ├── dashboard_routes.py     # Patient overview, stats aggregation & vitals logs
│   │   ├── payment_routes.py       # Payment processing & status confirmation
│   │   ├── prescription_routes.py  # E-prescription issuance & PDF generation
│   │   └── vision_routes.py        # Video frame analysis (BPM, blink, posture)
│   ├── services/
│   │   └── ai_bot_service.py       # Multi-LLM dispatcher (Gemini, Groq, OpenAI) + Medical Engine
│   └── utils/
│       ├── db.py                   # Local SQLite fallback client
│       └── supabase_client.py      # Live Supabase connection & service role client
│
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── clinical.css        # Centralized Clinical Design System (Dark & Light tokens)
│   │   └── theme.js                # Zero-flicker theme engine with persistence & mobile nav
│   └── templates/
│       ├── landing.html            # Marketing landing page
│       ├── login.html              # Authentication & 6-box OTP card
│       ├── register.html           # 4-stage enrollment wizard
│       ├── dashboard.html          # Patient health dashboard
│       ├── doctor_dashboard.html   # Physician clinical workspace
│       ├── appointments.html       # Doctor directory & appointment booking
│       ├── prescriptions.html      # Prescription history & PDF generation
│       ├── ai_predict.html         # Clinical symptom screening studio
│       ├── medibot.html            # Clinical AI Assistant messenger
│       ├── vision.html             # High-precision vision telemetry studio
│       └── health_report.html      # Printable clinical health summary document
│
├── ml_models/
│   ├── train_model.py              # ML ensemble training pipeline (Random Forest + Gradient Boosting)
│   ├── disease_model.pkl           # Trained serialized voting classifier artifact
│   └── model_metadata.json         # 158 symptom dimension schemas & disease metadata
│
└── database/
    ├── schema.sql                  # PostgreSQL / Supabase schema migrations
    └── medivision.db               # Local SQLite fallback database
```

---

## ⚙️ Local Development Setup

### 1. Prerequisites
- **Python 3.10+** (Recommended: Python 3.11)
- Git & pip

### 2. Clone and Install Dependencies
```bash
# Clone the repository
git clone https://github.com/your-username/Medicare.git
cd Medicare

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory (or copy from `.env.example`):

```env
FLASK_SECRET_KEY=medivision-secret-key-2026
FLASK_ENV=development
FLASK_PORT=5000
JWT_SECRET=medivision-jwt-secret-2026
JWT_EXPIRY_HOURS=24

# Supabase Database (Live Cloud DB)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGciOi...
SUPABASE_SERVICE_KEY=eyJhbGciOi...

# Twilio SMS 2FA Authentication
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Google Gemini API Key (Live Generative Clinical Assistant)
GEMINI_API_KEY=your_gemini_api_key
```

### 4. Run Application
```bash
python run.py
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser.

---

## 🚀 Production Cloud Deployment

### Deploy on Render (Recommended)
1. Push your code to GitHub.
2. Sign in to **[Render Dashboard](https://dashboard.render.com)**.
3. Click **New +** → **Web Service** and select your GitHub repository.
4. Set:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --workers 1 --threads 8 --bind 0.0.0.0:$PORT run:app`
5. Add your `.env` variables in the **Environment** settings.
6. Click **Deploy Web Service**.

### Deploy with Docker
```bash
# Build Docker image
docker build -t medivision-ai .

# Run container
docker run -d -p 5000:5000 --env-file .env --name medivision medivision-ai
```

---

## 🧪 Machine Learning Architecture

The diagnostic engine uses an **Ensemble Soft-Voting Classifier**:
- **Random Forest Classifier** (100 estimators)
- **Gradient Boosting Classifier** (learning rate: 0.1)
- **Features**: 158 clinical symptom vector spaces with weighted multi-factor scoring.
- **Output**: Ranked differential probabilities, disease descriptions, severity categories, and matched clinical precautions.

To re-train or extend the model with additional diseases:
```bash
python ml_models/train_model.py
```

---

## 🛡️ Security & Clinical Compliance
- **Authentication**: Role-based JWT access tokens + Twilio OTP 2FA.
- **Data Protection**: Supabase Row-Level Security (RLS) enforcement.
- **Medical Safety**: Built-in automated clinical disclaimers and acute emergency red flag triage on all assessments.

---

## 📄 License
Released under the **MIT License**.
