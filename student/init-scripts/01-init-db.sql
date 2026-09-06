-- =============================================
-- BigTech Mentoring — Database Initialization
-- Creates shared schema with sample data
-- =============================================
--
-- Данные генерируются как связная история, а не тремя независимыми
-- случайными таблицами:
--   * у каждого пользователя есть основная платформа и своя активность
--     (тяжёлый хвост: немногие пользователи делают много сессий);
--   * события идут воронкой page_view -> click -> add_to_cart -> checkout -> purchase,
--     и вероятность дойти до покупки зависит от платформы (ios > web > android);
--   * каждый заказ порождён событием purchase: тот же пользователь, тот же момент;
--   * события только после регистрации; окно данных — последние ~18 месяцев
--     до вчерашнего дня включительно, чтобы ежедневные DAG-и находили данные.

-- Shared schema for all students (read-only data)
CREATE SCHEMA IF NOT EXISTS shared_data;

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

-- Воспроизводимость: у всех студентов одинаковые данные
SELECT setseed(0.2024);

-- ---------- Пользователи ----------
-- Страны с разными долями, регистрации за последние ~18 месяцев
INSERT INTO shared_data.users (username, email, country, signup_date, is_premium)
SELECT
    'user_' || i,
    'user_' || i || '@example.com',
    CASE
        WHEN r < 0.30 THEN 'RU' WHEN r < 0.48 THEN 'US' WHEN r < 0.58 THEN 'DE'
        WHEN r < 0.66 THEN 'FR' WHEN r < 0.74 THEN 'UK' WHEN r < 0.81 THEN 'BR'
        WHEN r < 0.88 THEN 'IN' WHEN r < 0.93 THEN 'JP' WHEN r < 0.97 THEN 'KR'
        ELSE 'PL'
    END,
    CURRENT_DATE - 540 + (random() * 530)::int,
    random() < 0.25
FROM (SELECT i, random() AS r FROM generate_series(1, 10000) AS i) AS t;

-- ---------- Скрытые характеристики пользователей ----------
-- Основная платформа и число сессий (экспоненциальное распределение —
-- у большинства мало сессий, у немногих очень много; премиумы активнее)
CREATE TEMP TABLE user_latent AS
SELECT
    u.user_id,
    u.signup_date,
    u.country,
    CASE WHEN p < 0.45 THEN 'web' WHEN p < 0.75 THEN 'ios' ELSE 'android' END AS primary_platform,
    GREATEST(1, ceil(-ln(random()) * CASE WHEN u.is_premium THEN 9 ELSE 5 END))::int AS n_sessions
FROM (SELECT *, random() AS p FROM shared_data.users) AS u;

-- ---------- Сессии ----------
-- Сессия идёт на основной платформе пользователя (85%) или на случайной;
-- момент сессии — после регистрации и не позже вчерашнего дня
CREATE TEMP TABLE sessions AS
SELECT
    l.user_id,
    md5(l.user_id::text || '-' || s::text) AS session_id,
    CASE WHEN random() < 0.85 THEN l.primary_platform
         ELSE (ARRAY['web', 'ios', 'android'])[1 + floor(random() * 3)::int]
    END AS platform,
    (l.signup_date + (random() * (CURRENT_DATE - 1 - l.signup_date))::int)::timestamp
        + (random() * 86399)::int * interval '1 second' AS started_at,
    random() AS r_search,
    random() AS r_click,
    random() AS r_cart,
    random() AS r_checkout,
    random() AS r_purchase
FROM user_latent AS l
CROSS JOIN LATERAL generate_series(1, l.n_sessions) AS s;

-- ---------- Воронка ----------
-- Каждый следующий шаг возможен только после предыдущего.
-- Доходимость до checkout и purchase зависит от платформы: ios > web > android
CREATE TEMP TABLE funnel AS
SELECT
    s.*,
    (r_search < 0.50) AS did_search,
    (r_click < 0.65) AS did_click,
    (r_click < 0.65 AND r_cart < 0.40) AS did_cart,
    (r_click < 0.65 AND r_cart < 0.40
        AND r_checkout < CASE platform WHEN 'ios' THEN 0.70 WHEN 'web' THEN 0.60 ELSE 0.45 END) AS did_checkout,
    (r_click < 0.65 AND r_cart < 0.40
        AND r_checkout < CASE platform WHEN 'ios' THEN 0.70 WHEN 'web' THEN 0.60 ELSE 0.45 END
        AND r_purchase < CASE platform WHEN 'ios' THEN 0.80 WHEN 'web' THEN 0.70 ELSE 0.55 END) AS did_purchase
FROM sessions AS s;

-- ---------- События ----------
INSERT INTO shared_data.events (user_id, event_type, event_date, platform, session_id, properties)
SELECT user_id, 'signup', signup_date::timestamp + (random() * 86399)::int * interval '1 second',
       primary_platform, md5('signup-' || user_id::text), '{}'::jsonb
FROM user_latent
UNION ALL
SELECT user_id, 'page_view', started_at, platform, session_id, '{}'::jsonb
FROM funnel
UNION ALL
SELECT user_id, 'search', started_at + interval '15 seconds', platform, session_id, '{}'::jsonb
FROM funnel WHERE did_search
UNION ALL
SELECT user_id, 'click', started_at + interval '40 seconds', platform, session_id, '{}'::jsonb
FROM funnel WHERE did_click
UNION ALL
SELECT user_id, 'add_to_cart', started_at + interval '2 minutes', platform, session_id, '{}'::jsonb
FROM funnel WHERE did_cart
UNION ALL
SELECT user_id, 'checkout', started_at + interval '4 minutes', platform, session_id, '{}'::jsonb
FROM funnel WHERE did_checkout
UNION ALL
SELECT user_id, 'purchase', started_at + interval '5 minutes', platform, session_id, '{}'::jsonb
FROM funnel WHERE did_purchase;

-- ---------- Заказы ----------
-- Один заказ на каждое событие purchase: тот же пользователь, тот же момент.
-- Сумма зависит от категории, валюта — от страны пользователя
INSERT INTO shared_data.orders (user_id, order_date, amount, currency, status, product_category)
SELECT
    f.user_id,
    f.started_at + interval '5 minutes',
    round((
        (5 + random() * random() * 300)
        * CASE f.category
              WHEN 'electronics' THEN 2.0 WHEN 'software' THEN 1.2 WHEN 'clothing' THEN 0.8
              WHEN 'games' THEN 0.7 WHEN 'food' THEN 0.4 ELSE 0.3
          END
        * CASE WHEN l.country = 'RU' THEN 90 WHEN l.country IN ('DE', 'FR', 'PL') THEN 0.9 ELSE 1 END
    )::numeric, 2),
    CASE WHEN l.country = 'RU' THEN 'RUB' WHEN l.country IN ('DE', 'FR', 'PL') THEN 'EUR' ELSE 'USD' END,
    CASE WHEN f.r_status < 0.85 THEN 'completed' WHEN f.r_status < 0.90 THEN 'pending'
         WHEN f.r_status < 0.95 THEN 'refunded' ELSE 'cancelled' END,
    f.category
FROM (
    SELECT *,
           random() AS r_status,
           (ARRAY['electronics', 'clothing', 'food', 'books', 'games', 'software'])[1 + floor(random() * 6)::int] AS category
    FROM funnel WHERE did_purchase
) AS f
JOIN user_latent AS l USING (user_id);

DROP TABLE funnel;
DROP TABLE sessions;
DROP TABLE user_latent;

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
