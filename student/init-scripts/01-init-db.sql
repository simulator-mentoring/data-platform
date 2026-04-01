-- =============================================
-- BigTech Mentoring — Database Initialization
-- Creates shared schema with sample data
-- =============================================

-- Shared schema for all students (read-only data)
CREATE SCHEMA IF NOT EXISTS shared_data;

-- Sample tables that mimic a typical analytics database

-- Users table
CREATE TABLE shared_data.users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    country VARCHAR(50),
    signup_date DATE NOT NULL,
    is_premium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Events table (user actions)
CREATE TABLE shared_data.events (
    event_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES shared_data.users(user_id),
    event_type VARCHAR(50) NOT NULL,
    event_date TIMESTAMP NOT NULL,
    platform VARCHAR(20),
    session_id VARCHAR(100),
    properties JSONB
);

-- Orders table
CREATE TABLE shared_data.orders (
    order_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES shared_data.users(user_id),
    order_date TIMESTAMP NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) DEFAULT 'completed',
    product_category VARCHAR(50)
);

-- Insert sample users
INSERT INTO shared_data.users (username, email, country, signup_date, is_premium)
SELECT
    'user_' || i,
    'user_' || i || '@example.com',
    (ARRAY['RU','US','DE','FR','UK','BR','IN','JP','KR','PL'])[1 + (random()*9)::int],
    '2024-01-01'::date + (random()*730)::int,
    random() > 0.7
FROM generate_series(1, 10000) AS i;

-- Insert sample events
INSERT INTO shared_data.events (user_id, event_type, event_date, platform, session_id, properties)
SELECT
    1 + (random()*9999)::int,
    (ARRAY['page_view','click','purchase','signup','search','add_to_cart','checkout'])[1 + (random()*6)::int],
    '2024-06-01'::timestamp + (random()*600)::int * interval '1 day' + (random()*86400)::int * interval '1 second',
    (ARRAY['web','ios','android'])[1 + (random()*2)::int],
    md5(random()::text),
    '{}'::jsonb
FROM generate_series(1, 100000) AS i;

-- Insert sample orders
INSERT INTO shared_data.orders (user_id, order_date, amount, currency, status, product_category)
SELECT
    1 + (random()*9999)::int,
    '2024-06-01'::timestamp + (random()*600)::int * interval '1 day',
    round((random()*500 + 5)::numeric, 2),
    (ARRAY['USD','EUR','RUB'])[1 + (random()*2)::int],
    (ARRAY['completed','pending','refunded','cancelled'])[1 + (random()*3)::int],
    (ARRAY['electronics','clothing','food','books','games','software'])[1 + (random()*5)::int]
FROM generate_series(1, 50000) AS i;

-- Create read-only role for students
CREATE ROLE student_readonly;
GRANT USAGE ON SCHEMA shared_data TO student_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA shared_data TO student_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA shared_data GRANT SELECT ON TABLES TO student_readonly;

-- Create a sandbox schema where students can write
CREATE SCHEMA IF NOT EXISTS sandbox;
CREATE ROLE student_write;
GRANT USAGE, CREATE ON SCHEMA sandbox TO student_write;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA sandbox TO student_write;
ALTER DEFAULT PRIVILEGES IN SCHEMA sandbox GRANT ALL ON TABLES TO student_write;

-- Create student user (shared account for simplicity)
CREATE USER student WITH PASSWORD 'student_password_CHANGE_ME';
GRANT student_readonly TO student;
GRANT student_write TO student;

-- Indexes for common queries
CREATE INDEX idx_events_user_id ON shared_data.events(user_id);
CREATE INDEX idx_events_event_date ON shared_data.events(event_date);
CREATE INDEX idx_events_event_type ON shared_data.events(event_type);
CREATE INDEX idx_orders_user_id ON shared_data.orders(user_id);
CREATE INDEX idx_orders_order_date ON shared_data.orders(order_date);

-- Done
SELECT 'Database initialized: '
    || (SELECT count(*) FROM shared_data.users) || ' users, '
    || (SELECT count(*) FROM shared_data.events) || ' events, '
    || (SELECT count(*) FROM shared_data.orders) || ' orders'
AS status;
