# FileForge — Personal Online File Converter Plan

**Market pattern:** commercial online converters — drop a file, pick an output format, download. Large catalogs span documents, images, audio, video, archives, ebooks, CAD, etc., plus API jobs and auto-deletion after processing.

---

## Verdict (Read This Before Dreaming)

You can build a **personal online file converter** (same UX pattern, same job model, growing format catalog).  
You cannot match a mature commercial catalog in one Django weekend — and you shouldn’t try.

| | Typical commercial converter | Your personal FileForge |
|--|------------------------------|-------------------------|
| Formats | 200+ / many categories | Start ~5–20 pairs; grow by category |
| Engines | Many vendor + OSS tools behind one API | Same idea: **orchestrate** LibreOffice, ffmpeg, Pillow, pandoc, etc. |
| Ops | Multi-year infra, workers, security certs | Docker Compose on your machine/VPS |
| Goal | Paid SaaS at scale | Personal / private / eventually small SaaS |
| Honest claim | “Convert any file” (with huge matrix) | “Convert these formats” (expand over time) |

**Architecture truth:** those products are not one magic converter. They are a **job orchestrator** over many specialized engines. That is exactly the architecture we will copy — at personal scale.

---

## Product Vision

Build a **self-hosted / personal** file converter with modern online-converter UX:

1. Drop a file (or select one)
2. Pick target format from a filtered dropdown
3. Convert asynchronously
4. Download result
5. Auto-delete files after a short retention window

Later (parity features vs typical market products, optional):

6. Format catalog page (browse by category)
7. Conversion options per type (quality, page size, bitrate…)
8. REST API: import → convert → export job chain
9. Batch / multi-file
10. Auth, quotas, API keys if you ever expose it beyond yourself

Working name: **FileForge** (rename anytime).

**Positioning:** *Personal online file converter* — private by default, formats added deliberately, no fake “supports everything” homepage until the registry actually does.

---

## Core Principles

1. **Pair registry, not magic** — every conversion is an explicit registered handler.
2. **Orchestrate engines** — Django does not convert video; ffmpeg does. Django routes the job.
3. **Fail loud** — unsupported pairs never silently “try something”.
4. **Async by default after F1** — never block HTTP on heavy work.
5. **Ephemeral files** — process → download → delete (standard online-converter model).
6. **Security first** — allowlists, size caps, sandbox workers for untrusted files.
7. **SOLID engines** — HTTP/auth/jobs in Django; conversion logic in isolated engine modules/containers.

---

## High-Level Architecture (Job Orchestrator Pattern)

```text
Browser (dropzone + format picker + options)
  │
  ▼
Django API  ── create Job { import, convert, export }
  │
  ▼
Postgres / SQLite  (job + task state)
  │
  ▼
Queue (Redis + Celery)
  │
  ├─► Document worker     (LibreOffice / pandoc / python engines)
  ├─► Image worker        (Pillow / ImageMagick)
  ├─► Media worker        (ffmpeg)          ← later
  └─► Archive worker      (7z / unzip)      ← later
  │
  ▼
Object storage (local media → MinIO/S3)
  │
  ▼
Signed download URL  →  TTL cleanup job
```

Same mental model as commercial task APIs (`import` → `convert` → `export`), simplified for personal use.

### Suggested project layout

```text
fileforge/
  main.py
  config/                 # Django settings, urls, celery
  apps/
    accounts/             # auth (later)
    converter/            # jobs, upload API, download, catalog
    engines/              # pure conversion adapters (no Django views)
      registry.py         # source→target matrix + engine binding
      markdown_engine.py
      document_engine.py  # LibreOffice / pdf2docx / pandoc
      image_engine.py
      media_engine.py     # ffmpeg (later)
      archive_engine.py   # later
  templates/              # single convert page (dropzone + dropdown)
  static/
  media/                  # local only; S3/MinIO in prod
  docker/                 # worker images with LibreOffice/ffmpeg
```

Markdown pipeline lives in `engines/markdown/`; CLI entrypoint is `scripts/md_converter.py`.

---

## Category Roadmap (Format Catalog)

Grow **by category**, not random one-off formats.

