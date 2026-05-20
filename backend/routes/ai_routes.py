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
    """Predict diseases from symptoms"""
    try:
        data = request.get_json()
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
        
        # Save prediction to DB (must use service client — anon key blocked by RLS)
        try:
            from backend.utils.supabase_client import get_service_client
            supabase = get_service_client()
            user_id = data.get('user_id')
            if user_id:
                supabase.table('disease_predictions').insert({
                    'user_id': user_id,
                    'symptoms': symptoms,
                    'predictions': result['predictions'],
                    'top_disease': result['predictions'][0]['disease'] if result['predictions'] else None,
                    'confidence': result['predictions'][0]['probability'] / 100 if result['predictions'] else None,
                    'health_risk_score': result['health_risk_score']
                }).execute()
        except:
            pass
        
        return jsonify({"success": True, "result": result})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ai_bp.route('/symptoms/list', methods=['GET'])
def get_symptoms():
    """Get all available symptoms for autocomplete"""
    try:
        _, metadata = get_model()
        return jsonify({"symptoms": metadata['symptoms']})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ai_bp.route('/health-score', methods=['POST'])
def health_score_endpoint():
    """Compute AI health score"""
    try:
        data = request.get_json()
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
    """MediBot AI chat endpoint"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        history = data.get('history', [])
        
        if not message:
            return jsonify({"error": "Message required"}), 400
        

        # Try dynamic g4f API (Free dynamic LLM)
        try:
            from g4f.client import Client
            
            formatted_history = []
            for h in history[-6:]:  # Last 6 messages for context
                role = "assistant" if h['role'] == "assistant" else "user"
                formatted_history.append({"role": role, "content": h['content']})
            
            messages = [{"role": "system", "content": MEDIBOT_SYSTEM_PROMPT}] + formatted_history + [{"role": "user", "content": message}]
            
            client = Client()
            response = client.chat.completions.create(
                model="",
                messages=messages
            )
            
            bot_response = response.choices[0].message.content
            
            return jsonify({
                "success": True,
                "response": bot_response,
                "source": "ai"
            })
            
        except Exception as api_err:
            print(f"[MEDIBOT API ERROR] {api_err}")
            return jsonify({"error": "Failed to generate AI response. Please try again."}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


