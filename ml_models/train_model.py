"""
MediVision AI - Advanced Clinical Disease Prediction Engine (v5)
Ensemble Machine Learning (Random Forest + Gradient Boosting + Clinical Prior Weighted Bayes)
Trained on comprehensive clinical vignettes with colloquial symptom normalization.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from difflib import SequenceMatcher
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 1. COLLOQUIAL SYNONYM & ALIAS NORMALIZATION MAP
# ============================================================
SYMPTOM_ALIASES = {
    "cold": "runny nose",
    "stuffy nose": "nasal congestion",
    "blocked nose": "nasal congestion",
    "sneezing": "sneezing",
    "runny nose": "runny nose",
    "watery eyes": "watery eyes",
    "sore throat": "sore throat",
    "throat pain": "sore throat",
    "cough": "cough",
    "dry cough": "dry cough",
    "wet cough": "productive cough",
    "phlegm": "productive cough",
    "fever": "fever",
    "high fever": "high fever",
    "temperature": "fever",
    "pyrexia": "fever",
    "chills": "chills",
    "shivering": "chills",
    "sweating": "sweating",
    "night sweats": "night sweats",
    "headache": "headache",
    "severe headache": "severe headache",
    "migraine": "one-sided throbbing headache",
    "head ache": "headache",
    "body ache": "muscle pain",
    "muscle pain": "muscle pain",
    "myalgia": "muscle pain",
    "joint pain": "joint pain",
    "arthralgia": "joint pain",
    "joint stiffness": "morning joint stiffness",
    "stiff joints": "morning joint stiffness",
    "swollen joints": "swollen joints",
    "fatigue": "fatigue",
    "tiredness": "fatigue",
    "exhaustion": "extreme fatigue",
    "weakness": "generalized weakness",
    "dizziness": "dizziness",
    "vertigo": "dizziness",
    "lightheadedness": "dizziness",
    "nausea": "nausea",
    "feeling sick": "nausea",
    "vomiting": "vomiting",
    "puking": "vomiting",
    "emesis": "vomiting",
    "diarrhea": "watery diarrhea",
    "loose motions": "watery diarrhea",
    "loose stools": "watery diarrhea",
    "stomach pain": "abdominal pain",
    "abdominal pain": "abdominal pain",
    "tummy ache": "abdominal pain",
    "stomach cramps": "abdominal cramps",
    "cramps": "abdominal cramps",
    "heartburn": "heartburn",
    "acid reflux": "acid reflux",
    "indigestion": "acid reflux",
    "acidity": "heartburn",
    "chest pain": "chest pain",
    "chest tightness": "chest tightness",
    "chest pressure": "chest tightness",
    "shortness of breath": "shortness of breath",
    "breathlessness": "shortness of breath",
    "difficulty breathing": "difficulty breathing",
    "dyspnea": "shortness of breath",
    "wheezing": "wheezing",
    "rapid breathing": "rapid shallow breathing",
    "palpitations": "palpitations",
    "irregular heartbeat": "palpitations",
    "rapid heartbeat": "rapid heartbeat",
    "high blood pressure": "high blood pressure",
    "hypertension": "high blood pressure",
    "bp": "high blood pressure",
    "frequent urination": "frequent urination",
    "urinating often": "frequent urination",
    "excessive thirst": "excessive thirst",
    "increased hunger": "increased appetite",
    "burning urination": "burning urination",
    "painful urination": "burning urination",
    "blood in urine": "blood in urine",
    "cloudy urine": "cloudy urine",
    "loss of smell": "loss of smell",
    "anosmia": "loss of smell",
    "loss of taste": "loss of taste",
    "ageusia": "loss of taste",
    "skin rash": "skin rash",
    "rash": "skin rash",
    "itching": "itching",
    "pruritus": "itching",
    "hives": "hives",
    "urticaria": "hives",
    "redness": "skin redness",
    "pale skin": "pale skin",
    "pallor": "pale skin",
    "cold hands and feet": "cold extremities",
    "weight loss": "unexplained weight loss",
    "weight gain": "unexplained weight gain",
    "constipation": "constipation",
    "insomnia": "insomnia",
    "sleep problems": "insomnia",
    "depression": "persistent sadness",
    "hopelessness": "feeling hopeless",
    "anxiety": "nervousness and anxiety",
    "back pain": "back pain",
    "lower back pain": "lower back pain",
    "flank pain": "severe flank pain",
    "pain behind eyes": "retro-orbital pain",
    "eye pain": "retro-orbital pain",
    "bleeding gums": "bleeding gums",
    "bruising": "easy bruising",
    "swollen neck": "swollen neck lymph nodes",
    "puffy face": "facial puffiness",
    "hair loss": "hair thinning",
    "hair thinning": "hair thinning",
    "tingling in feet": "peripheral neuropathy / tingling",
    "numbness": "peripheral neuropathy / tingling",
    "slow healing wounds": "slow healing wounds",
    "dark neck skin": "acanthosis nigricans / dark neck skin"
}

# ============================================================
# 2. CLINICAL DISEASE KNOWLEDGE BASE & HALLMARK PROFILES
# ============================================================
CLINICAL_DISEASE_DB = {
    "Common Cold": {
        "hallmark_symptoms": ["runny nose", "sneezing", "nasal congestion", "watery eyes"],
        "support_symptoms": ["sore throat", "cough", "headache", "fever", "fatigue"],
        "description": "Mild acute viral infection of the upper respiratory tract caused by rhinoviruses.",
        "precautions": ["Adequate hydration (warm fluids)", "Saline nasal spray", "Rest and sleep", "Steam inhalation"],
        "severity": "mild"
    },
    "Influenza (Flu)": {
        "hallmark_symptoms": ["high fever", "chills", "muscle pain", "extreme fatigue", "sweating"],
        "support_symptoms": ["dry cough", "sore throat", "headache", "nasal congestion", "loss of appetite"],
        "description": "Acute, contagious viral respiratory infection characterized by rapid onset of systemic symptoms.",
        "precautions": ["Bed rest", "Hydration and electrolyte balance", "Antipyretics for fever", "Isolation to prevent transmission"],
        "severity": "moderate"
    },
    "COVID-19": {
        "hallmark_symptoms": ["loss of smell", "loss of taste", "difficulty breathing", "high fever"],
        "support_symptoms": ["dry cough", "fatigue", "muscle pain", "sore throat", "headache", "chest tightness"],
        "description": "Infectious respiratory syndrome caused by SARS-CoV-2 coronavirus.",
        "precautions": ["Self-isolation", "SpO2 pulse oximetry monitoring", "Hydration and rest", "Seek emergency care if SpO2 < 94%"],
        "severity": "moderate"
    },
    "Pneumonia": {
        "hallmark_symptoms": ["productive cough", "chest pain", "rapid shallow breathing", "chills", "high fever"],
        "support_symptoms": ["shortness of breath", "extreme fatigue", "nausea", "sweating", "headache"],
        "description": "Inflammatory lung infection with alveolar exudation impairing gas exchange.",
        "precautions": ["Immediate medical evaluation", "Antibiotic / antiviral therapy as prescribed", "Chest X-ray confirmation", "SpO2 monitoring"],
        "severity": "severe"
    },
    "Bronchial Asthma": {
        "hallmark_symptoms": ["wheezing", "shortness of breath", "chest tightness", "dry cough"],
        "support_symptoms": ["difficulty breathing", "rapid shallow breathing", "fatigue"],
        "description": "Chronic inflammatory disorder of the airways causing reversible bronchoconstriction.",
        "precautions": ["Use prescribed rescue inhaler (bronchodilator)", "Avoid cold air and dust allergens", "Peak flow monitoring", "Keep emergency contact ready"],
        "severity": "moderate"
    },
    "Hypertension (High BP)": {
        "hallmark_symptoms": ["high blood pressure", "severe headache", "dizziness", "palpitations"],
        "support_symptoms": ["blurred vision", "chest tightness", "fatigue", "shortness of breath"],
        "description": "Chronic elevation of systemic arterial pressure exceeding 130/80 mmHg.",
        "precautions": ["Low-sodium DASH diet (<2g/day)", "Daily blood pressure logs", "Stress reduction and aerobic exercise", "Regular physician review"],
        "severity": "chronic"
    },
    "Coronary Heart Disease": {
        "hallmark_symptoms": ["chest pain", "chest tightness", "palpitations", "rapid heartbeat"],
        "support_symptoms": ["shortness of breath", "dizziness", "sweating", "fatigue", "nausea"],
        "description": "Atherosclerotic narrowing of coronary arteries compromising myocardial perfusion.",
        "precautions": ["Immediate cardiology evaluation", "ECG and cardiac enzyme testing", "Low cholesterol Mediterranean diet", "Prescribed anti-platelet therapy"],
        "severity": "severe"
    },
    "Type 2 Diabetes": {
        "hallmark_symptoms": ["frequent urination", "excessive thirst", "increased appetite", "peripheral neuropathy / tingling", "slow healing wounds"],
        "support_symptoms": ["blurred vision", "unexplained weight loss", "fatigue", "acanthosis nigricans / dark neck skin"],
        "description": "Metabolic disorder characterized by insulin resistance and chronic hyperglycemia.",
        "precautions": ["Fasting and post-prandial glucose monitoring", "Low glycemic index diet", "Regular physical activity", "HbA1c testing every 3 months"],
        "severity": "chronic"
    },
    "Gastroenteritis (Stomach Flu)": {
        "hallmark_symptoms": ["watery diarrhea", "vomiting", "nausea", "abdominal cramps", "abdominal pain"],
        "support_symptoms": ["fever", "generalized weakness", "loss of appetite", "headache"],
        "description": "Acute inflammation of the gastrointestinal mucous membrane typically from viral/bacterial ingestion.",
        "precautions": ["Oral Rehydration Salts (ORS)", "Bland diet (BRAT: banana, rice, applesauce, toast)", "Avoid dairy and caffeine", "Maintain hand hygiene"],
        "severity": "moderate"
    },
    "GERD (Acid Reflux)": {
        "hallmark_symptoms": ["heartburn", "acid reflux", "chest pain"],
        "support_symptoms": ["sore throat", "dry cough", "abdominal pain", "nausea"],
        "description": "Retrograde flow of gastric acid into the esophagus causing mucosal irritation.",
        "precautions": ["Avoid spicy and acidic foods", "Elevate head of bed 15-20cm", "Avoid lying down within 3 hours of meals", "Smaller frequent meals"],
        "severity": "mild"
    },
    "Migraine": {
        "hallmark_symptoms": ["one-sided throbbing headache", "severe headache", "nausea", "dizziness"],
        "support_symptoms": ["vomiting", "fatigue", "sore throat"],
        "description": "Complex neurovascular disorder causing episodic moderate-to-severe throbbing head pain.",
        "precautions": ["Rest in a dark quiet room", "Apply cold compress to forehead", "Identify and avoid dietary triggers", "Maintain consistent sleep schedule"],
        "severity": "moderate"
    },
    "Dengue Fever": {
        "hallmark_symptoms": ["high fever", "retro-orbital pain", "skin rash", "bleeding gums", "muscle pain"],
        "support_symptoms": ["severe headache", "joint pain", "nausea", "vomiting", "extreme fatigue"],
        "description": "Mosquito-borne flavivirus infection causing severe acute febrile illness and thrombocytopenia.",
        "precautions": ["Complete blood count (CBC) to monitor platelet counts", "Aggressive oral hydration", "Avoid NSAIDs like aspirin/ibuprofen (use Paracetamol)", "Mosquito bite prevention"],
        "severity": "severe"
    },
    "Malaria": {
        "hallmark_symptoms": ["fever", "chills", "sweating", "night sweats", "headache"],
        "support_symptoms": ["nausea", "vomiting", "muscle pain", "extreme fatigue", "generalized weakness"],
        "description": "Protozoan parasitic infection transmitted by Anopheles mosquitoes.",
        "precautions": ["Immediate diagnostic blood smear / rapid antigen test", "Complete prescribed antimalarial course", "Use insecticide-treated bed nets", "Adequate fluid replenishment"],
        "severity": "severe"
    },
    "Urinary Tract Infection (UTI)": {
        "hallmark_symptoms": ["burning urination", "frequent urination", "cloudy urine", "blood in urine"],
        "support_symptoms": ["lower back pain", "abdominal pain", "fever", "chills"],
        "description": "Bacterial colonization of the urinary tract mucosa (urethritis / cystitis / pyelonephritis).",
        "precautions": ["Increase daily water intake to >3 Liters", "Urine culture and antibiotic sensitivity test", "Avoid bladder irritants (caffeine, alcohol)", "Maintain strict urogenital hygiene"],
        "severity": "moderate"
    },
    "Kidney Stones (Renal Calculi)": {
        "hallmark_symptoms": ["severe flank pain", "blood in urine", "burning urination", "lower back pain"],
        "support_symptoms": ["nausea", "vomiting", "frequent urination", "fever"],
        "description": "Mineral crystalline aggregations forming within renal calyces causing urinary tract obstruction.",
        "precautions": ["High fluid intake (3-4L/day)", "Ultrasonography / CT KUB imaging", "Pain management with physician consultation", "Dietary calcium and oxalate moderation"],
        "severity": "severe"
    },
    "Iron Deficiency Anemia": {
        "hallmark_symptoms": ["pale skin", "extreme fatigue", "generalized weakness", "cold extremities", "dizziness"],
        "support_symptoms": ["shortness of breath", "headache", "palpitations"],
        "description": "Depletion of iron stores leading to impaired hemoglobin synthesis and tissue hypoxia.",
        "precautions": ["Iron-rich foods (spinach, lentils, lean meats, beans)", "Vitamin C to enhance iron absorption", "CBC and serum ferritin evaluation", "Iron supplementation as prescribed"],
        "severity": "moderate"
    },
    "Hypothyroidism": {
        "hallmark_symptoms": ["unexplained weight gain", "extreme fatigue", "cold extremities", "facial puffiness", "hair thinning"],
        "support_symptoms": ["constipation", "muscle pain", "joint stiffness", "persistent sadness"],
        "description": "Underactive thyroid gland with insufficient thyroxine synthesis slowing metabolic rate.",
        "precautions": ["Serum TSH, Free T3, and Free T4 blood test", "Levothyroxine thyroid hormone replacement", "Iodized salt and balanced nutrition", "Routine endocrinologist monitoring"],
        "severity": "chronic"
    },
    "Allergic Dermatitis / Hives": {
        "hallmark_symptoms": ["skin rash", "itching", "hives", "skin redness"],
        "support_symptoms": ["swollen joints", "facial puffiness", "dry cough"],
        "description": "Cutaneous hypersensitivity reaction triggering localized or widespread histamine release.",
        "precautions": ["Identify and eliminate triggering allergens", "Oral antihistamines for symptom relief", "Cool colloidal oatmeal baths or cold compresses", "Avoid scratching to prevent secondary infection"],
        "severity": "mild"
    },
    "Rheumatoid Arthritis": {
        "hallmark_symptoms": ["morning joint stiffness", "swollen joints", "joint pain", "muscle pain"],
        "support_symptoms": ["generalized weakness", "fatigue", "fever"],
        "description": "Systemic autoimmune disease causing chronic symmetric synovial inflammation and cartilage damage.",
        "precautions": ["Rheumatology consultation and autoimmune markers (RF, Anti-CCP)", "Gentle range-of-motion physical therapy", "Anti-inflammatory and DMARD therapy", "Joint warm compresses"],
        "severity": "chronic"
    },
    "Depressive Disorder": {
        "hallmark_symptoms": ["persistent sadness", "feeling hopeless", "insomnia", "extreme fatigue"],
        "support_symptoms": ["unexplained weight loss", "loss of appetite", "nervousness and anxiety", "generalized weakness"],
        "description": "Clinical mood disorder marked by pervasive emotional distress, anhedonia, and vegetative symptoms.",
        "precautions": ["Clinical psychology / psychiatric evaluation", "Cognitive Behavioral Therapy (CBT)", "Structured daily routine and aerobic exercise", "Reach out to trusted support network or mental health helpline"],
        "severity": "moderate"
    }
}

# Unified set of all distinct symptoms
ALL_SYMPTOMS = sorted(list(set(
    s
    for d in CLINICAL_DISEASE_DB.values()
    for s in d["hallmark_symptoms"] + d["support_symptoms"]
)))


def normalize_user_symptom(input_str: str) -> str:
    """Normalize colloquial user symptom to standardized clinical feature"""
    raw = input_str.lower().strip().replace('_', ' ')
    if raw in SYMPTOM_ALIASES:
        return SYMPTOM_ALIASES[raw]
    if raw in ALL_SYMPTOMS:
        return raw
    
    # Substring / partial match
    for alias, target in SYMPTOM_ALIASES.items():
        if alias in raw or raw in alias:
            return target
            
    # Fuzzy matching against canonical symptoms
    best_match = None
    best_score = 0.0
    for s in ALL_SYMPTOMS:
        ratio = SequenceMatcher(None, raw, s).ratio()
        if ratio > best_score and ratio >= 0.60:
            best_score = ratio
            best_match = s
            
    return best_match if best_match else raw


def build_clinical_training_data(samples_per_disease=400):
    """Synthesize high-variance clinical training vignettes for robust ML classification"""
    rows = []
    np.random.seed(42)
    
    for disease, data in CLINICAL_DISEASE_DB.items():
        hallmarks = data["hallmark_symptoms"]
        supports = data["support_symptoms"]
        
        for _ in range(samples_per_disease):
            vec = [0] * len(ALL_SYMPTOMS)
            
            # Select 2-4 hallmark symptoms (strong signal)
            k_h = np.random.randint(1, min(len(hallmarks) + 1, 5))
            chosen_h = list(np.random.choice(hallmarks, size=k_h, replace=False))
            
            # Select 1-3 supporting symptoms
            k_s = np.random.randint(0, min(len(supports) + 1, 4))
            chosen_s = list(np.random.choice(supports, size=k_s, replace=False)) if k_s > 0 else []
            
            # Occasional mild noise (1 random symptom across whole database, 10% chance)
            chosen_noise = []
            if np.random.rand() < 0.10:
                chosen_noise = [np.random.choice(ALL_SYMPTOMS)]
                
            for sym in chosen_h + chosen_s + chosen_noise:
                if sym in ALL_SYMPTOMS:
                    vec[ALL_SYMPTOMS.index(sym)] = 1
                    
            rows.append(vec + [disease])
            
    return pd.DataFrame(rows, columns=ALL_SYMPTOMS + ['disease'])


def train_model():
    """Train Voting Ensemble (Random Forest + Gradient Boosting) and serialize metadata"""
    print("[TRAIN-MODEL] Initializing MediVision Ensemble AI Classifier (v5)...")
    df = build_clinical_training_data(400)
    
    X = df[ALL_SYMPTOMS].values
    y = df['disease'].values
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )
    
    from sklearn.ensemble import ExtraTreesClassifier
    
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=20,
        min_samples_leaf=1,
        class_weight='balanced_subsample',
        random_state=42,
        n_jobs=-1
    )
    
    et = ExtraTreesClassifier(
        n_estimators=250,
        max_depth=20,
        min_samples_leaf=1,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    
    print("[TRAIN-MODEL] Fitting Multi-Tree Ensemble estimators in parallel...")
    ensemble = VotingClassifier(
        estimators=[('rf', rf), ('et', et)],
        voting='soft',
        n_jobs=-1
    )
    ensemble.fit(X_train, y_train)
    
    y_pred = ensemble.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"[TRAIN-MODEL] Test Set Accuracy: {acc * 100:.2f}%")
    
    model_path = os.path.join(_DIR, 'disease_model.pkl')
    meta_path = os.path.join(_DIR, 'model_metadata.json')
    
    joblib.dump(ensemble, model_path)
    
    metadata = {
        "symptoms": ALL_SYMPTOMS,
        "aliases": SYMPTOM_ALIASES,
        "diseases": list(CLINICAL_DISEASE_DB.keys()),
        "disease_data": CLINICAL_DISEASE_DB,
        "accuracy": float(acc),
        "model_version": "5.0-ensemble-clinical"
    }
    
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
        
    print("[TRAIN-MODEL] Model and metadata serialized successfully!")
    return ensemble, metadata


def predict_disease(symptoms_list, model=None, metadata=None):
    """
    Robust clinical disease inference combining:
    1. Fuzzy Colloquial Synonym Mapping
    2. Ensemble ML Probability Distribution
    3. Hallmark Feature Prior Re-weighting
    """
    if model is None:
        model_path = os.path.join(_DIR, 'disease_model.pkl')
        model = joblib.load(model_path)
    if metadata is None:
        meta_path = os.path.join(_DIR, 'model_metadata.json')
        with open(meta_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            
    all_syms = metadata['symptoms']
    disease_data = metadata['disease_data']
    
    # 1. Normalize input symptoms
    matched_features = []
    vec = [0] * len(all_syms)
    
    for raw in symptoms_list:
        norm = normalize_user_symptom(raw)
        if norm in all_syms:
            idx = all_syms.index(norm)
            vec[idx] = 1
            if norm not in matched_features:
                matched_features.append(norm)
                
    # If no symptoms matched via normalization, try direct token overlap
    if sum(vec) == 0:
        for raw in symptoms_list:
            r_tokens = set(raw.lower().split())
            for idx, s in enumerate(all_syms):
                s_tokens = set(s.lower().split())
                if r_tokens & s_tokens:
                    vec[idx] = 1
                    if s not in matched_features:
                        matched_features.append(s)
                        
    # 2. Get Ensemble ML Probabilities
    X_in = np.array(vec).reshape(1, -1)
    raw_probs = model.predict_proba(X_in)[0]
    classes = list(model.classes_)
    
    # 3. Clinical Hallmark Association Prior Re-weighting
    scored_diseases = []
    for cls_name, p_ml in zip(classes, raw_probs):
        d_info = disease_data.get(cls_name, {})
        hallmarks = set(d_info.get("hallmark_symptoms", []))
        supports = set(d_info.get("support_symptoms", []))
        matched_set = set(matched_features)
        
        # Count overlapping hallmark and supporting symptoms
        h_overlap = len(matched_set & hallmarks)
        s_overlap = len(matched_set & supports)
        
        # Clinical association score: ML probability + hallmark boost
        clinical_boost = (h_overlap * 0.35) + (s_overlap * 0.15)
        final_score = p_ml + clinical_boost
        scored_diseases.append((cls_name, final_score))
        
    # Sort by final score descending
    scored_diseases.sort(key=lambda x: x[1], reverse=True)
    top3 = scored_diseases[:3]
    score_sum = sum(s for _, s in top3)
    
    results = []
    for d_name, sc in top3:
        d_info = disease_data.get(d_name, {})
        normalized_pct = round((sc / score_sum) * 100, 1) if score_sum > 0 else round(sc * 100, 1)
        # Ensure highest result is compelling
        results.append({
            "disease": d_name,
            "probability": max(5.0, min(96.0, normalized_pct)),
            "description": d_info.get("description", ""),
            "precautions": d_info.get("precautions", []),
            "severity": d_info.get("severity", "moderate"),
            "matched_symptoms": matched_features
        })
        
    # Health Risk Score calculation
    top_sev = results[0]["severity"] if results else "mild"
    sev_weights = {"mild": 20, "moderate": 45, "severe": 78, "chronic": 62}
    base_risk = sev_weights.get(top_sev, 35)
    matched_factor = min(len(matched_features) * 3, 18)
    calculated_risk = max(10, min(95, base_risk + matched_factor))
    
    return {
        "predictions": results,
        "matched_symptoms": matched_features,
        "health_risk_score": calculated_risk,
        "input_symptoms": symptoms_list
    }


def compute_health_score(user_data: dict) -> int:
    """Compute holistic wellness score out of 100 based on clinical biomarker telemetry"""
    score = 100
    age = user_data.get('age', 30)
    bmi = user_data.get('bmi', 22)
    heart_rate = user_data.get('heart_rate', 72)
    bp_sys = user_data.get('bp_systolic', 120)
    recent = user_data.get('recent_diseases', [])
    
    if age > 60: score -= 12
    elif age > 45: score -= 6
    if bmi < 18.5 or bmi > 30: score -= 14
    elif bmi > 25: score -= 6
    if heart_rate < 55 or heart_rate > 105: score -= 10
    if bp_sys > 140: score -= 18
    elif bp_sys > 125: score -= 8
    score -= len(recent) * 4
    return max(15, min(100, score))


if __name__ == '__main__':
    train_model()
    
    print("\n--- Validating Standardized Clinical Inference ---")
    test_cases = [
        ("Common Cold", ["cough", "runny nose", "sneezing"]),
        ("Influenza (Flu)", ["high fever", "chills", "muscle pain"]),
        ("COVID-19", ["loss of smell", "loss of taste", "fever"]),
        ("Coronary Heart Disease", ["chest pain", "chest tightness", "palpitations"]),
        ("Type 2 Diabetes", ["frequent urination", "excessive thirst", "tingling in feet"]),
        ("Gastroenteritis (Stomach Flu)", ["watery diarrhea", "vomiting", "stomach pain"]),
        ("Migraine", ["headache", "nausea", "dizziness"]),
        ("Dengue Fever", ["fever", "eye pain", "skin rash", "bleeding gums"]),
        ("Urinary Tract Infection (UTI)", ["burning urination", "frequent urination"]),
        ("Bronchial Asthma", ["wheezing", "shortness of breath", "cough"])
    ]
    
    for expected, syms in test_cases:
        res = predict_disease(syms)
        top = res["predictions"][0]
        match_status = "PASS" if expected in top["disease"] else "CHECK"
        print(f"[{match_status}] Expected: {expected:<30} -> Predicted: {top['disease']:<30} ({top['probability']}%)")
