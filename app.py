"""
MediVision AI - Main Flask Application
Production-grade healthcare AI system
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv

load_dotenv()

# Initialize Flask
app = Flask(
    __name__,
    template_folder='frontend/templates',
    static_folder='frontend/static'
)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'medivision-secret-2024')

# Session cookie must be Lax (not Strict) so the browser sends it on same-origin
# fetch() calls (e.g. login → OTP verify). Without this, session.get('pending_login_user')
# is always None and OTP verification always fails with "Session expired".
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set True in production with HTTPS

# CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# SocketIO for real-time vision alerts
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ============================================================
# Register Blueprints
# ============================================================
from backend.routes.auth_routes import auth_bp
from backend.routes.dashboard_routes import dashboard_bp
from backend.routes.ai_routes import ai_bp
from backend.routes.appointment_routes import appointment_bp
from backend.routes.vision_routes import vision_bp
from backend.routes.prescription_routes import prescription_bp
from backend.routes.payment_routes import payment_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
app.register_blueprint(ai_bp, url_prefix='/api/ai')
app.register_blueprint(appointment_bp, url_prefix='/api/appointments')
app.register_blueprint(vision_bp, url_prefix='/api/vision')
app.register_blueprint(prescription_bp, url_prefix='/api/prescriptions')
app.register_blueprint(payment_bp, url_prefix='/api/payments')

# ============================================================
# Frontend Routes
# ============================================================
from flask import render_template, redirect, url_for

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/doctor-dashboard')
def doctor_dashboard():
    return render_template('doctor_dashboard.html')

@app.route('/vision')
def vision():
    return render_template('vision.html')

@app.route('/ai-predict')
def ai_predict():
    return render_template('ai_predict.html')

@app.route('/medibot')
def medibot():
    return render_template('medibot.html')

@app.route('/appointments')
def appointments():
    return render_template('appointments.html')

@app.route('/prescriptions')
def prescriptions():
    return render_template('prescriptions.html')

@app.route('/health-report')
def health_report():
    return render_template('health_report.html')



# ============================================================
# SocketIO Events for Vision Alerts
# ============================================================
@socketio.on('connect')
def handle_connect():
    from flask import request as _req
    print(f'Client connected: {_req.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('vision_alert')
def handle_vision_alert(data):
    socketio.emit('alert_broadcast', data)

# ============================================================
# Run
# ============================================================
if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    print(f"""
╔══════════════════════════════════════════╗
║     MediVision AI - Starting Server     ║
║     http://localhost:{port}                ║
╚══════════════════════════════════════════╝
    """)
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
