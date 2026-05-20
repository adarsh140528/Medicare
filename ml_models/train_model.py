"""
MediVision AI - Disease Prediction Model Training (v4 - Final)
Uses simple everyday-language symptoms users actually type,
but with unique discriminative patterns per disease.
Run: python ml_models/train_model.py
"""

import pandas as pd
import numpy as np
import json
import joblib
import os
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# DISEASE DATASET - SIMPLE EVERYDAY LANGUAGE
# key_symptoms: UNIQUE to this disease (max 1-2 overlap with others)
# general_symptoms: common support symptoms
# ============================================================
DISEASES_DATA = {
    "Common Cold": {
        "key_symptoms": ["runny nose", "sneezing", "stuffy nose", "watery eyes", "clear discharge"],
        "general_symptoms": ["mild sore throat", "mild cough", "mild headache", "low fever"],
        "description": "A viral infection of the upper respiratory tract",
        "precautions": ["Rest", "Stay hydrated", "Avoid cold drinks", "Steam inhalation"],
        "severity": "mild"
    },
    "Influenza": {
        "key_symptoms": ["sudden high fever", "severe muscle pain", "extreme tiredness", "shivering", "sweating heavily"],
        "general_symptoms": ["dry cough", "sore throat", "headache", "loss of appetite"],
        "description": "A contagious respiratory illness caused by influenza viruses",
        "precautions": ["Bed rest", "Antiviral medication", "Flu vaccine", "Isolation"],
        "severity": "moderate"
    },
    "Dengue Fever": {
        "key_symptoms": ["pain behind eyes", "skin rash after fever", "low platelet count", "bleeding gums", "very high fever lasting 5 days"],
        "general_symptoms": ["severe headache", "joint pain", "nausea", "vomiting", "fatigue"],
        "description": "A mosquito-borne viral infection common in tropical regions",
        "precautions": ["Mosquito repellent", "Hydration", "Platelet monitoring", "Hospital care if severe"],
        "severity": "severe"
    },
    "Malaria": {
        "key_symptoms": ["fever every 2 days", "violent shaking chills", "enlarged spleen", "night sweats", "fever with rigor"],
        "general_symptoms": ["headache", "nausea", "vomiting", "fatigue", "anemia", "muscle pain"],
        "description": "A life-threatening disease caused by Plasmodium parasites",
        "precautions": ["Antimalarial drugs", "Mosquito nets", "Blood test", "Doctor consultation"],
        "severity": "severe"
    },
    "Type 2 Diabetes": {
        "key_symptoms": ["very frequent urination", "extreme thirst", "tingling in feet", "slow healing wounds", "darkened neck skin"],
        "general_symptoms": ["blurred vision", "frequent infections", "unexplained weight loss", "increased hunger", "fatigue"],
        "description": "A chronic condition affecting how your body metabolizes sugar",
        "precautions": ["Diet control", "Exercise", "Blood sugar monitoring", "Medication"],
        "severity": "chronic"
    },
    "Hypertension": {
        "key_symptoms": ["high blood pressure", "throbbing headache at back of head", "nosebleed", "ringing in ears", "pounding heartbeat"],
        "general_symptoms": ["dizziness", "blurred vision", "shortness of breath", "chest discomfort", "fatigue"],
        "description": "High blood pressure that can lead to serious health complications",
        "precautions": ["Low salt diet", "Exercise", "Stress management", "Medication"],
        "severity": "chronic"
    },
    "Asthma": {
        "key_symptoms": ["wheezing", "nighttime breathlessness", "triggered by dust or cold air", "chest tightness", "chronic dry cough worse at night"],
        "general_symptoms": ["shortness of breath", "breathlessness on exercise", "fatigue"],
        "description": "A condition causing airway inflammation and breathing difficulties",
        "precautions": ["Avoid triggers", "Inhaler", "Air purifier", "Regular checkups"],
        "severity": "moderate"
    },
    "Pneumonia": {
        "key_symptoms": ["cough with yellow or green phlegm", "chest pain when breathing", "shaking chills", "rapid shallow breathing", "crackling sound in chest"],
        "general_symptoms": ["high fever", "fatigue", "shortness of breath", "confusion in elderly", "nausea"],
        "description": "Infection causing inflammation in one or both lungs",
        "precautions": ["Antibiotics", "Rest", "Hydration", "Hospital if severe"],
        "severity": "severe"
    },
    "Gastroenteritis": {
        "key_symptoms": ["watery diarrhea", "sudden vomiting", "stomach cramps", "food poisoning", "multiple loose stools per day"],
        "general_symptoms": ["nausea", "abdominal pain", "dehydration", "mild fever", "loss of appetite"],
        "description": "Inflammation of the digestive tract, often viral or bacterial",
        "precautions": ["ORS solution", "Bland diet", "Rest", "Hygiene"],
        "severity": "moderate"
    },
    "Migraine": {
        "key_symptoms": ["one-sided pounding headache", "light sensitivity", "seeing flashing lights", "sound makes it worse", "nausea with headache"],
        "general_symptoms": ["severe headache", "vomiting", "dizziness", "neck stiffness"],
        "description": "A neurological condition causing intense headaches",
        "precautions": ["Dark quiet room", "Pain medication", "Identify triggers", "Stress reduction"],
        "severity": "moderate"
    },
    "Anemia": {
        "key_symptoms": ["pale skin", "pale inner eyelids", "spoon-shaped nails", "craving ice or dirt", "inflamed tongue"],
        "general_symptoms": ["extreme tiredness", "weakness", "cold hands and feet", "shortness of breath", "dizziness"],
        "description": "A condition where you lack enough red blood cells",
        "precautions": ["Iron-rich diet", "Iron supplements", "Vitamin B12", "Treat underlying cause"],
        "severity": "moderate"
    },
    "Thyroid Disorder": {
        "key_symptoms": ["always feeling cold", "puffy face", "slow heartbeat", "hair thinning", "unexplained weight gain despite diet"],
        "general_symptoms": ["constipation", "dry skin", "depression", "heavy periods", "swollen neck", "fatigue"],
        "description": "Conditions affecting thyroid gland function",
        "precautions": ["Thyroid medication", "Regular TSH tests", "Iodine in diet", "Avoid goitrogens"],
        "severity": "chronic"
    },
    "COVID-19": {
        "key_symptoms": ["loss of smell", "loss of taste", "positive covid test", "contact with covid patient", "difficulty breathing suddenly"],
        "general_symptoms": ["fever", "dry cough", "fatigue", "body aches", "sore throat", "headache"],
        "description": "Coronavirus disease caused by SARS-CoV-2",
        "precautions": ["Isolation", "Vaccination", "Mask", "Hydration", "Doctor if severe"],
        "severity": "moderate"
    },
    "Urinary Tract Infection": {
        "key_symptoms": ["burning while urinating", "blood in urine", "cloudy or smelly urine", "urge to urinate but little comes out", "pain in lower belly"],
        "general_symptoms": ["frequent urination", "pelvic pain", "lower back pain", "mild fever"],
        "description": "Infection in any part of the urinary system",
        "precautions": ["Antibiotics", "Hydration", "Cranberry juice", "Hygiene"],
        "severity": "moderate"
    },
    "Skin Allergy": {
        "key_symptoms": ["hives", "itchy red patches", "skin rash after touching something", "swelling of lips or face", "blistering skin"],
        "general_symptoms": ["itching", "redness", "dry flaky skin", "skin irritation"],
        "description": "Allergic reaction affecting the skin",
        "precautions": ["Avoid allergens", "Antihistamines", "Moisturizers", "Cold compress"],
        "severity": "mild"
    },
    "Depression": {
        "key_symptoms": ["no interest in activities you used to enjoy", "feeling hopeless", "thoughts of suicide", "inability to get out of bed", "withdrawing from friends"],
        "general_symptoms": ["persistent sadness", "sleep problems", "appetite changes", "low energy", "poor concentration"],
        "description": "A mental health disorder affecting mood and quality of life",
        "precautions": ["Therapy", "Antidepressants", "Exercise", "Social support"],
        "severity": "moderate"
    },
    "Arthritis": {
        "key_symptoms": ["morning joint stiffness over 1 hour", "swollen finger joints", "joint deformity", "both hands or knees affected equally", "warm swollen joints"],
        "general_symptoms": ["joint pain", "reduced movement", "fatigue", "weakness"],
        "description": "Inflammation of one or more joints causing pain and stiffness",
        "precautions": ["Physical therapy", "Anti-inflammatory drugs", "Exercise", "Weight management"],
        "severity": "chronic"
    },
    "Heart Disease": {
        "key_symptoms": ["chest pain during exercise", "pain spreading to left arm", "tightness in chest relieved by rest", "irregular heartbeats", "ankle and feet swelling"],
        "general_symptoms": ["shortness of breath", "dizziness", "cold sweats", "nausea", "fatigue"],
        "description": "Range of conditions affecting heart structure and function",
        "precautions": ["Medication", "Diet changes", "Exercise", "No smoking", "Regular checkups"],
        "severity": "severe"
    },
    "Kidney Stones": {
        "key_symptoms": ["severe pain in side and back", "pain radiating to groin area", "pink or red urine", "pain while urinating", "stone passed in urine"],
        "general_symptoms": ["nausea", "vomiting", "frequent urination", "fever if infected"],
        "description": "Hard deposits of minerals forming in the kidneys",
        "precautions": ["Hydration", "Low sodium diet", "Pain management", "Medical procedure if large"],
        "severity": "severe"
    },
    "GERD": {
        "key_symptoms": ["heartburn after eating", "acid coming back up throat", "sour taste in mouth", "burning feeling in chest after meals", "worse when lying down"],
        "general_symptoms": ["difficulty swallowing", "hoarse voice", "chronic cough after eating", "bloating", "burping"],
        "description": "Gastroesophageal reflux disease causing stomach acid to flow back",
        "precautions": ["Avoid trigger foods", "Elevate head", "Antacids", "Small meals"],
        "severity": "moderate"
    }
}

