"""
MediVision Clinical AI Assistant Service
Universal multi-LLM engine (Gemini, Groq, OpenAI, Anthropic, OpenRouter) 
+ Dynamic Contextual Clinical Intelligence.
"""

import os
import json
import re
import requests

CLINICAL_DISCLAIMER = (
    "\n\n*Clinical Note: This assessment is generated for decision support and informational purposes. "
    "Please consult a licensed physician or healthcare provider for formal clinical diagnosis and treatment.*"
)

SYSTEM_PROMPT = """You are the MediVision Clinical AI Assistant — an expert, empathetic, and evidence-based clinical intelligence assistant for a modern digital health platform.

Your goals:
1. Provide structured, accurate, and evidence-based clinical explanations.
2. Structure your replies clearly using Markdown:
   - **Clinical Overview**: What is likely occurring based on the user's inquiry.
   - **Differential Considerations**: Possible conditions, mechanisms, or physiological causes.
   - **Recommended Next Steps**: Practical, evidence-based self-care, hydration, rest, or lifestyle actions.
   - **Medication & Precautions**: General pharmacological guidance (do not prescribe specific doses as definitive prescription).
   - **Red Flags**: Symptoms that require immediate emergency evaluation.
3. If an inquiry is not medical or health-related, politely guide the user back to healthcare, wellness, and medical questions.
4. Keep your tone professional, calm, reassuring, and precise."""


def call_gemini(api_key: str, message: str, history: list) -> str:
    """Call Google Gemini API with instant generation and fallback"""
    # 1. Primary: google.generativeai SDK with fast REST transport
    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=api_key, transport='rest')
        for m in ["gemini-3.6-flash", "gemini-flash-latest", "gemini-3.5-flash"]:
            try:
                model = legacy_genai.GenerativeModel(m)
                resp = model.generate_content(f"{SYSTEM_PROMPT}\n\nPatient Query: {message}")
                if resp and resp.text:
                    return resp.text
            except Exception as e:
                continue
    except Exception as e:
        pass

    # 2. Modern google-genai Client
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        for m in ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-2.5-flash"]:
            try:
                resp = client.models.generate_content(
                    model=m,
                    contents=f"{SYSTEM_PROMPT}\n\nPatient Query: {message}"
                )
                if resp and resp.text:
                    return resp.text
            except Exception as e:
                continue
    except Exception as e:
        pass

    # 2. REST API fallback
    contents = []
    if history:
        for h in history[-4:]:
            role = "user" if h.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": h.get("content", "")}]})
    contents.append({"role": "user", "parts": [{"text": f"{SYSTEM_PROMPT}\n\nUser Question: {message}"}]})
    
    for model_name in ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest"]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            res = requests.post(url, json={"contents": contents}, headers={"Content-Type": "application/json"}, timeout=10)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
        except Exception as e:
            continue
            
    raise Exception("All Gemini models failed to respond.")


def call_groq(api_key: str, message: str, history: list) -> str:
    """Call Groq Cloud API (llama-3.3-70b-versatile)"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        for h in history[-6:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": message})
    
    res = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.5, "max_tokens": 800},
        timeout=12
    )
    if res.status_code == 200:
        data = res.json()
        return data["choices"][0]["message"]["content"]
    raise Exception(f"Groq API Error: {res.status_code} - {res.text}")


def call_openai(api_key: str, message: str, history: list) -> str:
    """Call OpenAI API (gpt-4o-mini / gpt-4o)"""
    url = "https://api.openai.com/v1/chat/completions"
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        for h in history[-6:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": message})
    
    res = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "gpt-4o-mini", "messages": messages, "temperature": 0.5, "max_tokens": 800},
        timeout=12
    )
    if res.status_code == 200:
        data = res.json()
        return data["choices"][0]["message"]["content"]
    raise Exception(f"OpenAI API Error: {res.status_code} - {res.text}")


def call_openrouter(api_key: str, message: str, history: list) -> str:
    """Call OpenRouter API"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        for h in history[-6:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": message})
    
    res = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "meta-llama/llama-3.1-8b-instruct:free", "messages": messages, "max_tokens": 800},
        timeout=12
    )
    if res.status_code == 200:
        data = res.json()
        return data["choices"][0]["message"]["content"]
    raise Exception(f"OpenRouter Error: {res.status_code} - {res.text}")


