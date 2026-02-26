"""
importer.py — File Importer for the Prep Tool
===============================================
Parses external files (HTML presentations, text files, etc.)
and extracts structured content into a session JSON format.

Supported formats:
  • reveal.js HTML presentations (.html)
  • Plain text / Markdown (.txt, .md)
"""

import os
import re
from bs4 import BeautifulSoup, NavigableString


# ── Public API ───────────────────────────────────────────────

def detect_file_type(filepath):
    """Detect the type of file for import."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in (".html", ".htm"):
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            head = f.read(5000)
        if "reveal" in head.lower() or 'class="slides"' in head:
            return "revealjs"
        return "html"
    if ext in (".txt", ".md"):
        return "text"
    return "unknown"


def import_file(filepath):
    """
    Import a file and return a dict with extracted session data.
    Returns: {
        "title", "subtitle", "date", "type",
        "stats_banner", "talking_points",
        "practice_questions", "cheatsheet_cards",
        "tips", "key_messages", "objections",
        "pitch_variants", "slides_summary"
    }
    """
    ftype = detect_file_type(filepath)
    if ftype == "revealjs":
        return _import_revealjs(filepath)
    elif ftype in ("html",):
        return _import_generic_html(filepath)
    elif ftype == "text":
        return _import_text(filepath)
    else:
        return {"error": f"Unsupported file type: {os.path.splitext(filepath)[1]}"}


# ── Reveal.js Parser ─────────────────────────────────────────

def _import_revealjs(filepath):
    """Parse a reveal.js presentation and extract structured content."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        html = f.read()

    soup = BeautifulSoup(html, "lxml")
    slides = soup.select("section")

    if not slides:
        slides = soup.select(".slides > *")

    result = {
        "title": "",
        "subtitle": "",
        "date": "",
        "type": "presentation",
        "format": "",
        "stats_banner": [],
        "talking_points": [],
        "practice_questions": [],
        "cheatsheet_cards": [],
        "tips": [],
        "key_messages": [],
        "pitch_variants": {"30sec": "", "60sec": "", "2min": ""},
        "objections": [],
        "slides_summary": [],
    }

    # ── Extract from each slide ──
    for i, slide in enumerate(slides):
        slide_data = _parse_slide(slide, i)
        result["slides_summary"].append(slide_data)

        # First slide → title info
        if i == 0:
            result["title"] = slide_data.get("title", "")
            result["subtitle"] = slide_data.get("subtitle", "")
            result["date"] = slide_data.get("date", "")

    # Detect type from ALL slide content (not just title)
    all_text = " ".join(
        (s.get("title", "") + " " + s.get("subtitle", "") + " " +
         s.get("section_label", "") + " " + s.get("content_text", ""))
        for s in result["slides_summary"]
    ).lower()
    if any(w in all_text for w in ["pitch", "proposal", "funding", "grant", "invest", "seed", "budget"]):
        result["type"] = "pitch"
    elif any(w in all_text for w in ["interview", "hiring", "candidate"]):
        result["type"] = "interview"
    else:
        result["type"] = "presentation"

    # Second pass: extract from slides
    for i, slide_data in enumerate(result["slides_summary"]):

        # Collect stats from any slide (but not budget line items)
        if slide_data.get("stats"):
            for stat in slide_data["stats"]:
                # Skip individual budget line items — keep totals and key figures
                val = stat["value"].strip()
                label_lower = stat["label"].lower()
                is_budget_item = (
                    val.startswith("$") and
                    any(w in label_lower for w in ["personnel", "conference", "fringe", "panel event", "data ("])
                )
                if not is_budget_item:
                    result["stats_banner"].append(stat)

        # Build talking points from substantive slides (skip title, Q&A)
        if i > 0 and slide_data.get("heading") and slide_data.get("content_text"):
            tp = _slide_to_talking_point(slide_data, i)
            if tp:
                result["talking_points"].append(tp)

        # Collect cards
        if slide_data.get("cards"):
            card = {
                "icon": _pick_icon_for_heading(slide_data.get("heading", "")),
                "title": slide_data.get("heading", f"Slide {i + 1}"),
                "items": [[c["title"], c.get("detail", "")] for c in slide_data["cards"]]
            }
            result["cheatsheet_cards"].append(card)

    # ── Deduplicate stats (same value appearing on multiple slides) ──
    seen = set()
    unique_stats = []
    for s in result["stats_banner"]:
        key = s["value"].strip()
        if key not in seen:
            seen.add(key)
            unique_stats.append(s)
    result["stats_banner"] = unique_stats

    # ── Generate practice questions from content ──
    result["practice_questions"] = _generate_practice_questions(result)

    # ── Generate tips ──
    result["tips"] = _generate_tips(result)

    # ── Extract key messages from stats + headings ──
    for s in result["stats_banner"]:
        result["key_messages"].append(f"{s['value']} — {s['label']}")
    for tp in result["talking_points"][:5]:
        if tp.get("label"):
            result["key_messages"].append(tp["label"])

    # ── Generate pitch variants if it's a pitch ──
    if result["type"] == "pitch":
        result["pitch_variants"] = _generate_pitch_variants(result)

    # Remove slides_summary from final output (internal use only)
    slides_info = result.pop("slides_summary")

    # Add format based on slide count
    result["format"] = f"Presentation ({len(slides_info)} slides)"

    return result