| Category | Personal target formats | Stage | Engine(s) |
|----------|-------------------------|-------|-----------|
| Documents | md, pdf, docx, txt, html, rtf | F1–F2 | reportlab, python-docx, pandoc, LibreOffice, pdf2docx |
| Images | png, jpg, webp, gif, bmp, tiff → pdf | F3 | Pillow / ImageMagick |
| Spreadsheets | csv, xlsx → pdf | F4 | openpyxl + LibreOffice |
| Slides | pptx → pdf | F4 | LibreOffice |
| Archives | zip, tar, 7z (pack/unpack) | F5 conversions | zipfile / tarfile / 7z |
| Audio | mp3, wav, flac, ogg | F6 conversions | ffmpeg |
| Video | mp4, webm, mkv (transcode) | F6 conversions | ffmpeg |
| E-books | epub ↔ pdf (optional) | F7 | calibre/ebook-convert |
| CAD / RAW / Fonts | **out of personal scope** unless you truly need them | — | — |

### Near-term conversion matrix

| Source | Targets | Stage |
|--------|---------|-------|
| `.md` / `.markdown` | `.pdf`, `.docx`, `.html`, `.txt` | F1–F2 |
| `.docx` | `.pdf`, `.txt`, `.html`, `.md` (best-effort) | F2 |
| `.pdf` | `.txt`, `.md`, `.docx` (best-effort / lossy) | F2–F3 |
| Images | `.png` / `.jpg` / `.webp` / `.pdf` | F3 |
| `.csv` / `.xlsx` | `.csv` / `.xlsx` / `.pdf` | F4 |
| `.pptx` | `.pdf` | F4 |
| Archives | zip ↔ tar ↔ tgz ↔ 7z | F5 conversions |
| Audio / Video | via ffmpeg (+ video→audio extract) | F6 conversions |

Rule: if a pair is not in the registry, the dropdown must not offer it. The homepage never claims formats the registry does not have.

### Reverse conversions (PDF → MD / PDF → DOCX)

Yes — we **can and should** support vice-versa pairs. They are first-class product features, not afterthoughts.

But be clear with users (and yourself): **forward ≠ reverse quality**.

| Pair | Feasible? | Quality expectation | Typical stack |
|------|-----------|---------------------|---------------|
| `md → pdf` / `md → docx` | Excellent | High fidelity (we control layout) | reportlab / python-docx (current) |
| `pdf → txt` | Good | Text extraction; layout mostly lost | pypdf / pdfminer.six |
| `pdf → md` | Medium | Headings/lists/tables are *heuristics*; images/complex layout degrade | pdfminer / pymupdf + custom structure rules; OCR if scanned |
| `pdf → docx` | Medium | Editable Word doc, not pixel-perfect clone | pdf2docx / LibreOffice; complex tables/columns often break |
| Scanned PDF (image-only) | Hard | Needs OCR first, then same pipeline | Tesseract / cloud OCR → then md/docx |

Product rule:

- Label reverse pairs in UI as **Best effort** where fidelity is imperfect.
- Prefer `pdf → txt` as the reliable baseline; `pdf → md` / `pdf → docx` as enhanced options.
- Detect scanned PDFs and either reject with a clear message or route through OCR (F6).

Do **not** promise “perfect round-trip” (`md → pdf → md` identical). That will fail for real documents.

---

## Feature Stages

### F0 — Product Spec Freeze *(before coding)*

**Goal:** lock “personal online converter” scope — UX yes, 200 formats no (yet).

Deliverables:

- [x] Final product name (working: FileForge)
- [x] MVP conversion pairs: `md → pdf`, `md → docx`
- [x] Max upload size (**100 MB** default global; per-pair caps: docs 25 / archives 50 / media 100)
- [x] Retention policy (suggest **24h** then delete — ephemeral processing)
- [x] Audience: **personal / private first** (single-user or LAN), public SaaS later optional
- [x] Auth decision for MVP: open local use vs simple password gate
- [x] Explicit non-goals for v1: audio/video/CAD/ebooks
- [x] Local Docker path planned even if F1 runs bare metal

Exit criteria: written decisions above approved.

---

### F1 — Django MVP (Markdown Converter Web App)

**Goal:** ship a usable web UI around the current Markdown converter.

Features:

- [x] Django project + `converter` app
- [x] Upload page (drag-drop + file picker)
- [x] Target format dropdown: `PDF`, `DOCX` (only when source is Markdown)
- [x] Sync conversion for small files (acceptable only in F1)
- [x] Download converted file
- [x] Basic validation: extension, size, MIME sniff
- [x] Flash/toast errors for unsupported files
- [x] Markdown pipeline in `engines/markdown/` + CLI in `scripts/md_converter.py`
- [x] Local media storage + `.gitignore` for uploads
- [x] `requirements.txt` / `pyproject` with pinned deps
- [x] README: run locally (`migrate`, `runserver`)

