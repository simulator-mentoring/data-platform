# Task 1: Установка и подключение

## Цель
Развернуть локальную среду и подключиться ко всем сервисам.

---

## Шаг 1: Установка Docker Desktop

### Mac
1. Скачайте Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Установите и запустите
3. Убедитесь, что Docker работает: откройте терминал и выполните:
```bash
docker --version
```

### Windows
1. Скачайте Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Включите WSL2 (если не включен): откройте PowerShell от администратора и выполните:
```powershell
wsl --install
```
3. Перезагрузите компьютер
4. Запустите Docker Desktop

---

## Шаг 2: Клонирование репозитория

```bash
git clone https://github.com/simulator-mentoring/data-platform.git
cd data-platform/student
```

---

## Шаг 3: Запуск всех сервисов

```bash
docker compose up -d
```

Первый запуск скачает образы (~5-10 минут в зависимости от интернета).

Подождите 2-3 минуты после запуска, затем проверьте:

```bash
docker compose ps
```

Все контейнеры должны быть в статусе `Up` или `healthy`:

| Контейнер | Статус |
|-----------|--------|
| mentoring-postgres | Up (healthy) |
| mentoring-pgbouncer | Up |
| airflow-metadata-pg | Up (healthy) |
| airflow-webserver | Up (healthy) |
| airflow-scheduler | Up |
| superset | Up |

---

## Шаг 4: Подключение DataGrip / DBeaver к базе данных

### Параметры подключения

| Параметр | Значение |
|----------|----------|
| Host | `localhost` |
| Port | `5432` |
| Database | `mentoring_db` |
| Username | `mentor_admin` |
| Password | `mentor_secret_2024` |

### DataGrip
1. Откройте DataGrip
2. Нажмите **+** → Data Source → **PostgreSQL**
3. Заполните параметры из таблицы выше
4. Нажмите **Test Connection** — должно быть зелёное OK
5. Нажмите **OK**

### DBeaver (бесплатная альтернатива)
1. Скачайте DBeaver: https://dbeaver.io/download/
2. Нажмите **New Database Connection** → **PostgreSQL**
3. Заполните параметры из таблицы выше
4. Нажмите **Test Connection** → **Finish**

### Проверка
После подключения вы должны видеть:
- Схему `shared_data` с таблицами: `users`, `events`, `orders`
- Схему `sandbox` (пустая — сюда вы будете писать свои таблицы)

Если видите только `public` — нажмите на "1 of N" рядом с названием базы и включите все схемы.

---

## Шаг 5: Проверка Airflow

1. Откройте браузер: http://localhost:8080
2. Логин: `admin`, пароль: `admin`
3. Вы должны увидеть DAG `example_daily_user_report`
4. Включите его (переключатель слева) и нажмите кнопку Play (Trigger DAG)
5. Дождитесь выполнения — все задачи должны стать зелёными

---

## Шаг 6: Проверка Superset

1. Откройте браузер: http://localhost:8088
2. Логин: `admin`, пароль: `admin`
3. Вы увидите главную страницу Superset

---

## Чек-лист выполнения

- [ ] Docker Desktop установлен и запущен
- [ ] `docker compose ps` — все контейнеры healthy/up
- [ ] DataGrip/DBeaver подключен к БД, видны таблицы в shared_data
- [ ] Airflow открывается, example DAG запустился успешно
- [ ] Superset открывается