def _parse_slide(slide, index):
    """Extract structured data from a single <section> slide."""
    data = {
        "index": index,
        "title": "",
        "subtitle": "",
        "heading": "",
        "section_label": "",
        "date": "",
        "content_text": "",
        "stats": [],
        "cards": [],
        "steps": [],
        "team_members": [],
        "budget_items": [],
        "is_dark": "dark-slide" in slide.get("class", []),
    }

    # Section label (e.g., "The Problem", "Our Solution")
    label_el = slide.select_one(".section-label")
    if label_el:
        data["section_label"] = _clean_text(label_el.get_text())
        data["heading"] = data["section_label"]

    # H1 (usually title slide)
    h1 = slide.select_one("h1")
    if h1:
        data["title"] = _clean_text(h1.get_text())

    # H2 (section heading)
    h2 = slide.select_one("h2")
    if h2:
        if not data["heading"]:
            data["heading"] = _clean_text(h2.get_text())
        if index == 0 and not data["title"]:
            data["title"] = _clean_text(h2.get_text())

    # Subtitle (first p after h1, or description text)
    if index == 0:
        for p in slide.select("p"):
            text = _clean_text(p.get_text())
            if text and len(text) > 10 and not data["subtitle"]:
                # Skip author names and dates
                if not _looks_like_date(text) and not _looks_like_name(text):
                    data["subtitle"] = text
                    break
        # Extract date
        for p in slide.select("p"):
            text = _clean_text(p.get_text())
            if _looks_like_date(text):
                data["date"] = text
                break

    # Stats: look for stat-box elements or big numbers
    for stat_el in slide.select(".stat-box"):
        num_el = stat_el.select_one(".stat-num")
        lbl_el = stat_el.select_one(".stat-lbl")
        if num_el and lbl_el:
            data["stats"].append({
                "value": _clean_text(_get_text(num_el)),
                "label": _clean_text(_get_text(lbl_el)),
            })

    # Also detect inline stats (big numbers with descriptions)
    if not data["stats"]:
        _extract_inline_stats(slide, data)

    # Cards (deliverables, features, etc.)
    for card_el in slide.select(".card"):
        h4 = card_el.select_one("h4")
        p = card_el.select_one("p")
        tag = card_el.select_one(".tag")
        if h4:
            data["cards"].append({
                "title": _clean_text(_get_text(h4)),
                "detail": _clean_text(_get_text(p)) if p else "",
                "tag": _clean_text(_get_text(tag)) if tag else "",
            })

    # Journey steps
    for step_el in slide.select(".step"):
        h4 = step_el.select_one("h4")
        p = step_el.select_one("p")
        months = step_el.select_one(".months")
        if h4:
            data["steps"].append({
                "title": _clean_text(_get_text(h4)),
                "detail": _clean_text(_get_text(p)) if p else "",
                "timing": _clean_text(_get_text(months)) if months else "",
            })

    # Team members
    for team_el in slide.select(".team-card"):
        h4 = team_el.select_one("h4")
        role = team_el.select_one(".role")
        badge = team_el.select_one(".badge")
        if h4:
            data["team_members"].append({
                "name": _clean_text(_get_text(h4)),
                "role": _clean_text(_get_text(role)) if role else "",
                "badge": _clean_text(_get_text(badge)) if badge else "",
            })

    # Budget items (from bar chart or budget sections)
    for bar in slide.select(".bar-row"):
        label_span = bar.select_one("span")
        amount_spans = bar.select("span")
        if len(amount_spans) >= 2:
            data["budget_items"].append({
                "label": _clean_text(amount_spans[0].get_text()),
                "amount": _clean_text(amount_spans[-1].get_text()),
            })

    # Pathway badges
    for badge in slide.select(".pw-badge"):
        h4 = badge.select_one("h4")
        p = badge.select_one("p")
        if h4:
            data["cards"].append({
                "title": _clean_text(h4.get_text()),
                "detail": _clean_text(p.get_text()) if p else "",
            })

    # General content text (for talking points)
    # Collect all meaningful text from p elements and callouts
    text_parts = []
    for el in slide.select("p, .callout p, li"):
        t = _clean_text(_get_text(el))
        if t and len(t) > 15:
            text_parts.append(t)
    data["content_text"] = " ".join(text_parts[:8])  # cap at 8 paragraphs

    # Q&A tiles
    for tile in slide.select(".qa-tile"):
        t = _clean_text(_get_text(tile))
        if t:
            data["cards"].append({"title": t, "detail": "Discussion topic"})

    return data


