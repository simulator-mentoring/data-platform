
Учебная среда, имитирующая стек продуктового аналитика / дата аналитика в Big Tech компании. Всё работает локально в Docker.

## Стек

| Компонент | Порт | Зачем |
|-----------|------|-------|
| **PostgreSQL** | 5432 | База данных с учебными данными |
| **PgBouncer** | 6432 | Пулинг соединений |
| **Airflow** | 8080 | Оркестрация ETL-пайплайнов |
| **Superset** | 8088 | Дашборды и аналитика |

```
┌─────────────────────────────────────────────┐
│  Docker (локально)                          │
│  ┌───────────┐ ┌──────────┐ ┌────────────┐ │
│  │ PostgreSQL│→│PgBouncer │→│  Superset   │ │
│  └───────────┘ └──────────┘ └────────────┘ │
│       ↕                                     │
│  ┌────────────────────────┐                 │
│  │  Airflow (web+scheduler)│                │
│  └────────────────────────┘                 │
└─────────────────────────────────────────────┘
```

---

## Быстрый старт

### 1. Установите Docker Desktop

- **Mac/Windows:** https://www.docker.com/products/docker-desktop/

### 2. Клонируйте и запустите

```bash
git clone https://github.com/simulator-mentoring/data-platform.git
cd data-platform/student
cp .env.example .env
docker compose up -d
```

Первый запуск скачает образы (~5-10 минут). Подождите 2-3 минуты, затем проверьте:

```bash
docker compose ps
```

### 3. Проверьте сервисы

| Сервис | URL | Логин | Пароль |
|--------|-----|-------|--------|
| Airflow | http://localhost:8080 | admin | admin |
| Superset | http://localhost:8088 | admin | admin |

### 4. Подключите DataGrip/DBeaver

| Параметр | Значение |
|----------|----------|
| Host | `localhost` |
| Port | `5432` |
| Database | `mentoring_db` |
| User | `mentor_admin` |
| Password | `mentor_secret_2024` |

---

## Задания

Задания расположены в папке `tasks/` с нарастающей сложностью:

| # | Файл | Тема |
|---|------|------|
| 1 | [task_01_setup.md](student/tasks/task_01_setup.md) | Установка и подключение |
| 2 | [task_02_sql_explore.md](student/tasks/task_02_sql_explore.md) | Исследование данных через SQL |
| 3 | [task_03_create_table.md](student/tasks/task_03_create_table.md) | Создание таблицы daily_metrics |
| 4 | [task_04_airflow_dag.md](student/tasks/task_04_airflow_dag.md) | Написать DAG в Airflow |
| 5 | [task_05_superset_dashboard.md](student/tasks/task_05_superset_dashboard.md) | Дашборд в Superset |

Шаблоны с TODO для заданий 3 и 4 лежат в `templates/`.

---

## Рабочий процесс (как в Big Tech)

```
1. git pull                    # Получить свежий код
2. Написать/изменить DAG       # В папке dags/
3. Проверить в Airflow UI      # localhost:8080
4. git add + commit + push     # Закоммитить
5. Создать Pull Request        # На GitHub
6. Code review                 # Ментор ревьюит
7. Merge                       # После одобрения
```

---

## Структура проекта

```
student/
├── docker-compose.yml       # Все сервисы
├── .env.example             # Шаблон настроек
├── init-scripts/            # SQL для инициализации БД
│   └── 01-init-db.sql
├── postgresql.conf          # Настройки PostgreSQL
├── dags/                    # Airflow DAGs (ваш код!)
│   └── example_daily_user_report.py
├── tasks/                   # Задания
│   ├── task_01_setup.md
│   ├── task_02_sql_explore.md
│   ├── task_03_create_table.md
│   ├── task_04_airflow_dag.md
│   └── task_05_superset_dashboard.md
├── templates/               # Шаблоны с TODO
│   ├── create_daily_metrics.sql
│   └── dag_daily_metrics.py
├── logs/                    # Логи Airflow
└── plugins/                 # Плагины Airflow
```

---

## Самые частые проблемы

### "Port already in use"
```bash
lsof -i :8080  # или :8088, :5432
# Остановите конфликтующий процесс или измените порт в docker-compose.yml
```

### "Airflow не стартует"
```bash
docker compose down -v
docker compose up -d
# Подождите 2-3 минуты
```

### "Not enough memory"
```bash
docker stats
# Убедитесь, что Docker Desktop выделено минимум 6GB RAM
```

### Остановить все сервисы
```bash
docker compose down       # Остановить (данные сохранятся)
docker compose down -v    # Остановить и удалить данные (полный сброс)
```
