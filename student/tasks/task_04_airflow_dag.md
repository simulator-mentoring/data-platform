# Task 4: Написать DAG в Airflow

## Цель
Написать DAG (Directed Acyclic Graph), который автоматически считает daily_metrics и загружает их в таблицу. Это основа работы дата-инженера в Big Tech.

---

## Что такое DAG?

DAG — это набор задач (tasks), связанных зависимостями. Airflow запускает задачи по расписанию.

Пример: `create_table → calculate_metrics → validate_results`

---

## Шаг 1: Изучите пример

Посмотрите файл `dags/example_daily_user_report.py` — это рабочий DAG. Обратите внимание на:
- Импорты (DAG, PostgresOperator, PythonOperator)
- `default_args` — настройки по умолчанию
- `with DAG(...)` — определение DAG
- `>>` — зависимости между задачами
- `postgres_conn_id="mentoring_db"` — подключение к БД

---

## Шаг 2: Откройте шаблон

Откройте файл `templates/dag_daily_metrics.py` — в нём шаблон DAG с TODO-комментариями.

Скопируйте его в папку dags:
```bash
cp templates/dag_daily_metrics.py dags/dag_daily_metrics.py
```

---

## Шаг 3: Заполните TODO

В шаблоне есть 3 задачи:

### Task 1: create_table
PostgresOperator — создаёт таблицу `sandbox.daily_metrics` если она не существует (CREATE TABLE IF NOT EXISTS).

### Task 2: calculate_metrics
PostgresOperator — вычисляет метрики за вчерашний день и вставляет в таблицу.

Используйте `INSERT INTO ... SELECT ...` с `ON CONFLICT (report_date) DO UPDATE` — чтобы при повторном запуске данные обновлялись, а не дублировались.

### Task 3: validate_results
PythonOperator — проверяет, что данные за вчера появились в таблице. Если строка не найдена — бросает исключение.

---

## Шаг 4: Запуск в Airflow

1. Откройте http://localhost:8080
2. Найдите ваш DAG `dag_daily_metrics` (появится через ~30 секунд после сохранения файла)
3. Включите его (toggle слева)
4. Нажмите кнопку **Trigger DAG** (Play)
5. Нажмите на DAG → Graph — посмотрите, как выполняются задачи
6. Все 3 задачи должны стать зелёными (success)

### Если задача красная (failed):
1. Нажмите на красную задачу
2. Выберите **Log**
3. Прочитайте ошибку — обычно это опечатка в SQL или неправильное имя таблицы
4. Исправьте файл `dags/dag_daily_metrics.py`
5. Airflow автоматически подхватит изменения
6. Нажмите **Clear** на задаче и перезапустите

---

## Шаг 5: Проверка в DataGrip

Вернитесь в DataGrip и выполните:

```sql
SELECT * FROM sandbox.daily_metrics
ORDER BY report_date DESC
LIMIT 10;
```

Должна появиться строка за вчерашний день.

---

## Шаг 6: Git + Merge Request

```bash
git checkout -b feature/daily-metrics-dag
git add dags/dag_daily_metrics.py
git commit -m "Add daily metrics DAG"
git push origin feature/daily-metrics-dag
```

Создайте Merge Request на GitHub и отправьте ментору на ревью.

---

## Чек-лист выполнения

- [ ] Шаблон скопирован в dags/
- [ ] Все TODO заполнены
- [ ] DAG появился в Airflow UI
- [ ] DAG запущен, все 3 задачи зелёные
- [ ] Данные появились в sandbox.daily_metrics (проверили в DataGrip)
- [ ] Создан MR на GitHub
