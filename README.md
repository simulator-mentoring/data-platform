Учебная среда, имитирующая стек продуктового аналитика / дата-аналитика в Big Tech компании. Всё работает локально в Docker.

## Зачем всё это?

Представьте: вы вышли на работу аналитиком данных в крупную IT-компанию. Первый день. Вам дают доступ к базе данных с миллионами строк, показывают дашборд, который обновляется каждое утро, и говорят: "Разберись, как это работает, и сделай новый отчёт".

Именно это мы сейчас и будем делать — но в безопасной учебной среде.

**Ваш путь в этом курсе:**

1. **Подключиться к базе данных** — как это делают аналитики каждый день, открыв DataGrip или DBeaver
2. **Написать SQL-запросы** — найти инсайты в данных о пользователях, заказах и событиях
3. **Построить витрину данных** — создать таблицу с ежедневными метриками (revenue, новые пользователи, конверсия)
4. **Автоматизировать расчёты** — написать пайплайн в Airflow, который обновляет витрину каждый день без вашего участия
5. **Собрать дашборд** — визуализировать данные в Superset, чтобы бизнес видел красивые графики
6. **Работать через Git** — код ревью, pull request'ы, ветки — как в настоящей команде

В итоге у вас будет **полный цикл**: данные в базе → автоматический расчёт → дашборд, который обновляется сам. Это именно то, что делают аналитики и дата-инженеры в Яндексе, Тинькофф, Ozon и других компаниях.

---

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
│  ┌───────────┐ ┌──────────┐ ┌────────────┐  │
│  │ PostgreSQL│→│PgBouncer │→│  Superset  │  │
│  └───────────┘ └──────────┘ └────────────┘  │
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

| # | Файл | Тип | Тема |
|---|------|-----|------|
| 1 | [task_01_setup.md](student/tasks/task_01_setup.md) | Практика | Установка и подключение |
| 2 | [task_02_sql_explore.md](student/tasks/task_02_sql_explore.md) | Практика | Исследование данных через SQL |
| 3 | [task_03_create_table.md](student/tasks/task_03_create_table.md) | Практика | Создание таблицы daily_metrics |
| - | [theory_airflow.md](student/tasks/theory_airflow.md) | Теория | Что такое Airflow и зачем он нужен |
| 4 | [task_04_airflow_dag.md](student/tasks/task_04_airflow_dag.md) | Практика | Написать DAG в Airflow |
| - | [theory_git.md](student/tasks/theory_git.md) | Теория | Git и GitHub: зачем и как |
| 5 | [task_05_superset_dashboard.md](student/tasks/task_05_superset_dashboard.md) | Практика | Дашборд в Superset |

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
│   ├── theory_airflow.md    # Теория: зачем Airflow
│   ├── task_04_airflow_dag.md
│   ├── theory_git.md        # Теория: Git и GitHub
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
