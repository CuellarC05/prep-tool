"""
Hibbs Institute — Interview, Presentation & Pitch Prep Tool
============================================================
A Flask web app for preparing for interviews, presentations, and pitches.
Supports multiple sessions with tailored modes for each type.

Usage:
    python app.py          (runs on http://localhost:5050)
    Or double-click run.bat

Environment variables (optional, for deployment):
    PREP_TOOL_SECRET   – Flask secret key (auto-generated if unset)
    PREP_TOOL_USER     – Username for login (set to enable auth)
    PREP_TOOL_PASS     – Password for login
    PREP_TOOL_PORT     – Port to run on (default: 5050)
    PREP_TOOL_LOGO     – Path to logo image (optional)
"""

import os
import json
import uuid
import base64
import glob
import hashlib
import secrets
import functools
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, jsonify, send_file, abort, session as flask_session,
    Response
)

from importer import import_file, detect_file_type

# ── Load .env file if present (for local dev) ────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, that's fine

# ── App setup ────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("PREP_TOOL_SECRET", secrets.token_hex(32))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

# ── Authentication ───────────────────────────────────────────
# Set PREP_TOOL_USER and PREP_TOOL_PASS environment variables to enable auth.
# When unset, the app runs without authentication (local dev mode).
AUTH_USER = os.environ.get("PREP_TOOL_USER", "").strip()
AUTH_PASS = os.environ.get("PREP_TOOL_PASS", "").strip()
AUTH_ENABLED = bool(AUTH_USER and AUTH_PASS)

# Hash the password so it's not stored in plain text in memory
AUTH_PASS_HASH = hashlib.sha256(AUTH_PASS.encode()).hexdigest() if AUTH_PASS else ""


def login_required(f):
    """Decorator: redirects to login page if auth is enabled and user isn't logged in."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if AUTH_ENABLED and not flask_session.get("authenticated"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page — only active when AUTH_ENABLED is True."""
    if not AUTH_ENABLED:
        return redirect(url_for("dashboard"))

    error = None
    if request.method == "POST":
        user = request.form.get("username", "").strip()
        pw = request.form.get("password", "").strip()
        pw_hash = hashlib.sha256(pw.encode()).hexdigest()
        if user == AUTH_USER and pw_hash == AUTH_PASS_HASH:
            flask_session["authenticated"] = True
            flask_session.permanent = True
            next_url = request.args.get("next", url_for("dashboard"))
            return redirect(next_url)
        error = "Invalid username or password."

    return render_template("login.html", error=error, logo=LOGO_DATA_URI)


@app.route("/logout")
def logout():
    flask_session.clear()
    return redirect(url_for("login"))


# ── Logo ─────────────────────────────────────────────────────
LOGO_PATH = os.environ.get("PREP_TOOL_LOGO", "")
if not LOGO_PATH or not os.path.exists(LOGO_PATH):
    LOGO_PATH = os.path.join(
        os.path.dirname(BASE_DIR),
        "..", "7. Hibbs Branding", "Logos",
        "utt_rgb_Level_1C_Hibbs_horizontal-white.png"
    )
if not os.path.exists(LOGO_PATH):
    LOGO_PATH = r"C:\Users\ccuel\OneDrive - University of Texas at Tyler\Hibbs Institute UT Tyler\7. Hibbs Branding\Logos\utt_rgb_Level_1C_Hibbs_horizontal-white.png"

LOGO_DATA_URI = None
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    LOGO_DATA_URI = f"data:image/png;base64,{b64}"


# ── Session types ────────────────────────────────────────────
SESSION_TYPES = {
    "interview":    {"label": "Interview",     "icon": "fa-microphone",      "color": "#003A63"},
    "presentation": {"label": "Presentation",  "icon": "fa-chalkboard-user", "color": "#E87722"},
    "pitch":        {"label": "Pitch",         "icon": "fa-rocket",          "color": "#F2A900"},
}