ALL_SYMPTOMS = sorted(set(
    s
    for d in DISEASES_DATA.values()
    for s in d["key_symptoms"] + d["general_symptoms"]
))

print(f"Total diseases: {len(DISEASES_DATA)}")
print(f"Total unique symptoms: {len(ALL_SYMPTOMS)}")


def build_dataset(samples=350):
    rows = []
    np.random.seed(42)
    for disease, data in DISEASES_DATA.items():
        key = data["key_symptoms"]
        gen = data["general_symptoms"]
        for _ in range(samples):
            vec = [0] * len(ALL_SYMPTOMS)
            # Always pick 2-4 key symptoms
            n_key = np.random.randint(2, min(5, len(key) + 1))
            chosen_key = list(np.random.choice(key, size=n_key, replace=False))
            # 1-3 general symptoms
            n_gen = np.random.randint(1, min(4, len(gen) + 1))
            chosen_gen = list(np.random.choice(gen, size=n_gen, replace=False))
            for s in chosen_key + chosen_gen:
                if s in ALL_SYMPTOMS:
                    vec[ALL_SYMPTOMS.index(s)] = 1
            rows.append(vec + [disease])
    return pd.DataFrame(rows, columns=ALL_SYMPTOMS + ['disease'])


def train_model():
    print("\n🏥 Training MediVision Disease Prediction Model (v4)...")
    df = build_dataset(350)
    X = df[ALL_SYMPTOMS].values
    y = df['disease'].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )
    print(f"Training: {len(X_train)} | Test: {len(X_test)}")

    rf = RandomForestClassifier(
        n_estimators=500, max_depth=None,
        min_samples_leaf=1, class_weight='balanced',
        random_state=42, n_jobs=-1
    )
    gb = GradientBoostingClassifier(
        n_estimators=250, learning_rate=0.08,
        max_depth=5, subsample=0.85, random_state=42
    )

    print("Training Random Forest...")
    rf.fit(X_train, y_train)
    print("Training Gradient Boosting...")
    gb.fit(X_train, y_train)
    print("Building Voting Ensemble...")
    ensemble = VotingClassifier([('rf', rf), ('gb', gb)], voting='soft')
    ensemble.fit(X_train, y_train)

    y_pred = ensemble.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n✅ Ensemble Accuracy: {accuracy:.2%}")

    cv = cross_val_score(rf, X, y, cv=StratifiedKFold(5, shuffle=True, random_state=42), n_jobs=-1)
    print(f"✅ RF Cross-Val: {cv.mean():.2%} ± {cv.std():.2%}")

    # Per class
    report = classification_report(y_test, y_pred, output_dict=True)
    for cls, m in report.items():
        if cls not in ['accuracy', 'macro avg', 'weighted avg']:
            marker = "✅" if m['f1-score'] >= 0.95 else "⚠️"
            print(f"  {marker} {cls}: {m['f1-score']:.2%}")

    os.makedirs('ml_models', exist_ok=True)
    joblib.dump(ensemble, 'ml_models/disease_model.pkl')
    meta = {
        "symptoms": ALL_SYMPTOMS,
        "diseases": list(DISEASES_DATA.keys()),
        "disease_data": DISEASES_DATA,
        "accuracy": float(accuracy),
        "model_type": "VotingEnsemble_v4"
    }
    with open('ml_models/model_metadata.json', 'w') as f:
        json.dump(meta, f, indent=2)
    print(f"\n✅ Model saved!\n🎯 Ready for inference!")
    return ensemble, meta


