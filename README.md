# Hibbs Institute — Interview, Presentation & Pitch Prep Tool

A full-stack Flask web application for preparing for interviews, rehearsing presentations, and practicing pitches. Built for the **Hibbs Institute for Business & Economic Research** at **The University of Texas at Tyler**.

> **Live demo:** Deploy your own instance with one click — see [Deployment](#deployment) below.

---

## Features at a Glance

| Feature | Description |
|---------|-------------|
| **Three session types** | Interview, Presentation, and Pitch — each with tailored features |
| **Speaker Notes** | Rich talking points with key stats, source citations, do/don't tips, transitions |
| **Confidence Tracker** | Rate each talking point 1–5, see an overall readiness dashboard with color-coded bars |
| **Rehearsal / Teleprompter** | Step through slides one at a time with large text, timer, dot navigation, and fullscreen mode |
| **Practice Mode** | Timed flashcard Q&A with answer reveal, self-rating, and session history tracking |
| **Quick Reference** | Cheat sheet cards with key data — printable as a compact reference |
| **Pitch Timer** | Visual countdown ring for 30s / 60s / 2min pitch variants with scripts |
| **Objection Handling** | Anticipated tough questions with prepared responses |
| **Key Messages Checklist** | Check off core messages during practice runs |
| **Authentication** | Optional username/password login for team deployments |
| **Dark Mode** | Toggle between light and dark themes |
| **Keyboard Shortcuts** | Space (timer), ← → (navigate), R (reveal), F (fullscreen) |
| **Import from Files** | Parse existing HTML/reveal.js presentations into structured sessions |
| **Session Manager** | Create, edit, duplicate, delete — all through the web UI |
| **Mobile Ready** | Responsive design for phone, tablet, and desktop |

---

## Quick Start

### Option 1: One-click (Windows)
Double-click **`run.bat`** — installs Flask if needed and opens your browser.

### Option 2: Command line
```bash
pip install -r requirements.txt
python app.py
```
Open **http://localhost:5050**

### Option 3: With authentication
```bash
# Set credentials (PowerShell)
$env:PREP_TOOL_USER = "cecilia"
$env:PREP_TOOL_PASS = "your-password"
python app.py
```

---

## Screenshots

### Dashboard
*Session manager with type badges, stats, and quick actions.*

### Speaker Notes + Confidence Tracker
*Talking point cards with emoji-based confidence ratings and a readiness dashboard.*

### Rehearsal / Teleprompter Mode
*Step-through slides with large text, timer, dot navigation, and fullscreen.*

### Practice Mode
*Timed Q&A flashcards with answer reveal, self-rating, and session history.*

### Pitch Timer
*Visual countdown ring with 30s/60s/2min pitch scripts and key messages checklist.*

### Quick Reference (Printable)
*Cheat sheet cards — click Print for a clean 2-column reference page.*

---

## Architecture

```
┌───────────────────────────────────────────────────┐
│                   Flask Backend                    │
│  app.py (routes, API, auth, session management)    │
│  importer.py (HTML/reveal.js parser)               │
├───────────────────────────────────────────────────┤
│                   Templates (Jinja2)               │
│  base.html → dashboard / session / editor / login  │
├───────────────────────────────────────────────────┤
│                 Frontend (Vanilla JS)              │
│  session.js (modes, timers, confidence, rehearsal) │
│  editor.js (dynamic form builder, API save)        │
│  app.js (theme toggle)                             │
├───────────────────────────────────────────────────┤
│              Data Layer (JSON files)               │
│  sessions/*.json — one file per session            │
│  localStorage — confidence & practice history      │
└───────────────────────────────────────────────────┘
```

## File Structure

```
├── app.py                  # Flask application + auth + API
├── importer.py             # File parser (reveal.js, HTML, text)
├── run.bat                 # One-click launcher (Windows)
├── requirements.txt        # Python dependencies
├── Procfile                # Deployment (Render, Railway)
├── render.yaml             # Render.com blueprint
├── .env.example            # Environment variable template
├── .gitignore              # Keeps personal sessions out of repo
├── sessions/               # JSON session data
│   └── sample-demo.json    # Sample session (ships with repo)
├── templates/
│   ├── base.html           # Base layout (header, footer, nav)
│   ├── login.html          # Authentication page
│   ├── dashboard.html      # Session manager grid
│   ├── session.html        # Session view (6 modes/panels)
│   ├── edit_session.html   # Tabbed editor
│   ├── new_session.html    # Create / import
│   └── import_session.html # File import wizard
└── static/
    ├── css/styles.css      # Full design system (1800+ lines)
    └── js/
        ├── app.js          # Theme toggle
        ├── session.js      # Session view logic
        └── editor.js       # Editor logic
```

---

## Deployment

### Render.com (Recommended — free tier)

1. Push to GitHub
2. Go to [render.com](https://render.com) → **New Web Service**
3. Connect your repo — Render auto-detects the `render.yaml`
4. Set environment variables:
   - `PREP_TOOL_USER` → your username
   - `PREP_TOOL_PASS` → your password
5. Deploy — you'll get a `yourapp.onrender.com` URL

### Railway / Heroku
The included `Procfile` works with any platform that supports it:
```
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
```

### PythonAnywhere
Upload files directly and configure WSGI to point at `app:app`.

---

## Security

| Concern | How it's handled |
|---------|------------------|
| **Authentication** | Optional login (set `PREP_TOOL_USER` and `PREP_TOOL_PASS` env vars) |
| **Password storage** | SHA-256 hashed in memory — never stored in plain text |
| **Session secrets** | Auto-generated 256-bit secret key if `PREP_TOOL_SECRET` not set |
| **Personal data** | `.gitignore` excludes all session JSONs except the sample demo |
| **Deployment** | `FLASK_DEBUG=0` in production, gunicorn for WSGI |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PREP_TOOL_SECRET` | Auto-generated | Flask secret key |
| `PREP_TOOL_USER` | *(empty — auth disabled)* | Username for login |
| `PREP_TOOL_PASS` | *(empty — auth disabled)* | Password for login |
| `PREP_TOOL_PORT` | `5050` | Port to run on |
| `PREP_TOOL_LOGO` | *(auto-detect)* | Path to logo image |
| `FLASK_DEBUG` | `1` | Set to `0` in production |

---

## Tech Stack

- **Backend:** Python 3.12 + Flask
- **Frontend:** HTML5, CSS3, Vanilla JavaScript (no build step)
- **Fonts:** Montserrat + Open Sans (Google Fonts)
- **Icons:** Font Awesome 6.5
- **Data:** JSON files + localStorage
- **Deployment:** Gunicorn + Render/Railway/PythonAnywhere
- **Branding:** UT Tyler official colors — Navy `#003A63`, Orange `#E87722`, Gold `#F2A900`

---

## Author

**Cecilia Cuellar, Ph.D.** — Economist | Research Analyst
[Hibbs Institute for Business & Economic Research](https://www.uttyler.edu/hibbs/) — The University of Texas at Tyler

---

## License

This project was built for internal use at the Hibbs Institute. Feel free to fork and adapt for your own interview, presentation, or pitch preparation needs.
