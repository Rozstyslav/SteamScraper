# Steam Scraper API

FastAPI-сервіс із трьома способами отримання даних Steam:

- `http` — пошук через HTTP API Steam;
- `headless` — отримання деталей і рецензій у headless Chrome;
- `non_headless` — відкриття сторінки гри у видимому Chrome.

Кожне виконання зберігається у SQLite. Список історії містить коротку
інформацію, а окремий маршрут повертає повний результат або помилку.

## Вимоги

- Python 3.13 або новіший;
- Chrome або Chromium для browser-сценаріїв;
- [uv](https://docs.astral.sh/uv/) — рекомендований менеджер залежностей.
- Docker Desktop — лише для запуску через Docker Compose.

Окремо встановлювати ChromeDriver не потрібно: Selenium Manager знаходить або
завантажує сумісний драйвер автоматично.

## Встановлення

```powershell
git clone <repository-url>
cd SteamScraper
uv sync
```

Без `uv`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install .
```

## Конфігурація

Усі параметри мають значення за замовчуванням. За потреби їх можна змінити
через змінні середовища. Повний перелік наведений у `.env.example`.

Приклад для PowerShell:

```powershell
$env:DATABASE_PATH="data/steam_scraper.sqlite3"
$env:STEAM_TIMEOUT_SECONDS="15"
$env:BROWSER_HEADLESS="true"
```

Файл `.env.example` є документацією параметрів; застосунок читає саме змінні
оточення і не завантажує `.env` автоматично.

## Запуск

```powershell
uv run uvicorn main:app --host 127.0.0.1 --port 8000
```

Після запуску документація OpenAPI доступна за адресою
`http://127.0.0.1:8000/docs`.

## Запуск через Docker

Найпростіший варіант — Docker Compose:

```powershell
docker compose up --build
```

API буде доступне за адресою `http://localhost:8000`, а Swagger UI —
`http://localhost:8000/docs`. SQLite зберігається у named volume
`steam_scraper_data`, тому історія не зникає після перезапуску контейнера.

Зупинка:

```powershell
docker compose down
```

Команда вище не видаляє історію. Для явного видалення volume разом із даними:

```powershell
docker compose down --volumes
```

Без Compose:

```powershell
docker build -t steam-scraper .
docker run --rm -p 8000:8000 -v steam-scraper-data:/data steam-scraper
```

Образ містить Chromium, ChromeDriver і Xvfb. Тому всі три сценарії працюють без
встановлення браузера на хості. `non_headless` запускається у віртуальному
дисплеї контейнера: сторінка відкривається, але вікно не відображається на
робочому столі хоста.

## API

### HTTP-пошук

```http
POST /api/v1/games/search
Content-Type: application/json

{"query": "Portal", "limit": 3}
```

### Відкриття гри у браузері

```http
POST /api/v1/games/open
Content-Type: application/json

{"name": "Portal 2"}
```

### Деталі через headless-браузер

```http
POST /api/v1/games/details
Content-Type: application/json

{"name": "Portal 2", "reviews_count": 3}
```

### Історія

```http
GET /api/v1/histories?limit=20&offset=0
GET /api/v1/histories/{history_id}
```

Перший маршрут повертає `id`, метод, запит, статус і часові позначки. Другий
додатково повертає результат або опис помилки.

## Коди помилок

- `404` — гру або запис історії не знайдено;
- `422` — некоректні вхідні дані;
- `502` — Steam повернув помилкову відповідь;
- `503` — браузер недоступний або не зміг відобразити сторінку;
- `504` — сплив таймаут запиту до Steam.

Під час завершення сервіс закриває керований екземпляр Chrome. Headless-драйвер
також завжди закривається у `finally`, зокрема після помилок і таймаутів.

## Тести

```powershell
uv run pytest
```

Тести використовують окрему тимчасову SQLite і не змінюють робочу історію.
