# Task 2: Исследование данных через SQL

## Цель
Познакомиться с данными в базе, написать аналитические запросы.

Все запросы выполняйте в DataGrip / DBeaver, подключившись к `mentoring_db`.

---

## Описание данных

В схеме `shared_data` три связанные таблицы. Данные синтетические, но устроены
как настоящие: у каждого пользователя своя основная платформа и своя активность,
события идут воронкой `page_view → click → add_to_cart → checkout → purchase`,
и каждый заказ порождён событием `purchase` — тот же пользователь, тот же момент
времени. События появляются только после регистрации; окно данных — последние
~18 месяцев до вчерашнего дня.

**users** — пользователи сервиса
| Колонка | Тип | Описание |
|---------|-----|----------|
| user_id | int | ID пользователя |
| username | varchar | Имя |
| email | varchar | Email |
| country | varchar | Страна (RU, US, DE...) |
| signup_date | date | Дата регистрации |
| is_premium | boolean | Премиум-подписка |

**events** — действия пользователей
| Колонка | Тип | Описание |
|---------|-----|----------|
| event_id | int | ID события |
| user_id | int | ID пользователя |
| event_type | varchar | Тип: page_view, click, purchase, signup, search, add_to_cart, checkout |
| event_date | timestamp | Дата и время |
| platform | varchar | Платформа: web, ios, android |
| session_id | varchar | ID сессии |

**orders** — заказы
| Колонка | Тип | Описание |
|---------|-----|----------|
| order_id | int | ID заказа |
| user_id | int | ID пользователя |
| order_date | timestamp | Дата заказа |
| amount | decimal | Сумма |
| currency | varchar | Валюта: USD, EUR, RUB |
| status | varchar | Статус: completed, pending, refunded, cancelled |
| product_category | varchar | Категория: electronics, clothing, food, books, games, software |

---

## Задание 1: Знакомство с таблицами

Посмотрите первые 10 строк каждой таблицы:

```sql
SELECT * FROM shared_data.users LIMIT 10;
SELECT * FROM shared_data.events LIMIT 10;
SELECT * FROM shared_data.orders LIMIT 10;
```

Посчитайте количество строк:
```sql
SELECT count(*) FROM shared_data.users;
SELECT count(*) FROM shared_data.events;
SELECT count(*) FROM shared_data.orders;
```

**Ожидаемый результат:** 10,000 users, ~185,000 events, ~7,000 orders

---

## Задание 2: Пользователи по странам

Напишите запрос, который покажет количество пользователей в каждой стране, отсортированное по убыванию.

**Подсказка:** `GROUP BY country ORDER BY count DESC`

**Ожидаемый результат:** 10 строк (RU, US, DE, FR, UK, BR, IN, JP, KR, PL), примерно по ~1000 в каждой

---

## Задание 3: Топ-5 дней по количеству заказов

Найдите 5 дней, в которые было больше всего заказов. Выведите дату и количество заказов.

**Подсказка:** используйте `order_date::date` для приведения timestamp к дате

---

## Задание 4: Revenue по месяцам

Посчитайте суммарную выручку (amount) по месяцам, только для заказов со статусом `completed` и валютой `USD`.

**Подсказка:**
```sql
date_trunc('month', order_date) AS month
```

**Ожидаемый формат:**

| month | total_revenue |
|-------|---------------|
| 2025-05-01 | 12345.67 |
| 2025-06-01 | 11234.56 |
| ... | ... |

---

## Задание 5: Средний чек по странам (JOIN)

Найдите средний чек (amount) для каждой страны. Для этого нужно соединить таблицы `orders` и `users`.

**Подсказка:**
```sql
SELECT u.country, ROUND(AVG(o.amount), 2) as avg_order
FROM shared_data.orders o
JOIN shared_data.users u ON o.user_id = u.user_id
WHERE o.status = 'completed'
GROUP BY u.country
ORDER BY avg_order DESC;
```

---

## Задание 6: Конверсия по платформам

Посчитайте для каждой платформы (web, ios, android):
- Количество уникальных пользователей с событиями
- Количество уникальных пользователей с заказами
- Конверсию (% пользователей с заказами от пользователей с событиями)

У заказов нет колонки `platform` — платформа известна только у событий. Заказ
порождён событием `purchase` на той же платформе и в тот же момент, поэтому
платформу заказа можно взять из этого события (JOIN по `user_id` и времени).
Пользователь может пользоваться несколькими платформами — тогда он попадёт
в несколько строк, это нормально.

**Подсказка:** нужно использовать подзапросы или CTE (WITH), и JOIN двух агрегаций.

**Ожидаемый результат:** конверсия заметно различается по платформам —
выше всего на iOS, ниже всего на Android.

---

## Чек-лист выполнения

- [X] Задание 1: посмотрели данные, посчитали строки
- [X] Задание 2: пользователи по странам
- [X] Задание 3: топ-5 дней по заказам
- [X] Задание 4: revenue по месяцам
- [X] Задание 5: средний чек по странам (JOIN)
- [X] Задание 6: конверсия по платформам (CTE + JOIN)

task 2

SELECT
	country,
	COUNT(*) AS count
FROM
	shared_data.users
GROUP BY
	country
ORDER BY
	count DESC;

task 3


SELECT
	order_date::date AS date,
	COUNT(DISTINCT order_id) AS orders_cnt
FROM
	shared_data.orders
GROUP BY
	order_date::date
ORDER BY
	orders_cnt DESC
LIMIT 5;

task 4


SELECT
	DATE_TRUNC('month', order_date)::date AS month,
	ROUND(SUM(amount), 2) AS total_revenue
FROM
	shared_data.orders
WHERE
	status = 'completed'
	AND currency = 'USD'
GROUP BY
	DATE_TRUNC('month', order_date)
ORDER BY
	month;


task 5

SELECT
	u.country,
	ROUND(AVG(o.amount), 2) AS avg_order
FROM
	shared_data.orders o
JOIN
	shared_data.users u
	ON o.user_id = u.user_id
WHERE
	o.status = 'completed'
	AND o.currency = 'USD'
GROUP BY
	u.country
ORDER BY
	avg_order DESC;

task 6

WITH ev AS (
	SELECT
		platform,
		COUNT(DISTINCT user_id) AS users_events
	FROM
		shared_data.events
	WHERE
		platform IN ('web', 'ios', 'android')
	GROUP BY
		platform
),
ord AS (
	SELECT
		e.platform,
		COUNT(DISTINCT o.user_id) AS users_orders
	FROM
		shared_data.orders o
	INNER JOIN
		shared_data.events e
		ON e.user_id = o.user_id
		AND e.event_type = 'purchase'
		AND e.event_date = o.order_date
	WHERE
		e.platform IN ('web', 'ios', 'android')
	GROUP BY
		e.platform
)
SELECT
	ev.platform,
	ev.users_events,
	COALESCE(ord.users_orders, 0) AS users_orders,
	ROUND(
		100.0 * COALESCE(ord.users_orders, 0) / NULLIF(ev.users_events, 0),
	2) AS cr_pct
FROM
	ev
LEFT JOIN
	ord USING (platform)
ORDER BY
	cr_pct DESC;