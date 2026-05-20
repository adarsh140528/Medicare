-- ============================================================
-- MediVision AI - Supabase PostgreSQL Schema
-- Run this in Supabase SQL Editor
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- USERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE,
    password_hash TEXT NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(10),
    blood_group VARCHAR(5),
    address TEXT,
    face_embedding JSONB,           -- Stored face vector
    face_registered BOOLEAN DEFAULT FALSE,
    profile_photo TEXT,             -- Base64 or URL
    health_score INTEGER DEFAULT 50,
    role VARCHAR(20) DEFAULT 'patient',  -- patient | doctor | admin
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- OTP TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS otp_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    phone VARCHAR(20),
    otp_code VARCHAR(6) NOT NULL,
    purpose VARCHAR(30) DEFAULT 'login',  -- login | register | reset
    is_used BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- LOGIN ACTIVITY TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS login_activity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    login_method VARCHAR(20),       -- face | otp | password
    face_confidence DECIMAL(5,4),
    success BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- APPOINTMENTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES users(id) ON DELETE CASCADE,
    doctor_id UUID REFERENCES users(id),
    doctor_name VARCHAR(255),
    specialty VARCHAR(100),
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending',  -- pending | confirmed | cancelled | completed
    meeting_link TEXT,
    notes TEXT,
    payment_status VARCHAR(20) DEFAULT 'unpaid',
    payment_amount DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- PAYMENTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    appointment_id UUID REFERENCES appointments(id),
    user_id UUID REFERENCES users(id),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(5) DEFAULT 'INR',
    payment_method VARCHAR(30),     -- card | upi | netbanking | wallet
    transaction_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',  -- pending | success | failed | refunded
    gateway_response JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- PRESCRIPTIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS prescriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES users(id) ON DELETE CASCADE,
    doctor_id UUID REFERENCES users(id),
    appointment_id UUID REFERENCES appointments(id),
    doctor_name VARCHAR(255),
    diagnosis TEXT,
    medicines JSONB NOT NULL,       -- Array of {name, dosage, frequency, duration}
    notes TEXT,
    follow_up_date DATE,
    pdf_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- DISEASE PREDICTIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS disease_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    symptoms JSONB NOT NULL,        -- Array of symptom strings
    predictions JSONB NOT NULL,     -- [{disease, probability, description}]
    top_disease VARCHAR(255),
    confidence DECIMAL(5,4),
    health_risk_score INTEGER,
    recommendations JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- HEALTH RECORDS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS health_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    record_type VARCHAR(50),        -- blood_test | xray | mri | vitals
    title VARCHAR(255),
    data JSONB,
    file_url TEXT,
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- VITALS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS vitals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    heart_rate INTEGER,
    blood_pressure_sys INTEGER,
    blood_pressure_dia INTEGER,
    temperature DECIMAL(4,1),
    oxygen_saturation INTEGER,
    weight DECIMAL(5,2),
    height DECIMAL(5,2),
    bmi DECIMAL(4,2),
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- VISION SESSIONS TABLE (OpenCV)
-- ============================================================
CREATE TABLE IF NOT EXISTS vision_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_start TIMESTAMPTZ DEFAULT NOW(),
    session_end TIMESTAMPTZ,
    fatigue_alerts INTEGER DEFAULT 0,
    posture_alerts INTEGER DEFAULT 0,
    blink_count INTEGER DEFAULT 0,
    avg_heart_rate INTEGER,
    skin_analysis JSONB,
    mask_detected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- CHAT HISTORY TABLE (MediBot)
-- ============================================================
CREATE TABLE IF NOT EXISTS chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(10) NOT NULL,      -- user | assistant
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- NOTIFICATIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    message TEXT,
    type VARCHAR(30),               -- appointment | health | alert | system
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_predictions_user ON disease_predictions(user_id);
CREATE INDEX idx_vitals_user ON vitals(user_id, recorded_at DESC);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);

-- ============================================================
-- SAMPLE DOCTORS DATA
-- ============================================================
INSERT INTO users (full_name, email, phone, password_hash, gender, role, health_score) VALUES
('Dr. Priya Sharma', 'dr.priya@medivision.ai', '+919876543210', '$2b$12$placeholder', 'female', 'doctor', 95),
('Dr. Rahul Mehta', 'dr.rahul@medivision.ai', '+919876543211', '$2b$12$placeholder', 'male', 'doctor', 95),
('Dr. Ananya Patel', 'dr.ananya@medivision.ai', '+919876543212', '$2b$12$placeholder', 'female', 'doctor', 95),
('Dr. Vikram Singh', 'dr.vikram@medivision.ai', '+919876543213', '$2b$12$placeholder', 'male', 'doctor', 95);

-- ============================================================
-- ROW LEVEL SECURITY (Enable for production)
-- ============================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE prescriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE disease_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE vitals ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- RLS POLICIES — SERVICE ROLE BYPASS
-- The backend uses SUPABASE_SERVICE_KEY which bypasses RLS
-- automatically in Supabase. These policies are for completeness
-- and to allow anon reads where needed.
-- 
-- IMPORTANT: Without these policies the anon key cannot read
-- users/vitals/etc even for server-side logic. The backend now
-- always uses the service key for all DB reads/writes, so these
-- policies are only needed if you ever use the anon client.
-- ============================================================

-- Allow service role full access (Supabase does this automatically,
-- but explicit policies prevent confusion):
CREATE POLICY "service_role_all_users" ON users
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_all_appointments" ON appointments
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_all_prescriptions" ON prescriptions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_all_predictions" ON disease_predictions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_all_vitals" ON vitals
    FOR ALL TO service_role USING (true) WITH CHECK (true);
