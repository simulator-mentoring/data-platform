# BigTech Mentoring — Infrastructure Setup

## Обзор

Учебная среда, имитирующая стек Big Tech компании:

| Компонент | Где работает | Зачем |
|-----------|-------------|-------|
| **PostgreSQL** | VPS сервер | Общая база с учебными данными |
| **PgBouncer** | VPS сервер | Пулинг коннектов (40 студентов) |
| **GitHub** | Облако (бесплатно) | Код, DAGи, code review, Pull Requests |
| **Airflow** | Локально у студента | Оркестрация ETL-пайплайнов |
| **Superset** | Локально у студента | Дашборды и аналитика |

```
┌─────────────────────────────┐
│  VPS Сервер (4GB RAM)       │
│  ┌───────────┐ ┌──────────┐ │
│  │ PostgreSQL│→│PgBouncer │──── порт 6432
│  └───────────┘ └──────────┘ │
└─────────────────────────────┘
          ↕ TCP :6432
┌─────────────────────────────┐
│  Локально у студента        │
│  ┌────────┐ ┌────────────┐  │
│  │Airflow │ │  Superset   │  │
│  └────────┘ └────────────┘  │
│  ┌────────────────────────┐ │
│  │ Local PG (metadata)    │ │
│  └────────────────────────┘ │
└─────────────────────────────┘
```

---

## Часть 1: Настройка сервера (для ментора)

### Требования
- VPS: 4GB RAM, 50GB диск, Ubuntu 22/24
- Docker + Docker Compose

### Шаг 1: Установка Docker

```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Устанавливаем Docker Compose plugin
sudo apt install docker-compose-plugin -y

# Перелогиниваемся
exit
# (подключиться заново)
```

### Шаг 2: Развёртывание базы

```bash
# Клонируем репозиторий (или копируем файлы)
cd ~
mkdir mentoring-server && cd mentoring-server

# Копируем файлы из папки server/:
# - docker-compose.yml
# - .env
# - postgresql.conf
# - init-scripts/01-init-db.sql

# ВАЖНО: Измените пароли в .env!
nano .env

# Запускаем
docker compose up -d

# Проверяем
docker compose ps
docker compose logs postgres
```

### Шаг 3: Настройка firewall

```bash
# Открываем только порт PgBouncer
sudo ufw allow 22/tcp       # SSH
sudo ufw allow 6432/tcp     # PgBouncer
sudo ufw enable

# Проверяем подключение извне
# (с другой машины)
psql -h YOUR_SERVER_IP -p 6432 -U student -d mentoring_db
```

### Шаг 4: Проверка данных

```bash
docker compose exec postgres psql -U mentor_admin -d mentoring_db -c "
  SELECT 'users' as tbl, count(*) FROM shared_data.users
  UNION ALL
  SELECT 'events', count(*) FROM shared_data.events
  UNION ALL
  SELECT 'orders', count(*) FROM shared_data.orders;
"
```

Ожидаемый результат: ~10,000 users, ~100,000 events, ~50,000 orders.

---

## Часть 2: Настройка студента

### Требования
- Docker Desktop (Windows/Mac) или Docker Engine (Linux)
- 8GB+ RAM
- Git

### Шаг 1: Установка Docker Desktop

**Windows:**
1. Скачайте Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Включите WSL2 (если не включен): `wsl --install`
3. Перезагрузите компьютер
4. Запустите Docker Desktop

**Mac:**
1. Скачайте Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Установите и запустите

**Linux:**
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

### Шаг 2: Клонирование репозитория

```bash
# Клонируем учебный репозиторий
git clone https://github.com/YOUR_ORG/bigtech-mentoring.git
cd bigtech-mentoring/student
```

### Шаг 3: Настройка .env

```bash
# Заполните IP-адрес сервера (получите от ментора)
cp .env.example .env
nano .env  # или откройте в любом редакторе
```

Измените `YOUR_SERVER_IP` на реальный IP сервера.

### Шаг 4: Запуск

```bash
# Первый запуск (скачает образы ~5-10 мин)
docker compose up -d

# Подождите 1-2 минуты, затем проверьте
docker compose ps
```

### Шаг 5: Проверка

| Сервис | URL | Логин | Пароль |
|--------|-----|-------|--------|
| Airflow | http://localhost:8080 | admin | admin |
| Superset | http://localhost:8088 | admin | admin |

### Шаг 6: Подключение Superset к серверной базе

1. Откройте Superset: http://localhost:8088
2. Settings → Database Connections → + Database
3. Выберите PostgreSQL
4. Заполните:
   - Host: `YOUR_SERVER_IP`
   - Port: `6432`
   - Database: `mentoring_db`
   - Username: `student`
   - Password: (пароль от ментора)
5. Test Connection → Connect

---

## Рабочий процесс (как в Big Tech)

### Ежедневный цикл

```
1. git pull                    # Получить свежий код
2. Написать/изменить DAG       # В папке dags/
3. Проверить в Airflow UI      # localhost:8080
4. git add + commit + push     # Закоммитить
5. Создать Pull Request        # На GitHub
6. Code review                 # Другие студенты ревьюят
7. Merge                       # После аппрува
```

### Создание нового DAG

```bash
# Создайте файл в папке dags/
touch dags/my_first_pipeline.py


# Напишите DAG (используйте example_daily_user_report.py как шаблон)

# Airflow подхватит файл автоматически через ~30 секунд
# Проверьте в UI: http://localhost:8080
```

---

## Troubleshooting

### "Port already in use"
```bash
# Проверить что занимает порт
lsof -i :8080  # или :8088, :5433
# Остановить конфликтующий процесс или изменить порт в docker-compose.yml
```

### "Cannot connect to remote database"
```bash
# Проверить доступность сервера
telnet YOUR_SERVER_IP 6432

# Проверить .env файл
cat .env | grep REMOTE_DB_HOST
```

### "Airflow webserver not starting"
```bash
# Переинициализировать
docker compose down -v
docker compose up -d
# Подождать 2-3 минуты
```

### "Not enough memory"
```bash
# Проверить использование памяти
docker stats

# Если Superset ест слишком много, перезапустить только его
docker compose restart superset
```

### Windows: "Docker Desktop requires WSL2"
```powershell
# В PowerShell от администратора
wsl --install
# Перезагрузить компьютер
```
