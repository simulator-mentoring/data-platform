# BigTech Mentoring — Симулятор бигтеха

Учебная среда, имитирующая стек Big Tech компании: PostgreSQL + Airflow + Superset.

## Быстрый старт

### 1. Установите Docker Desktop
- **Mac**: https://www.docker.com/products/docker-desktop/
- **Windows**: https://www.docker.com/products/docker-desktop/ (нужен WSL2)

### 2. Клонируйте репозиторий
```bash
git clone https://github.com/simulator-mentoring/data-platform.git
cd data-platform/student
```

**Windows**: все команды выполняй в терминале WSL — открой «Ubuntu» из меню
Пуск (не PowerShell и не cmd). Клонируй в домашнюю папку WSL (`cd ~`), не на
диск `C:\`. Если в WSL не находится `docker` — Docker Desktop → Settings →
Resources → **WSL Integration** → включи для своего дистрибутива.

### 3. Запустите всё
```bash
docker compose up -d
```
Первый запуск займёт 5-10 минут (скачивание образов). Подождите 2-3 минуты после запуска.

### 4. Проверьте
```bash
docker compose ps
```
Все контейнеры должны быть `Up` / `healthy`.

### 5. Откройте сервисы

| Сервис | URL | Логин | Пароль |
|--------|-----|-------|--------|
| **Airflow** | http://localhost:8080 | admin | admin |
| **Superset** | http://localhost:8088 | admin | admin |
| **PostgreSQL** (DataGrip) | localhost:5432 | mentor_admin | mentor_secret_2024 |

---

## Задания

Выполняйте по порядку:

| # | Задание | Файл | Что изучите |
|---|---------|------|-------------|
| 1 | Установка и подключение | [task_01_setup.md](tasks/task_01_setup.md) | Docker, DataGrip, Airflow, Superset |
| 2 | SQL-запросы | [task_02_sql_explore.md](tasks/task_02_sql_explore.md) | SELECT, JOIN, GROUP BY, CTE |
| 3 | Создание таблицы | [task_03_create_table.md](tasks/task_03_create_table.md) | CREATE TABLE, INSERT...SELECT, витрины |
| 4 | DAG в Airflow | [task_04_airflow_dag.md](tasks/task_04_airflow_dag.md) | DAG, операторы, Git workflow |
| 5 | Дашборд в Superset | [task_05_superset_dashboard.md](tasks/task_05_superset_dashboard.md) | Charts, Dashboards, BI |

---

## Архитектура

```
┌─────────────────────────────────────────────┐
│  Docker (локально)                          │
│                                             │
│  ┌───────────┐     ┌──────────┐             │
│  │ PostgreSQL │────→│PgBouncer │ :6432       │
│  │   :5432    │     └──────────┘             │
│  └───────────┘                              │
│       ↑  shared_data (read-only)            │
│       ↑  sandbox (read-write)               │
│                                             │
│  ┌──────────┐      ┌──────────┐             │
│  │ Airflow  │      │ Superset │             │
│  │  :8080   │      │  :8088   │             │
│  └──────────┘      └──────────┘             │
└─────────────────────────────────────────────┘
         ↕                    ↕
    DataGrip/DBeaver      Браузер
```

---

## Данные

В схеме `shared_data` три таблицы:
- **users** (10,000) — пользователи с country, signup_date, is_premium
- **events** (~185,000) — действия воронкой: page_view → click → add_to_cart → checkout → purchase, плюс signup
- **orders** (~7,000) — заказы с amount, currency, status, product_category; каждый порождён событием purchase

Схема `sandbox` — для ваших таблиц (запись разрешена).

---

## Рабочий процесс (как в Big Tech)

```
1. git pull                    # Получить свежий код
2. Написать/изменить DAG       # В папке dags/
3. Проверить в Airflow UI      # localhost:8080
4. git add + commit + push     # Закоммитить
5. Создать Merge Request       # На GitHub
6. Code review от ментора      # Ментор проверяет
7. Merge                       # После аппрува
```

---

## Полезные команды

```bash
# Запустить все сервисы
docker compose up -d

# Остановить все сервисы
docker compose down

# Остановить и удалить все данные (полный сброс)
docker compose down -v

# Посмотреть логи конкретного сервиса
docker compose logs airflow-webserver
docker compose logs postgres

# Перезапустить один сервис
docker compose restart superset
```

---

## Troubleshooting

### "Port already in use"
```bash
lsof -i :8080   # Кто занимает порт?
```

### "Airflow webserver not starting"
```bash
docker compose down -v
docker compose up -d
# Подождать 2-3 минуты
```

### "Not enough memory"
```bash
docker stats   # Проверить использование
docker compose restart superset   # Перезапустить тяжёлый сервис
```

### Windows: "Docker Desktop requires WSL2"
```powershell
wsl --install
# Перезагрузить компьютер
```

### Данные обновились, а у меня старые

Учебные данные пересобраны: заказы теперь порождаются событиями `purchase`,
конверсия различается по платформам, события идут после регистрации. Данные
создаются один раз при первом запуске, поэтому для обновления нужен полный
сброс (таблицы в `sandbox` при этом тоже удалятся):

```bash
git pull
docker compose down -v
docker compose up -d
```

### Airflow: DAG падает с «connection mentoring_db not defined»

Коннекшн приходит из переменной окружения `AIRFLOW_CONN_MENTORING_DB` —
в списке Connections в UI он **не отображается**, это нормально, DAG-и его видят.
Если ошибка есть — у тебя старая версия проекта, обнови и пересоздай контейнеры:

```bash
git pull
docker compose up -d --force-recreate
```

Ручной запасной вариант:

```bash
docker exec -it airflow-webserver airflow connections add 'mentoring_db' \
    --conn-type 'postgres' \
    --conn-host 'pgbouncer' \
    --conn-schema 'mentoring_db' \
    --conn-login 'mentor_admin' \
    --conn-password 'mentor_secret_2024' \
    --conn-port '5432'
```

### Superset не пускает по admin / admin

Пересоздай админа вручную:

```bash
docker exec -it superset superset fab create-admin \
    --username admin --firstname Admin --lastname User \
    --email admin@example.com --password admin
```

### Скрипты падают с `\r: command not found` или `bad interpreter` (Windows)

Git подменил переводы строк (CRLF). В репозитории стоит `.gitattributes`,
который это предотвращает, — если клонировал старую версию, переклонируй проект
и работай из WSL.