Models (minimal):

```text
ConversionJob
  - id (uuid)
  - original_name
  - source_format
  - target_format
  - status (pending/processing/done/failed)
  - input_file
  - output_file (nullable)
  - error_message (nullable)
  - created_at
  - expires_at
```

Tech:

- Django 5.x
- python-docx, reportlab (existing)
- Bootstrap/Tailwind for a clean single-page UI (pick one; don’t mix)

Exit criteria:

- User can upload an `.md`, choose PDF or DOCX, download result.
- Invalid uploads are rejected with clear messages.

---

### F2 — Job Queue + Better Documents + UX Polish

**Goal:** stop blocking HTTP; expand document conversions; make UX feel like a product.

Features:

- [x] Background workers (Celery + Redis **or** Django-Q2 — pick one stack)
- [x] Job status polling / HTMX / WebSocket-lite progress UI
- [x] Conversion history page (session-based or user-based)
- [x] Add pairs:
  - `md → html`
  - `md → txt`
  - `docx → pdf` (LibreOffice/headless or external converter later)
  - `docx → txt`
  - `docx → md` (best-effort structure mapping)
  - `pdf → txt` (reliable text extract)
  - `pdf → md` (structured extract; best-effort)
  - `pdf → docx` (best-effort via pdf2docx and/or LibreOffice)
- [x] UI badge: **Best effort** on reverse/lossy pairs
- [x] Dynamic dropdown API: `GET /api/formats/?source=pdf` (etc.)
- [x] Per-job progress states in UI (`Queued → Converting → Ready`)
- [x] Auto-delete expired jobs (management command + cron/celery beat)
- [x] Structured logging + correlation id per job

Risks / honesty:

- `docx → pdf` on Windows/Linux usually needs **LibreOffice** or a paid API. Pure-Python quality is weak. Plan for an external dependency.
- `pdf → md` / `pdf → docx` are **lossy**. Multi-column layouts, nested tables, footnotes, and vector graphics will not survive cleanly.
- Scanned PDFs need OCR — defer to F6 unless F3 explicitly pulls it in.

Exit criteria:

- Large-ish Markdown converts without request timeouts.
- Dropdown is driven by registry, not hardcoded HTML.

---

### F3 — Images + Multi-file + Hardening

**Goal:** broaden usefulness; harden security and reliability.

Features:

- [x] Image conversions via Pillow:
  - png/jpg/webp/gif/bmp → png/jpg/webp (no identity pairs)
  - image → pdf
- [x] Batch upload (multiple files, same target format)
- [x] ZIP download for batch results
- [x] Rate limiting (IP / user)
- [x] Content-type verification beyond extension
- [x] Virus scanning hook (ClamAV optional)
- [x] Admin panel for failed jobs / metrics
- [x] Unit + integration tests for each registered pair

Exit criteria:

- Image + Markdown paths both production-usable locally.
- Abuse basics covered (size, rate, type checks).

---

### F4 — Office/Data Formats + Accounts

**Goal:** turn prototype into sticky multi-user product.

Features:

- [ ] Auth (email/password or social login)
- [ ] Per-user history, quotas, storage usage
- [x] Spreadsheet conversions (`csv ↔ xlsx`, export `pdf`)
- [x] `pptx → pdf` (again: LibreOffice dependency)
- [ ] API keys for programmatic conversion (`POST /api/v1/convert`)
- [ ] Webhook callback on job completion
- [ ] Stripe/LemonSqueezy billing skeleton (free tier + paid quota)

Exit criteria:

- Logged-in users get history + quotas.
- External clients can convert via API.

**Progress note:** conversion pairs (spreadsheets + slides) shipped first; accounts/API/billing deferred.

---

### F5 — Production Platform

**Goal:** deployable, observable, scalable service.

**Progress note:** archive **conversion pairs** shipped first (zip/tar/tgz/7z); platform items below remain deferred.

Features:

- [x] Archive conversions (`zip` ↔ `tar` ↔ `tgz` ↔ `7z`; 7z needs `7z`/`p7zip`)
- [ ] Docker Compose (web + worker + redis + db)
- [ ] Postgres (replace SQLite)
- [ ] Object storage (S3/MinIO) for inputs/outputs
- [ ] Signed download URLs
- [ ] Horizontal worker scaling
- [ ] Prometheus/Sentry (errors + latency)
- [ ] CDN for static assets
- [ ] Backup + retention enforcement
- [ ] Legal pages: privacy, ToS, file-processing disclosure
- [ ] Optional: Kubernetes later (don’t start here)

