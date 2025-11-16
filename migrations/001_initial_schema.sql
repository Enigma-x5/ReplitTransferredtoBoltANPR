/*
  # Initial ANPR City Schema

  ## Overview
  This migration creates the foundational database schema for the ANPR City API.
  It includes tables for user management, camera configuration, video uploads,
  license plate detection events, human-in-the-loop corrections, BOLO alerts,
  licensing/metering, data exports, and audit logging.

  ## Tables Created

  ### 1. users
  - Core authentication and authorization
  - Supports admin and clerk roles
  - Password hashing with bcrypt

  ### 2. cameras
  - Camera registry with geospatial data (lat/lon/heading)
  - RTSP URL storage for live streams
  - Active status tracking

  ### 3. uploads
  - Video upload tracking and job management
  - Links to cameras and uploading users
  - Status workflow: queued -> processing -> done/failed

  ### 4. events
  - License plate detection records
  - Includes plate text, normalized version, confidence, bounding box
  - Review workflow: unreviewed -> confirmed/corrected/rejected
  - Links to cameras and uploads

  ### 5. corrections
  - Human corrections to detected plates
  - Tracks original vs corrected values
  - Export tracking for retraining datasets

  ### 6. bolos (Be On the Lookout)
  - Alert patterns for specific plates
  - Webhook and email notification configuration
  - Priority and expiration support

  ### 7. bolo_matches
  - Records when an event matches a BOLO
  - Notification delivery tracking

  ### 8. licenses
  - License key management for on-prem deployments
  - Feature flags and camera limits
  - Node activation tracking

  ### 9. usage_reports
  - Metering data from client deployments
  - Camera count and event volume tracking

  ### 10. exports
  - Async export job tracking
  - Produces labeled datasets for retraining

  ### 11. audit_logs
  - Comprehensive activity logging
  - User actions, IP addresses, timestamps

  ## Security
  - All tables created with RLS disabled initially (application-level security via JWT)
  - Passwords stored as bcrypt hashes
  - Audit logging for compliance

  ## Indexes
  - Primary keys on all id columns (UUID)
  - Foreign key indexes for joins
  - Search indexes on plates, timestamps, status fields
*/

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enums
CREATE TYPE user_role AS ENUM ('admin', 'clerk');
CREATE TYPE upload_status AS ENUM ('queued', 'processing', 'done', 'failed');
CREATE TYPE review_state AS ENUM ('unreviewed', 'confirmed', 'corrected', 'rejected');
CREATE TYPE export_status AS ENUM ('pending', 'processing', 'completed', 'failed');

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'clerk',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Cameras table
CREATE TABLE IF NOT EXISTS cameras (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    heading DOUBLE PRECISION,
    rtsp_url TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cameras_active ON cameras(active);
CREATE INDEX IF NOT EXISTS idx_cameras_location ON cameras(lat, lon);

-- Uploads table
CREATE TABLE IF NOT EXISTS uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(255) UNIQUE NOT NULL,
    camera_id UUID REFERENCES cameras(id),
    uploaded_by UUID NOT NULL REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    status upload_status DEFAULT 'queued',
    error_message TEXT,
    metadata JSONB,
    events_detected INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_uploads_job_id ON uploads(job_id);
CREATE INDEX IF NOT EXISTS idx_uploads_status ON uploads(status);
CREATE INDEX IF NOT EXISTS idx_uploads_camera ON uploads(camera_id);
CREATE INDEX IF NOT EXISTS idx_uploads_user ON uploads(uploaded_by);

-- Events table
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    upload_id UUID NOT NULL REFERENCES uploads(id),
    camera_id UUID NOT NULL REFERENCES cameras(id),
    plate VARCHAR(50) NOT NULL,
    normalized_plate VARCHAR(50) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    bbox JSONB NOT NULL,
    frame_no INTEGER NOT NULL,
    captured_at TIMESTAMP NOT NULL,
    crop_path TEXT NOT NULL,
    review_state review_state DEFAULT 'unreviewed',
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_plate ON events(plate);
CREATE INDEX IF NOT EXISTS idx_events_normalized ON events(normalized_plate);
CREATE INDEX IF NOT EXISTS idx_events_camera ON events(camera_id);
CREATE INDEX IF NOT EXISTS idx_events_upload ON events(upload_id);
CREATE INDEX IF NOT EXISTS idx_events_captured ON events(captured_at);
CREATE INDEX IF NOT EXISTS idx_events_review_state ON events(review_state);

-- Corrections table
CREATE TABLE IF NOT EXISTS corrections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id),
    original_plate VARCHAR(50) NOT NULL,
    corrected_plate VARCHAR(50) NOT NULL,
    corrected_by UUID NOT NULL REFERENCES users(id),
    confidence_before DOUBLE PRECISION NOT NULL,
    comments TEXT,
    is_exported BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_corrections_event ON corrections(event_id);