def _extract_inline_stats(slide, data):
    """Extract stats from inline styled elements (not using .stat-box class)."""
    # Look for elements with very large font sizes containing numbers
    for el in slide.find_all(style=True):
        style = el.get("style", "")
        text = _clean_text(_get_text(el))

        # Match big numbers: percentages, dollar amounts, plain numbers
        if re.search(r'font-size:\s*2\.\d+em|font-weight:\s*[789]00', style):
            num_match = re.match(r'^[\$]?\d[\d,]*[%]?$', text.strip())
            if num_match:
                # Find the next sibling or nearby element with description
                desc = ""
                parent = el.parent
                if parent:
                    for sib in parent.children:
                        if sib != el and not isinstance(sib, NavigableString):
                            sib_text = _clean_text(_get_text(sib))
                            if sib_text and len(sib_text) > 5 and sib_text != text:
                                desc = sib_text
                                break
                if desc:
                    data["stats"].append({"value": text.strip(), "label": desc})


def _slide_to_talking_point(slide_data, index):
    """Convert a parsed slide into a talking point."""
    heading = slide_data.get("heading", "") or slide_data.get("section_label", "")
    if not heading:
        return None

    # Build rich note from content
    note_parts = []

    # Add section label as heading
    if slide_data.get("section_label"):
        note_parts.append(f"<p><strong>{slide_data['section_label']}</strong></p>")

    # Add stats
    for stat in slide_data.get("stats", []):
        note_parts.append(
            f'<p><span class="key-stat">{stat["value"]}</span> — {stat["label"]}</p>'
        )

    # Add steps
    for step in slide_data.get("steps", []):
        note_parts.append(
            f'<p><strong>{step["title"]}</strong>: {step["detail"]}'
            + (f' <em>({step["timing"]})</em>' if step.get("timing") else "")
            + "</p>"
        )

    # Add cards as bullet points
    if slide_data.get("cards"):
        items = "".join(
            f'<li><strong>{c["title"]}</strong>: {c.get("detail", "")}</li>'
            for c in slide_data["cards"]
        )
        note_parts.append(f"<ul>{items}</ul>")

    # Add team members
    for tm in slide_data.get("team_members", []):
        note_parts.append(
            f'<p><span class="key-stat">{tm["name"]}</span> — {tm["role"]}'
            + (f' ({tm["badge"]})' if tm.get("badge") else "")
            + "</p>"
        )

    # Add budget items
    if slide_data.get("budget_items"):
        items = "".join(
            f'<li>{b["label"]}: <strong>{b["amount"]}</strong></li>'
            for b in slide_data["budget_items"]
        )
        note_parts.append(f"<p><strong>Budget Breakdown:</strong></p><ul>{items}</ul>")

    # Add general content if we don't have structured data
    if not note_parts and slide_data.get("content_text"):
        note_parts.append(f"<p>{slide_data['content_text'][:500]}</p>")

    if not note_parts:
        return None

    return {
        "id": re.sub(r'[^a-z0-9]+', '-', heading.lower()).strip('-')[:30],
        "label": heading,
        "number": f"Slide {index + 1}",
        "timing": "~1-2 min",
        "question": f"Tell me about: {heading}",
        "note": "\n".join(note_parts),
        "source": "Imported from presentation",
        "tip_do": f"Lead with the key insight from this section.",
        "tip_dont": "Don't read slides verbatim — speak naturally.",
    }