Exit criteria:

- One-command local prod-like stack.
- Clear SLOs: conversion success rate, p95 job time, storage growth.

---

### F6 — Nice-to-Haves / Differentiators (Optional)

**Progress note:** media **conversion pairs** shipped first (ffmpeg audio/video + video→audio); polish items below remain deferred. Only after F1–F5 platform are real for the rest:

- [x] Audio conversions (`mp3` / `wav` / `flac` / `ogg`, non-identity)
- [x] Video transcode (`mp4` / `webm` / `mkv`) + extract audio (`→ mp3` / `wav`)
- [ ] OCR (`image/pdf → searchable text/pdf`)
- [ ] Watermarking / branding on outputs
- [ ] Template-based Markdown themes (corporate PDF skins)
- [ ] Side-by-side preview before download
- [ ] Collaborative shared conversion links
- [ ] Plugin SDK so new engines can be added without touching views
- [ ] Desktop wrapper (Tauri/Electron) calling the same API

---

## UX Flow (MVP)

1. Land on single conversion page
2. Drop file
3. App detects source type → populates dropdown
4. User picks target
5. Click **Convert**
6. Show progress
7. **Download** button appears
8. File expires after configured TTL

Empty/error states required:

- Unsupported source type
- Unsupported target for that source
- File too large
- Conversion failed (engine error)

---

## Engine Registry Design (Critical)

Do **not** sprinkle `if format == ...` across views.

```python
# conceptual
@dataclass(frozen=True)
class ConversionPair:
    source: str          # "md"
    target: str          # "pdf"
    engine: Callable
    max_bytes: int
    timeout_sec: int

REGISTRY = {
    ("md", "pdf"): ConversionPair(...),
    ("md", "docx"): ConversionPair(...),
}
```

Views/API only:

1. Detect source format
2. Look up pair
3. Create job
4. Execute/enqueue engine

Adding a format later = add one engine + one registry entry.

---

## Security Checklist (Non-Negotiable)

- [x] Allowlist extensions + MIME sniffing
- [x] Max upload size + max pages/pixels for documents/images
- [x] Store uploads outside web root / private storage
- [x] Never execute uploaded files
- [x] Sanitize filenames
- [x] Time-limited download links
- [x] Rate limits
- [x] CSRF on form posts; auth tokens on API
- [x] Worker runs with least privilege
- [x] LibreOffice/conversions in sandbox/container if used

**Implementation notes (security hardening pass):**

| Control | How |
|---------|-----|
| Allowlist + sniff | `ALLOWED_SOURCE_EXTENSIONS` enforced in form + `create_job`; magic-byte sniff in `engines/sniff.py`; declared↔sniffed must match; no invented `md` from extensionless text |
| Size / pages / pixels | Global + per-pair byte caps; `CONVERSION_MAX_PDF_PAGES` (default 200); `CONVERSION_MAX_IMAGE_PIXELS` (default 40M) + Pillow `MAX_IMAGE_PIXELS` |
| Private storage | `MEDIA_URL=""` by default; downloads only via app views; Docker volume at `/var/fileforge/media` (outside repo tree) |
| Never execute uploads | Fixed-argv subprocesses only (`soffice`/`ffmpeg`/`7z`/`clamscan`); downloads forced `as_attachment` + `application/octet-stream` |
| Sanitize filenames | `sanitize_display_name` for DB/UI; opaque `{uuid}{ext}` on disk via `storage_object_name` |
| Time-limited downloads | Session ownership **and** `TimestampSigner` token (`?token=`); TTL bound to job `expires_at` |
| Rate limits | Cache-backed IP throttle; production uses Redis (`CACHE_URL`); `X-Forwarded-For` only when `USE_X_FORWARDED_FOR=True` |
| CSRF / API auth | Django CSRF middleware + form token; mutating API keys deferred to F4 accounts — session binds jobs today |
| Worker least privilege | Non-root `appuser`; Compose `cap_drop: ALL`, `no-new-privileges`, mem/CPU/pids limits; Redis/Postgres not published to host |
| LO sandbox | Conversions in hardened worker container (`read_only` rootfs, tmpfs scratch, isolated LO profile); not host-privileged |
---

## Tech Stack Recommendation

