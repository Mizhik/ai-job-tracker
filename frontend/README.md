# AI Job Tracker Frontend

React + TypeScript + Vite веб-інтерфейс для проєкту AI Job Tracker.

> **Stage 07.2 — Авторизація та сесія користувача:** Реалізовано авторизацію, реєстрацію, збереження сесії в пам'яті браузера (in-memory access token + HttpOnly refresh cookie) та проксі для розробки.

## Архітектура авторизації

- **Access Token:** Зберігається тільки в оперативній пам'яті (`ApiClient` / `AuthContext`), ніколи не зберігається в `localStorage` чи `sessionStorage`.
- **Сесія та Refresh Cookie:** Сервер встановлює HttpOnly cookie для оновлення токена.
- **Відновлення сесії:** При перезавантаженні сторінки клієнт робить `GET /users/csrf`, отримує CSRF-токен, викликає `POST /users/refresh` із заголовком `X-CSRF-Token`, та запитує дані профілю `GET /users/me`.
- **Автоматичне оновлення токена:** При виконанні захищених запитів і отриманні `401 Unauthorized`, клієнт автоматично виконує single-flight оновлення токена та повторює оригінальний запит (щонайбільше один раз).
- **Вихід із системи:** Виклик `POST /users/logout` з CSRF-токеном анулює сесію на сервері та очищає локальний стан авторизації.

## Локальна розробка та Vite Dev Proxy

Vite налаштовано на проксіювання маршрутів `/users` та `/jobs` на бекенд. За замовчуванням цільова адреса бекенду — `http://localhost:8000`.

Для зміни адреси бекенду створити файл `.env.local` у папці `frontend/`:

```env
VITE_BACKEND_TARGET=http://localhost:8000
```

### 1. Установка залежностей

```bash
npm ci
```

### 2. Перевірка типів TypeScript

```bash
npm run typecheck
```

### 3. Запуск у режимі розробки

```bash
npm run dev
```

### 4. Збірка для продакшну

```bash
npm run build
```

### 5. Попередній перегляд збірки

```bash
npm run preview
```
