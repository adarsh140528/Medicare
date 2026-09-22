"""
MediVision AI - Full System Integration & Feature Test Suite
Tests all modules, APIs, database operations, ML models, and frontend endpoints.
"""

import unittest
import json
import base64
import numpy as np
import cv2
from datetime import datetime, timedelta
from app import app
from backend.utils.supabase_client import get_service_client
from backend.utils.db import init_db

class TestMediVisionSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = app.test_client()
        cls.db = get_service_client()
        
    def test_01_frontend_routes(self):
        """Verify all HTML template frontend routes render with HTTP 200"""
        routes = [
            '/',
            '/login',
            '/register',
            '/dashboard',
            '/doctor-dashboard',
            '/vision',
            '/ai-predict',
            '/medibot',
            '/appointments',
            '/prescriptions',
            '/health-report'
        ]
        for route in routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200, f"Route {route} failed with status {response.status_code}")

    def test_02_auth_password_login_and_otp(self):
        """Test patient direct password login (no 2FA required)"""
        login_res = self.client.post('/api/auth/login/password', json={
            'email': 'demo@medivision.ai',
            'password': 'demo123',
            'role': 'patient'
        })
        self.assertEqual(login_res.status_code, 200)
        data = login_res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('token', data)
        self.assertEqual(data['user']['email'], 'demo@medivision.ai')

    def test_03_auth_doctor_login(self):
        """Test doctor direct password login (no 2FA required)"""
        login_res = self.client.post('/api/auth/login/password', json={
            'email': 'dr.priya@medivision.ai',
            'password': 'doctor123',
            'role': 'doctor'
        })
        self.assertEqual(login_res.status_code, 200)
        data = login_res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('token', data)
        self.assertEqual(data['user']['role'], 'doctor')

    def test_04_auth_registration(self):
        """Test registering a new patient account with direct token generation"""
        timestamp = int(datetime.utcnow().timestamp())
        reg_payload = {
            'full_name': f'Test User {timestamp}',
            'email': f'test_{timestamp}@example.com',
            'phone': f'+9199{timestamp % 100000000:08d}',
            'password': 'Password@123',
            'date_of_birth': '1998-04-12',
            'gender': 'Male',
            'blood_group': 'O+',
            'address': 'Test Avenue 101',
            'role': 'patient'
        }
        res = self.client.post('/api/auth/register', json=reg_payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('token', data)
        self.assertIn('user', data)

    def test_05_ai_disease_prediction_and_symptoms(self):
        """Test ML disease prediction, symptom list, and persistence in Supabase/DB"""
        # 1. Symptom catalog
        symptom_res = self.client.get('/api/ai/symptoms/list')
        self.assertEqual(symptom_res.status_code, 200)
        symptoms_data = symptom_res.get_json()
        self.assertTrue(symptoms_data.get('success'))
        self.assertTrue(len(symptoms_data.get('symptoms', [])) > 0)
        
        # Login patient to get token directly
        login_res = self.client.post('/api/auth/login/password', json={'email': 'demo@medivision.ai', 'password': 'demo123', 'role': 'patient'})
        token = login_res.get_json()['token']
        auth_headers = {'Authorization': f'Bearer {token}'}

        # 2. Disease prediction with sample symptoms and auth headers
        pred_res = self.client.post('/api/ai/predict', headers=auth_headers, json={
            'symptoms': ['headache', 'fever', 'fatigue'],
            'user_profile': {'age': 32, 'bmi': 23.5}
        })
        self.assertEqual(pred_res.status_code, 200)
        pred_data = pred_res.get_json()
        self.assertTrue(pred_data.get('success'))
        result = pred_data.get('result', {})
        self.assertIn('predictions', result)
        self.assertTrue(len(result['predictions']) > 0)
        self.assertIn('health_score', result)
        self.assertIn('recommendations', result)

        # 3. Verify record was stored in disease_predictions table
        user_id = login_res.get_json()['user']['id']
        pred_db = self.db.table('disease_predictions').select('*').eq('user_id', user_id).execute()
        self.assertTrue(len(pred_db.data) > 0)

    def test_06_ai_health_score_calculation(self):
        """Test AI health score computing endpoint"""
        res = self.client.post('/api/ai/health-score', json={
            'age': 28,
            'bmi': 21.5,
            'recent_diseases': []
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('health_score', data)
        self.assertIn('risk_level', data)
        self.assertIn('recommendations', data)

    def test_07_ai_medibot_chat_and_persistence(self):
        """Test MediBot AI Clinical Chat Assistant, chat history persistence, and clearing"""
        # Login patient to get token directly
        login_res = self.client.post('/api/auth/login/password', json={'email': 'demo@medivision.ai', 'password': 'demo123', 'role': 'patient'})
        token = login_res.get_json()['token']
        auth_headers = {'Authorization': f'Bearer {token}'}

        # 1. Send chat message
        res = self.client.post('/api/ai/medibot/chat', headers=auth_headers, json={
            'message': 'What are the symptoms and precautions for seasonal flu?',
            'history': []
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('response', data)
        self.assertTrue(len(data['response']) > 20)

        # 2. Verify messages saved in DB / Supabase via history endpoint
        hist_res = self.client.get('/api/ai/medibot/history', headers=auth_headers)
        self.assertEqual(hist_res.status_code, 200)
        hdata = hist_res.get_json()
        self.assertTrue(hdata.get('success'))
        self.assertTrue(len(hdata.get('messages', [])) >= 2)

        # 3. Clear chat history
        clear_res = self.client.post('/api/ai/medibot/clear', headers=auth_headers)
        self.assertEqual(clear_res.status_code, 200)
        cdata = clear_res.get_json()
        self.assertTrue(cdata.get('success'))

        # 4. Verify history is empty after clear
        hist_after = self.client.get('/api/ai/medibot/history', headers=auth_headers)
        self.assertEqual(len(hist_after.get_json().get('messages', [])), 0)

    def test_08_appointments_flow(self):
        """Test doctor listing, booking, viewing, and cancelling appointments"""
        # 1. Login as demo patient to get token directly
        login_res = self.client.post('/api/auth/login/password', json={
            'email': 'demo@medivision.ai',
            'password': 'demo123',
            'role': 'patient'
        })
        token = login_res.get_json()['token']
        auth_headers = {'Authorization': f'Bearer {token}'}

        # 2. Get doctors list
        doc_res = self.client.get('/api/appointments/doctors')
        self.assertEqual(doc_res.status_code, 200)
        docs = doc_res.get_json().get('doctors', [])
        self.assertTrue(len(docs) > 0)
        first_doc = docs[0]

        # 3. Book appointment for tomorrow
        tomorrow = (datetime.utcnow() + timedelta(days=2)).strftime('%Y-%m-%d')
        book_res = self.client.post('/api/appointments/book', headers=auth_headers, json={
            'doctor_name': first_doc['name'],
            'specialty': first_doc['specialty'],
            'date': tomorrow,
            'time': '10:30',
            'fee': first_doc['fee'],
            'reason': 'Routine Annual Health Assessment'
        })
        self.assertEqual(book_res.status_code, 200)
        bdata = book_res.get_json()
        self.assertTrue(bdata.get('success'))
        appointment_id = bdata['details']['id']

        # 4. List appointments
        list_res = self.client.get('/api/appointments/list', headers=auth_headers)
        self.assertEqual(list_res.status_code, 200)
        appointments = list_res.get_json().get('appointments', [])
        self.assertTrue(any(a['id'] == appointment_id for a in appointments))

        # 5. Cancel the appointment
        cancel_res = self.client.post(f'/api/appointments/cancel/{appointment_id}', headers=auth_headers)
        self.assertEqual(cancel_res.status_code, 200)
        cdata = cancel_res.get_json()
        self.assertTrue(cdata.get('success'))

    def test_09_prescriptions_and_pdf_export(self):
        """Test prescription creation by doctor and PDF export generation"""
        # 1. Login as doctor directly
        login_res = self.client.post('/api/auth/login/password', json={
            'email': 'dr.priya@medivision.ai',
            'password': 'doctor123',
            'role': 'doctor'
        })
        doc_token = login_res.get_json()['token']
        doc_headers = {'Authorization': f'Bearer {doc_token}'}

        # 2. Doctor creates prescription for demo patient
        pat_res = self.db.table('users').select('id').eq('email', 'demo@medivision.ai').execute()
        patient_id = pat_res.data[0]['id']

        create_res = self.client.post('/api/prescriptions/create', headers=doc_headers, json={
            'patient_id': patient_id,
            'diagnosis': 'Acute Pharyngitis & Mild Fever',
            'medicines': [
                {'name': 'Amoxicillin 500mg', 'dosage': '1 tablet', 'frequency': '3 times daily', 'duration': '5 days'},
                {'name': 'Paracetamol 650mg', 'dosage': '1 tablet', 'frequency': 'As needed for fever', 'duration': '3 days'}
            ],
            'notes': 'Take medications with meals. Drink plenty of warm fluids.',
            'follow_up_date': (datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%d')
        })
        self.assertEqual(create_res.status_code, 200)
        self.assertTrue(create_res.get_json().get('success'))

        # 3. Patient logs in directly and lists prescriptions
        plogin = self.client.post('/api/auth/login/password', json={'email': 'demo@medivision.ai', 'password': 'demo123', 'role': 'patient'})
        pat_token = plogin.get_json()['token']
        pat_headers = {'Authorization': f'Bearer {pat_token}'}

        plist_res = self.client.get('/api/prescriptions/list', headers=pat_headers)
        self.assertEqual(plist_res.status_code, 200)
        prescriptions = plist_res.get_json().get('prescriptions', [])
        self.assertTrue(len(prescriptions) > 0)

        # 4. Generate & Download PDF for prescription
        pdf_res = self.client.post('/api/prescriptions/generate-pdf', json={
            'id': 'RX-TEST-001',
            'doctor_name': 'Dr. Priya Sharma',
            'specialty': 'General Medicine',
            'patient_name': 'Demo Patient',
            'age': '30',
            'gender': 'Other',
            'diagnosis': 'Acute Pharyngitis',
            'medicines': [
                {'name': 'Amoxicillin', 'dosage': '500mg', 'frequency': 'TDS', 'duration': '5 days'}
            ],
            'notes': 'Stay hydrated.',
            'follow_up': 'After 1 week'
        })
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.mimetype, 'application/pdf')
        self.assertTrue(len(pdf_res.data) > 1000)

    def test_10_payments_flow(self):
        """Test payment gateway initialization, processing, and transaction history"""
        # Login patient directly
        login_res = self.client.post('/api/auth/login/password', json={'email': 'demo@medivision.ai', 'password': 'demo123', 'role': 'patient'})
        auth_headers = {'Authorization': f"Bearer {login_res.get_json()['token']}"}

        # 1. Initiate payment
        init_res = self.client.post('/api/payments/initiate', headers=auth_headers, json={'amount': 500})
        self.assertEqual(init_res.status_code, 200)
        txn_id = init_res.get_json().get('transaction_id')
        self.assertIsNotNone(txn_id)

        # 2. Process payment
        proc_res = self.client.post('/api/payments/process', headers=auth_headers, json={
            'amount': 500,
            'transaction_id': txn_id,
            'payment_method': 'upi'
        })
        self.assertEqual(proc_res.status_code, 200)
        self.assertTrue(proc_res.get_json().get('success'))

        # 3. View payment history
        hist_res = self.client.get('/api/payments/history', headers=auth_headers)
        self.assertEqual(hist_res.status_code, 200)
        hdata = hist_res.get_json()
        self.assertTrue(hdata.get('success'))
        self.assertTrue(len(hdata.get('payments', [])) > 0)

    def test_11_dashboard_and_vitals(self):
        """Test patient dashboard overview and vitals logging"""
        login_res = self.client.post('/api/auth/login/password', json={'email': 'demo@medivision.ai', 'password': 'demo123', 'role': 'patient'})
        auth_headers = {'Authorization': f"Bearer {login_res.get_json()['token']}"}

        # 1. Save Vitals
        vitals_res = self.client.post('/api/dashboard/vitals', headers=auth_headers, json={
            'heart_rate': 72,
            'bp_systolic': 120,
            'bp_diastolic': 80,
            'oxygen_saturation': 98,
            'weight': 68.5,
            'temperature': 98.4
        })
        self.assertEqual(vitals_res.status_code, 200)
        self.assertTrue(vitals_res.get_json().get('success'))

        # 2. Overview
        dash_res = self.client.get('/api/dashboard/overview', headers=auth_headers)
        self.assertEqual(dash_res.status_code, 200)
        ddata = dash_res.get_json()
        self.assertTrue(ddata.get('success'))
        self.assertIn('stats', ddata['data'])
        self.assertIn('vitals_history', ddata['data'])

    def test_12_vision_face_detection(self):
        """Test computer vision face detection endpoint with synthetic frame"""
        # Create a simple synthetic image with a circle (or face shape)
        img = np.zeros((300, 300, 3), dtype=np.uint8)
        img[:] = (240, 240, 240)
        # Encode image to base64
        _, buffer = cv2.imencode('.jpg', img)
        b64_img = 'data:image/jpeg;base64,' + base64.b64encode(buffer).decode()

        res = self.client.post('/api/vision/face/detect', json={'image': b64_img})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('faces_detected', data)
        self.assertIn('processed_image', data)

if __name__ == '__main__':
    unittest.main(verbosity=2)
