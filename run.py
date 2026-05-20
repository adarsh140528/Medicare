#!/usr/bin/env python3
"""
MediVision AI - Quick Start Script
Run: python run.py
"""
import os
import sys
import subprocess

_DIR = os.path.dirname(os.path.abspath(__file__))

def check_model():
    model_path = os.path.join(_DIR, 'ml_models', 'disease_model.pkl')
    if not os.path.exists(model_path):
        print("Training ML model (first time setup)...")
        subprocess.run([sys.executable, os.path.join(_DIR, 'ml_models', 'train_model.py')], check=True)
        print("Model trained!\n")

def create_env():
    env_path = os.path.join(_DIR, '.env')
    example_path = os.path.join(_DIR, '.env.example')
    if not os.path.exists(env_path) and os.path.exists(example_path):
        import shutil
        shutil.copy(example_path, env_path)
        print("Created .env from template. Edit it with your credentials.\n")

if __name__ == '__main__':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print("""
==================================================
         MediVision AI - Quick Start
   AI-Powered Smart Healthcare System
==================================================
""")
    create_env()
    check_model()
    
    print("🚀 Starting MediVision AI server...")
    print("📍 Open http://localhost:5000 in your browser")
    print("─" * 50)
    
    from app import socketio, app
    port = int(os.getenv('FLASK_PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
