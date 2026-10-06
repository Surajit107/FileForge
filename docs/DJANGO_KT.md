# FileForge — Django Knowledge Transfer (KT)

**Who this is for:** you, learning Django while building FileForge.  
**Goal:** understand *core Django wiring* — where things live, how they connect, and what you must configure vs “import”.

Read the **Core concepts** section carefully. Bookmark the cheat sheets. Come back when something feels magical.

---

## 1. The one-sentence mental model

```text
Browser → URL → View → (Form / Service / Engine) → Template → HTML back to browser
```

| Piece | Job |
|-------|-----|
| **URL** | Maps a path (`/`, `/jobs/...`) to a Python function |
| **View** | Handles the HTTP request (thin — don’t put conversion logic here) |
| **Form** | Validates upload + target format |
| **Service** | Orchestrates job create + run |
| **Engine** | Actually converts the file (no Django imports) |
| **Model** | Saves job state in the database |
| **Template** | HTML Django fills with data |
| **Static** | CSS / JS / images (not database content) |

---

## 2. Core Django concepts (the wiring)

### 2.0 The #1 beginner confusion

In normal Python you write:

```python
from something import helper
```

In Django, many things are **not imported that way**. They are **wired by settings + string names**.

| Thing | How Django finds it | Do you `import` it? |
|-------|---------------------|---------------------|
| Templates (HTML) | `TEMPLATES` setting + string path in `render()` | **No** Python import of the HTML file |
| Static CSS/JS | `STATICFILES_DIRS` + `{% static %}` | **No** — load tag in template |
| Apps | `INSTALLED_APPS` list | App code: yes when you use it; registration: settings |
| URLs | `ROOT_URLCONF` + `include()` | Yes — `include("apps.converter.urls")` |
| Views | Imported inside `urls.py` | Yes — normal Python import |
| Models | App in `INSTALLED_APPS` + import where used | Yes — `from apps.converter.models import ...` |
| Settings values | `from django.conf import settings` | Yes — but values come from settings modules / `.env` |

**Rule:**  
- **Python logic** (views, forms, models, services) → normal `import`  
- **HTML / CSS / JS files** → configure in settings, then reference by **path string**

---

### 2.1 Templates — “I put a file in `templates/`. Now what?”

You do **not** import HTML into Python.

#### Step A — Tell Django where the folder is (one-time config)

In `config/settings/base.py`:

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],   # ← our project templates/
        "APP_DIRS": True,                   # ← also look in each app’s templates/
        "OPTIONS": {
            "context_processors": [
                # ... see section 2.6
            ],
        },
    },
]
```

| Setting | Meaning in FileForge |
|---------|----------------------|
| `DIRS` | Always search `FILE_CONVERTER/templates/` |
| `APP_DIRS = True` | Also search `apps/<app>/templates/` if you add those later |

Once this exists, **new HTML files just go in the folder**. No extra import.

#### Step B — Use the template from a view (string path)

```python
# apps/converter/views.py
from django.shortcuts import render