| Layer | Choice | Why |
|-------|--------|-----|
| Web | Django 5 + Django templates (HTMX) | Fast MVP, less JS ceremony |
| API (F4) | Django REST Framework | Clean for API keys/webhooks |
| Queue | Celery + Redis | Mature; or Django-Q2 if you want simpler ops |
| DB | SQLite → Postgres | SQLite fine until F5 |
| Markdown engines | reportlab + python-docx (current) | Already working |
| Images | Pillow | Standard |
| Office→PDF | LibreOffice headless in Docker | Best quality/cost tradeoff |
| Frontend | HTMX + lightweight CSS | Enough until F4 |

Avoid overbuilding React/Next for F1–F3 unless you specifically want a separate SPA.

---

## Delivery Timeline (Rough)

Assumes 1 focused engineer building a **personal** online file converter:

| Stage | Estimate | Outcome |
|-------|----------|---------|
| F0 | 0.5 day | Scope locked |
| F1 | 2–4 days | Dropzone UI: MD→PDF/DOCX |
| F2 | 1–2 weeks | Async jobs + reverse PDF/DOCX + catalog API |
| F3 | 1–2 weeks | Images + batch + hardening |
| F4 | 1–2 weeks | Office/sheets + auth/API skeleton |
| F5 | 1–2 weeks | Docker/Postgres/MinIO personal deploy |
| F6 | 2–4 weeks | ffmpeg audio/video (optional) |

Mature commercial converters took years and teams. Your usable personal app for **core UX + documents/images** is realistic in weeks–months. Full market-catalog parity is not the goal.

---

## What We Will Explicitly Not Do in MVP

- Market it as “200+ formats” or “convert any file”
- Synchronous conversion of huge PDFs/videos
- Building 30 formats before the job/registry system exists
- Storing user files forever
- Skipping validation because “it’s just a prototype”
- Reimplementing ffmpeg/LibreOffice in pure Python

---

## Market Reality Check

Copy the **product pattern**, not someone else’s branding or inflated scope:

| Market feature | Personal FileForge approach |
|----------------|-----------------------------|
| Dropzone + format dropdown | F1 must feel this good |
| Format catalog by category | F2 static page from registry |
| Auto-delete after processing | F1 TTL + F2 cleanup beat |
| Job API (import/convert/export) | F4 simplified DRF jobs |
| Per-format options | F3+ (e.g. image quality, page size) |
| 200+ formats | Category roadmap over months |
| Security certifications | Sensible defaults; not ISO theatre for personal use |
| Usage billing | Only if you open it to others (F4+) |

If you only need conversions for yourself, **self-hosted FileForge** wins for common doc/image pairs — and keeps files on your machine.

---

## Immediate Next Step After This Plan

Implement **F1** as a personal mini online converter:

1. Scaffold Django project (**FileForge**)
2. Single page: dropzone → target dropdown → Convert → Download
3. Move Markdown conversion into an engine module
4. Ship only `md → pdf` and `md → docx`
5. Show “Supported formats” from registry (even if only 2 targets)

No F2/F3 work until that loop is demoable end-to-end.

---

## Decision Log

| Decision | Choice | Status |
|----------|--------|--------|
| Product type | Personal online file converter | Locked |
| Framework | Django 5 + split settings | Done (scaffolded) |
| Layout | `apps/` + `engines/` + `config/` | Done |
| MVP pairs | `md→pdf`, `md→docx` | Done (F1) |
| MVP auth | Open local use; password gate deferred | Done (F0) |
| Frontend | Django templates + Tailwind CSS v4 | Done (F1 UI polish) |
| Queue | Celery + Redis (sync fallback for local/dev) | Done (F2) |
| Images + batch + rate limit | Pillow engines, ConversionBatch ZIP, IP throttle, optional ClamAV hook | Done (F3) |
| F4 office conversions | csv↔xlsx (openpyxl); csv/xlsx/pptx→pdf (LibreOffice Calc/Impress); accounts/API deferred | Done (F4 conversions) |
| F5 archive conversions | zip↔tar↔tgz↔7z (stdlib + optional 7-Zip); platform (Postgres/MinIO/Compose) deferred | Done (F5 conversions) |
| F6 media conversions | ffmpeg audio/video + video→audio; OCR/preview/SDK deferred | Done (F6 conversions) |
| Security checklist | Allowlist+sniff, page/pixel caps, private MEDIA, UUID disk names, signed download tokens, Redis rate-limit cache, hardened Compose worker | Done |
| Storage | Local private media (signed downloads); MinIO/S3 still F5 platform | In progress |
| Media (audio/video) | F6 conversions via ffmpeg | Done |
| Full commercial catalog day-1 | **No** | Locked |

Update this table when decisions are finalized.