def _generate_practice_questions(result):
    """Generate practice questions from extracted content."""
    questions = []

    title = result.get("title", "this topic")

    # Overview question
    questions.append({
        "q": f"In one sentence, what is this presentation about?",
        "points": [
            result.get("title", ""),
            result.get("subtitle", ""),
        ]
    })

    # Stats-based question
    if result["stats_banner"]:
        questions.append({
            "q": "What are the key statistics that support your argument?",
            "points": [
                f'{s["value"]} — {s["label"]}'
                for s in result["stats_banner"][:6]
            ]
        })

    # One question per talking point
    for tp in result["talking_points"]:
        if tp.get("label"):
            questions.append({
                "q": tp.get("question", f"Explain the section on: {tp['label']}"),
                "points": _extract_points_from_note(tp.get("note", "")),
            })

    # What's next / impact question
    questions.append({
        "q": "What is the broader impact or next step?",
        "points": [
            f"Key message: {msg}" for msg in result.get("key_messages", [])[:4]
        ]
    })

    # Filter out questions with empty points
    return [q for q in questions if q.get("points") and any(p for p in q["points"])]


def _generate_tips(result):
    """Generate presentation tips from content."""
    tips = [
        f"Open strong: lead with your most compelling stat or fact",
        f"Know your <b>{len(result.get('talking_points', []))} talking points</b> cold — practice transitions between them",
    ]

    if result["stats_banner"]:
        top_stat = result["stats_banner"][0]
        tips.append(
            f'Memorize the key number: <b>{top_stat["value"]}</b> ({top_stat["label"]})'
        )

    tips.extend([
        "Make eye contact with the panel — don't read your slides",
        "Keep answers concise. If they want more detail, they'll ask",
        "Have your <b>elevator pitch</b> ready (30-second version)",
        "Anticipate tough questions and prepare calm, evidence-based answers",
        "End with a clear <b>call to action</b> — what do you want them to do?",
    ])

    return tips