CREATE INDEX IF NOT EXISTS idx_corrections_corrected_plate ON corrections(corrected_plate);
CREATE INDEX IF NOT EXISTS idx_corrections_exported ON corrections(is_exported);

-- BOLOs table
CREATE TABLE IF NOT EXISTS bolos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plate_pattern VARCHAR(100) NOT NULL,
    description TEXT,
    created_by UUID NOT NULL REFERENCES users(id),
    active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 1,
    notification_webhook TEXT,
    notification_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bolos_pattern ON bolos(plate_pattern);
CREATE INDEX IF NOT EXISTS idx_bolos_active ON bolos(active);

-- BOLO Matches table
CREATE TABLE IF NOT EXISTS bolo_matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bolo_id UUID NOT NULL REFERENCES bolos(id),
    event_id UUID NOT NULL REFERENCES events(id),
    matched_at TIMESTAMP DEFAULT NOW(),
    notification_sent BOOLEAN DEFAULT false,
    notification_error TEXT
);

CREATE INDEX IF NOT EXISTS idx_bolo_matches_bolo ON bolo_matches(bolo_id);
CREATE INDEX IF NOT EXISTS idx_bolo_matches_event ON bolo_matches(event_id);

-- Licenses table
CREATE TABLE IF NOT EXISTS licenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    license_key VARCHAR(255) UNIQUE NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    node_id VARCHAR(255),
    features JSONB NOT NULL DEFAULT '{}',
    camera_limit INTEGER NOT NULL DEFAULT 10,
    activated_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_licenses_key ON licenses(license_key);
CREATE INDEX IF NOT EXISTS idx_licenses_customer ON licenses(customer_id);
CREATE INDEX IF NOT EXISTS idx_licenses_node ON licenses(node_id);

-- Usage Reports table
CREATE TABLE IF NOT EXISTS usage_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id VARCHAR(255) NOT NULL,
    camera_count INTEGER NOT NULL,
    event_count INTEGER DEFAULT 0,
    metadata JSONB,
    reported_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_node ON usage_reports(node_id);
CREATE INDEX IF NOT EXISTS idx_usage_reported ON usage_reports(reported_at);

-- Exports table
CREATE TABLE IF NOT EXISTS exports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    requested_by UUID NOT NULL REFERENCES users(id),
    status export_status DEFAULT 'pending',
    filters JSONB,
    item_count INTEGER DEFAULT 0,
    storage_path TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_exports_requester ON exports(requested_by);
CREATE INDEX IF NOT EXISTS idx_exports_status ON exports(status);

-- Audit Logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cameras_updated_at BEFORE UPDATE ON cameras
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert bootstrap admin user (password: changeme123)
-- Password hash generated with bcrypt rounds=12
INSERT INTO users (email, username, hashed_password, role)
VALUES (
    'admin@example.com',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5qlJfWvKW6jO6',
    'admin'
) ON CONFLICT (email) DO NOTHING;