def predict_disease(symptoms_list, model=None, metadata=None):
    if model is None:
        model = joblib.load('ml_models/disease_model.pkl')
    if metadata is None:
        with open('ml_models/model_metadata.json') as f:
            metadata = json.load(f)

    all_syms = metadata['symptoms']
    disease_data = metadata['disease_data']

    vec = [0] * len(all_syms)
    matched = []

    for symptom in symptoms_list:
        sl = symptom.lower().strip()
        done = False
        # Exact match
        for i, s in enumerate(all_syms):
            if sl == s:
                vec[i] = 1
                if s not in matched:
                    matched.append(s)
                done = True
                break
        if not done:
            # Best partial match: prefer longer overlap
            best_i, best_score = -1, 0
            for i, s in enumerate(all_syms):
                # score = length of matching substring
                if sl in s:
                    score = len(sl)
                elif s in sl:
                    score = len(s)
                else:
                    # word overlap
                    words_sl = set(sl.split())
                    words_s = set(s.split())
                    score = len(words_sl & words_s) * 3
                if score > best_score:
                    best_score = score
                    best_i = i
            if best_i >= 0 and best_score >= 3:
                vec[best_i] = 1
                if all_syms[best_i] not in matched:
                    matched.append(all_syms[best_i])

    probs = model.predict_proba(np.array(vec).reshape(1, -1))[0]
    classes = model.classes_
    sorted_probs = sorted(zip(classes, probs), key=lambda x: x[1], reverse=True)

    top3 = sorted_probs[:3]
    total = sum(p for _, p in top3)

    results = []
    for disease, prob in top3:
        d = disease_data.get(disease, {})
        norm = round((prob / total) * 100, 1) if total > 0 else round(prob * 100, 1)
        results.append({
            "disease": disease,
            "probability": norm,
            "description": d.get("description", ""),
            "precautions": d.get("precautions", []),
            "severity": d.get("severity", "unknown"),
            "matched_symptoms": matched
        })

    # Health risk score
    top_raw = sorted_probs[0][1]
    sev = results[0]["severity"] if results else "mild"
    sev_base = {"mild": 18, "moderate": 42, "severe": 72, "chronic": 60}.get(sev, 30)
    conf = max(0.5, min(top_raw * 1.5, 1.0))
    bonus = min(len(matched) * 2, 15)
    risk = max(5, min(92, int(sev_base * conf + bonus)))

    return {
        "predictions": results,
        "matched_symptoms": matched,
        "health_risk_score": risk,
        "input_symptoms": symptoms_list
    }