def _generate_pitch_variants(result):
    """Generate 30s/60s/2min pitch scripts from extracted content."""
    title = result.get("title", "this project")
    subtitle = result.get("subtitle", "")

    # Build key facts list
    facts = []
    for s in result.get("stats_banner", [])[:4]:
        facts.append(f'{s["value"]} {s["label"]}')

    tp_summaries = []
    for tp in result.get("talking_points", [])[:5]:
        tp_summaries.append(tp.get("label", ""))

    facts_str = ". ".join(facts[:3]) + "." if facts else ""
    topics_str = ", ".join(tp_summaries[:3]) if tp_summaries else ""

    thirty = (
        f"{title}. {subtitle}. "
        + (f"Key facts: {facts_str} " if facts_str else "")
        + "This presentation covers the problem, our solution, and the path forward."
    )

    sixty = (
        f"{title}: {subtitle}.\n\n"
        + (f"The data is clear — {facts_str}\n\n" if facts_str else "")
        + (f"We address this through: {topics_str}.\n\n" if topics_str else "")
        + "The result is an evidence-based approach that delivers actionable outcomes."
    )

    two_min = (
        f"Let me walk you through {title}.\n\n"
        + (f"{subtitle}.\n\n" if subtitle else "")
        + (f"Here are the numbers that matter: {facts_str}\n\n" if facts_str else "")
    )
    for tp in result.get("talking_points", [])[:5]:
        two_min += f"{tp.get('label', '')}: {_strip_html(tp.get('note', ''))[:200]}\n\n"
    two_min += "That's what we're building. Thank you."

    return {"30sec": thirty, "60sec": sixty, "2min": two_min}


# ── Generic HTML Parser ──────────────────────────────────────

def _import_generic_html(filepath):
    """Parse a generic HTML file and extract headings + content."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        html = f.read()

    soup = BeautifulSoup(html, "lxml")

    # Get title
    title_el = soup.select_one("title") or soup.select_one("h1")
    title = _clean_text(title_el.get_text()) if title_el else os.path.basename(filepath)

    # Extract sections by headings
    talking_points = []
    for h in soup.select("h1, h2, h3"):
        heading = _clean_text(h.get_text())
        content = []
        sib = h.find_next_sibling()
        while sib and sib.name not in ("h1", "h2", "h3"):
            t = _clean_text(sib.get_text())
            if t:
                content.append(t)
            sib = sib.find_next_sibling()

        if heading and content:
            talking_points.append({
                "id": re.sub(r'[^a-z0-9]+', '-', heading.lower()).strip('-')[:30],
                "label": heading,
                "number": f"Section {len(talking_points) + 1}",
                "timing": "~1-2 min",
                "question": f"Tell me about: {heading}",
                "note": "<p>" + "</p><p>".join(content[:5]) + "</p>",
                "source": "Imported",
                "tip_do": "Focus on the main takeaway.",
                "tip_dont": "Don't go off-topic.",
            })

    result = {
        "title": title,
        "subtitle": "",
        "date": "",
        "type": "presentation",
        "format": "Imported from HTML",
        "stats_banner": [],
        "talking_points": talking_points,
        "practice_questions": [],
        "cheatsheet_cards": [],
        "tips": _generate_tips({"stats_banner": [], "talking_points": talking_points}),
    }
    result["practice_questions"] = _generate_practice_questions(result)
    return result


# ── Text / Markdown Parser ───────────────────────────────────

def _import_text(filepath):
    """Parse a plain text or Markdown file."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    lines = text.strip().split("\n")
    title = lines[0].lstrip("#").strip() if lines else os.path.basename(filepath)

    # Split by headings (# or === underlines)
    sections = []
    current_heading = ""
    current_content = []

    for line in lines[1:]:
        stripped = line.strip()
        if stripped.startswith("#") or (stripped and all(c in "=-" for c in stripped) and len(stripped) > 3):
            if current_heading and current_content:
                sections.append((current_heading, "\n".join(current_content)))
            if stripped.startswith("#"):
                current_heading = stripped.lstrip("#").strip()
            else:
                current_heading = current_content[-1] if current_content else stripped
                current_content = []
            current_content = []
        else:
            if stripped:
                current_content.append(stripped)

    if current_heading and current_content:
        sections.append((current_heading, "\n".join(current_content)))

    talking_points = []
    for heading, content in sections:
        talking_points.append({
            "id": re.sub(r'[^a-z0-9]+', '-', heading.lower()).strip('-')[:30],
            "label": heading,
            "number": f"Section {len(talking_points) + 1}",
            "timing": "~1-2 min",
            "question": f"Tell me about: {heading}",
            "note": "<p>" + content.replace("\n\n", "</p><p>").replace("\n", "<br>") + "</p>",
            "source": "Imported",
            "tip_do": "Focus on the main takeaway.",
            "tip_dont": "Don't go off-topic.",
        })

    result = {
        "title": title,
        "subtitle": "",
        "date": "",
        "type": "presentation",
        "format": "Imported from text",
        "stats_banner": [],
        "talking_points": talking_points,
        "practice_questions": [],
        "cheatsheet_cards": [],
        "tips": _generate_tips({"stats_banner": [], "talking_points": talking_points}),
    }
    result["practice_questions"] = _generate_practice_questions(result)
    return result


