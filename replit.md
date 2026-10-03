# AutoParts Hub — инструкции для Replit и следующих сессий

Это Django 5 приложение, реализующее учебный интернет-магазин автозапчастей. Источник требований — `docs/spec.md`.

## Запуск

1. `pip install -r requirements.txt`
2. `python manage.py migrate`
3. `python manage.py seed_demo`
4. `python manage.py runserver 0.0.0.0:$PORT`

На Replit `DATABASE_URL` и SMTP-настройки берутся из Secrets. Без `DATABASE_URL` используется SQLite, без SMTP — консольный email backend.

## Перед завершением изменений

- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test`
- проверить страницы на ширине 375, 768 и 1440 px;
- не изменять `Product.stock` напрямую: использовать `catalog.services.adjust_stock` или сервисы заказов, чтобы сохранить `StockMovement`.

## Ключевые правила

- интерфейс и письма на русском языке, валюта — рубли;
- публичен только каталог, операции покупателя требуют входа;
- заказ резервирует и списывает остаток атомарно при checkout;
- успешная тестовая карта: `4242 4242 4242 4242`, отказ: `4000 0000 0000 0002`;
- в отчёты продаж входят только оплаченные и доставленные заказы;
- custom admin расположен в `/staff/`, Django admin — в `/django-admin/`;
- старый TypeScript прототип в `artifacts/`, `lib/`, `scripts/` не является частью runtime.
