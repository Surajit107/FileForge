# FileForge

Personal online file converter built with **Django** and a framework-agnostic **engines** layer.

Upload a file → choose an output format → download the result.

**Currently supported (F2)**

| Source | Targets |
|--------|---------|
| Markdown (`.md`) | PDF, DOCX, HTML, TXT |
| DOCX | PDF *(LibreOffice required)*, TXT, MD *(best effort)* |
| PDF | TXT, MD *(best effort)*, DOCX *(best effort)* |

Roadmap: [docs/PLAN.md](docs/PLAN.md)

---

## Requirements

- **Python** 3.11+ (3.12 / 3.14 also fine) — prefer an install on your programming drive
- **[uv](https://docs.astral.sh/uv/)** (creates/manages project `.venv` and lockfile)
- **Git** (optional)
- **Docker** + Docker Compose (optional)

Source of truth for Python deps: `pyproject.toml` + `uv.lock`.  
`requirements/*.txt` are **exported lock snapshots** for Docker / pip fallback — regenerate after dependency changes:

```bash
uv export --no-hashes --no-emit-project -o requirements/local.txt
uv export --no-hashes --no-emit-project -o requirements/base.txt
uv export --no-hashes --no-emit-project --group prod -o requirements/production.txt
```

---

## Quick start (first time)

Copy-paste from the repository root (`FILE_CONVERTER/`):

**Windows (Git Bash):**

```bash
# uv on PATH (this machine: P:\Tools\uv)
export PATH="/p/Tools/uv:$PATH"

uv sync
cp .env.example .env
source .venv/Scripts/activate
python main.py migrate
python main.py runserver
```

**Windows (PowerShell):**

```powershell
# uv on PATH (this machine: P:\Tools\uv)
$env:Path = "P:\Tools\uv;$env:Path"

uv sync
Copy-Item .env.example .env
.\.venv\Scripts\Activate.ps1
python main.py migrate
python main.py runserver
```

**macOS / Linux:**

```bash
uv sync
cp .env.example .env
source .venv/bin/activate
python main.py migrate
python main.py runserver
```

Or skip activation and use `uv run` for any command:

```bash
uv run python main.py migrate
uv run python main.py runserver
```

When the server starts, open:

**http://127.0.0.1:8000/**

Stop the server with `Ctrl + C`.

### uv locations on this machine (P: programming drive)

| What | Path |
|------|------|
| `uv` binary | `P:\Tools\uv` |
| Package cache | `P:\DevData\uv\cache` |
| Managed Python (if uv downloads one) | `P:\DevData\uv\python` |
| uv tools | `P:\DevData\uv\tools` |
| Global uv config | `P:\DevData\uv\uv.toml` (`UV_CONFIG_FILE`) |
| Project venv | `P:\Projects\PROTOTYPES\FILE_CONVERTER\.venv` |

User env vars already point cache/python/tool dirs at `P:\DevData\uv\...`. Open a **new** terminal after install so PATH picks up `P:\Tools\uv`.

---

## Daily run (already set up)

If the project is already initialized:

```bash
# 1) Go to project root
cd /path/to/FILE_CONVERTER

# 2) Ensure deps match lockfile (cheap if unchanged)
uv sync

# 3) Activate venv OR use uv run
source .venv/Scripts/activate          # Git Bash (Windows)
# source .venv/bin/activate            # macOS / Linux
# .\.venv\Scripts\Activate.ps1         # PowerShell

# 4) Start server
python main.py runserver
# uv run python main.py runserver
```

Then open **http://127.0.0.1:8000/**

### Optional: async workers (F2)

Local default keeps `CONVERSION_SYNC_ENABLED=True` (convert inside the request). For real queue mode:

```bash
# Terminal A — Redis (Docker)
docker run --rm -p 6379:6379 redis:7-alpine

# Terminal B — Celery worker
source .venv/Scripts/activate
celery -A config worker -l info

# Terminal C — Celery beat (hourly expired-job purge)
celery -A config beat -l info

# Terminal D — web
# set CONVERSION_SYNC_ENABLED=False in .env first
python main.py runserver
```

`docx → pdf` requires LibreOffice (`soffice` on PATH). Without it, that pair fails with a clear error. `uv` does **not** install LibreOffice.

---

## 1. Initialize the project (detailed)

Run all commands from the repository root.

### 1.1 Install uv (once per machine)

**Windows (PowerShell):**

```powershell
$env:UV_INSTALL_DIR = "P:\Tools\uv"
irm https://astral.sh/uv/install.ps1 | iex
```

Add `P:\Tools\uv` to your user PATH if the installer did not.

### 1.2 Create `.venv` and install dependencies

```bash
uv sync
```

This creates project-local `.venv` and installs from `uv.lock`.

Activate (optional if you use `uv run`):

**Windows (Git Bash):**

```bash
source .venv/Scripts/activate
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

| File | Use |
|------|-----|
| `pyproject.toml` | Declared dependencies + `prod` group |
| `uv.lock` | Locked versions (commit this) |
| `requirements/local.txt` | Exported local snapshot (Docker/pip) |
| `requirements/production.txt` | Exported prod snapshot (Docker/pip) |

### 1.3 Configure environment

```bash
cp .env.example .env
```

Edit `.env` locally as needed. Do not commit secrets. Available keys are documented only in `.env.example`.

### 1.4 Apply database migrations

```bash
uv run python main.py migrate
```

Creates local `db.sqlite3`.

### 1.5 (Optional) Create admin user

```bash
uv run python main.py createsuperuser
```

### 1.6 Verify setup

```bash
uv run python main.py check
```

Expected: `System check identified no issues`.

---

## 2. Run the development server

### 2.1 Start

With the virtualenv **activated**, or via `uv run`:

```bash
python main.py runserver
# uv run python main.py runserver
```

Default bind: `127.0.0.1:8000`.

You should see output similar to:

```text
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

(Exact wording may vary by Django version / OS.)

### 2.2 Open the app

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8000/ | Main convert page |
| http://127.0.0.1:8000/health/ | Health check (`{"status":"ok",...}`) |
| http://127.0.0.1:8000/admin/ | Django admin (after createsuperuser) |

Leave the terminal open while the server is running.

### 2.3 Use the convert UI

1. Open http://127.0.0.1:8000/
2. Drop or browse a Markdown file (example: `samples/Pronti_Deed_Exit_Risk_Table.md`)
3. Select **PDF** or **DOCX**
4. Click **Convert**
5. On the job page, click **Download**

### 2.3.1 Frontend CSS (Tailwind)

UI styles are built with Tailwind CSS v4.

```bash
# first time (needs Node.js)
npm install

# while editing templates / static/src/input.css
npm run css:watch

# one-shot production build
npm run css:build
```

| Path | Role |
|------|------|
| `static/src/input.css` | Source theme + `@source` paths |
| `static/css/app.css` | Generated CSS Django serves |
| `templates/` | HTML with Tailwind utility classes |

### 2.4 Stop the server

Press `Ctrl + C` in the terminal where `runserver` is running.

### 2.5 Custom host / port

```bash
# different port
python main.py runserver 8001

# allow LAN access
python main.py runserver 0.0.0.0:8000
```

Then open `http://127.0.0.1:8001/` (or your machine IP if using `0.0.0.0`).

### 2.6 If the server fails to start

| Symptom | What to do |
|---------|------------|
| `ModuleNotFoundError: No module named 'django'` | `uv sync`, then activate `.venv` or use `uv run` |
| `uv: command not found` | Add `P:\Tools\uv` to PATH; open a new terminal |
| `No such file or directory: main.py` | `cd` into the repo root first |
| Port already in use | `python main.py runserver 8001` |
| Config errors | Ensure `.env` exists (`cp .env.example .env`) |

---

## 3. CLI conversion (without the web server)

```bash
# activate venv first, or prefix with uv run:

python scripts/md_converter.py samples/Pronti_Deed_Exit_Risk_Table.md -f pdf
python scripts/md_converter.py samples/Pronti_Deed_Exit_Risk_Table.md -f docx
python scripts/md_converter.py samples/Pronti_Deed_Exit_Risk_Table.md -f both -o samples/out
```

---

## 4. Tests

```bash
uv run python main.py test tests.engines tests.converter --settings=config.settings.test
```

---

## 5. Common management commands

```bash
uv run python main.py makemigrations
uv run python main.py migrate
uv run python main.py purge_expired_jobs
uv run python main.py collectstatic --noinput
uv run python main.py shell
```

---

## 6. Settings modules

| Module | Use |
|--------|-----|
| `config.settings.local` | Development (`main.py` default) |
| `config.settings.production` | Gunicorn / Docker |
| `config.settings.test` | Tests |

Config keys: see `.env.example` only.

---

## 7. Project structure

```text
.
├── apps/
│   ├── core/              # health endpoint, shared context
│   └── converter/         # upload UI, jobs, services, admin
├── config/
│   ├── settings/          # base / local / production / test
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── engines/               # conversion logic (no Django views)
│   ├── registry.py
│   └── markdown/
├── docs/
├── samples/
├── scripts/
├── templates/
├── static/
├── media/                 # uploads + outputs (gitignored)
├── tests/
├── docker/
├── main.py
├── pyproject.toml         # dependency source of truth
├── uv.lock                # locked versions (commit)
├── .env.example
└── requirements/          # exported snapshots for Docker/pip
```

**Architecture rules**

- Django apps own HTTP + persistence.
- `engines/` owns conversion logic.
- Views stay thin; flow lives in `apps/converter/services/`.
- New format = new engine + one registry entry.

---

## 8. Docker (optional)

```bash
cp .env.example .env
# fill .env for your environment

docker compose -f docker/docker-compose.yml up --build
```

App: http://127.0.0.1:8000/

Stop:

```bash
docker compose -f docker/docker-compose.yml down
```

Docker still installs from `requirements/production.txt` (exported from `uv.lock`). Re-export after changing deps.

---

## 9. Troubleshooting

| Problem | Fix |
|---------|-----|
| Django not found | `uv sync` (recreates/repairs `.venv`) |
| `uv` not found | Ensure `P:\Tools\uv` is on PATH; new terminal |
| Config / secret errors | Compare your `.env` with `.env.example` |
| Port 8000 busy | `python main.py runserver 8001` |
| Upload rejected | Use a `.md` file; check upload limits in `.env` |
| Stale files | `python main.py purge_expired_jobs` |
| `docx → pdf` fails | Install LibreOffice; `uv` cannot provide `soffice` |

---

## 10. Docs

| Doc | Purpose |
|-----|---------|
| [docs/DJANGO_KT.md](docs/DJANGO_KT.md) | **Start here if you're new to Django** — folder map + where to edit what |
| [docs/PLAN.md](docs/PLAN.md) | Product roadmap and planned work |
| [docs/README.md](docs/README.md) | Docs index |
| [samples/README.md](samples/README.md) | Sample files |
