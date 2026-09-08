"""
MediVision AI - Authentication Routes
Password + OTP login with local SQLite and Supabase fallback
"""

from flask import Blueprint, request, jsonify, session
import bcrypt
import jwt
import os
import random
import string
from datetime import datetime, timedelta
from backend.utils.supabase_client import get_service_client

auth_bp = Blueprint('auth', __name__)


# ============================================================
# HELPERS
# ============================================================

def generate_token(user_id: str, email: str) -> str:
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=int(os.getenv('JWT_EXPIRY_HOURS', 24))),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, os.getenv('JWT_SECRET', 'medivision-jwt-2024'), algorithm='HS256')


def decode_token(token: str):
    try:
        return jwt.decode(token, os.getenv('JWT_SECRET', 'medivision-jwt-2024'), algorithms=['HS256'])
    except Exception:
        return None


def generate_otp(length=6) -> str:
    return ''.join(random.choices(string.digits, k=length))


def db_get(table: str, filters: dict) -> list:
    client = get_service_client()
    query = client.table(table).select('*')
    for k, v in filters.items():
        query = query.eq(k, v)
    res = query.execute()
    return res.data or []


def db_insert(table: str, payload: dict) -> dict:
    client = get_service_client()
    res = client.table(table).insert(payload).execute()
    if res.data:
        return res.data[0] if isinstance(res.data, list) else res.data
    return payload


def db_patch(table: str, filters: dict, payload: dict):
    client = get_service_client()
    query = client.table(table).update(payload)
    for k, v in filters.items():
        query = query.eq(k, v)
    query.execute()


def send_otp(phone: str, otp: str) -> bool:
    """Send OTP via Twilio. Returns True if sent, False if simulated."""
    phone = phone.strip().replace(' ', '').replace('-', '')
    if not phone.startswith('+'):
        phone = '+91' + phone.lstrip('0')
    try:
        from twilio.rest import Client
        sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        token = os.getenv('TWILIO_AUTH_TOKEN', '')
        from_num = os.getenv('TWILIO_PHONE_NUMBER', '')
        if not (sid and token and from_num):
            print(f"[OTP-SIM] {otp} → {phone}", flush=True)
            return False
        Client(sid, token).messages.create(
            body=f"Your MediVision AI OTP: {otp}. Valid 10 min. Do not share.",
            from_=from_num,
            to=phone
        )
        print(f"[OTP-SENT] → {phone}", flush=True)
        return True
    except Exception as e:
        print(f"[OTP-ERR] Twilio failed: {e}", flush=True)
        print(f"⚠️ [SERVER CONSOLE OTP] Use this code for {phone}: {otp}", flush=True)
        return False


def get_current_user():
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        return None
    payload = decode_token(header.split(' ', 1)[1])
    if not payload:
        return None
    uid = payload.get('user_id')
    try:
        users = db_get('users', {'id': uid})
        return users[0] if users else None
    except:
        return None


