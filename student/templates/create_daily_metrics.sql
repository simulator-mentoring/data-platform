-- =============================================
-- Task 3: Создание таблицы daily_metrics
-- Заполните все TODO и выполните в DataGrip
-- =============================================

-- Шаг 1: Создание таблицы
CREATE TABLE IF NOT EXISTS sandbox.daily_metrics (
    report_date     DATE PRIMARY KEY,
    total_users     INTEGER NOT NULL DEFAULT 0,
    new_users       INTEGER NOT NULL DEFAULT 0,
    total_events    INTEGER NOT NULL DEFAULT 0,
    total_orders    INTEGER NOT NULL DEFAULT 0,
    total_revenue   DECIMAL(12, 2) NOT NULL DEFAULT 0,
    avg_order_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW()
);


-- Шаг 2: Заполнение данными
-- TODO: Напишите INSERT...SELECT, который заполнит таблицу
--
-- Подсказка: используйте generate_series для создания дат,
-- и LEFT JOIN с подзапросами для каждой метрики
--
-- Структура запроса:

INSERT INTO sandbox.daily_metrics (
    report_date,
    total_users,
    new_users,
    total_events,
    total_orders,
    total_revenue,
    avg_order_amount
)
SELECT
    d.dt AS report_date,

    -- TODO: total_users — сколько пользователей зарегистрировалось ДО КОНЦА этого дня
    -- Подсказка: (SELECT count(*) FROM shared_data.users WHERE signup_date <= d.dt)
    0 AS total_users,

    -- TODO: new_users — сколько зарегистрировалось ИМЕННО в этот день
    -- Подсказка: используйте signup_date = d.dt
    0 AS new_users,

    -- TODO: total_events — количество событий за этот день
    -- Подсказка: event_date::date = d.dt
    0 AS total_events,

    -- TODO: total_orders — количество заказов за этот день
    -- Подсказка: order_date::date = d.dt
    0 AS total_orders,

    -- TODO: total_revenue — сумма amount заказов со статусом 'completed' за этот день
    -- Подсказка: WHERE status = 'completed' AND order_date::date = d.dt
    0 AS total_revenue,

    -- TODO: avg_order_amount — средний amount заказов за этот день
    -- Подсказка: COALESCE(AVG(...), 0)
    0 AS avg_order_amount

FROM generate_series(
    '2024-06-01'::date,
    '2026-01-31'::date,
    '1 day'::interval
) AS d(dt)

ON CONFLICT (report_date) DO UPDATE SET
    total_users = EXCLUDED.total_users,
    new_users = EXCLUDED.new_users,
    total_events = EXCLUDED.total_events,
    total_orders = EXCLUDED.total_orders,
    total_revenue = EXCLUDED.total_revenue,
    avg_order_amount = EXCLUDED.avg_order_amount,
    created_at = NOW();


-- Шаг 3: Проверка
SELECT
    count(*) AS total_days,
    min(report_date) AS first_date,
    max(report_date) AS last_date,
    round(avg(total_revenue), 2) AS avg_daily_revenue,
    round(avg(new_users), 1) AS avg_daily_new_users
FROM sandbox.daily_metrics
WHERE total_orders > 0;
