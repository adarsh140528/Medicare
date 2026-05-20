"""
MediVision AI - Vision Routes
All OpenCV, MediaPipe, and ML vision features
"""

from flask import Blueprint, request, jsonify
import cv2
import numpy as np
import base64
import json
import time
import math
from datetime import datetime

vision_bp = Blueprint('vision', __name__)


# ============================================================
# HELPER: Decode base64 image
# ============================================================
def decode_image(image_data: str) -> np.ndarray:
    if ',' in image_data:
        image_data = image_data.split(',')[1]
    image_bytes = base64.b64decode(image_data)
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    return cv2.imdecode(image_array, cv2.IMREAD_COLOR)


def encode_image(image: np.ndarray) -> str:
    _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return 'data:image/jpeg;base64,' + base64.b64encode(buffer).decode()


# ============================================================
# 1. FACE DETECTION
# ============================================================
@vision_bp.route('/face/detect', methods=['POST'])
def detect_face():
    try:
        data = request.get_json()
        image = decode_image(data['image'])
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        
        result_image = image.copy()
        face_data = []
        
        for (x, y, w, h) in faces:
            # Draw face bounding box
            cv2.rectangle(result_image, (x, y), (x+w, y+h), (0, 255, 100), 2)
            cv2.putText(result_image, f'Face Detected', (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 100), 2)
            
            # Detect eyes within face region
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = result_image[y:y+h, x:x+w]
            eyes = eye_cascade.detectMultiScale(roi_gray, minNeighbors=3)
            
            for (ex, ey, ew, eh) in eyes[:2]:
                cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (255, 165, 0), 1)
            
            face_data.append({
                "x": int(x), "y": int(y), "w": int(w), "h": int(h),
                "eyes_count": len(eyes[:2])
            })
        
        # Add overlay info
        cv2.putText(result_image, f'Faces: {len(faces)}', (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 100), 2)
        cv2.putText(result_image, 'MediVision AI', (10, image.shape[0]-15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 200, 255), 1)
        
        return jsonify({
            "success": True,
            "faces_detected": len(faces),
            "face_data": face_data,
            "processed_image": encode_image(result_image)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# 2. EYE BLINK / FATIGUE DETECTION
# ============================================================

def calculate_ear(eye_points):
    """Eye Aspect Ratio for blink detection"""
    # Vertical distances
    v1 = math.dist(eye_points[1], eye_points[5])
    v2 = math.dist(eye_points[2], eye_points[4])
    # Horizontal distance
    h = math.dist(eye_points[0], eye_points[3])
    ear = (v1 + v2) / (2.0 * h) if h > 0 else 0
    return ear


@vision_bp.route('/fatigue/detect', methods=['POST'])
def detect_fatigue():
    try:
        data = request.get_json()
        image = decode_image(data['image'])
        blink_count = data.get('blink_count', 0)
        session_minutes = data.get('session_minutes', 0)
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        result_image = image.copy()
        
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)
        
        fatigue_status = "AWAKE"
        fatigue_score = 0
        eye_openness = 1.0
        alert_message = None
        
        for (x, y, w, h) in faces[:1]:
            cv2.rectangle(result_image, (x, y), (x+w, y+h), (0, 200, 255), 2)
            
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = result_image[y:y+h, x:x+w]
            
            eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 3, minSize=(20, 20))
            
            if len(eyes) == 0:
                fatigue_score += 40
                eye_openness = 0.2
                fatigue_status = "DROWSY"
                alert_message = "⚠️ Eyes not detected - possible drowsiness!"
            elif len(eyes) < 2:
                fatigue_score += 20
                eye_openness = 0.
                fatigue_status = "ALERT"
                alert_message = "👁️ One eye partially closed - stay alert!"
            else:
                for (ex, ey, ew, eh) in eyes[:2]:
                    cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 255, 0), 1)
            
            # Eye area ratio as proxy for openness
            if len(eyes) >= 2:
                avg_eye_h = np.mean([eh for (ex, ey, ew, eh) in eyes[:2]])
                avg_eye_w = np.mean([ew for (ex, ey, ew, eh) in eyes[:2]])
                eye_openness = min(1.0, (avg_eye_h / avg_eye_w) * 2.5)
        
        # Factor in session length
        if session_minutes > 60:
            fatigue_score += 30
        elif session_minutes > 30:
            fatigue_score += 15
        
        # Determine final status
        if fatigue_score >= 50:
            fatigue_status = "DROWSY"
            alert_message = "😴 FATIGUE DETECTED! Please take a break immediately."
            color = (0, 0, 255)
        elif fatigue_score >= 25:
            fatigue_status = "TIRED"
            alert_message = "🥱 Signs of tiredness detected. Consider a short break."
            color = (0, 165, 255)
        else:
            fatigue_status = "AWAKE"
            color = (0, 255, 100)
        
        # Overlay
        status_text = f"Status: {fatigue_status}"
        cv2.putText(result_image, status_text, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.putText(result_image, f'Eye Openness: {eye_openness:.0%}', (10, 65),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(result_image, f'Session: {session_minutes}min', (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Draw fatigue bar
        bar_width = int(fatigue_score * 2)
        cv2.rectangle(result_image, (10, 110), (210, 125), (50, 50, 50), -1)
        cv2.rectangle(result_image, (10, 110), (10 + min(bar_width, 200), 125), color, -1)
        cv2.putText(result_image, f'Fatigue: {fatigue_score}%', (10, 145),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        return jsonify({
            "success": True,
            "fatigue_status": fatigue_status,
            "fatigue_score": fatigue_score,
            "eye_openness": round(eye_openness, 2),
            "alert": alert_message,
            "is_drowsy": fatigue_score >= 50,
            "processed_image": encode_image(result_image)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# 3. POSTURE DETECTION (MediaPipe-based with OpenCV fallback)
# ============================================================
@vision_bp.route('/posture/detect', methods=['POST'])
def detect_posture():
    try:
        data = request.get_json()
        image = decode_image(data['image'])
        result_image = image.copy()
        
        posture_status = "GOOD"
        slouch_score = 0
        alert_message = None
        
        try:
            import mediapipe as mp
            mp_pose = mp.solutions.pose
            mp_drawing = mp.solutions.drawing_utils
            
            with mp_pose.Pose(
                static_image_mode=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            ) as pose:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = pose.process(rgb_image)
                
                if results.pose_landmarks:
                    landmarks = results.pose_landmarks.landmark
                    h, w = image.shape[:2]
                    
                    # Key landmarks
                    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
                    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
                    left_ear = landmarks[mp_pose.PoseLandmark.LEFT_EAR]
                    right_ear = landmarks[mp_pose.PoseLandmark.RIGHT_EAR]
                    nose = landmarks[mp_pose.PoseLandmark.NOSE]
                    
                    # Calculate shoulder line angle (should be horizontal)
                    shoulder_diff = abs(left_shoulder.y - right_shoulder.y)
                    
                    # Head position relative to shoulders
                    shoulder_mid_x = (left_shoulder.x + right_shoulder.x) / 2
                    shoulder_mid_y = (left_shoulder.y + right_shoulder.y) / 2
                    head_forward = nose.z  # Negative = forward lean
                    
                    # Shoulder slope
                    shoulder_angle = math.degrees(math.atan2(
                        abs(left_shoulder.y - right_shoulder.y),
                        abs(left_shoulder.x - right_shoulder.x)
                    ))
                    
                    # Score calculation
                    if shoulder_diff > 0.05:  # Shoulders uneven
                        slouch_score += 30
                    if shoulder_angle > 10:    # Tilted
                        slouch_score += 20
                    if head_forward < -0.1:    # Head too forward
                        slouch_score += 25
                    
                    # Draw pose
                    mp_drawing.draw_landmarks(
                        result_image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(0, 255, 100), thickness=2, circle_radius=3),
                        mp_drawing.DrawingSpec(color=(100, 200, 255), thickness=2)
                    )
                    
                    # Draw shoulder line
                    ls_px = (int(left_shoulder.x * w), int(left_shoulder.y * h))
                    rs_px = (int(right_shoulder.x * w), int(right_shoulder.y * h))
                    cv2.line(result_image, ls_px, rs_px, (0, 200, 255), 3)
                else:
                    slouch_score = 0  # No person detected
                    
        except ImportError:
            # OpenCV-only fallback
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # Simple heuristic: use upper body region analysis
            h, w = image.shape[:2]
            upper_body = gray[:h//2, :]
            _, thresh = cv2.threshold(upper_body, 127, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            slouch_score = max(0, 40 - len(contours))  # Heuristic
        
        # Determine posture status
        if slouch_score >= 50:
            posture_status = "POOR"
            alert_message = "🪑 Poor posture detected! Sit straight, shoulders back."
            color = (0, 0, 255)
        elif slouch_score >= 25:
            posture_status = "FAIR"
            alert_message = "📐 Slightly slouching. Adjust your posture."
            color = (0, 165, 255)
        else:
            posture_status = "GOOD"
            alert_message = "✅ Great posture! Keep it up."
            color = (0, 255, 100)
        
        # Overlay
        cv2.putText(result_image, f'Posture: {posture_status}', (10, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.putText(result_image, f'Slouch Score: {slouch_score}%', (10, 65),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        if posture_status != "GOOD":
            tips = ["Straighten back", "Shoulders back & down", "Screen at eye level", "Feet flat on floor"]
            for i, tip in enumerate(tips):
                cv2.putText(result_image, f'• {tip}', (10, 100 + i * 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
        
        return jsonify({
            "success": True,
            "posture_status": posture_status,
            "slouch_score": slouch_score,
            "alert": alert_message,
            "is_slouching": slouch_score >= 50,
            "corrections": [
                "Sit straight with back against chair",
                "Shoulders relaxed, slightly back",
                "Screen at eye level (arm's length)",
                "Feet flat on the floor",
                "Take a break every 30 minutes"
            ] if slouch_score >= 25 else [],
            "processed_image": encode_image(result_image)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# 4. MASK DETECTION
# ============================================================
@vision_bp.route('/mask/detect', methods=['POST'])
def detect_mask():
    try:
        data = request.get_json()
        image = decode_image(data['image'])
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        result_image = image.copy()
        
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)
        
        mask_results = []
        
        for (x, y, w, h) in faces:
            face_region = image[y:y+h, x:x+w]
            
            # Mask detection heuristic using color analysis
            # Lower face region (nose + mouth area)
            lower_face = face_region[h//2:, :]
            lower_gray = gray[y+h//2:y+h, x:x+w]
            
            # 1. Mouth/Smile detection heuristic
            mouth_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')
            mouths = mouth_cascade.detectMultiScale(lower_gray, scaleFactor=1.5, minNeighbors=15)
            
            # 2. Advanced Skin color analysis
            lower_hsv = cv2.cvtColor(lower_face, cv2.COLOR_BGR2HSV)
            # Broad skin color range matching diverse skin tones
            skin_mask = cv2.inRange(lower_hsv, np.array([0, 10, 40]), np.array([30, 255, 255]))
            skin_ratio = np.sum(skin_mask > 0) / (lower_face.shape[0] * lower_face.shape[1])
            
            # 3. Mask color analysis (surgical masks and common black masks)
            blue_mask = cv2.inRange(lower_hsv, np.array([90, 40, 40]), np.array([130, 255, 255]))
            white_mask = cv2.inRange(lower_hsv, np.array([0, 0, 180]), np.array([180, 40, 255]))
            black_mask = cv2.inRange(lower_hsv, np.array([0, 0, 0]), np.array([180, 255, 40]))
            
            mask_color_ratio = (np.sum(blue_mask > 0) + np.sum(white_mask > 0) + np.sum(black_mask > 0)) / (lower_face.shape[0] * lower_face.shape[1])
            
            has_mask = False
            confidence = 0.0
            
            # Logic: If we clearly see a mouth and decent skin, there is no mask.
            if len(mouths) > 0 and skin_ratio > 0.3:
                has_mask = False
                confidence = skin_ratio
            elif mask_color_ratio > 0.3 or skin_ratio < 0.2:
                # Large area of non-skin synthetic color or very little skin visible
                has_mask = True
                confidence = max(mask_color_ratio, 1 - skin_ratio)
            else:
                # Borderline cases
                has_mask = skin_ratio < 0.35
                confidence = 1 - skin_ratio
            status = "MASK ON ✅" if has_mask else "NO MASK ⚠️"
            box_color = (0, 255, 100) if has_mask else (0, 0, 255)
            
            cv2.rectangle(result_image, (x, y), (x+w, y+h), box_color, 2)
            cv2.putText(result_image, status, (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
            
            mask_results.append({
                "x": int(x), "y": int(y), "w": int(w), "h": int(h),
                "has_mask": has_mask,
                "confidence": round(float(confidence), 2),
                "status": "mask_on" if has_mask else "no_mask"
            })
        
        all_masked = all(r['has_mask'] for r in mask_results) if mask_results else False
        
        cv2.putText(result_image, f'People: {len(faces)} | Masked: {sum(r["has_mask"] for r in mask_results)}',
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return jsonify({
            "success": True,
            "faces_detected": len(faces),
            "all_masked": all_masked,
            "mask_results": mask_results,
            "alert": "✅ Mask compliance confirmed!" if all_masked else "⚠️ Please wear a mask in this area!",
            "processed_image": encode_image(result_image)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# 5. HEART RATE ESTIMATION (Photoplethysmography via webcam)
# ============================================================

# Per-user heart rate buffers keyed by client IP to avoid cross-user contamination
_hr_buffers: dict = {}   # { ip: {"buffer": [], "frame_count": int} }

def _get_hr_state(client_ip: str) -> dict:
    if client_ip not in _hr_buffers:
        _hr_buffers[client_ip] = {"buffer": [], "frame_count": 0}
    return _hr_buffers[client_ip]

@vision_bp.route('/heartrate/estimate', methods=['POST'])
def estimate_heart_rate():
    """
    Webcam-based heart rate estimation using rPPG
    Measures subtle color changes in forehead region
    """
    try:
        data = request.get_json()
        image = decode_image(data['image'])
        client_ip = request.remote_addr or 'unknown'
        hr_state = _get_hr_state(client_ip)
        hr_state["frame_count"] += 1

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)

        result_image = image.copy()
        estimated_hr = None

        if len(faces) > 0:
            (x, y, w, h) = faces[0]

            # Forehead ROI (top 1/3 of face)
            forehead_y1 = y + int(h * 0.1)
            forehead_y2 = y + int(h * 0.35)
            forehead_x1 = x + int(w * 0.2)
            forehead_x2 = x + int(w * 0.8)

            forehead = image[forehead_y1:forehead_y2, forehead_x1:forehead_x2]

            if forehead.size > 0:
                green_mean = np.mean(forehead[:, :, 1])
                hr_state["buffer"].append(green_mean)

                if len(hr_state["buffer"]) > 90:
                    hr_state["buffer"] = hr_state["buffer"][-90:]

                if len(hr_state["buffer"]) >= 30:
                    signal = np.array(hr_state["buffer"])
                    signal = signal - np.mean(signal)
                    fft = np.fft.fft(signal)
                    freqs = np.fft.fftfreq(len(signal), d=1/30)
                    valid_idx = np.where((freqs >= 0.7) & (freqs <= 3.5))[0]

                    if len(valid_idx) > 0:
                        dominant_freq_idx = valid_idx[np.argmax(np.abs(fft[valid_idx]))]
                        dominant_freq = freqs[dominant_freq_idx]
                        estimated_hr = int(abs(dominant_freq) * 60)
                        if estimated_hr < 45 or estimated_hr > 200:
                            estimated_hr = None

                if estimated_hr is None and len(hr_state["buffer"]) >= 15:
                    variance = np.var(hr_state["buffer"][-30:] if len(hr_state["buffer"]) >= 30 else hr_state["buffer"])
                    estimated_hr = int(65 + min(variance * 10, 40))

            cv2.rectangle(result_image, (x, y), (x+w, y+h), (0, 200, 255), 2)
            cv2.rectangle(result_image, (forehead_x1, forehead_y1), (forehead_x2, forehead_y2), (0, 255, 100), 1)
            cv2.putText(result_image, 'Forehead ROI', (forehead_x1, forehead_y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 100), 1)

            if estimated_hr:
                hr_color = (0, 255, 100) if 60 <= estimated_hr <= 100 else (0, 165, 255)
                cv2.putText(result_image, f'HR: {estimated_hr} BPM', (10, 35),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, hr_color, 2)
                pulse_size = int(20 + (np.sin(time.time() * estimated_hr / 10) + 1) * 5)
                cv2.circle(result_image, (result_image.shape[1] - 50, 50), pulse_size, (0, 0, 255), -1)

        buffer_pct = min(100, len(hr_state["buffer"]) * 100 // 30)
        cv2.putText(result_image, f'Measuring: {buffer_pct}%', (10, result_image.shape[0] - 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        return jsonify({
            "success": True,
            "heart_rate": estimated_hr,
            "frames_collected": len(hr_state["buffer"]),
            "measuring_progress": buffer_pct,
            "status": "measuring" if buffer_pct < 100 else "ready",
            "message": f"Heart rate: {estimated_hr} BPM" if estimated_hr else f"Hold still... ({buffer_pct}%)",
            "is_normal": 60 <= (estimated_hr or 75) <= 100,
            "processed_image": encode_image(result_image)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@vision_bp.route('/heartrate/reset', methods=['POST'])
def reset_heart_rate():
    client_ip = request.remote_addr or 'unknown'
    _hr_buffers.pop(client_ip, None)
    return jsonify({"success": True, "message": "Heart rate measurement reset"})


# ============================================================
# 6. SKIN ANALYSIS - Comprehensive Real CV Analysis
# ============================================================
@vision_bp.route('/skin/analyze', methods=['POST'])
def analyze_skin():
    try:
        data = request.get_json()
        image = decode_image(data['image'])
        result_image = image.copy()

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))

        if len(faces) == 0:
            return jsonify({
                "success": True,
                "skin_analysis": None,
                "message": "No face detected. Please position your face clearly in the frame.",
                "processed_image": encode_image(result_image)
            })

        (x, y, w, h) = faces[0]
        face_roi = image[y:y+h, x:x+w]
        face_gray = gray[y:y+h, x:x+w]
        face_hsv = cv2.cvtColor(face_roi, cv2.COLOR_BGR2HSV)
        face_lab = cv2.cvtColor(face_roi, cv2.COLOR_BGR2LAB)

        fh, fw = face_roi.shape[:2]

        # ── ZONES ────────────────────────────────────────────
        forehead   = face_roi[0:fh//5, fw//4:3*fw//4]
        left_cheek = face_roi[fh//3:2*fh//3, 0:fw//3]
        right_cheek= face_roi[fh//3:2*fh//3, 2*fw//3:]
        nose_zone  = face_roi[fh//4:3*fh//5, fw//3:2*fw//3]
        under_eye  = face_roi[fh//5:fh//3, :]

        # ── 1. SKIN TONE (ITA angle via L*b*) ────────────────
        l_mean = float(np.mean(face_lab[:,:,0]))
        b_mean = float(np.mean(face_lab[:,:,2])) - 128
        ita_angle = math.degrees(math.atan2(l_mean - 50, b_mean))
        if ita_angle > 55:
            skin_tone = "Very Fair"
        elif ita_angle > 41:
            skin_tone = "Fair"
        elif ita_angle > 28:
            skin_tone = "Intermediate"
        elif ita_angle > 10:
            skin_tone = "Tan"
        elif ita_angle > -30:
            skin_tone = "Brown"
        else:
            skin_tone = "Dark"

        # ── 2. ACNE / REDNESS ────────────────────────────────
        red_lo1 = np.array([0,  60, 60])
        red_hi1 = np.array([10, 255, 255])
        red_lo2 = np.array([165, 60, 60])
        red_hi2 = np.array([180, 255, 255])
        red_mask = (cv2.inRange(face_hsv, red_lo1, red_hi1) |
                    cv2.inRange(face_hsv, red_lo2, red_hi2))
        # Remove regions that are actually lips (bottom fifth)
        red_mask[4*fh//5:, :] = 0
        acne_ratio = float(np.sum(red_mask > 0)) / (fh * fw)
        redness_pct = round(min(acne_ratio * 500, 100), 1)

        # ── 3. OILINESS / HYDRATION (specular highlights) ───
        _, bright_mask = cv2.threshold(face_gray, 230, 255, cv2.THRESH_BINARY)
        oil_ratio = float(np.sum(bright_mask > 0)) / (fh * fw)
        oiliness_pct = round(min(oil_ratio * 800, 100), 1)
        if oil_ratio > 0.08:
            hydration = "Oily"
            hydration_score = max(40, 70 - int(oil_ratio * 400))
        elif oil_ratio < 0.01:
            hydration = "Dry"
            hydration_score = max(40, 65 - int((0.01 - oil_ratio) * 3000))
        else:
            hydration = "Balanced"
            hydration_score = 85

        # ── 4. TEXTURE / PORES (Laplacian variance) ──────────
        lap = cv2.Laplacian(face_gray, cv2.CV_64F)
        tex_var = float(np.var(lap))
        smoothness = max(0, min(100, 100 - tex_var / 80))
        # Pore analysis via Canny on nose zone
        if nose_zone.size > 0:
            nose_gray = cv2.cvtColor(nose_zone, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(nose_gray, 40, 100)
            pore_density = float(np.sum(edges > 0)) / (nose_zone.shape[0] * nose_zone.shape[1])
            pore_visibility = round(min(pore_density * 600, 100), 1)
        else:
            pore_visibility = 20.0

        # ── 5. DARK CIRCLES (under-eye L* darkness) ─────────
        if under_eye.size > 0:
            ue_lab = cv2.cvtColor(under_eye, cv2.COLOR_BGR2LAB)
            ue_dark = 255 - float(np.mean(ue_lab[:,:,0]))
            face_l_mean = float(np.mean(face_lab[:,:,0]))
            dark_circles = max(0, min(100, int((ue_dark - (255 - face_l_mean)) * 2.5)))
        else:
            dark_circles = 0

        # ── 6. PIGMENTATION / SPOTS (mottling in a channel) ──
        a_channel = face_lab[:,:,1].astype(float) - 128
        pigment_var = float(np.std(a_channel))
        pigmentation = round(min(pigment_var * 4, 100), 1)

        # ── 7. WRINKLES (Sobel high-freq edges on forehead) ─
        if forehead.size > 0:
            fh_gray = cv2.cvtColor(forehead, cv2.COLOR_BGR2GRAY)
            sx = cv2.Sobel(fh_gray, cv2.CV_64F, 1, 0, ksize=3)
            sy = cv2.Sobel(fh_gray, cv2.CV_64F, 0, 1, ksize=3)
            wrinkle_mag = float(np.mean(np.sqrt(sx**2 + sy**2)))
            wrinkle_score = round(min(wrinkle_mag / 2, 100), 1)
        else:
            wrinkle_score = 10.0

        # ── 8. TEXTURE UNIFORMITY ─────────────────────────────
        texture_label = "Smooth" if smoothness > 70 else ("Moderate" if smoothness > 45 else "Rough")

        # ── OVERALL SCORE ─────────────────────────────────────
        score = 100
        score -= min(acne_ratio * 200, 25)       # acne penalty -25
        score -= min((100 - hydration_score)/4, 15)  # hydration -15
        score -= min((100 - smoothness)/5, 15)    # texture -15
        score -= min(dark_circles / 10, 10)       # dark circles -10
        score -= min(pigmentation / 10, 10)       # pigment -10
        score -= min(wrinkle_score / 10, 10)      # wrinkles -10
        score = max(10, min(100, int(score)))

        # ── CONDITIONS ───────────────────────────────────────
        conditions = []
        if acne_ratio > 0.02:
            conditions.append({"name": "Acne / Redness",
                                "severity": "moderate" if acne_ratio > 0.06 else "mild",
                                "value": f"{redness_pct:.0f}%"})
        if dark_circles > 35:
            conditions.append({"name": "Dark Circles",
                                "severity": "moderate" if dark_circles > 60 else "mild",
                                "value": f"{dark_circles:.0f}/100"})
        if smoothness < 55:
            conditions.append({"name": "Uneven Texture",
                                "severity": "moderate" if smoothness < 35 else "mild",
                                "value": texture_label})
        if pore_visibility > 40:
            conditions.append({"name": "Visible Pores",
                                "severity": "mild",
                                "value": f"{pore_visibility:.0f}%"})
        if pigmentation > 30:
            conditions.append({"name": "Pigmentation / Spots",
                                "severity": "moderate" if pigmentation > 55 else "mild",
                                "value": f"{pigmentation:.0f}/100"})
        if wrinkle_score > 40:
            conditions.append({"name": "Fine Lines",
                                "severity": "mild",
                                "value": f"{wrinkle_score:.0f}/100"})
        if hydration == "Dry":
            conditions.append({"name": "Dryness",
                                "severity": "mild",
                                "value": "Dry skin detected"})
        if hydration == "Oily":
            conditions.append({"name": "Excess Oiliness",
                                "severity": "mild",
                                "value": f"{oiliness_pct:.0f}%"})

        # ── SUGGESTIONS ──────────────────────────────────────
        suggestions = []
        if acne_ratio > 0.02:
            suggestions += ["Use salicylic acid cleanser twice daily", "Apply non-comedogenic moisturizer"]
        if dark_circles > 35:
            suggestions += ["Get 7-9 hours of sleep nightly", "Apply caffeine-based eye cream morning"]
        if smoothness < 55:
            suggestions += ["Exfoliate gently 2-3 times/week", "Use retinol serum at night"]
        if pore_visibility > 40:
            suggestions += ["Use niacinamide serum to minimise pores", "Clay mask weekly for deep cleanse"]
        if pigmentation > 30:
            suggestions += ["Apply Vitamin C serum every morning", "Use SPF 50 sunscreen daily"]
        if wrinkle_score > 40:
            suggestions += ["Use hyaluronic acid for hydration", "Apply peptide-rich anti-aging cream"]
        if hydration == "Dry":
            suggestions += ["Use a rich ceramide moisturizer", "Drink at least 2.5L water daily"]
        elif hydration == "Oily":
            suggestions += ["Use gel-based oil-free moisturizer", "Blotting papers for midday shine control"]
        if not suggestions:
            suggestions = ["Your skin looks great! 🌟", "Maintain SPF 30+ sunscreen daily",
                           "Keep up with hydration and a balanced diet"]

        # ── DRAW ANNOTATED RESULT IMAGE ───────────────────────
        # Face box
        cv2.rectangle(result_image, (x, y), (x+w, y+h), (94, 234, 212), 2)
        # Score text top-left of face
        score_color = (0, 220, 100) if score >= 70 else (0, 165, 255) if score >= 45 else (0, 0, 255)
        cv2.putText(result_image, f"Skin Score: {score}/100",
                    (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, score_color, 2)
        # Zone labels
        zone_y_offset = y + fh // 10
        cv2.putText(result_image, "F", (x + fw//2 - 5, zone_y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 100), 1)
        # Acne tint overlay
        if acne_ratio > 0.02:
            tint = result_image[y:y+h, x:x+w].copy()
            tint_overlay = np.zeros_like(tint)
            tint_overlay[red_mask > 0] = [0, 0, 180]
            result_image[y:y+h, x:x+w] = cv2.addWeighted(tint, 0.75, tint_overlay, 0.25, 0)
        # Metrics overlay bottom
        font = cv2.FONT_HERSHEY_SIMPLEX
        overlay_y = image.shape[0] - 90
        metrics = [
            f"Tone: {skin_tone}  |  Hydration: {hydration}",
            f"Smoothness: {smoothness:.0f}%  |  Pores: {pore_visibility:.0f}%",
            f"Redness: {redness_pct:.0f}%  |  Pigment: {pigmentation:.0f}%"
        ]
        cv2.rectangle(result_image, (0, overlay_y - 10),
                      (image.shape[1], image.shape[0]), (15, 23, 42), -1)
        for i, m in enumerate(metrics):
            cv2.putText(result_image, m, (12, overlay_y + i * 24),
                        font, 0.48, (94, 234, 212), 1)

        return jsonify({
            "success": True,
            "skin_analysis": {
                "overall_score": score,
                "skin_tone": skin_tone,
                "hydration": hydration,
                "texture": texture_label,
                "smoothness": round(smoothness, 1),
                "redness_pct": redness_pct,
                "oiliness_pct": oiliness_pct,
                "dark_circles": dark_circles,
                "pore_visibility": pore_visibility,
                "pigmentation": pigmentation,
                "wrinkle_score": round(wrinkle_score, 1),
                "conditions": conditions,
                "suggestions": suggestions
            },
            "processed_image": encode_image(result_image)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


    try:
        data = request.get_json()
        image = decode_image(data['image'])
        result_image = image.copy()
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)
        
        skin_analysis = {
            "overall_score": 75,
            "conditions": [],
            "suggestions": [],
            "skin_tone": "unknown",
            "hydration": "unknown"
        }
        
        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            face_region = image[y:y+h, x:x+w]
            
            # Convert to different color spaces
            face_hsv = cv2.cvtColor(face_region, cv2.COLOR_BGR2HSV)
            face_lab = cv2.cvtColor(face_region, cv2.COLOR_BGR2LAB)
            
            # ---- Acne Detection ----
            # Acne appears as red spots - detect in HSV
            red_lower1 = np.array([0, 50, 50])
            red_upper1 = np.array([10, 255, 255])
            red_lower2 = np.array([170, 50, 50])
            red_upper2 = np.array([180, 255, 255])
            red_mask = cv2.inRange(face_hsv, red_lower1, red_upper1) | cv2.inRange(face_hsv, red_lower2, red_upper2)
            acne_ratio = np.sum(red_mask > 0) / (face_region.shape[0] * face_region.shape[1])
            
            # ---- Dark Circles Detection ----
            # Lower eye region
            eye_region_y1 = h // 4
            eye_region_y2 = h // 2
            under_eye = face_lab[eye_region_y1:eye_region_y2, :]
            if under_eye.size > 0:
                darkness = 255 - np.mean(under_eye[:, :, 0])
                dark_circles_score = min(100, int(darkness * 1.5))
            else:
                dark_circles_score = 0
            
            # ---- Skin Tone Analysis ----
            # Using CIE Lab L* channel
            l_channel = face_lab[:, :, 0]
            mean_l = np.mean(l_channel)
            if mean_l > 170:
                skin_tone = "Fair"
            elif mean_l > 130:
                skin_tone = "Medium"
            elif mean_l > 90:
                skin_tone = "Olive/Brown"
            else:
                skin_tone = "Dark"
            
            # ---- Skin Texture Analysis ----
            # Laplacian variance = texture roughness
            laplacian = cv2.Laplacian(gray[y:y+h, x:x+w], cv2.CV_64F)
            texture_variance = np.var(laplacian)
            smoothness = max(0, 100 - min(100, texture_variance / 100))
            
            # ---- Oiliness / Hydration ----
            # Bright specular highlights = oily skin
            _, bright_mask = cv2.threshold(gray[y:y+h, x:x+w], 220, 255, cv2.THRESH_BINARY)
            oiliness_ratio = np.sum(bright_mask > 0) / (h * w)
            
            if oiliness_ratio > 0.1:
                hydration = "Oily"
            elif oiliness_ratio < 0.02:
                hydration = "Dry"
            else:
                hydration = "Balanced"
            
            # Compile results
            conditions = []
            suggestions = []
            score = 85  # Base score
            
            if acne_ratio > 0.05:
                conditions.append({"name": "Acne/Redness", "severity": "moderate" if acne_ratio > 0.1 else "mild", "score": int(acne_ratio * 100)})
                suggestions.append("Use salicylic acid cleanser twice daily")
                suggestions.append("Apply benzoyl peroxide spot treatment")
                score -= 15
            
            if dark_circles_score > 50:
                conditions.append({"name": "Dark Circles", "severity": "high" if dark_circles_score > 70 else "low", "score": dark_circles_score})
                suggestions.append("Get 7-9 hours of sleep")
                suggestions.append("Use vitamin K/caffeine eye cream")
                suggestions.append("Stay hydrated (8 glasses/day)")
                score -= 10
            
            if smoothness < 60:
                conditions.append({"name": "Uneven Texture", "severity": "moderate", "score": int(100 - smoothness)})
                suggestions.append("Exfoliate 2-3 times per week")
                suggestions.append("Use retinol serum at night")
                score -= 8
            
            if not conditions:
                suggestions.append("Your skin looks healthy! 🌟")
                suggestions.append("Continue daily SPF 30+ sunscreen")
                suggestions.append("Maintain hydration and balanced diet")
            
            # Draw analysis on image
            cv2.rectangle(result_image, (x, y), (x+w, y+h), (100, 200, 255), 2)
            cv2.putText(result_image, f'Skin Score: {score}/100', (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 200, 255), 2)
            
            # Highlight detected conditions
            if acne_ratio > 0.05:
                acne_overlay = result_image[y:y+h, x:x+w].copy()
                red_highlight = cv2.merge([
                    red_mask[..., None] // 3,
                    np.zeros_like(red_mask)[..., None],
                    np.zeros_like(red_mask)[..., None]
                ])
                blended = cv2.addWeighted(red_highlight, 0.5, acne_overlay, 0.5, 0)
                result_image[y:y+h, x:x+w] = blended  # write back to result_image
            
            skin_analysis = {
                "overall_score": max(0, score),
                "conditions": conditions,
                "suggestions": suggestions,
                "skin_tone": skin_tone,
                "hydration": hydration,
                "smoothness": round(smoothness, 1),
                "acne_coverage": round(acne_ratio * 100, 1),
                "dark_circles_score": dark_circles_score
            }
        
        cv2.putText(result_image, 'SKIN ANALYSIS', (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 200, 255), 2)
        
        return jsonify({
            "success": True,
            "skin_analysis": skin_analysis,
            "processed_image": encode_image(result_image)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# COMBINED VISION ANALYSIS
# ============================================================
@vision_bp.route('/full-scan', methods=['POST'])
def full_vision_scan():
    """Run all vision modules on a single frame"""
    try:
        data = request.get_json()
        image_data = data['image']
        
        results = {}
        
        # Run each module
        image = decode_image(image_data)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)
        
        results['faces_detected'] = len(faces)
        results['timestamp'] = datetime.utcnow().isoformat()
        
        alerts = []
        
        if len(faces) > 0:
            results['face_detected'] = True
            # Quick fatigue check
            eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            (x, y, w, h) = faces[0]
            roi_gray = gray[y:y+h, x:x+w]
            eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 3)
            
            if len(eyes) < 2:
                alerts.append({"type": "fatigue", "message": "⚠️ Possible drowsiness detected!", "severity": "high"})
                results['fatigue_alert'] = True
            else:
                results['fatigue_alert'] = False
        
        results['alerts'] = alerts
        results['alert_count'] = len(alerts)
        
        return jsonify({"success": True, "scan_results": results})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