# ── Helper functions ─────────────────────────────────────────
def load_all_sessions():
    """Load all session JSON files, sorted by modified date."""
    sessions = []
    for fname in os.listdir(SESSIONS_DIR):
        if fname.endswith(".json"):
            try:
                with open(os.path.join(SESSIONS_DIR, fname), "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append(data)
            except Exception:
                continue
    sessions.sort(key=lambda s: s.get("modified", s.get("created", "")), reverse=True)
    return sessions


def load_session(session_id):
    """Load a single session by ID."""
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_session(data):
    """Save a session to disk. Assigns ID if missing."""
    if "id" not in data or not data["id"]:
        data["id"] = uuid.uuid4().hex[:8]
    if "created" not in data:
        data["created"] = datetime.now().isoformat()
    data["modified"] = datetime.now().isoformat()
    path = os.path.join(SESSIONS_DIR, f"{data['id']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return data


def empty_session(session_type="interview"):
    """Return an empty session template."""
    base = {
        "title": "",
        "type": session_type,
        "subtitle": "",
        "date": "",
        "format": "",
        "stats_banner": [],
        "talking_points": [],
        "practice_questions": [],
        "cheatsheet_cards": [],
        "tips": [],
    }
    if session_type == "pitch":
        base["pitch_variants"] = {"30sec": "", "60sec": "", "2min": ""}
        base["key_messages"] = []
        base["objections"] = []
    if session_type == "presentation":
        base["slides"] = []
    return base


# ── Routes ───────────────────────────────────────────────────

@app.route("/")
@login_required
def dashboard():
    sessions = load_all_sessions()
    return render_template(
        "dashboard.html",
        sessions=sessions,
        types=SESSION_TYPES,
        logo=LOGO_DATA_URI,
    )


@app.route("/session/<session_id>")
@login_required
def view_session(session_id):
    session = load_session(session_id)
    if not session:
        return redirect(url_for("dashboard"))
    return render_template(
        "session.html",
        session=session,
        session_json=json.dumps(session, ensure_ascii=False),
        types=SESSION_TYPES,
        logo=LOGO_DATA_URI,
    )


@app.route("/new", methods=["GET", "POST"])
@login_required
def new_session():
    if request.method == "POST":
        stype = request.form.get("type", "interview")
        data = empty_session(stype)
        data["title"] = request.form.get("title", "Untitled Session")
        data["subtitle"] = request.form.get("subtitle", "")
        data["date"] = request.form.get("date", "")
        data["format"] = request.form.get("format", "")
        saved = save_session(data)
        return redirect(url_for("edit_session", session_id=saved["id"]))
    return render_template(
        "new_session.html",
        types=SESSION_TYPES,
        logo=LOGO_DATA_URI,
    )


@app.route("/edit/<session_id>")
@login_required
def edit_session(session_id):
    session = load_session(session_id)
    if not session:
        return redirect(url_for("dashboard"))
    return render_template(
        "edit_session.html",
        session=session,
        session_json=json.dumps(session, ensure_ascii=False),
        types=SESSION_TYPES,
        logo=LOGO_DATA_URI,
    )


@app.route("/duplicate/<session_id>", methods=["POST"])
@login_required
def duplicate_session(session_id):
    session = load_session(session_id)
    if not session:
        return redirect(url_for("dashboard"))
    session.pop("id", None)
    session.pop("created", None)
    session["title"] = session.get("title", "") + " (Copy)"
    saved = save_session(session)
    return redirect(url_for("edit_session", session_id=saved["id"]))


@app.route("/delete/<session_id>", methods=["POST"])
@login_required
def delete_session(session_id):
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(path):
        os.remove(path)
    return redirect(url_for("dashboard"))


# ── Import routes ────────────────────────────────────────────

@app.route("/import", methods=["GET", "POST"])
@login_required
def import_session():
    """Import a session from an external file."""
    error = None
    preview = None
    folder_path = request.args.get("folder", request.form.get("folder", ""))
    filename = request.args.get("filename", request.form.get("filename", ""))

    # Scan folder for importable files
    available_files = []
    if folder_path and os.path.isdir(folder_path):
        for ext in ("*.html", "*.htm", "*.txt", "*.md"):
            for fp in glob.glob(os.path.join(folder_path, ext)):
                fname = os.path.basename(fp)
                ftype = detect_file_type(fp)
                available_files.append({
                    "name": fname,
                    "type": ftype,
                    "path": fp,
                    "selected": fname == filename or os.path.splitext(fname)[0] == filename,
                })

    if request.method == "POST":
        action = request.form.get("action", "preview")

        # Resolve full path
        if folder_path and filename:
            # Try with and without extension
            filepath = os.path.join(folder_path, filename)
            if not os.path.exists(filepath):
                filepath = os.path.join(folder_path, filename + ".html")
            if not os.path.exists(filepath):
                filepath = os.path.join(folder_path, filename + ".htm")
            if not os.path.exists(filepath):
                filepath = os.path.join(folder_path, filename + ".txt")
        else:
            filepath = ""

        if not filepath or not os.path.exists(filepath):
            error = f"File not found. Please check the folder path and filename."
        else:
            try:
                imported = import_file(filepath)
                if "error" in imported:
                    error = imported["error"]
                elif action == "preview":
                    preview = imported
                elif action == "create":
                    # Create the session from imported data
                    session_type = imported.get("type", "presentation")
                    data = empty_session(session_type)

                    # Override with imported content
                    data["title"] = imported.get("title", "Imported Session")
                    data["subtitle"] = imported.get("subtitle", "")
                    data["date"] = imported.get("date", "")
                    data["format"] = imported.get("format", "")
                    data["stats_banner"] = imported.get("stats_banner", [])
                    data["talking_points"] = imported.get("talking_points", [])
                    data["practice_questions"] = imported.get("practice_questions", [])
                    data["cheatsheet_cards"] = imported.get("cheatsheet_cards", [])
                    data["tips"] = imported.get("tips", [])

                    if session_type == "pitch":
                        data["pitch_variants"] = imported.get("pitch_variants", {"30sec": "", "60sec": "", "2min": ""})
                        data["key_messages"] = imported.get("key_messages", [])
                        data["objections"] = imported.get("objections", [])

                    saved = save_session(data)
                    return redirect(url_for("view_session", session_id=saved["id"]))
            except Exception as e:
                error = f"Import failed: {str(e)}"

    return render_template(
        "import_session.html",
        types=SESSION_TYPES,
        logo=LOGO_DATA_URI,
        folder_path=folder_path,
        filename=filename,
        available_files=available_files,
        preview=preview,
        error=error,
    )


@app.route("/api/scan-folder", methods=["POST"])
@login_required
def api_scan_folder():
    """Scan a folder for importable files (AJAX endpoint)."""
    data = request.get_json()
    folder = data.get("folder", "")
    if not folder or not os.path.isdir(folder):
        return jsonify({"error": "Folder not found", "files": []})

    files = []
    for ext in ("*.html", "*.htm", "*.txt", "*.md"):
        for fp in glob.glob(os.path.join(folder, ext)):
            fname = os.path.basename(fp)
            ftype = detect_file_type(fp)
            size = os.path.getsize(fp)
            files.append({
                "name": fname,
                "type": ftype,
                "size": f"{size / 1024:.1f} KB",
                "path": fp,
            })
    files.sort(key=lambda x: x["name"])
    return jsonify({"files": files, "folder": folder})


# ── API endpoints ────────────────────────────────────────────

@app.route("/api/session/<session_id>", methods=["GET"])
@login_required
def api_get_session(session_id):
    session = load_session(session_id)
    if not session:
        return jsonify({"error": "Not found"}), 404
    return jsonify(session)


@app.route("/api/session/<session_id>", methods=["PUT"])
@login_required
def api_update_session(session_id):
    session = load_session(session_id)
    if not session:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json()
    session.update(data)
    save_session(session)
    return jsonify({"ok": True, "session": session})


@app.route("/api/session/<session_id>/talking-point", methods=["POST"])
@login_required
def api_add_talking_point(session_id):
    session = load_session(session_id)
    if not session:
        return jsonify({"error": "Not found"}), 404
    tp = request.get_json()
    session.setdefault("talking_points", []).append(tp)
    save_session(session)
    return jsonify({"ok": True})


@app.route("/api/session/<session_id>/talking-point/<int:idx>", methods=["DELETE"])
@login_required
def api_delete_talking_point(session_id, idx):
    session = load_session(session_id)
    if not session:
        return jsonify({"error": "Not found"}), 404
    pts = session.get("talking_points", [])
    if 0 <= idx < len(pts):
        pts.pop(idx)
        save_session(session)
    return jsonify({"ok": True})


@app.route("/api/session/<session_id>/practice-question", methods=["POST"])
@login_required
def api_add_practice_question(session_id):
    session = load_session(session_id)
    if not session:
        return jsonify({"error": "Not found"}), 404
    pq = request.get_json()
    session.setdefault("practice_questions", []).append(pq)
    save_session(session)
    return jsonify({"ok": True})


@app.route("/api/session/<session_id>/cheatsheet-card", methods=["POST"])
@login_required
def api_add_cheatsheet_card(session_id):
    session = load_session(session_id)
    if not session:
        return jsonify({"error": "Not found"}), 404
    card = request.get_json()
    session.setdefault("cheatsheet_cards", []).append(card)
    save_session(session)
    return jsonify({"ok": True})


# ── Main ─────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PREP_TOOL_PORT", 5050))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    print()
    print("=" * 60)
    print("  Hibbs Institute - Interview, Presentation & Pitch Prep")
    print(f"  http://localhost:{port}")
    if AUTH_ENABLED:
        print(f"  Auth ENABLED — login required (user: {AUTH_USER})")
    else:
        print("  Auth DISABLED — open access (set PREP_TOOL_USER to enable)")
    print("=" * 60)
    print()
    app.run(debug=debug, port=port, use_reloader=debug)
