# 🏥 MediVision AI — Smart Healthcare System

> **AI-Powered Healthcare Platform** with Computer Vision, Disease Prediction, and Intelligent Chatbot

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green)](https://flask.palletsprojects.com)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.9-red)](https://opencv.org)
[![Scikit-learn](https://img.shields.io/badge/Scikit--learn-1.4-orange)](https://scikit-learn.org)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-purple)](https://supabase.com)

---

## 🚀 Features Overview

| Feature | Technology | Status |
|---------|-----------|--------|
| Face Recognition Login | OpenCV + Haar Cascades | ✅ |
| OTP 2FA Authentication | Twilio / Simulated | ✅ |
| AI Disease Prediction | Scikit-learn (GradientBoosting) | ✅ |
| MediBot AI Chatbot | Anthropic Claude API | ✅ |
| Fatigue Detection | OpenCV + EAR | ✅ |
| Posture Analysis | MediaPipe Pose | ✅ |
| Mask Detection | OpenCV + HSV | ✅ |
| Heart Rate Estimation | rPPG via webcam | ✅ |
| Skin Analysis | CIE Lab color analysis | ✅ |
| Smart Dashboard | Chart.js + Real-time | ✅ |
| PDF Prescriptions | ReportLab | ✅ |
| Appointment Booking | Full CRUD + Payment | ✅ |
| Health Reports | Radar + Trend Charts | ✅ |
| Voice Input | Web Speech API | ✅ |

---

## 📁 Project Structure

```
medivision/
├── app.py                          # Flask app + SocketIO entry point
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment config template
├── .env                            # Your environment variables (create from example)
│
├── backend/
│   ├── __init__.py
│   ├── routes/
│   │   ├── auth_routes.py          # Face + OTP login/register
│   │   ├── ai_routes.py            # Disease prediction + MediBot
│   │   ├── vision_routes.py        # All 6 OpenCV vision modules
│   │   ├── dashboard_routes.py     # Dashboard data APIs
│   │   ├── appointment_routes.py   # Doctor booking system
│   │   ├── prescription_routes.py  # PDF prescription generator
│   │   └── payment_routes.py       # Payment processing
│   ├── models/
│   │   └── __init__.py
│   └── utils/
│       └── supabase_client.py      # Supabase DB client
│
├── frontend/
│   ├── templates/
│   │   ├── landing.html            # Marketing landing page
│   │   ├── login.html              # Face ID + OTP login
│   │   ├── register.html           # Multi-step registration
│   │   ├── dashboard.html          # Main health dashboard
│   │   ├── vision.html             # Live vision monitoring
│   │   ├── medibot.html            # AI chatbot interface
│   │   └── health_report.html      # Downloadable health report
│   └── static/
│       ├── css/                    # Additional CSS files
│       ├── js/                     # Additional JS files
│       └── assets/                 # Images, icons
│
├── ml_models/
│   ├── train_model.py              # Model training script
│   ├── disease_model.pkl           # Trained model (auto-generated)
│   └── model_metadata.json         # Symptoms + disease data
│
└── database/
    └── schema.sql                  # Supabase PostgreSQL schema
```

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.10 or higher
- pip package manager
- Node.js (optional, for React frontend)
- Webcam (for vision features)
- Supabase account (free tier works)

### Step 1: Clone and Setup

```bash
# Navigate to project directory
cd medivision

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ **Note:** `dlib` installation may require CMake. Install it first:
> ```bash
> pip install cmake
> pip install dlib
> ```
> 
> On Ubuntu/Debian:
> ```bash
> sudo apt-get install build-essential cmake libboost-all-dev
> ```

### Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials:
nano .env  # or use any text editor
```

**Required environment variables:**
```env
FLASK_SECRET_KEY=your-random-secret-key-here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
JWT_SECRET=your-jwt-secret

# Optional (for real OTP):
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE_NUMBER=+1234567890

# Optional (for AI chatbot):
ANTHROPIC_API_KEY=sk-ant-...
```

### Step 4: Setup Supabase Database

1. Create a free account at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to **SQL Editor**
4. Run the schema:

```bash
# Copy content from database/schema.sql
# Paste into Supabase SQL Editor and click Run
```

5. Copy your project URL and API keys from **Settings → API**

### Step 5: Train the ML Model

```bash
python ml_models/train_model.py
```

Expected output:
```
🏥 Training MediVision Disease Prediction Model...
Training Gradient Boosting Classifier...
✅ Model Accuracy: 94.00%
✅ Cross-Val Score: 93.50% ± 2.10%
✅ Model saved: ml_models/disease_model.pkl
✅ Metadata saved: ml_models/model_metadata.json
🎯 Ready for inference!
```

### Step 6: Run the Application

```bash
python app.py
```

Expected output:
```
╔══════════════════════════════════════════╗
║     MediVision AI - Starting Server     ║
║     http://localhost:5000               ║
╚══════════════════════════════════════════╝
```

Open your browser: **http://localhost:5000**

---

## 🎯 Demo Credentials

If you don't want to set up Supabase immediately, use demo mode:

| Field | Value |
|-------|-------|
| Email | `demo@medivision.ai` |
| Password | `demo123` |
| OTP | `123456` |

The system automatically falls back to demo mode if the database is unavailable.

---

## 🔐 Authentication Flow

```
User → Enter Email →
     ↓                    
     Password Login    
          ↓                    
     Password Check   
               ↓
           OTP Sent (Twilio / Simulated)
               ↓
           Enter 6-digit OTP
               ↓
           JWT Token Generated
               ↓
           Access Dashboard
```

---

## 🧠 AI Disease Prediction

The ML model supports 20 diseases:
- Common Cold, Influenza, COVID-19
- Dengue Fever, Malaria
- Type 2 Diabetes, Hypertension
- Asthma, Pneumonia, Anemia
- Thyroid Disorder, Arthritis
- Heart Disease, Kidney Stones
- Depression, Migraine, GERD
- Gastroenteritis, UTI, Skin Allergy

**Model:** Gradient Boosting Classifier
**Accuracy:** ~94% on test set
**Features:** 65+ unique symptoms
**Output:** Top 3 predictions + probabilities + precautions + health risk score

---

## 👁️ Vision Modules

| Module | Technology | Output |
|--------|-----------|--------|
| Face Detection | Haar Cascades | Face bounding boxes |
| Fatigue Detection | EAR + Eye Cascade | Drowsiness score + alert |
| Posture Analysis | MediaPipe Pose | Shoulder angle + corrections |
| Mask Detection | HSV Color Analysis | Per-face compliance |
| Heart Rate | rPPG (Green channel) | BPM estimate |
| Skin Analysis | CIE Lab Color | Conditions + suggestions |

---

## 🏗️ Architecture

```
Browser ←→ Flask (App Server) ←→ Supabase (PostgreSQL)
               ↕
        OpenCV Vision Engine
        Scikit-learn ML Models
        Anthropic Claude API (MediBot)
        ReportLab (PDF Generation)
        Twilio (OTP SMS)
        SocketIO (Real-time Alerts)
```

---

## 🌐 API Endpoints

### Authentication
- `POST /api/auth/register` — Register with face enrollment
- `POST /api/auth/login/face` — Face recognition login
- `POST /api/auth/login/password` — Password login
- `POST /api/auth/login/otp/verify` — OTP verification
- `POST /api/auth/logout` — Logout

### AI
- `POST /api/ai/predict` — Disease prediction from symptoms
- `GET /api/ai/symptoms/list` — Available symptoms
- `POST /api/ai/medibot/chat` — MediBot chatbot
- `POST /api/ai/health-score` — Compute AI health score

### Vision
- `POST /api/vision/face/detect` — Face detection
- `POST /api/vision/fatigue/detect` — Fatigue analysis
- `POST /api/vision/posture/detect` — Posture analysis
- `POST /api/vision/mask/detect` — Mask compliance
- `POST /api/vision/heartrate/estimate` — Heart rate estimation
- `POST /api/vision/skin/analyze` — Skin analysis

### Appointments
- `GET /api/appointments/doctors` — List doctors
- `POST /api/appointments/book` — Book appointment
- `GET /api/appointments/list` — User appointments
- `POST /api/appointments/cancel/<id>` — Cancel

### Prescriptions
- `GET /api/prescriptions/list` — User prescriptions
- `POST /api/prescriptions/generate-pdf` — Download PDF

---

## 🛠️ Troubleshooting

**Camera not working:**
- Ensure browser has camera permissions
- Use HTTPS in production (camera requires secure context)
- Chrome: Settings → Privacy → Camera

**dlib installation fails:**
```bash
# Ubuntu
sudo apt-get install build-essential cmake
pip install dlib

# Mac
brew install cmake
pip install dlib

# Windows: Download pre-built wheel from:
# https://github.com/jloh02/dlib/releases
```

**MediaPipe issues:**
```bash
pip install mediapipe --upgrade
```

**Model not found:**
```bash
python ml_models/train_model.py
```

---

## 📦 Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Flask | 3.0.0 | Web framework |
| flask-socketio | 5.3.6 | Real-time alerts |
| opencv-python | 4.9.0.80 | Computer vision |
| mediapipe | 0.10.9 | Pose detection |
| scikit-learn | 1.4.0 | ML models |
| supabase | 2.3.0 | Database |
| reportlab | 4.1.0 | PDF generation |
| anthropic | latest | MediBot AI |
| twilio | 8.12.0 | OTP SMS |
| bcrypt | 4.1.2 | Password hashing |
| PyJWT | 2.8.0 | JWT tokens |

---

## 🎓 College Project Information

**Project Title:** AI-Powered Smart Healthcare System with OpenCV Vision + OTP Authentication

**Technologies Used:**
- Backend: Python Flask, SocketIO
- Frontend: HTML5, CSS3 (CSS Variables, Animations), Vanilla JavaScript
- Database: Supabase (PostgreSQL)
- AI/ML: Scikit-learn (GradientBoosting), Anthropic Claude
- Vision: OpenCV 4.9, MediaPipe, rPPG
- Auth: JWT, bcrypt, Twilio OTP
- PDF: ReportLab
- Charts: Chart.js

**Key Innovations:**
1. Hybrid biometric authentication (Face + OTP)
2. Webcam-based heart rate estimation using rPPG
3. Real-time posture correction using MediaPipe
4. AI health risk scoring system
5. Skin analysis using CIE Lab color space

---

## 👨‍💻 Development Notes

- All vision processing happens server-side via base64 image transfer
- ML model auto-trains on first run if .pkl file not found
- Demo mode activates automatically when database is unavailable
- Frontend uses no external CSS framework — all custom
- Fonts: Clash Display (headings) + DM Sans (body)

---

*Built with ❤️ for MediVision AI — Making healthcare intelligent, accessible, and human.*
