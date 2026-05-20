"""MediVision AI - Payment Routes — saves to DB, per-user"""
from flask import Blueprint, request, jsonify
import uuid
from datetime import datetime

payment_bp = Blueprint('payments', __name__)


def _get_auth_user():
    from backend.routes.auth_routes import get_current_user
    return get_current_user()


@payment_bp.route('/initiate', methods=['POST'])
def initiate_payment():
    user = _get_auth_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    data = request.get_json() or {}
    amount = float(data.get('amount', 0))
    if amount <= 0:
        return jsonify({"success": False, "error": "Invalid payment amount"}), 400
    transaction_id = "TXN" + str(uuid.uuid4())[:8].upper()
    return jsonify({
        "success": True,
        "transaction_id": transaction_id,
        "amount": amount,
        "currency": "INR",
        "payment_methods": ["card", "upi", "netbanking", "wallet"],
        "message": "Payment gateway initialized"
    })


@payment_bp.route('/process', methods=['POST'])
def process_payment():
    """Process a payment and persist it to the DB."""
    user = _get_auth_user()
    data = request.get_json() or {}

    receipt_id = "RCP-" + str(uuid.uuid4())[:8].upper()
    transaction_id = data.get('transaction_id') or ("TXN" + str(uuid.uuid4())[:8].upper())

    # Persist to DB if authenticated
    if user:
        try:
            from backend.utils.supabase_client import get_service_client
            supabase = get_service_client()
            supabase.table('payments').insert({
                "user_id": user['id'],
                "appointment_id": data.get('appointment_id'),
                "amount": float(data.get('amount', 0)),
                "currency": "INR",
                "payment_method": data.get('payment_method', 'upi'),
                "transaction_id": transaction_id,
                "status": "success",
                "gateway_response": {"receipt_id": receipt_id},
            }).execute()
            
            if data.get('appointment_id'):
                supabase.table('appointments').update({"payment_status": "paid"}).eq('id', data.get('appointment_id')).execute()
        except Exception as e:
            print(f"[PAYMENT-SAVE] {e}")

    return jsonify({
        "success": True,
        "transaction_id": transaction_id,
        "status": "success",
        "message": "Payment successful! Appointment confirmed.",
        "receipt_id": receipt_id
    })


@payment_bp.route('/history', methods=['GET'])
def payment_history():
    user = _get_auth_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        from backend.utils.supabase_client import get_service_client
        supabase = get_service_client()
        res = supabase.table('payments')\
            .select('*')\
            .eq('user_id', user['id'])\
            .order('created_at', desc=True)\
            .execute()
        payments = res.data or []
        total = sum(float(p.get('amount', 0)) for p in payments if p.get('status') == 'success')
        return jsonify({"success": True, "payments": payments, "total_spent": round(total, 2)})
    except Exception as e:
        print(f"[PAYMENTS] {e}")
        return jsonify({"success": True, "payments": [], "total_spent": 0})