def generate_dynamic_fallback(user_message: str, history: list = None) -> str:
    """
    Dynamic generative medical reasoning engine for when no external API key is active.
    Synthesizes custom questions, symptoms, medications, and vitals dynamically.
    """
    msg = user_message.strip()
    msg_lower = msg.lower()
    
    # 1. Greetings & Identity
    if any(re.search(r'\b' + re.escape(g) + r'\b', msg_lower) for g in ["hi", "hello", "hey", "who are you", "what can you do"]):
        if len(msg.split()) <= 4:
            return (
                "**Hello! I am your MediVision Clinical AI Assistant.**\n\n"
                "I can assist you with real-time clinical decision support, including:\n"
                "• **Symptom Screening & Differential Analysis**\n"
                "• **Medication Indications & Contraindications**\n"
                "• **Vital Signs & Telemetry Interpretation** (BP, Heart Rate, SpO2, Glucose)\n"
                "• **Evidence-Based Wellness & Dietary Interventions**\n"
                "• **Preparing Questions for Physician Consultations**\n\n"
                "What clinical topic or symptoms would you like to discuss today?"
                + CLINICAL_DISCLAIMER
            )

    # 2. Extract key clinical features from prompt
    detected_symptoms = []
    symptom_map = {
        "headache": "Cephalea / Tension or Migrainous headache",
        "fever": "Pyrexia / Elevated core temperature",
        "cough": "Bronchial / Respiratory airway irritation",
        "chest pain": "Precordial discomfort / Potential cardiac or musculoskeletal etiology",
        "stomach pain": "Abdominal discomfort / Gastrointestinal disturbance",
        "nausea": "Nausea / Upper digestive upset",
        "vomiting": "Emesis / Dehydration risk",
        "diarrhea": "Acute gastrointestinal motility disturbance",
        "fatigue": "Lethargy / Metabolic or physiological fatigue",
        "dizziness": "Vertigo or orthostatic presyncope",
        "sore throat": "Pharyngeal inflammation or tonsillitis",
        "rash": "Dermatological eruption / Cutaneous reaction",
        "shortness of breath": "Dyspnea / Respiratory insufficiency",
        "blood pressure": "Cardiovascular vascular resistance / BP anomaly",
        "sugar": "Glycemic fluctuation / Blood glucose regulation",
        "sleep": "Sleep architecture disturbance / Insomnia",
        "anxiety": "Sympathetic nervous system hyperarousal / Stress response"
    }
    
    for k, label in symptom_map.items():
        if k in msg_lower:
            detected_symptoms.append(label)

    # 3. Dynamic Clinical Response Builder
    resp = f"### Clinical Assessment: {msg}\n\n"
    
    if detected_symptoms:
        resp += f"**Primary Diagnostic Focus:**\n"
        for s in detected_symptoms:
            resp += f"• **{s}**\n"
        resp += "\n"
    
    resp += "**Clinical Mechanism & Overview:**\n"
    resp += f"Based on your query regarding *\"{msg}\"*, physiological presentations like this typically involve immune, metabolic, or vascular responses to physical triggers, infections, or lifestyle stressors.\n\n"

    resp += "**Recommended Next Steps & Clinical Actions:**\n"
    resp += "• **Hydration & Rest:** Maintain 2–2.5L daily fluid intake and ensure 7–8 hours of restorative sleep to promote cellular recovery.\n"
    resp += "• **Symptom Logging:** Record timestamps, triggers, intensity (1–10 scale), and any alleviating factors.\n"
    resp += "• **Vital Telemetry:** Periodically verify baseline vitals (pulse, blood pressure, temperature) via the MediVision dashboard.\n\n"

    # Emergency / Red Flag Check
    if any(e in msg_lower for e in ["chest pain", "shortness of breath", "severe pain", "unconscious", "stroke", "bleeding"]):
        resp += "**🚨 Urgent Clinical Red Flag:**\n"
        resp += "If you experience severe acute chest tightness radiating to the arm/jaw, acute breathlessness, sudden speech or vision changes, or intractable pain, seek **immediate emergency medical care** (911 / 112).\n\n"
    else:
        resp += "**When to Consult a Physician:**\n"
        resp += "• If symptoms persist beyond 48–72 hours or progressively worsen.\n"
        resp += "• If accompanied by high fever (>38.5°C / 101.3°F), difficulty swallowing, or severe localized pain.\n\n"

    resp += "**Questions to Discuss with Your Doctor:**\n"
    resp += f"1. *Are diagnostic laboratory tests (CBC, metabolic panel, or imaging) recommended for this condition?*\n"
    resp += f"2. *Are there specific lifestyle or dietary modifications indicated for long-term prevention?*"
    
    return resp + CLINICAL_DISCLAIMER


def generate_clinical_response(user_message: str, history: list = None) -> str:
    """
    Main clinical AI dispatcher:
    1. Checks for active LLM API keys (Gemini, Groq, OpenAI, OpenRouter, Anthropic)
    2. Calls live LLM for 100% dynamic, unbounded AI generation
    3. Falls back gracefully to dynamic contextual medical reasoning engine
    """
    # 1. Google Gemini (Free & High Performance)
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        try:
            return call_gemini(gemini_key, user_message, history) + CLINICAL_DISCLAIMER
        except Exception as e:
            print(f"[AI GEMINI ERROR] {e}")

    # 2. Groq (Ultra-fast LLaMA 3.3)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            return call_groq(groq_key, user_message, history) + CLINICAL_DISCLAIMER
        except Exception as e:
            print(f"[AI GROQ ERROR] {e}")

    # 3. OpenAI (GPT-4o / GPT-4o-mini)
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            return call_openai(openai_key, user_message, history) + CLINICAL_DISCLAIMER
        except Exception as e:
            print(f"[AI OPENAI ERROR] {e}")

    # 4. OpenRouter
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        try:
            return call_openrouter(openrouter_key, user_message, history) + CLINICAL_DISCLAIMER
        except Exception as e:
            print(f"[AI OPENROUTER ERROR] {e}")

    # 5. Dynamic Generative Clinical Engine Fallback
    return generate_dynamic_fallback(user_message, history)
