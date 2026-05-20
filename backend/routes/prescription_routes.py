"""MediVision AI - Prescription Routes"""
from flask import Blueprint, request, jsonify, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
import io
import json
from datetime import datetime
import os

prescription_bp = Blueprint('prescriptions', __name__)


def safe_text(value, fallback=''):
    """Strip non-ASCII characters so ReportLab's Helvetica font doesn't crash."""
    text = str(value) if value is not None else fallback
    return text.encode('ascii', 'ignore').decode('ascii')

@prescription_bp.route('/list', methods=['GET'])
def list_prescriptions():
    from backend.routes.auth_routes import get_current_user
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        from backend.utils.supabase_client import get_service_client
        supabase = get_service_client()
        res = supabase.table('prescriptions')\
            .select('*')\
            .eq('patient_id', user['id'])\
            .order('created_at', desc=True)\
            .execute()
        return jsonify({"success": True, "prescriptions": res.data or []})
    except Exception as e:
        print(f"[PRESCRIPTIONS] {e}")
        return jsonify({"error": "Could not load prescriptions."}), 500

@prescription_bp.route('/generate-pdf', methods=['POST'])
def generate_prescription_pdf():
    """Generate downloadable prescription PDF"""
    try:
        data = request.get_json()
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Header - Hospital/Clinic
        c.setFillColor(colors.HexColor('#0d9488'))  # Teal
        c.rect(0, height - 120, width, 120, fill=True, stroke=False)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(40, height - 55, "MediVision AI Healthcare")
        c.setFont("Helvetica", 12)
        c.drawString(40, height - 80, "AI-Powered Smart Healthcare System")
        c.drawString(40, height - 100, "Tel: +91 98765 43210  |  Email: care@medivision.ai")
        
        # Right side - Rx symbol
        c.setFont("Helvetica-Bold", 60)
        c.drawString(width - 100, height - 80, "Rx")
        
        # Doctor info
        y = height - 160
        c.setFillColor(colors.HexColor('#1e293b'))
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, f"Dr. {safe_text(data.get('doctor_name'), 'Consulting Physician')}")
        c.setFont("Helvetica", 11)
        c.drawString(40, y - 20, f"Specialization: {safe_text(data.get('specialty'), 'General Physician')}")
        c.drawString(40, y - 35, f"Reg. No: MCI-{safe_text(data.get('reg_no'), '12345')}")
        
        # Date on right
        c.drawRightString(width - 40, y, f"Date: {safe_text(data.get('date'), datetime.now().strftime('%d %B %Y'))}")
        c.drawRightString(width - 40, y - 20, f"Prescription ID: RX-{safe_text(data.get('id'), '001')}")
        
        # Divider
        y -= 60
        c.setStrokeColor(colors.HexColor('#e2e8f0'))
        c.setLineWidth(1.5)
        c.line(40, y, width - 40, y)
        
        # Patient Info
        y -= 25
        c.setFillColor(colors.HexColor('#64748b'))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, "PATIENT INFORMATION")
        y -= 18
        c.setFillColor(colors.HexColor('#1e293b'))
        c.setFont("Helvetica", 11)
        c.drawString(40, y, f"Name: {safe_text(data.get('patient_name'), 'Patient')}")
        c.drawString(250, y, f"Age: {safe_text(data.get('age'), '--')}  |  Gender: {safe_text(data.get('gender'), '--')}")
        y -= 18
        c.drawString(40, y, f"Diagnosis: {safe_text(data.get('diagnosis'), '--')}")
        c.drawString(350, y, f"BP: {safe_text(data.get('bp'), '--')}  |  Weight: {safe_text(data.get('weight'), '--')}")
        
        # Divider
        y -= 20
        c.line(40, y, width - 40, y)
        
        # Medicines
        y -= 30
        c.setFillColor(colors.HexColor('#64748b'))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, "PRESCRIBED MEDICINES")
        
        medicines = data.get('medicines', [])
        for i, med in enumerate(medicines, 1):
            y -= 30
            c.setFillColor(colors.HexColor('#0d9488'))
            c.circle(55, y + 5, 10, fill=True, stroke=False)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(55, y + 1, str(i))
            
            c.setFillColor(colors.HexColor('#1e293b'))
            c.setFont("Helvetica-Bold", 12)
            c.drawString(75, y + 5, f"{safe_text(med.get('name'))} - {safe_text(med.get('dosage'))}")
            c.setFont("Helvetica", 10)
            c.setFillColor(colors.HexColor('#64748b'))
            c.drawString(75, y - 10, f"Frequency: {safe_text(med.get('frequency'))}  |  Duration: {safe_text(med.get('duration'))}")
            
            if i < len(medicines):
                c.setStrokeColor(colors.HexColor('#f1f5f9'))
                c.line(70, y - 20, width - 40, y - 20)
            
            y -= 15
        
        # Notes
        y -= 30
        c.setStrokeColor(colors.HexColor('#e2e8f0'))
        c.line(40, y + 15, width - 40, y + 15)
        c.setFillColor(colors.HexColor('#64748b'))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, "NOTES & INSTRUCTIONS")
        y -= 20
        c.setFillColor(colors.HexColor('#1e293b'))
        c.setFont("Helvetica", 10)
        notes = safe_text(data.get('notes'), 'Take medicines as prescribed. Follow up if symptoms persist.')
        words = notes.split()
        line = ""
        for word in words:
            if len(line + word) < 80:
                line += word + " "
            else:
                c.drawString(40, y, line)
                y -= 15
                line = word + " "
        if line:
            c.drawString(40, y, line)
        
        # Follow up
        y -= 40
        c.setFillColor(colors.HexColor('#fef3c7'))
        c.roundRect(40, y - 5, width - 80, 30, 5, fill=True, stroke=False)
        c.setFillColor(colors.HexColor('#92400e'))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y + 8, f"Follow-up: {safe_text(data.get('follow_up'), 'After 4 weeks')}")
        
        # Footer
        y = 80
        c.setStrokeColor(colors.HexColor('#0d9488'))
        c.setLineWidth(2)
        c.line(40, y + 30, width - 40, y + 30)
        
        c.setFillColor(colors.HexColor('#64748b'))
        c.setFont("Helvetica", 9)
        c.drawString(40, y + 15, "This prescription is computer generated and digitally signed.")
        c.drawString(40, y, "For emergency, call: 112 | Helpline: 1800-MEDIVISION")
        c.drawRightString(width - 40, y + 15, f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M')}")
        c.drawRightString(width - 40, y, "MediVision AI Platform v2.0")
        
        # Doctor signature area
        c.setStrokeColor(colors.HexColor('#94a3b8'))
        c.setLineWidth(1)
        c.line(width - 200, 120, width - 40, 120)
        c.setFillColor(colors.HexColor('#64748b'))
        c.setFont("Helvetica", 9)
        c.drawCentredString(width - 120, 110, "Doctor's Signature")
        
        c.save()
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'prescription_{data.get("id", "RX001")}.pdf'
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@prescription_bp.route('/create', methods=['POST'])
def create_prescription():
    from backend.routes.auth_routes import get_current_user
    user = get_current_user()
    if not user or user.get('role') != 'doctor':
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        patient_id = data.get('patient_id')
        appointment_id = data.get('appointment_id')
        medicines = data.get('medicines', [])
        diagnosis = data.get('diagnosis', '')
        notes = data.get('notes', '')
        follow_up_date = data.get('follow_up_date')

        if not patient_id or not medicines:
            return jsonify({"success": False, "error": "Patient ID and medicines are required"}), 400

        from backend.utils.supabase_client import get_service_client
        import uuid
        supabase = get_service_client()
        
        record = {
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "doctor_id": user['id'],
            "appointment_id": appointment_id,
            "doctor_name": user['full_name'],
            "diagnosis": diagnosis,
            "medicines": medicines,
            "notes": notes,
            "follow_up_date": follow_up_date,
            "pdf_url": None
        }

        res = supabase.table('prescriptions').insert(record).execute()
        return jsonify({"success": True, "message": "Prescription created successfully", "prescription": res.data[0] if res.data else None})

    except Exception as e:
        return jsonify({"error": str(e)}), 500




