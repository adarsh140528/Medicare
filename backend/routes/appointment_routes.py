"""MediVision AI - Appointment Routes — per-user, uses service client to bypass RLS"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid

appointment_bp = Blueprint('appointments', __name__)

def _get_auth_user():
    from backend.routes.auth_routes import get_current_user
    return get_current_user()

@appointment_bp.route('/doctors', methods=['GET'])
def get_doctors():
    """Fetch doctors dynamically from registered users table."""
    try:
        from backend.utils.supabase_client import get_service_client
        supabase = get_service_client()
        res = supabase.table('users').select('*').eq('role', 'doctor').execute()
        doctors_db = res.data or []
        
        docs = []
        # We assign some static default values for fee and availability 
        # since currently the users table doesn't track these professional metrics deeply.
        for idx, user in enumerate(doctors_db):
            docs.append({
                "id": user['id'],
                "name": user['full_name'],
                "specialty": "General Medicine",
                "experience": "10+ years",
                "rating": 4.8,
                "fee": 500 + ((idx % 3) * 100),
                "available": ["09:00", "10:30", "14:00", "15:30", "17:00"]
            })
            
        specialty = request.args.get('specialty')
        if specialty:
            docs = [d for d in docs if specialty.lower() in d['specialty'].lower()]
            
        return jsonify({"success": True, "doctors": docs})
    except Exception as e:
        print(f"[DOCTOR-LIST] Error: {e}")
        return jsonify({"success": False, "error": "Could not fetch doctors."})


@appointment_bp.route('/book', methods=['POST'])
def book_appointment():
    user = _get_auth_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('date') or not data.get('time') or not data.get('doctor_name'):
            return jsonify({"success": False, "error": "Doctor, date, and time are required"}), 400

        # Reject past dates
        try:
            appt_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            if appt_date < datetime.utcnow().date():
                return jsonify({"success": False, "error": "Cannot book an appointment for a past date."}), 400
        except ValueError:
            return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}), 400

        from backend.utils.supabase_client import get_service_client
        supabase = get_service_client()

        record = {
            "patient_id": user['id'],
            "doctor_name": data.get('doctor_name'),
            "specialty": data.get('specialty'),
            "appointment_date": data.get('date'),
            "appointment_time": data.get('time'),
            "reason": data.get('reason', ''),
            "payment_amount": float(data.get('fee', 0)),   # ← fixed column name
            "status": "pending",
            "payment_status": "unpaid"
        }

        result = supabase.table('appointments').insert(record).execute()
        if not result.data:
            return jsonify({"success": False, "error": "Failed to save appointment. Please try again."}), 500

        appointment_id = result.data[0]['id']
        short_id = appointment_id[:8].upper()
        return jsonify({
            "success": True,
            "appointment_id": f"APT-{short_id}",
            "message": f"Appointment confirmed! ID: APT-{short_id}",
            "details": {
                "id": appointment_id,
                "doctor": data.get('doctor_name'),
                "date": data.get('date'),
                "time": data.get('time'),
                "status": "pending"
            }
        })

    except Exception as e:
        print(f"[BOOK-APT] Error: {e}")
        return jsonify({"success": False, "error": f"Could not book appointment. Error: {str(e)}"}), 500


@appointment_bp.route('/list', methods=['GET'])
def list_appointments():
    user = _get_auth_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        from backend.utils.supabase_client import get_service_client
        supabase = get_service_client()
        res = supabase.table('appointments')\
            .select('*').eq('patient_id', user['id'])\
            .order('appointment_date', desc=False).execute()
        return jsonify({"success": True, "appointments": res.data or []})
    except Exception as e:
        print(f"[LIST-APT] {e}")
        return jsonify({"error": "Could not load appointments."}), 500


@appointment_bp.route('/cancel/<appointment_id>', methods=['POST'])
def cancel_appointment(appointment_id):
    user = _get_auth_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        from backend.utils.supabase_client import get_service_client
        supabase = get_service_client()
        result = supabase.table('appointments')\
            .update({"status": "cancelled"})\
            .eq('id', appointment_id)\
            .eq('patient_id', user['id'])\
            .execute()
        if not result.data:
            return jsonify({"success": False, "error": "Appointment not found or already cancelled."}), 404
        return jsonify({"success": True, "message": f"Appointment {appointment_id} cancelled."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@appointment_bp.route('/doctor-list', methods=['GET'])
def doctor_appointments():
    user = _get_auth_user()
    if not user or user.get('role') != 'doctor':
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    try:
        from backend.utils.supabase_client import get_service_client
        supabase = get_service_client()
        # Find appointments by doctor name
        doc_name = user['full_name'].replace('Dr. ', '').strip()
        res = supabase.table('appointments')\
            .select('*').ilike('doctor_name', f'%{doc_name}%')\
            .order('appointment_date', desc=False).execute()
        return jsonify({"success": True, "appointments": res.data or []})
    except Exception as e:
        return jsonify({"error": "Could not load appointments."}), 500

@appointment_bp.route('/accept/<appointment_id>', methods=['POST'])
def accept_appointment(appointment_id):
    user = _get_auth_user()
    if not user or user.get('role') != 'doctor':
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    try:
        from backend.utils.supabase_client import get_service_client
        supabase = get_service_client()
        supabase.table('appointments').update({"status": "confirmed"}).eq('id', appointment_id).execute()
        return jsonify({"success": True, "message": "Appointment accepted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@appointment_bp.route('/mark-paid/<appointment_id>', methods=['POST'])
def mark_paid(appointment_id):
    user = _get_auth_user()
    if not user or user.get('role') != 'doctor':
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    try:
        from backend.utils.supabase_client import get_service_client
        supabase = get_service_client()
        supabase.table('appointments').update({"payment_status": "paid"}).eq('id', appointment_id).execute()
        return jsonify({"success": True, "message": "Payment accepted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
