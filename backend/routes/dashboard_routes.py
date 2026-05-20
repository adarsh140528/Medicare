"""
MediVision AI - Dashboard Routes
Returns real per-user data — uses service client to bypass RLS.
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid

dashboard_bp = Blueprint('dashboard', __name__)


def _get_auth_user():
    from backend.routes.auth_routes import get_current_user
    return get_current_user()


@dashboard_bp.route('/overview', methods=['GET'])
def get_overview():
    current_user = _get_auth_user()
    if not current_user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        from backend.utils.supabase_client import get_service_client
        supabase = get_service_client()
        uid = current_user['id']

        def safe_query(fn):
            """Run a supabase query; return empty list on any error."""
            try:
                result = fn()
                return result.data or []
            except Exception as qe:
                print(f"[DASHBOARD-QUERY] {qe}")
                return []

        appointments = safe_query(lambda: supabase.table('appointments')
            .select('*').eq('patient_id', uid)
            .order('appointment_date', desc=False).limit(10).execute())

        vitals_history = safe_query(lambda: supabase.table('vitals')
            .select('*').eq('user_id', uid)
            .order('recorded_at', desc=True).limit(7).execute())

        recent_predictions = safe_query(lambda: supabase.table('disease_predictions')
            .select('*').eq('user_id', uid)
            .order('created_at', desc=True).limit(5).execute())

        notifications = safe_query(lambda: supabase.table('notifications')
            .select('*').eq('user_id', uid)
            .order('created_at', desc=True).limit(10).execute())

        prescriptions = safe_query(lambda: supabase.table('prescriptions')
            .select('id').eq('patient_id', uid).execute())

        today_str = str(datetime.utcnow().date())
        unread_alerts = len([n for n in notifications if not n.get('is_read')])
        upcoming = [a for a in appointments if a.get('status') != 'cancelled']

        return jsonify({"success": True, "data": {
            "user": {
                "full_name": current_user.get('full_name', 'Patient'),
                "health_score": current_user.get('health_score', 75),
                "email": current_user.get('email')
            },
            "stats": {
                "appointments_today": len([a for a in appointments if str(a.get('appointment_date', '')) == today_str]),
                "total_appointments": len(upcoming),
                "prescriptions": len(prescriptions),
                "total_predictions": len(recent_predictions),
                "alerts": unread_alerts,
                "streak_days": 0
            },
            "appointments": appointments,
            "vitals_history": vitals_history,
            "recent_predictions": recent_predictions,
            "notifications": notifications
        }})

    except Exception as e:
        print(f"[DASHBOARD] Error: {e}")
        return jsonify({"success": False, "error": "Failed to load dashboard data. Please try again."}), 500


@dashboard_bp.route('/vitals', methods=['POST'])
def save_vitals():
    current_user = _get_auth_user()
    if not current_user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        from backend.utils.supabase_client import get_service_client
        supabase = get_service_client()

        record = {
            "user_id": current_user['id'],
            "recorded_at": datetime.utcnow().isoformat()
        }
        if data.get('heart_rate'): record['heart_rate'] = int(data['heart_rate'])
        if data.get('bp_systolic'): record['blood_pressure_sys'] = int(data['bp_systolic'])
        if data.get('bp_diastolic'): record['blood_pressure_dia'] = int(data['bp_diastolic'])
        if data.get('oxygen_saturation'): record['oxygen_saturation'] = int(data['oxygen_saturation'])
        if data.get('weight'): record['weight'] = float(data['weight'])
        if data.get('temperature'): record['temperature'] = float(data['temperature'])

        supabase.table('vitals').insert(record).execute()
        return jsonify({"success": True, "message": "Vitals saved successfully!"})

    except Exception as e:
        print(f"[VITALS-SAVE] {e}")
        return jsonify({"error": f"Could not save vitals. Error: {str(e)}"}), 500


@dashboard_bp.route('/health-score', methods=['GET'])
def get_health_score():
    current_user = _get_auth_user()
    if not current_user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    score = current_user.get('health_score', 75)
    return jsonify({"success": True, "health_score": score, "risk_level": "Low" if score >= 70 else "Moderate", "trend": "stable"})