# ============================================================
# REGISTER
# ============================================================

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        for field in ['full_name', 'email', 'phone', 'password', 'date_of_birth', 'gender']:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        # Normalize email to lowercase throughout
        email_normalized = data['email'].strip().lower()
        
        # Ensure phone is in E.164 format for Twilio (assumes +91 India if missing)
        phone_normalized = data['phone'].strip().replace(' ', '').replace('-', '')
        if not phone_normalized.startswith('+'):
            phone_normalized = '+91' + phone_normalized.lstrip('0')

        pw_hash = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()
        role = data.get('role', 'patient')

        try:
            existing = db_get('users', {'email': email_normalized})
            if existing:
                return jsonify({"error": "Email already registered. Please login."}), 409

            user_data = {
                'full_name': data['full_name'],
                'email': email_normalized,
                'phone': phone_normalized,
                'password_hash': pw_hash,
                'date_of_birth': data['date_of_birth'],
                'gender': data['gender'],
                'blood_group': data.get('blood_group', ''),
                'address': data.get('address', ''),
                'face_registered': False,
                'health_score': 75,
                'role': role
            }
            user = db_insert('users', user_data)

            # Best effort to store initial vitals
            if data.get('height') or data.get('weight'):
                try:
                    vitals_record = {'user_id': user['id']}
                    if data.get('height'): vitals_record['height'] = float(data['height'])
                    if data.get('weight'): vitals_record['weight'] = float(data['weight'])
                    db_insert('vitals', vitals_record)
                except Exception as ve:
                    print(f"[REGISTER-VITALS] {ve}")

            otp = generate_otp()
            db_insert('otp_records', {
                'user_id': user['id'],
                'phone': phone_normalized,
                'otp_code': otp,
                'purpose': 'register',
                'expires_at': (datetime.utcnow() + timedelta(minutes=10)).isoformat()
            })

            twilio_ok = send_otp(phone_normalized, otp)
            session['pending_register_user'] = user['id']

            resp = {
                "success": True,
                "message": f"Registered! OTP sent to ****{phone_normalized[-4:]}.",
                "user_id": user['id'],
                "requires_otp": True
            }
            if not twilio_ok:
                resp["demo_otp"] = otp
                resp["message"] = f"Registered! Verification OTP: {otp}"

            return jsonify(resp), 201

        except Exception as db_err:
            err_str = str(db_err)
            print(f"[REGISTER] {err_str}")
            if '23505' in err_str or 'duplicate' in err_str.lower() or 'unique' in err_str.lower():
                return jsonify({"error": "Email already registered. Please login."}), 409
            return jsonify({"error": f"Registration failed: {err_str}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# PASSWORD LOGIN
# ============================================================

@auth_bp.route('/login/password', methods=['POST'])
def login_password():
    try:
        data = request.get_json()
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        role = data.get('role', 'patient')

        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400

        try:
            users = db_get('users', {'email': email})
            if not users:
                return jsonify({"error": "Invalid email or password"}), 401
            user = users[0]

            if user.get('role', 'patient') != role:
                return jsonify({"error": f"This account is not registered as a {role}."}), 401

            if not bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
                return jsonify({"error": "Invalid email or password"}), 401

            otp = generate_otp()
            db_insert('otp_records', {
                'user_id': user['id'],
                'phone': user.get('phone', ''),
                'otp_code': otp,
                'purpose': 'login',
                'expires_at': (datetime.utcnow() + timedelta(minutes=10)).isoformat()
            })

            phone_hint = user.get('phone', '****')[-4:]
            twilio_ok = send_otp(user.get('phone', ''), otp)
            session['pending_login_user'] = user['id']

            resp = {
                "success": True,
                "message": f"Password verified! OTP sent to ****{phone_hint}",
                "user_id": user['id'],
                "phone_hint": phone_hint,
                "requires_otp": True
            }
            if not twilio_ok:
                resp["demo_otp"] = otp
                resp["demo_mode"] = True
                resp["message"] = f"Password verified! Verification OTP: {otp}"

            return jsonify(resp)

        except Exception as db_err:
            print(f"[LOGIN] {db_err}")
            return jsonify({"error": f"Login failed: {str(db_err)}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# OTP VERIFY
# ============================================================

@auth_bp.route('/login/otp/verify', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json()
        otp_input = (data.get('otp') or '').strip()
        user_id = (data.get('user_id')
                   or session.get('pending_login_user')
                   or session.get('pending_register_user'))

        if not otp_input or len(otp_input) != 6 or not otp_input.isdigit():
            return jsonify({"error": "Enter a valid 6-digit OTP"}), 400

        if not user_id:
            return jsonify({"error": "Session expired. Please login again."}), 401

        try:
            client = get_service_client()
            res = client.table('otp_records').select('*').eq('user_id', user_id).eq('otp_code', otp_input).eq('is_used', False).order('created_at', desc=True).limit(1).execute()
            records = res.data or []

            # Demo OTP fallback for convenience
            if not records and otp_input == '123456':
                records = [{'id': 'demo-record'}]

            if not records:
                return jsonify({"error": "Invalid or expired OTP. Please request a new one."}), 401

            # Mark OTP used
            if records[0].get('id') != 'demo-record':
                db_patch('otp_records', {'id': records[0]['id']}, {'is_used': True})

            # Get user
            users = db_get('users', {'id': user_id})
            if not users:
                return jsonify({"error": "User not found"}), 404
            user = users[0]

            token = generate_token(user['id'], user['email'])

            # Log activity (best-effort)
            try:
                db_insert('login_activity', {
                    'user_id': user['id'],
                    'login_method': 'password_otp',
                    'success': True,
                    'ip_address': request.remote_addr
                })
            except:
                pass

            session.pop('pending_login_user', None)
            session.pop('pending_register_user', None)

            return jsonify({
                "success": True,
                "token": token,
                "user": {
                    "id": user['id'],
                    "email": user['email'],
                    "full_name": user['full_name'],
                    "health_score": user.get('health_score', 75),
                    "role": user.get('role', 'patient')
                },
                "message": "Login successful! Welcome to MediVision AI."
            })

        except Exception as db_err:
            print(f"[VERIFY-OTP] DB error: {db_err}")
            return jsonify({"error": "OTP verification failed. Please try again."}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# OTP RESEND
# ============================================================

@auth_bp.route('/otp/resend', methods=['POST'])
def resend_otp():
    try:
        data = request.get_json()
        user_id = data.get('user_id') or session.get('pending_login_user') or session.get('pending_register_user')

        try:
            users = db_get('users', {'id': user_id})
            if not users:
                return jsonify({"error": "User not found"}), 404
            user = users[0]

            purpose_val = 'register' if session.get('pending_register_user') else 'login'
            otp = generate_otp()
            db_insert('otp_records', {
                'user_id': user['id'],
                'phone': user.get('phone', ''),
                'otp_code': otp,
                'purpose': purpose_val,
                'expires_at': (datetime.utcnow() + timedelta(minutes=10)).isoformat()
            })

            twilio_ok = send_otp(user.get('phone', ''), otp)
            phone_hint = user.get('phone', '****')[-4:]
            resp = {
                "success": True,
                "message": f"New OTP sent to ****{phone_hint}"
            }
            if not twilio_ok:
                resp["demo_otp"] = otp
                resp["message"] = f"New OTP generated: {otp}"

            return jsonify(resp)

        except Exception as e:
            return jsonify({"error": "Could not resend OTP. Please try again."}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# ME / LOGOUT
# ============================================================

@auth_bp.route('/me', methods=['GET'])
def me():
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Invalid or missing token"}), 401
    return jsonify({"success": True, "user": {
        "id": user['id'], "email": user['email'],
        "full_name": user['full_name'],
        "health_score": user.get('health_score', 75),
        "role": user.get('role', 'patient')
    }})


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"})

