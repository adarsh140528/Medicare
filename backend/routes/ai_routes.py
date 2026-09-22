"""
MediVision AI - AI/ML Routes
Disease prediction + MediBot chatbot
"""

from flask import Blueprint, request, jsonify
import json
import os
import joblib
import numpy as np
from datetime import datetime

ai_bp = Blueprint('ai', __name__)

# Absolute path to project root — so model loads regardless of working directory
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load ML model lazily
_model = None
_metadata = None

def get_model():
    global _model, _metadata
    if _model is None:
        try:
            model_path = os.path.join(_BASE_DIR, 'ml_models', 'disease_model.pkl')
            meta_path  = os.path.join(_BASE_DIR, 'ml_models', 'model_metadata.json')
            _model = joblib.load(model_path)
            with open(meta_path) as f:
                _metadata = json.load(f)
        except:
            # Auto-train if model doesn't exist
            from ml_models.train_model import train_model
            _model, _metadata = train_model()
    return _model, _metadata


# ============================================================
# DISEASE PREDICTION
# ============================================================

@ai_bp.route('/predict', methods=['POST'])
def predict_disease():
    """Predict diseases from symptoms and persist to Supabase/DB"""
    try:
        data = request.get_json() or {}
        symptoms = data.get('symptoms', [])
        user_profile = data.get('user_profile', {})
        
        if not symptoms:
            return jsonify({"error": "Please provide at least one symptom"}), 400
        
        model, metadata = get_model()
        
        from ml_models.train_model import predict_disease as ml_predict, compute_health_score
        result = ml_predict(symptoms, model, metadata)
        
        # Compute health score
        health_score = compute_health_score({
            'age': user_profile.get('age', 30),
            'bmi': user_profile.get('bmi', 22),
            'recent_diseases': [r['disease'] for r in result['predictions'][:1]]
        })
        
        result['health_score'] = health_score
        result['recommendations'] = get_health_recommendations(health_score, user_profile)
        result['timestamp'] = datetime.utcnow().isoformat()
        
        # Resolve user ID from JWT header or payload
        from backend.routes.auth_routes import get_current_user
        from backend.utils.supabase_client import get_service_client
        
        auth_user = get_current_user()
        user_id = data.get('user_id') or (auth_user['id'] if auth_user else None)
        
        if user_id:
            try:
                supabase = get_service_client()
                top_disease_name = result['predictions'][0]['disease'] if result['predictions'] else 'General Assessment'
                confidence_val = (result['predictions'][0]['probability'] / 100.0) if result['predictions'] else 0.5

                # 1. Save prediction record
                supabase.table('disease_predictions').insert({
                    'user_id': user_id,
                    'symptoms': symptoms,
                    'predictions': result['predictions'],
                    'top_disease': top_disease_name,
                    'confidence': confidence_val,
                    'health_risk_score': result.get('health_risk_score', 30),
                    'recommendations': result.get('recommendations', [])
                }).execute()

                # 2. Update user health score in users table
                supabase.table('users').update({
                    'health_score': health_score
                }).eq('id', user_id).execute()

                # 3. Add clinical notification
                supabase.table('notifications').insert({
                    'user_id': user_id,
                    'title': 'AI Symptom Assessment Completed',
                    'message': f'Differential assessment completed. Top indication: {top_disease_name}. Health score: {health_score}/100.',
                    'type': 'clinical_alert',
                    'is_read': False
                }).execute()

            except Exception as db_e:
                print(f"[PREDICTION-SAVE-ERROR] {db_e}")
        
        return jsonify({"success": True, "result": result})
        
    except Exception as e:
        print(f"[PREDICT ERROR] {e}")
        return jsonify({"error": str(e)}), 500


@ai_bp.route('/symptoms/list', methods=['GET'])
def get_symptoms():
    """Get all available symptoms for autocomplete"""
    try:
        _, metadata = get_model()
        return jsonify({"success": True, "symptoms": metadata['symptoms']})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ai_bp.route('/health-score', methods=['POST'])
