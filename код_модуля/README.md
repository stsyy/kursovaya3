# Модуль администратора программного комплекса управления диспансером

Серверная часть: Python 3.12+, Django 5.2, Django REST Framework, PostgreSQL 16.
Клиентская часть: Vue.js 3, Vue Router, Axios, сборка Vite.

## Запуск

1. Создать базу данных PostgreSQL:
   `createuser -P medadmin` (пароль `medadmin`), `createdb -O medadmin medadmin`.
   Параметры подключения задаются переменными DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT.
   Для быстрого запуска без PostgreSQL можно задать `DB_ENGINE=sqlite`.
2. Серверная часть:
   ```
   cd backend
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py seed_demo        # демонстрационные данные, вход admin / admin12345
   ```
3. Клиентская часть:
   ```
   cd frontend
   npm install
   npm run build                     # сборка в frontend/dist, её отдаёт Django
   ```
4. `cd backend && python manage.py runserver` и открыть http://localhost:8000.

Для разработки клиентской части можно запустить `npm run dev` (порт 5173, запросы /api
перенаправляются на Django).

## Тесты

```
cd backend
python -m playwright install chromium     # один раз, для UI-тестов
python manage.py test tests.test_unit_accounts tests.test_unit_schedule tests.test_unit_appointments  # модульные
python manage.py test tests.test_integration_api                                                      # интеграционные
python manage.py test tests.test_ui                                                                   # UI (нужна сборка frontend)
```

## SMS-шлюз

По умолчанию SMS пишутся в журнал (SMS_BACKEND=console). Для реального шлюза:
SMS_BACKEND=http, SMS_GATEWAY_URL, SMS_GATEWAY_TOKEN, SMS_SENDER.