def compute_health_score(user_data: dict) -> int:
    score = 100
    age = user_data.get('age', 30)
    bmi = user_data.get('bmi', 22)
    heart_rate = user_data.get('heart_rate', 72)
    bp_sys = user_data.get('bp_systolic', 120)
    recent = user_data.get('recent_diseases', [])
    if age > 60: score -= 15
    elif age > 45: score -= 8
    if bmi < 18.5 or bmi > 30: score -= 15
    elif bmi > 25: score -= 5
    if heart_rate < 60 or heart_rate > 100: score -= 10
    if bp_sys > 140: score -= 20
    elif bp_sys > 120: score -= 8
    score -= len(recent) * 5
    return max(0, min(100, score))


if __name__ == '__main__':
    model, meta = train_model()

    print("\n" + "=" * 65)
    print("REAL-WORLD USER INPUT TESTS (words users actually type)")
    print("=" * 65)
    tests = [
        ("Common Cold",          ["runny nose", "sneezing", "stuffy nose", "watery eyes"]),
        ("Influenza",            ["sudden high fever", "severe muscle pain", "shivering", "sweating heavily"]),
        ("Dengue Fever",         ["pain behind eyes", "skin rash after fever", "very high fever lasting 5 days"]),
        ("Malaria",              ["fever every 2 days", "violent shaking chills", "night sweats"]),
        ("Type 2 Diabetes",      ["very frequent urination", "extreme thirst", "tingling in feet", "slow healing wounds"]),
        ("Hypertension",         ["high blood pressure", "throbbing headache at back of head", "nosebleed"]),
        ("Asthma",               ["wheezing", "nighttime breathlessness", "triggered by dust or cold air"]),
        ("Pneumonia",            ["cough with yellow or green phlegm", "chest pain when breathing", "shaking chills"]),
        ("Gastroenteritis",      ["watery diarrhea", "sudden vomiting", "stomach cramps", "food poisoning"]),
        ("Migraine",             ["one-sided pounding headache", "light sensitivity", "seeing flashing lights"]),
        ("Anemia",               ["pale skin", "pale inner eyelids", "spoon-shaped nails", "craving ice or dirt"]),
        ("Thyroid Disorder",     ["always feeling cold", "puffy face", "hair thinning", "unexplained weight gain despite diet"]),
        ("COVID-19",             ["loss of smell", "loss of taste", "dry cough", "fatigue"]),
        ("Urinary Tract Infection", ["burning while urinating", "blood in urine", "cloudy or smelly urine"]),
        ("Skin Allergy",         ["hives", "itchy red patches", "skin rash after touching something"]),
        ("Depression",           ["no interest in activities you used to enjoy", "feeling hopeless", "withdrawing from friends"]),
        ("Arthritis",            ["morning joint stiffness over 1 hour", "swollen finger joints", "warm swollen joints"]),
        ("Heart Disease",        ["chest pain during exercise", "pain spreading to left arm", "ankle and feet swelling"]),
        ("Kidney Stones",        ["severe pain in side and back", "pain radiating to groin area", "pink or red urine"]),
        ("GERD",                 ["heartburn after eating", "acid coming back up throat", "sour taste in mouth"]),
    ]

    correct = 0
    for expected, syms in tests:
        r = predict_disease(syms, model, meta)
        top = r['predictions'][0]
        ok = "✅" if top['disease'] == expected else "❌"
        if top['disease'] == expected:
            correct += 1
        print(f"{ok} {expected:28} → {top['disease']:28} ({top['probability']}%) Risk:{r['health_risk_score']}")

    print(f"\n🎯 Score: {correct}/{len(tests)} ({correct/len(tests)*100:.0f}%)")