def health_score_endpoint():
    """Compute AI health score"""
    try:
        data = request.get_json() or {}
        from ml_models.train_model import compute_health_score as ml_score
        score = ml_score(data)
        
        risk_level = "Low" if score >= 70 else "Medium" if score >= 40 else "High"
        
        return jsonify({
            "success": True,
            "health_score": score,
            "risk_level": risk_level,
            "recommendations": get_health_recommendations(score, data)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_health_recommendations(score: int, profile: dict) -> list:
    recs = []
    if score < 40:
        recs.extend(["Immediate medical consultation recommended", "Monitor vital signs daily"])
    elif score < 70:
        recs.extend(["Schedule a health checkup", "Improve diet and exercise routine"])
    else:
        recs.extend(["Maintain your healthy lifestyle", "Annual health checkup recommended"])
    
    if profile.get('bmi', 22) > 25:
        recs.append("Consider weight management program")
    if profile.get('age', 30) > 45:
        recs.append("Regular cardiac and diabetes screening recommended")
    
    return recs


# ============================================================
# MEDIBOT CHATBOT
# ============================================================

MEDIBOT_SYSTEM_PROMPT = """You are MediBot 🤖, an expert AI health assistant for MediVision AI platform.
You provide helpful, accurate, and empathetic healthcare information.

Guidelines:
- Give clear, concise health advice and information
- Suggest precautions and when to see a doctor
- Never diagnose definitively - always recommend professional consultation
- Be warm, supportive, and encouraging
- For emergencies, always direct to emergency services
- Provide evidence-based information
- Format responses with bullet points when listing precautions or steps
- Keep responses focused and practical (max 150 words)

You can help with:
- Symptom information and possible causes
- General health advice and wellness tips  
- Medication general information (not prescribing)
- Diet and nutrition guidance
- Mental health support and resources
- Preventive healthcare advice
"""


@ai_bp.route('/medibot/chat', methods=['POST'])
def medibot_chat():
    """Clinical AI Assistant chat endpoint with database persistence in Supabase/SQLite"""
    try:
        data = request.get_json() or {}
        message = data.get('message', '').strip()
        history = data.get('history', [])
        
        if not message:
            return jsonify({"error": "Message required"}), 400
        
        from backend.routes.auth_routes import get_current_user
        from backend.utils.supabase_client import get_service_client
        
        auth_user = get_current_user()
        user_id = data.get('user_id') or (auth_user['id'] if auth_user else None)
        supabase = get_service_client()

        # If history wasn't provided by client, load recent messages from DB
        if not history and user_id:
            try:
                res = supabase.table('chat_history').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(8).execute()
                db_msgs = res.data or []
                db_msgs.reverse()
                history = [{"role": m.get('role', 'user'), "content": m.get('message', '')} for m in db_msgs]
            except Exception as he:
                print(f"[CHAT-HISTORY-LOAD] {he}")
        
        from backend.services.ai_bot_service import generate_clinical_response
        bot_response = generate_clinical_response(message, history)

        # Store both user message and assistant reply to chat_history table in Supabase/DB
        if user_id:
            try:
                supabase.table('chat_history').insert([
                    {
                        'user_id': user_id,
                        'role': 'user',
                        'message': message,
                        'created_at': datetime.utcnow().isoformat()
                    },
                    {
                        'user_id': user_id,
                        'role': 'assistant',
                        'message': bot_response,
                        'created_at': datetime.utcnow().isoformat()
                    }
                ]).execute()
            except Exception as se:
                print(f"[CHAT-HISTORY-SAVE] {se}")
        
        return jsonify({
            "success": True,
            "response": bot_response,
            "source": "clinical_ai"
        })
            
    except Exception as e:
        print(f"[MEDIBOT ERROR] {e}")
        return jsonify({"error": "An error occurred while generating clinical response."}), 500


@ai_bp.route('/medibot/history', methods=['GET'])
def get_chat_history():
    """Retrieve persistent conversation history for authenticated user"""
    from backend.routes.auth_routes import get_current_user
    from backend.utils.supabase_client import get_service_client
    
    auth_user = get_current_user()
    if not auth_user:
        return jsonify({"success": True, "messages": []})
    
    try:
        supabase = get_service_client()
        res = supabase.table('chat_history').select('*').eq('user_id', auth_user['id']).order('created_at', desc=False).limit(50).execute()
        messages = res.data or []
        return jsonify({"success": True, "messages": messages})
    except Exception as e:
        print(f"[CHAT-HISTORY-FETCH] {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@ai_bp.route('/medibot/clear', methods=['POST'])
def clear_chat_history():
    """Clear chat conversation history for authenticated user"""
    from backend.routes.auth_routes import get_current_user
    from backend.utils.supabase_client import get_service_client
    
    auth_user = get_current_user()
    if not auth_user:
        return jsonify({"success": True, "message": "Cleared session"})
    
    try:
        supabase = get_service_client()
        supabase.table('chat_history').delete().eq('user_id', auth_user['id']).execute()
        return jsonify({"success": True, "message": "Chat history cleared successfully."})
    except Exception as e:
        print(f"[CHAT-HISTORY-CLEAR] {e}")
        return jsonify({"success": False, "error": str(e)}), 500



