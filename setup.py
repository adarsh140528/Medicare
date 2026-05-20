#!/usr/bin/env python3
"""
MediVision AI — Setup & Verification Script
Run: python setup.py
This script:
  1. Checks Python version
  2. Installs dependencies (with fallbacks for hard packages)
  3. Creates .env from template
  4. Trains the ML model
  5. Verifies everything works
  6. Launches the server
"""

import sys
import os
import subprocess
import shutil

RESET  = '\033[0m'
BOLD   = '\033[1m'
GREEN  = '\033[92m'
YELLOW = '\033[93m'
RED    = '\033[91m'
CYAN   = '\033[96m'
TEAL   = '\033[36m'

def log(emoji, msg, color=RESET):
    print(f"{color}{emoji}  {msg}{RESET}")

def header(title):
    print(f"\n{TEAL}{BOLD}{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}{RESET}\n")

def check_python():
    header("Checking Python Version")
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 9):
        log("❌", f"Python 3.9+ required. You have {v.major}.{v.minor}", RED)
        sys.exit(1)
    log("✅", f"Python {v.major}.{v.minor}.{v.micro} — OK", GREEN)

def install_packages():
    header("Installing Dependencies")
    
    # Core packages (easy to install)
    core_packages = [
        "flask==3.0.0",
        "flask-cors==4.0.0", 
        "flask-socketio==5.3.6",
        "python-dotenv==1.0.0",
        "scikit-learn==1.4.0",
        "numpy==1.26.3",
        "pandas==2.1.4",
        "Pillow==10.2.0",
        "scipy==1.12.0",
        "joblib==1.3.2",
        "reportlab==4.1.0",
        "bcrypt==4.1.2",
        "PyJWT==2.8.0",
        "eventlet==0.35.1",
        "requests==2.31.0",
        "matplotlib==3.8.2",
    ]
    
    # Vision packages (may need system deps)
    vision_packages = [
        "opencv-python==4.9.0.80",
        "mediapipe==0.10.9",
    ]
    
    # Optional packages
    optional_packages = [
        "supabase==2.3.0",
        "twilio==8.12.0",
        "anthropic",
    ]
    
    log("📦", "Installing core packages...", CYAN)
    for pkg in core_packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])
            log("  ✓", pkg.split("==")[0], GREEN)
        except subprocess.CalledProcessError:
            log("  ⚠️", f"Failed: {pkg}", YELLOW)
    
    log("👁️", "Installing vision packages...", CYAN)
    for pkg in vision_packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])
            log("  ✓", pkg.split("==")[0], GREEN)
        except subprocess.CalledProcessError:
            log("  ⚠️", f"Failed: {pkg} — some vision features may not work", YELLOW)
    
    log("🔌", "Installing optional packages...", CYAN)
    for pkg in optional_packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])
            log("  ✓", pkg.split("==")[0], GREEN)
        except:
            log("  ℹ️", f"{pkg.split('==')[0]} not installed — demo mode will be used", YELLOW)
    
    # dlib (special case)
    log("🔧", "Attempting dlib install (optional, may require cmake)...", CYAN)
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "dlib", "-q"], 
                              stderr=subprocess.DEVNULL)
        log("  ✓", "dlib", GREEN)
    except:
        log("  ℹ️", "dlib skipped — face detection will use Haar cascades (still works!)", YELLOW)

def setup_env():
    header("Setting Up Environment")
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            shutil.copy('.env.example', '.env')
            log("✅", "Created .env from template", GREEN)
        else:
            with open('.env', 'w') as f:
                f.write("FLASK_SECRET_KEY=medivision-dev-secret-2024\n")
                f.write("FLASK_ENV=development\n")
                f.write("FLASK_PORT=5000\n")
                f.write("JWT_SECRET=medivision-jwt-2024\n")
            log("✅", "Created minimal .env file", GREEN)
    else:
        log("ℹ️", ".env already exists — skipping", YELLOW)
    
    log("💡", "Edit .env to add Supabase, Twilio, and Anthropic credentials", CYAN)

