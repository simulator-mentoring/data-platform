# Task 5: Дашборд в Superset

## Цель
Подключить Superset к базе данных, создать графики и собрать дашборд.
Это завершающий этап: данные собраны → витрина построена → визуализация готова.

---

## Шаг 1: Подключение базы данных

1. Откройте Superset: http://localhost:8088
2. Логин: `admin`, пароль: `admin`
3. В верхнем меню: **Settings** → **Database Connections**
4. Нажмите **+ Database**
5. Выберите **PostgreSQL**
6. Заполните:
   - **Host**: `pgbouncer` (имя контейнера внутри Docker-сети)
   - **Port**: `5432`
   - **Database name**: `mentoring_db`
   - **Username**: `mentor_admin`
   - **Password**: `mentor_secret_2024`
7. Нажмите **Test Connection** — должно быть зелёное
8. Нажмите **Connect**

---

## Шаг 2: Создание Dataset

Dataset — это таблица или запрос, на основе которого строятся графики.

1. В верхнем меню: **SQL** → **SQL Lab**
2. Выберите вашу базу данных
3. Попробуйте запрос:
```sql
SELECT * FROM sandbox.daily_metrics ORDER BY report_date LIMIT 10;
```
4. Убедитесь, что данные есть

Теперь создайте dataset:
1. В верхнем меню: **+** → **Dataset**
2. Выберите:
   - Database: ваша подключенная база
   - Schema: `sandbox`
   - Table: `daily_metrics`
3. Нажмите **Add**

Создайте ещё один dataset:
1. **+** → **Dataset**
2. Schema: `shared_data`, Table: `users`
3. **Add**

---

## Шаг 3: График — Revenue по дням (Line Chart)

1. Зайдите в dataset `daily_metrics`
2. Нажмите **Create Chart**
3. Выберите тип: **Line Chart**
4. Настройте:
   - **X-Axis**: `report_date`
   - **Metrics**: `SUM(total_revenue)`
   - **Time Grain**: `Day`
5. Нажмите **Update Chart**
6. Если всё ок — нажмите **Save** → назовите "Revenue по дням"
7. Выберите **Add to new dashboard** → назовите "Daily Metrics"

---

## Шаг 4: График — Пользователи по странам (Pie Chart)

1. Зайдите в dataset `users`
2. **Create Chart** → выберите **Pie Chart**
3. Настройте:
   - **Dimensions**: `country`
   - **Metrics**: `COUNT(*)`
4. **Update Chart**
5. **Save** → "Пользователи по странам" → добавьте к дашборду "Daily Metrics"

---

## Шаг 5: Дополнительные графики (бонус)

Попробуйте добавить на дашборд ещё графики:

- **Bar Chart**: количество заказов по категориям (product_category)
- **Line Chart**: new_users по дням из daily_metrics
- **Big Number**: общее количество пользователей (COUNT из users)
- **Table**: топ-10 дней по выручке

---

## Шаг 6: Настройка дашборда

1. Откройте ваш дашборд "Daily Metrics"
2. Нажмите **Edit Dashboard** (карандаш вверху справа)
3. Перетащите графики, измените размеры
4. Добавьте заголовки и разделители через **+** → **Header** / **Divider**
5. Нажмите **Save**

---

## Чек-лист выполнения

- [ ] База подключена к Superset (Test Connection — OK)
- [ ] Datasets созданы (daily_metrics + users)
- [ ] Line Chart: revenue по дням
- [ ] Pie Chart: пользователи по странам
- [ ] Дашборд "Daily Metrics" собран из 2+ графиков
- [ ] (Бонус) Добавлены дополнительные графики