return render(
    request,
    "converter/convert.html",   # ← string path under templates/
    {
        "form": form,
        "pairs": list_pairs(),
    },
)
```

| You wrote | Django looks for |
|-----------|------------------|
| `"converter/convert.html"` | `templates/converter/convert.html` |
| `"base.html"` | `templates/base.html` |

There is **no** `from templates.converter import convert`.

#### Step C — Inside HTML: extend / blocks / variables

```django
{# templates/converter/convert.html #}
{% extends "base.html" %}          {# reuse layout — string name again #}

{% block title %}Convert — {{ SITE_NAME }}{% endblock %}

{% block content %}
  <h1>Convert a file</h1>
  {{ form }}                       {# data passed from the view #}
{% endblock %}
```

| Template tag / syntax | What it does |
|-----------------------|--------------|
| `{% extends "base.html" %}` | Child page inherits layout from parent |
| `{% block content %}` | Hole in parent that child fills |
| `{{ variable }}` | Print a value from context |
| `{% if %}` / `{% for %}` | Logic in the template |
| `{% url 'converter:home' %}` | Build a URL from a **named route** |
| `{% csrf_token %}` | Hidden field required for POST forms |
| `{% load static %}` | Enable the `static` tag (must be first when needed) |
| `{% static 'css/app.css' %}` | URL to a file under `static/` |

#### Context = data the template can see

Whatever you pass as the 3rd argument to `render()` becomes usable as `{{ name }}`:

```python
render(request, "converter/job_detail.html", {"job": job})
# template can use: {{ job.original_name }}, {{ job.status }}, ...
```

Extra variables can also come from **context processors** (see 2.6) — e.g. `{{ SITE_NAME }}` without passing it in every view.

#### Checklist: add a new page

1. Create `templates/converter/my_page.html` (usually `{% extends "base.html" %}`)
2. Write a view that `return render(request, "converter/my_page.html", {...})`
3. Wire a URL in `apps/converter/urls.py`
4. **No** settings change if the file is already under `templates/`

---

### 2.2 Static files — CSS / JS (also not imported)

#### Config (settings)

```python
STATIC_URL = "/static/"                    # URL prefix in the browser
STATICFILES_DIRS = [BASE_DIR / "static"]   # where we keep project static/
STATIC_ROOT = BASE_DIR / "staticfiles"     # collectstatic output (deploy)
```

#### In the template (this is the “import”)

```django
{% load static %}
<link rel="stylesheet" href="{% static 'css/app.css' %}">
<script src="{% static 'js/convert.js' %}"></script>
```

| You wrote | Browser asks for | File on disk |
|-----------|------------------|--------------|
| `{% static 'css/app.css' %}` | `/static/css/app.css` | `static/css/app.css` |
| `{% static 'js/convert.js' %}` | `/static/js/convert.js` | `static/js/convert.js` |

`{% load static %}` is required **in that template** (or a parent that already loaded it — we load it in `base.html`).

#### Static vs media

| | `static/` | `media/` |
|--|-----------|----------|
| Who creates files? | You (CSS/JS) | Users / conversion jobs |
| Config | `STATICFILES_DIRS` / `STATIC_URL` | `MEDIA_ROOT` / `MEDIA_URL` |
| In templates | `{% static '...' %}` | Usually via model `.url` or a download view |

---

### 2.3 URLs — how `/` finds your view

#### Root URLconf (settings points here)

```python
# config/settings/base.py
ROOT_URLCONF = "config.urls"
```

#### Root includes apps

```python
# config/urls.py
urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", include("apps.core.urls")),
    path("", include("apps.converter.urls")),   # string import of urlpatterns
]
```

#### App URLs import views (normal Python)

```python
# apps/converter/urls.py
from apps.converter import views

app_name = "converter"   # namespace → converter:home

urlpatterns = [
    path("", views.convert_home, name="home"),
    path("jobs/<uuid:job_id>/", views.job_detail, name="job_detail"),
]
```

| Piece | Role |
|-------|------|
| `path("...", view, name="...")` | URL pattern → view function + name |
| `app_name = "converter"` | Namespace so names don’t clash |
| `{% url 'converter:home' %}` | Template builds `/` from the name |
| `redirect("converter:job_detail", job_id=job.id)` | Same idea in Python |

**Flow:**

```text
http://127.0.0.1:8000/
  → ROOT_URLCONF = config.urls
  → include apps.converter.urls
  → path "" → views.convert_home
```

---

### 2.4 Apps — `INSTALLED_APPS`

Django only “knows” about apps listed here:

```python
# config/settings/base.py
LOCAL_APPS = [
    "apps.core",
    "apps.converter",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
```

| If you forget to add an app… | What breaks |
|------------------------------|-------------|
| New app not in `INSTALLED_APPS` | Models/migrations/admin ignored |
| App is listed | Django loads `models.py`, `admin.py`, etc. |

Creating a folder under `apps/` is not enough — **register it**.

---

### 2.5 Models — database as Python classes

```python
# apps/converter/models.py
class ConversionJob(models.Model):
    original_name = models.CharField(...)
    status = models.CharField(...)
```

| Concept | Meaning |
|---------|---------|
| Model class | One DB table (usually) |
| Field | One column |
| `job.save()` | Insert/update row |
| `ConversionJob.objects.get(...)` | Query |

**Migration workflow (never skip):**

```text
Edit models.py
  → python main.py makemigrations   # creates migration file
  → python main.py migrate          # applies it to the DB
```

Views/services import models normally:

```python
from apps.converter.models import ConversionJob
```

---

### 2.6 Context processors — variables in *every* template

Configured in settings (string paths to functions):

```python
"context_processors": [
    "django.contrib.messages.context_processors.messages",
    "apps.core.context_processors.site_meta",  # our custom one
]
```

Our function:

```python
# apps/core/context_processors.py
def site_meta(request):
    return {"SITE_NAME": settings.SITE_NAME}
```

So every template can use `{{ SITE_NAME }}` without each view passing it.

| Built-in processor | Gives you |
|--------------------|-----------|
| `request` | `{{ request }}` |
| `auth` | `{{ user }}`, `{{ perms }}` |
| `messages` | flash messages loop in `base.html` |

---

### 2.7 Forms — validate before you trust input

```python
# apps/converter/forms.py
class ConversionForm(forms.Form):
    source_file = forms.FileField(...)
    target_format = forms.ChoiceField(...)
```

In the view:

```python
form = ConversionForm(request.POST or None, request.FILES or None)
if request.method == "POST" and form.is_valid():
    data = form.cleaned_data   # safe, validated values
```

In the template:

```django
<form method="post" enctype="multipart/form-data">
  {% csrf_token %}
  {{ form.source_file }}
  {{ form.target_format }}
  <button type="submit">Convert</button>
</form>
```

| Must remember | Why |
|---------------|-----|
| `method="post"` | Sending data |
| `enctype="multipart/form-data"` | File uploads |
| `{% csrf_token %}` | Without it → **403 Forbidden** |
| `request.FILES` | Files are not in `request.POST` |

Widget CSS classes (Tailwind) are set in Python `attrs={...}` because Django renders the `<input>` HTML.

---

### 2.8 Views — thin HTTP adapters

A view is just a function (or class) that:

1. Receives `request`
2. Maybe validates a form / loads a model
3. Returns an `HttpResponse` (`render`, `redirect`, `JsonResponse`, `FileResponse`)

```python
def convert_home(request):
    ...
    return render(request, "converter/convert.html", {"form": form, "pairs": pairs})
```

**Import chain that matters:**

```text
urls.py  --imports-->  views.py  --imports-->  forms / models / services
views.py  --string-->  "converter/convert.html"   (no import)
```

---

### 2.9 Middleware (short)

Middleware = code that runs on **every** request/response (security, sessions, CSRF, messages…).

Configured as a list in `MIDDLEWARE` in settings. You rarely edit this in F1 — just know CSRF and sessions come from here.

---

### 2.10 Settings — the control panel

| File | Role |
|------|------|
| `config/settings/base.py` | Shared: apps, templates, static, upload limits |
| `config/settings/local.py` | Dev (`DEBUG=True`) |
| `config/settings/production.py` | Deploy |
| `.env` | Secrets / env-specific values |

`main.py` sets:

```python
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
```

Reading settings in code:

```python
from django.conf import settings
settings.SITE_NAME
settings.CONVERSION_MAX_UPLOAD_BYTES
```

---

### 2.11 Mini “wiring map” for FileForge

```text
main.py
  └─ DJANGO_SETTINGS_MODULE = config.settings.local
       ├─ INSTALLED_APPS → apps.converter, apps.core, ...
       ├─ ROOT_URLCONF → config.urls
       │     └─ include apps.converter.urls
       │           └─ path "" → views.convert_home
       │                 ├─ ConversionForm (import)
       │                 ├─ create_and_run (import)
       │                 └─ render(..., "converter/convert.html", context)
       │                       └─ TEMPLATES DIRS → templates/converter/convert.html
       │                             ├─ extends "base.html"
       │                             ├─ {% load static %} → static/css/app.css
       │                             └─ {{ SITE_NAME }} ← context_processors.site_meta
       ├─ TEMPLATES DIRS = templates/
       ├─ STATICFILES_DIRS = static/
       └─ MEDIA_ROOT = media/
```

If something “isn’t working”, walk this map: **settings → urls → view → template/static**.

---

## 3. Project map (tree + purpose)

```text
FILE_CONVERTER/                  ← project root (run commands from here)
│
├── main.py                      ← like manage.py — start server, migrate, etc.
├── .env / .env.example          ← secrets & config (never commit real .env)
├── db.sqlite3                   ← local database file (gitignored)
├── package.json                 ← npm scripts for Tailwind CSS
│
├── config/                      ← Django project settings + root URLs
│   ├── settings/
│   │   ├── base.py              ← shared settings (apps, templates, static, limits)
│   │   ├── local.py             ← development (DEBUG=True)
│   │   ├── production.py        ← Docker / real deploy
│   │   └── test.py              ← tests
│   ├── urls.py                  ← ROOT urlpatterns (admin, health, converter)
│   ├── wsgi.py / asgi.py        ← how the web server loads Django
│   └── celery.py                ← placeholder for F2 async workers
│
├── apps/                        ← Django “apps” (features that talk to HTTP + DB)
│   ├── core/                    ← tiny shared bits (health check, site name)
│   └── converter/               ← THE main feature app (upload / jobs / download)
│
├── engines/                     ← conversion logic ONLY (no views, no templates)
│   ├── registry.py              ← source→target matrix (what is allowed)
│   └── markdown/                ← md → pdf / docx implementation
│
├── templates/                   ← HTML pages (Django Template Language)
│   ├── base.html                ← shell: brand, messages, footer
│   └── converter/
│       ├── convert.html         ← home convert form
│       └── job_detail.html      ← result / download page
│
├── static/                      ← frontend assets Django serves as /static/...
│   ├── src/input.css            ← Tailwind SOURCE (edit this)
│   ├── css/app.css              ← Tailwind BUILD output (generated)
│   └── js/convert.js            ← dropzone + format dropdown JS
│
├── media/                       ← uploaded + converted files (gitignored)
├── tests/                       ← automated tests
├── scripts/                     ← CLI helpers (e.g. md_converter.py)
├── samples/                     ← sample .md files for manual testing
├── docker/                      ← container setup
├── requirements/                ← Python dependencies
└── docs/                        ← plans + this KT
```

### Why split `apps/` and `engines/`?

| Layer | Allowed to know about Django? | Why |
|-------|-------------------------------|-----|
| `apps/converter/` | Yes | Needs models, request, response, admin |
| `engines/` | **No** | Same converters work from CLI, workers, or API |

**Rule of thumb:** if it converts bytes → `engines/`. If it talks to a browser or DB row → `apps/`.

---

## 4. Request walkthrough (convert a file)

```text
1. Browser GET /
2. config/urls.py → includes apps/converter/urls.py
3. path "" → views.convert_home
4. View builds ConversionForm + list_pairs() from engines.registry
5. render("converter/convert.html") → Django finds templates/converter/convert.html
   (because TEMPLATES["DIRS"] includes templates/)

--- user drops file, picks PDF, clicks Convert ---

6. Browser POST /  (multipart form + CSRF token)
7. Same view: form.is_valid()
8. services.conversion.create_and_run(...)
9. Creates ConversionJob row (model)
10. Calls engines.registry to run the right engine
11. Saves output under media/outputs/
12. Redirect → /jobs/<uuid>/
13. job_detail template → Download button → /jobs/<uuid>/download/
```

| Step | File |
|------|------|
| Root routes | `config/urls.py` |
| App routes | `apps/converter/urls.py` |
| Home / job / download / formats API | `apps/converter/views.py` |
| Form validation | `apps/converter/forms.py` |
| Job orchestration | `apps/converter/services/conversion.py` |
| DB shape | `apps/converter/models.py` |
| Allowed pairs | `engines/registry.py` |
| Actual MD conversion | `engines/markdown/` |
| HTML | `templates/converter/*.html` |
| Dropzone JS | `static/js/convert.js` |
| Template/static config | `config/settings/base.py` |

---

## 5. Django app anatomy (`apps/converter/`)

| File | What it is | When you edit it |
|------|------------|------------------|
| `apps.py` | Registers the app with Django | Rarely |
| `models.py` | Database tables as Python classes | New fields / job states |
| `migrations/` | History of DB schema changes | Via `makemigrations` |
| `views.py` | HTTP handlers | New pages / API endpoints |
| `urls.py` | Paths inside this app | New URL names |
| `forms.py` | Form fields + validation | Upload rules, widgets |
| `admin.py` | Django admin UI for models | Inspect jobs in `/admin/` |
| `services/` | Business logic | Conversion flow changes |
| `exceptions.py` | Domain errors | New failure types |
| `management/commands/` | CLI commands | Cron / cleanup |

---

## 6. Tailwind CSS (FileForge-specific)

```text
Edit:   static/src/input.css     (+ classes in HTML)
Build:  npm run css:build / css:watch
Serve:  static/css/app.css       ← {% static 'css/app.css' %}
```

Changing Tailwind classes in HTML does nothing until you rebuild (or keep `css:watch` running).

---

## 7. Where do I change…? (cheat sheet)

| I want to… | Go here |
|------------|---------|
| Change homepage look | `templates/base.html`, `templates/converter/convert.html`, `static/src/input.css` |
| Make Django see a new template folder | `TEMPLATES["DIRS"]` in `config/settings/base.py` |
| Pass new data into a page | the view’s `render(..., context)` dict |
| Make a variable available on every page | context processor + register in `TEMPLATES` options |
| Change dropzone behavior | `static/js/convert.js` |
| Style form `<input>` / `<select>` | `apps/converter/forms.py` widget `attrs` + CSS rebuild |
| Add a new URL page | view + `urls.py` + template (no template “import”) |
| Change upload validation | `apps/converter/forms.py` + settings / `.env` |
| Change DB fields | `models.py` → `makemigrations` → `migrate` |
| Add `md → html` | `engines/` + `engines/registry.py` |
| Change site title | `.env` → `SITE_NAME` |
| Register a new Django app | create app + add to `INSTALLED_APPS` |

---

## 8. Adding a new conversion pair (future you)

1. Implement conversion in `engines/<category>/`
2. Register the pair in `engines/registry.py`
3. Form / dropdown / “Supported conversions” update from the registry
4. Add a test under `tests/`

Do **not** sprinkle `if format == ...` in views.

---

## 9. Daily commands

```bash
python main.py runserver
python main.py migrate
python main.py makemigrations
python main.py createsuperuser
python main.py check
python main.py purge_expired_jobs

npm run css:watch
npm run css:build
```

---

## 10. Common beginner traps

1. **Looking for `import templates...`** — templates are string paths + settings, not Python imports.
2. **Forgetting `{% load static %}`** — `{% static %}` won’t work.
3. **Forgetting `{% csrf_token %}`** — POST → 403.
4. **File upload without `enctype="multipart/form-data"`** — file never arrives.
5. **New app folder but not in `INSTALLED_APPS`** — Django ignores it.
6. **Editing `static/css/app.css` by hand** — wiped on Tailwind rebuild; edit `static/src/input.css`.
7. **Hardcoding `/jobs/...`** — use `{% url 'converter:job_detail' job.id %}`.
8. **Editing an already-applied migration** — make a **new** migration instead.
9. **Fat views** — conversion logic belongs in `engines/` / `services/`.

---

## 11. Tutorial names vs this repo

| Tutorial usually says | This repo uses |
|-----------------------|----------------|
| `manage.py` | `main.py` |
| Project package `mysite/` | `config/` |
| Apps at root `polls/` | `apps/converter/`, `apps/core/` |
| Business logic in views | `services/` + `engines/` |
| One `settings.py` | Split `config/settings/*` |

---

## 12. Suggested learning order

1. Read **§2 Core concepts** (especially templates + URLs)  
2. Open `config/settings/base.py` → find `TEMPLATES`, `STATICFILES_DIRS`, `INSTALLED_APPS`  
3. Open `config/urls.py` → `apps/converter/urls.py` → `views.convert_home`  
4. Open `convert.html` → match `{{ form }}` / `{{ pairs }}` to the view context  
5. Open `forms.py` → `models.py` → `services/conversion.py`  
6. Change one template class → `npm run css:build` → refresh  

---

## Related docs

| Doc | Purpose |
|-----|---------|
| [PLAN.md](PLAN.md) | Product stages F0–F6 |
| [../README.md](../README.md) | Install, run, Docker |