def train_model():
    header("Training ML Model")
    if os.path.exists('ml_models/disease_model.pkl'):
        log("ℹ️", "Model already trained — skipping (delete disease_model.pkl to retrain)", YELLOW)
        return
    
    log("🧠", "Training Gradient Boosting disease prediction model...", CYAN)
    try:
        result = subprocess.run(
            [sys.executable, 'ml_models/train_model.py'],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            log("✅", "Model trained successfully!", GREEN)
            # Show accuracy from output
            for line in result.stdout.split('\n'):
                if 'Accuracy' in line or 'Cross-Val' in line:
                    log("  📊", line.strip(), GREEN)
        else:
            log("⚠️", "Model training had warnings — may still work", YELLOW)
            print(result.stderr[:500])
    except subprocess.TimeoutExpired:
        log("⚠️", "Training timed out — will retry on server start", YELLOW)
    except Exception as e:
        log("⚠️", f"Training error: {e} — demo mode will be used", YELLOW)

def verify_imports():
    header("Verifying Critical Imports")
    checks = [
        ("flask", "Flask web server"),
        ("flask_socketio", "Real-time WebSocket"),
        ("sklearn", "Scikit-learn ML"),
        ("numpy", "NumPy arrays"),
        ("cv2", "OpenCV vision"),
        ("reportlab", "PDF generation"),
        ("jwt", "JWT authentication"),
        ("bcrypt", "Password hashing"),
    ]
    
    all_ok = True
    for module, desc in checks:
        try:
            __import__(module)
            log(f"  ✓", f"{desc} ({module})", GREEN)
        except ImportError:
            log(f"  ⚠️", f"{desc} ({module}) — NOT installed", YELLOW)
            if module in ('flask', 'sklearn', 'numpy'):
                all_ok = False
    
    optional_checks = [
        ("mediapipe", "MediaPipe pose detection"),
        ("supabase", "Supabase database"),
        ("anthropic", "Claude AI (MediBot)"),
        ("twilio", "Twilio OTP SMS"),
    ]
    
    print()
    for module, desc in optional_checks:
        try:
            __import__(module)
            log(f"  ✓", f"{desc} ({module})", GREEN)
        except ImportError:
            log(f"  ○", f"{desc} — optional, demo mode available", YELLOW)
    
    return all_ok

def create_dirs():
    """Ensure all required directories exist"""
    dirs = ['ml_models', 'backend/routes', 'backend/utils', 'backend/models',
            'frontend/templates', 'frontend/static/css', 'frontend/static/js',
            'frontend/static/assets', 'database']
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def print_startup_info():
    header("MediVision AI — Ready to Launch!")
    print(f"""{TEAL}
  ╔══════════════════════════════════════════════════╗
  ║         🏥 MediVision AI — Launch Info          ║
  ╠══════════════════════════════════════════════════╣
  ║                                                  ║
  ║  🌐 Main App:    http://localhost:5000           ║
  ║  🎯 Showcase:    http://localhost:5000/showcase  ║
  ║  📊 Dashboard:   http://localhost:5000/dashboard ║
  ║  👁️ Vision:      http://localhost:5000/vision    ║
  ║  🤖 MediBot:     http://localhost:5000/medibot   ║
  ║                                                  ║
  ╚══════════════════════════════════════════════════╝
{RESET}""")

def launch_server():
    header("Launching MediVision AI Server")
    log("🚀", "Starting server on http://localhost:5000", GREEN)
    log("⏹️", "Press Ctrl+C to stop", YELLOW)
    print()
    
    try:
        from app import socketio, app
        port = int(os.getenv('FLASK_PORT', 5000))
        socketio.run(app, host='0.0.0.0', port=port, debug=False)
    except ImportError as e:
        log("❌", f"Import error: {e}", RED)
        log("💡", "Try: pip install flask flask-socketio eventlet", YELLOW)


if __name__ == '__main__':
    print(f"""{TEAL}{BOLD}
╔══════════════════════════════════════════════════════╗
║     🏥 MediVision AI — Setup & Launch Script        ║
║     AI-Powered Smart Healthcare System              ║
╚══════════════════════════════════════════════════════╝
{RESET}""")
    
    args = sys.argv[1:]
    
    if '--install' in args or len(args) == 0:
        check_python()
        create_dirs()
        install_packages()
        setup_env()
        train_model()
        ok = verify_imports()
        print_startup_info()
        
        if ok:
            launch_server()
        else:
            log("⚠️", "Some core packages missing. Run: pip install -r requirements.txt", YELLOW)
    
    elif '--train' in args:
        train_model()
    
    elif '--verify' in args:
        verify_imports()
    
    elif '--run' in args:
        setup_env()
        if not os.path.exists('ml_models/disease_model.pkl'):
            train_model()
        print_startup_info()
        launch_server()
    
    else:
        print("Usage:")
        print("  python setup.py           — Full setup + launch")
        print("  python setup.py --run     — Just run (skip install)")
        print("  python setup.py --train   — Retrain ML model")
        print("  python setup.py --verify  — Check installations")