# ── Utility Functions ─────────────────────────────────────────

def _clean_text(text):
    """Clean extracted text: collapse whitespace, strip."""
    if not text:
        return ""
    # Preserve space where <br> tags were (they become newlines after get_text)
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _get_text(el):
    """Get text from a BeautifulSoup element, using spaces as separator for br tags."""
    if el is None:
        return ""
    return el.get_text(separator=" ")


def _strip_html(html_str):
    """Remove HTML tags from a string."""
    return re.sub(r'<[^>]+>', '', html_str).strip()


def _looks_like_date(text):
    """Check if text looks like a date."""
    date_patterns = [
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\b',
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
        r'\b(?:Spring|Summer|Fall|Winter)\s+\d{4}\b',
    ]
    for pat in date_patterns:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


def _looks_like_name(text):
    """Check if text looks like a person's name (e.g., has Dr., Ph.D., etc.)."""
    name_patterns = [r'\bDr\.\b', r'\bPh\.?D\.?\b', r'\bD\.?E\.?D\.?\b', r'\bM\.?D\.?\b']
    for pat in name_patterns:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


def _pick_icon_for_heading(heading):
    """Pick an emoji icon based on heading keywords."""
    h = heading.lower()
    if any(w in h for w in ["problem", "challenge", "gap", "issue"]):
        return "⚠️"
    if any(w in h for w in ["solution", "approach", "method"]):
        return "💡"
    if any(w in h for w in ["deliver", "output", "result"]):
        return "📦"
    if any(w in h for w in ["team", "people", "who"]):
        return "👥"
    if any(w in h for w in ["budget", "cost", "invest", "money"]):
        return "💰"
    if any(w in h for w in ["fund", "grant", "pathway", "scale"]):
        return "🚀"
    if any(w in h for w in ["data", "stat", "number", "index"]):
        return "📊"
    if any(w in h for w in ["aim", "research", "study"]):
        return "🎯"
    if any(w in h for w in ["close", "conclusion", "summary", "thank"]):
        return "🏁"
    if any(w in h for w in ["question", "q&a", "discuss"]):
        return "❓"
    return "📋"


def _extract_points_from_note(html_note):
    """Extract bullet points from an HTML note string."""
    soup = BeautifulSoup(html_note, "lxml")
    points = []

    # Get list items
    for li in soup.select("li"):
        t = _clean_text(li.get_text())
        if t:
            points.append(t)

    # Get key-stat spans
    if not points:
        for span in soup.select(".key-stat"):
            t = _clean_text(span.get_text())
            if t:
                points.append(t)

    # Fall back to paragraph text
    if not points:
        for p in soup.select("p"):
            t = _clean_text(p.get_text())
            if t and len(t) > 15:
                points.append(t[:120])

    return points[:6]


# ── Quick test ───────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        import json
        result = import_file(sys.argv[1])
        output = json.dumps(result, indent=2, ensure_ascii=False)
        sys.stdout.buffer.write(output.encode("utf-8"))
        print()  # newline
    else:
        print("Usage: python importer.py <filepath>")
