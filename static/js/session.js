/* ═══════════════════════════════════════════════════════════
   Hibbs Institute — Prep Tool — Session View JS
   Handles: mode switching, practice mode, pitch timer,
   topic filtering, keyboard shortcuts, self-rating,
   confidence tracker, teleprompter, practice history
   ═══════════════════════════════════════════════════════════ */

// SESSION is injected by the template as a global variable

const STORAGE_KEY_CONFIDENCE = 'hibbs-confidence-' + SESSION.id;
const STORAGE_KEY_HISTORY    = 'hibbs-practice-history-' + SESSION.id;

// ── Mode switching ──────────────────────────────────────
function switchMode(mode, btn) {
    document.querySelectorAll('.mode-tab').forEach(t => t.classList.remove('active'));
    if (btn) btn.classList.add('active');
    document.querySelectorAll('.mode-panel').forEach(p => p.classList.remove('visible'));
    const panel = document.getElementById('panel-' + mode);
    if (panel) panel.classList.add('visible');
    // Init practice on first open
    if (mode === 'practice' && currentQ === -1 && SESSION.practice_questions && SESSION.practice_questions.length) {
        nextPracticeQuestion();
    }
    // Init rehearsal on first open
    if (mode === 'teleprompter' && !rehearsalInitialized) {
        initRehearsal();
    }
}

// ── Topic filtering ─────────────────────────────────────
function filterTopic(topic, btn) {
    document.querySelectorAll('.topic-chip').forEach(c => c.classList.remove('active'));
    if (btn) btn.classList.add('active');
    document.querySelectorAll('.tp-card').forEach(card => {
        card.style.display = (topic === 'all' || card.dataset.topic === topic) ? '' : 'none';
    });
}


// ══════════════════════════════════════════════════════════
// CONFIDENCE TRACKER
// ══════════════════════════════════════════════════════════

let confidenceData = {};

function loadConfidence() {
    try {
        const stored = localStorage.getItem(STORAGE_KEY_CONFIDENCE);
        if (stored) confidenceData = JSON.parse(stored);
    } catch(e) { confidenceData = {}; }
    applyConfidenceUI();
}

function saveConfidence() {
    localStorage.setItem(STORAGE_KEY_CONFIDENCE, JSON.stringify(confidenceData));
}

function rateConfidence(idx, level) {
    confidenceData[idx] = level;
    saveConfidence();
    applyConfidenceUI();
}

function resetConfidence() {
    confidenceData = {};
    localStorage.removeItem(STORAGE_KEY_CONFIDENCE);
    applyConfidenceUI();
}

function applyConfidenceUI() {
    const tpCards = document.querySelectorAll('.tp-card[data-tp-idx]');
    let total = 0, count = 0;

    tpCards.forEach(card => {
        const idx = card.dataset.tpIdx;
        const level = confidenceData[idx] || 0;

        // Apply confidence class to the card
        card.classList.remove('conf-level-1', 'conf-level-2', 'conf-level-3', 'conf-level-4', 'conf-level-5', 'conf-level-0');
        card.classList.add('conf-level-' + level);

        // Highlight buttons
        card.querySelectorAll('.conf-btn').forEach(btn => {
            const btnLevel = parseInt(btn.dataset.level);
            btn.classList.toggle('active', btnLevel === level);
        });

        // Update bar in dashboard
        const bar = document.getElementById('conf-bar-' + idx);
        const val = document.getElementById('conf-val-' + idx);
        if (bar) {
            bar.style.width = level ? (level / 5 * 100) + '%' : '0%';
            bar.className = 'confidence-bar-fill conf-fill-' + level;
        }
        if (val) val.textContent = level ? level + '/5' : '—';

        if (level > 0) { total += level; count++; }
    });

    // Overall score
    const overallScore = document.getElementById('confidence-overall-score');
    const overallEl = document.getElementById('confidence-overall');
    if (overallScore) {
        if (count > 0) {
            const avg = (total / count).toFixed(1);
            overallScore.textContent = avg + '/5';
            // Color the overall indicator
            const avgNum = parseFloat(avg);
            overallEl.className = 'confidence-overall';
            if (avgNum >= 4) overallEl.classList.add('conf-overall-high');
            else if (avgNum >= 2.5) overallEl.classList.add('conf-overall-mid');
            else overallEl.classList.add('conf-overall-low');
        } else {
            overallScore.textContent = '—';
            overallEl.className = 'confidence-overall';
        }
    }
}


// ══════════════════════════════════════════════════════════
// PRACTICE MODE
// ══════════════════════════════════════════════════════════

let currentQ = -1;
let timerInterval = null;
let timerSeconds = 0;
let timerRunning = false;
let ratings = {};
let practiceStartTime = null;

function nextPracticeQuestion() {
    const questions = SESSION.practice_questions || [];
    if (!questions.length) return;
    currentQ = (currentQ + 1) % questions.length;

    // If we just wrapped around back to 0 (and not the first open), save the session
    if (currentQ === 0 && Object.keys(ratings).length > 0) {
        savePracticeSession();
    }

    const data = questions[currentQ];

    // Track when practice starts
    if (!practiceStartTime) practiceStartTime = new Date();

    // Update question text
    const el = document.getElementById('practice-question');
    if (el) el.textContent = data.q;

    // Reset reveal
    const revealBox = document.getElementById('reveal-box');
    if (revealBox) {
        revealBox.classList.remove('show');
        revealBox.innerHTML = '';
    }

    // Reset self-rating
    const ratingEl = document.getElementById('self-rating');
    if (ratingEl) ratingEl.style.display = 'none';
    document.querySelectorAll('.stars button').forEach(b => b.classList.remove('active'));

    // Reset timer
    resetTimer();

    // Update progress
    updateProgress();
}

function updateProgress() {
    const total = (SESSION.practice_questions || []).length;
    if (total === 0) return;
    const fill = document.getElementById('progress-fill');
    const text = document.getElementById('progress-text');
    if (fill) fill.style.width = ((currentQ + 1) / total * 100) + '%';
    if (text) text.textContent = (currentQ + 1) + ' / ' + total;
}

function toggleTimer() {
    if (timerRunning) {
        pauseTimer();
    } else {
        startTimer();
    }
}

function startTimer() {
    timerRunning = true;
    const btn = document.getElementById('timer-btn');
    if (btn) btn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause';
    timerInterval = setInterval(() => {
        timerSeconds++;
        updateTimerDisplay();
    }, 1000);
}

function pauseTimer() {
    clearInterval(timerInterval);
    timerRunning = false;
    const btn = document.getElementById('timer-btn');
    if (btn) btn.innerHTML = '<i class="fa-solid fa-play"></i> Resume';
}

function resetTimer() {
    clearInterval(timerInterval);
    timerRunning = false;
    timerSeconds = 0;
    updateTimerDisplay();
    const btn = document.getElementById('timer-btn');
    if (btn) btn.innerHTML = '<i class="fa-solid fa-play"></i> Start Timer';
}

function updateTimerDisplay() {
    const m = Math.floor(timerSeconds / 60);
    const s = timerSeconds % 60;
    const display = document.getElementById('timer-display');
    if (!display) return;
    display.textContent = m + ':' + (s < 10 ? '0' : '') + s;
    // Color feedback
    if (timerSeconds <= 90) {
        display.style.color = 'var(--green)';
    } else if (timerSeconds <= 120) {
        display.style.color = 'var(--orange)';
    } else {
        display.style.color = 'var(--red)';
    }
}

function revealAnswer() {
    const questions = SESSION.practice_questions || [];
    if (currentQ < 0 || currentQ >= questions.length) return;
    const data = questions[currentQ];
    let html = '<h4><i class="fa-solid fa-bullseye"></i> Key Points to Hit:</h4><ul>';
    (data.points || []).forEach(p => html += '<li>' + p + '</li>');
    html += '</ul>';
    const box = document.getElementById('reveal-box');
    if (box) {
        box.innerHTML = html;
        box.classList.add('show');
    }
    // Show self-rating
    const ratingEl = document.getElementById('self-rating');
    if (ratingEl) ratingEl.style.display = 'block';
}

function rateAnswer(rating) {
    ratings[currentQ] = rating;
    document.querySelectorAll('.stars button').forEach((btn, i) => {
        btn.classList.toggle('active', i < rating);
    });
}


// ══════════════════════════════════════════════════════════
// PRACTICE SESSION HISTORY
// ══════════════════════════════════════════════════════════

function savePracticeSession() {
    if (Object.keys(ratings).length === 0) return;

    const history = loadPracticeHistory();
    const total = Object.values(ratings).reduce((a, b) => a + b, 0);
    const avg = total / Object.keys(ratings).length;

    history.push({
        date: new Date().toISOString(),
        questionsAttempted: Object.keys(ratings).length,
        totalQuestions: (SESSION.practice_questions || []).length,
        averageRating: Math.round(avg * 100) / 100,
        ratings: { ...ratings },
        durationMinutes: practiceStartTime
            ? Math.round((new Date() - practiceStartTime) / 60000 * 10) / 10
            : 0,
    });

    // Keep only last 20 sessions
    while (history.length > 20) history.shift();

    localStorage.setItem(STORAGE_KEY_HISTORY, JSON.stringify(history));
    ratings = {};
    practiceStartTime = new Date();
    updateHistoryRibbon();
}

function loadPracticeHistory() {
    try {
        const stored = localStorage.getItem(STORAGE_KEY_HISTORY);
        return stored ? JSON.parse(stored) : [];
    } catch(e) { return []; }
}

function updateHistoryRibbon() {
    const history = loadPracticeHistory();
    const countEl = document.getElementById('history-sessions-count');
    const avgEl = document.getElementById('history-avg-rating');

    if (countEl) countEl.textContent = history.length;
    if (avgEl) {
        if (history.length > 0) {
            const totalAvg = history.reduce((a, h) => a + h.averageRating, 0) / history.length;
            avgEl.textContent = totalAvg.toFixed(1);
        } else {
            avgEl.textContent = '—';
        }
    }

    // Update detail panel
    renderHistoryEntries(history);
}

function renderHistoryEntries(history) {
    const container = document.getElementById('history-entries');
    if (!container) return;

    if (history.length === 0) {
        container.innerHTML = '<p class="history-empty">No practice history yet. Complete a full set of questions to see results here.</p>';
        return;
    }

    let html = '<div class="history-list">';
    history.slice().reverse().forEach((h, i) => {
        const date = new Date(h.date);
        const dateStr = date.toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' });
        const timeStr = date.toLocaleTimeString('en-US', { hour:'numeric', minute:'2-digit' });
        const stars = '★'.repeat(Math.round(h.averageRating)) + '☆'.repeat(5 - Math.round(h.averageRating));
        const pct = Math.round(h.questionsAttempted / h.totalQuestions * 100);

        html += `
        <div class="history-entry">
            <div class="history-entry-date">${dateStr} at ${timeStr}</div>
            <div class="history-entry-stats">
                <span class="history-stars">${stars}</span>
                <span>${h.averageRating.toFixed(1)}/5</span>
                <span class="history-entry-sep">&middot;</span>
                <span>${h.questionsAttempted}/${h.totalQuestions} Qs (${pct}%)</span>
                ${h.durationMinutes ? `<span class="history-entry-sep">&middot;</span><span>${h.durationMinutes} min</span>` : ''}
            </div>
        </div>`;
    });
    html += '</div>';
    container.innerHTML = html;
}

function toggleHistoryPanel() {
    const panel = document.getElementById('practice-history-panel');
    if (panel) {
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    }
}

function clearPracticeHistory() {
    if (!confirm('Clear all practice history for this session?')) return;
    localStorage.removeItem(STORAGE_KEY_HISTORY);
    ratings = {};
    updateHistoryRibbon();
}


// ══════════════════════════════════════════════════════════
// TELEPROMPTER / REHEARSAL MODE
// ══════════════════════════════════════════════════════════

let rehearsalInitialized = false;
let rehearsalSlide = 0;
let rehearsalTimer = null;
let rehearsalSeconds = 0;
let rehearsalRunning = false;

function initRehearsal() {
    rehearsalInitialized = true;
    goToRehearsalSlide(0);
}

function goToRehearsalSlide(idx) {
    const slides = document.querySelectorAll('.teleprompter-slide');
    const dots = document.querySelectorAll('.teleprompter-dot');
    const totalSlides = slides.length;
    if (idx < 0 || idx >= totalSlides) return;

    rehearsalSlide = idx;

    slides.forEach((s, i) => {
        s.classList.toggle('active', i === idx);
    });
    dots.forEach((d, i) => {
        d.classList.toggle('active', i === idx);
        // Mark visited
        if (i <= idx) d.classList.add('visited');
    });

    // Update counter
    const counter = document.getElementById('rehearsal-current');
    if (counter) counter.textContent = idx + 1;

    // Update prev/next state
    const prev = document.getElementById('rehearsal-prev');
    const next = document.getElementById('rehearsal-next');
    if (prev) prev.disabled = (idx === 0);
    if (next) {
        if (idx === totalSlides - 1) {
            next.innerHTML = '<i class="fa-solid fa-flag-checkered"></i> Finish';
        } else {
            next.innerHTML = 'Next <i class="fa-solid fa-arrow-right"></i>';
        }
    }

    // Scroll to active slide
    const activeSlide = document.querySelector('.teleprompter-slide.active');
    if (activeSlide) {
        activeSlide.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function nextRehearsalSlide() {
    const slides = document.querySelectorAll('.teleprompter-slide');
    if (rehearsalSlide < slides.length - 1) {
        goToRehearsalSlide(rehearsalSlide + 1);
    } else {
        // Finish rehearsal
        pauseRehearsal();
        const timer = document.getElementById('rehearsal-timer');
        if (timer) timer.style.color = 'var(--green)';
    }
}

function prevRehearsalSlide() {
    if (rehearsalSlide > 0) {
        goToRehearsalSlide(rehearsalSlide - 1);
    }
}

function toggleRehearsal() {
    if (rehearsalRunning) {
        pauseRehearsal();
    } else {
        startRehearsal();
    }
}

function startRehearsal() {
    rehearsalRunning = true;
    const btn = document.getElementById('rehearsal-play-btn');
    if (btn) btn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause';

    rehearsalTimer = setInterval(() => {
        rehearsalSeconds++;
        updateRehearsalTimerDisplay();
    }, 1000);
}

function pauseRehearsal() {
    clearInterval(rehearsalTimer);
    rehearsalRunning = false;
    const btn = document.getElementById('rehearsal-play-btn');
    if (btn) btn.innerHTML = '<i class="fa-solid fa-play"></i> Resume';
}

function resetRehearsal() {
    clearInterval(rehearsalTimer);
    rehearsalRunning = false;
    rehearsalSeconds = 0;
    updateRehearsalTimerDisplay();
    const btn = document.getElementById('rehearsal-play-btn');
    if (btn) btn.innerHTML = '<i class="fa-solid fa-play"></i> Start Rehearsal';

    // Reset dots
    document.querySelectorAll('.teleprompter-dot').forEach(d => d.classList.remove('visited'));
    goToRehearsalSlide(0);
}

function updateRehearsalTimerDisplay() {
    const m = Math.floor(rehearsalSeconds / 60);
    const s = rehearsalSeconds % 60;
    const el = document.getElementById('rehearsal-timer');
    if (el) {
        el.textContent = m + ':' + (s < 10 ? '0' : '') + s;
        el.style.color = '';
    }
}

function setTeleprompterFontSize(level) {
    const display = document.getElementById('teleprompter-display');
    if (!display) return;
    display.className = 'teleprompter-display teleprompter-size-' + level;
}

function toggleTeleprompterFullscreen() {
    const panel = document.getElementById('panel-teleprompter');
    if (!panel) return;
    if (document.fullscreenElement) {
        document.exitFullscreen();
    } else {
        panel.requestFullscreen().catch(() => {});
    }
}


// ══════════════════════════════════════════════════════════
// PRINT QUICK REFERENCE
// ══════════════════════════════════════════════════════════

function printQuickRef() {
    // Switch to cheatsheet mode, then print
    switchMode('cheatsheet', document.querySelector('[data-mode="cheatsheet"]'));
    setTimeout(() => window.print(), 300);
}


// ══════════════════════════════════════════════════════════
// PITCH TIMER (countdown)
// ══════════════════════════════════════════════════════════

let pitchDuration = 30; // seconds
let pitchRemaining = 30;
let pitchInterval = null;
let pitchRunning = false;
const CIRCUMFERENCE = 2 * Math.PI * 90; // 565.48

function selectPitchVariant(seconds, btn) {
    // Update active button
    document.querySelectorAll('.pitch-var-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');

    pitchDuration = seconds;
    resetPitchTimer();

    // Update pitch text
    const textEl = document.getElementById('pitch-text');
    if (textEl && SESSION.pitch_variants) {
        const key = seconds === 30 ? '30sec' : seconds === 60 ? '60sec' : '2min';
        const text = SESSION.pitch_variants[key];
        textEl.innerHTML = text || '<em>No script written for this variant yet.</em>';
    }
}

function togglePitchTimer() {
    if (pitchRunning) {
        pausePitchTimer();
    } else {
        startPitchTimer();
    }
}

function startPitchTimer() {
    pitchRunning = true;
    const btn = document.getElementById('pitch-btn');
    if (btn) btn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause';

    pitchInterval = setInterval(() => {
        pitchRemaining--;
        updatePitchDisplay();
        if (pitchRemaining <= 0) {
            clearInterval(pitchInterval);
            pitchRunning = false;
            if (btn) btn.innerHTML = '<i class="fa-solid fa-rotate-left"></i> Reset';
            // Flash red
            const countdown = document.getElementById('pitch-countdown');
            if (countdown) {
                countdown.style.color = 'var(--red)';
                countdown.textContent = "TIME!";
            }
        }
    }, 1000);
}

function pausePitchTimer() {
    clearInterval(pitchInterval);
    pitchRunning = false;
    const btn = document.getElementById('pitch-btn');
    if (btn) btn.innerHTML = '<i class="fa-solid fa-play"></i> Resume';
}

function resetPitchTimer() {
    clearInterval(pitchInterval);
    pitchRunning = false;
    pitchRemaining = pitchDuration;
    updatePitchDisplay();
    const btn = document.getElementById('pitch-btn');
    if (btn) btn.innerHTML = '<i class="fa-solid fa-play"></i> Start';
}

function updatePitchDisplay() {
    const m = Math.floor(pitchRemaining / 60);
    const s = pitchRemaining % 60;
    const countdown = document.getElementById('pitch-countdown');
    if (countdown) {
        countdown.textContent = m + ':' + (s < 10 ? '0' : '') + s;
        // Color: green > 50%, orange 20-50%, red < 20%
        const pct = pitchRemaining / pitchDuration;
        if (pct > 0.5) countdown.style.color = 'var(--green)';
        else if (pct > 0.2) countdown.style.color = 'var(--orange)';
        else countdown.style.color = 'var(--red)';
    }

    // Update ring
    const ring = document.getElementById('ring-fill');
    if (ring) {
        const offset = CIRCUMFERENCE * (1 - pitchRemaining / pitchDuration);
        ring.style.strokeDashoffset = offset;
        const pct = pitchRemaining / pitchDuration;
        if (pct > 0.5) ring.style.stroke = 'var(--green)';
        else if (pct > 0.2) ring.style.stroke = 'var(--orange)';
        else ring.style.stroke = 'var(--red)';
    }
}


// ══════════════════════════════════════════════════════════
// KEYBOARD SHORTCUTS
// ══════════════════════════════════════════════════════════

document.addEventListener('keydown', (e) => {
    // Don't trigger in input fields
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

    const practiceVisible = document.getElementById('panel-practice')?.classList.contains('visible');
    const pitchVisible = document.getElementById('panel-pitch')?.classList.contains('visible');
    const teleprompterVisible = document.getElementById('panel-teleprompter')?.classList.contains('visible');

    if (practiceVisible) {
        if (e.code === 'Space') {
            e.preventDefault();
            toggleTimer();
        } else if (e.code === 'ArrowRight') {
            e.preventDefault();
            nextPracticeQuestion();
        } else if (e.code === 'KeyR') {
            e.preventDefault();
            revealAnswer();
        }
    }

    if (pitchVisible) {
        if (e.code === 'Space') {
            e.preventDefault();
            togglePitchTimer();
        }
    }

    if (teleprompterVisible) {
        if (e.code === 'Space') {
            e.preventDefault();
            toggleRehearsal();
        } else if (e.code === 'ArrowRight') {
            e.preventDefault();
            nextRehearsalSlide();
        } else if (e.code === 'ArrowLeft') {
            e.preventDefault();
            prevRehearsalSlide();
        } else if (e.code === 'KeyF') {
            e.preventDefault();
            toggleTeleprompterFullscreen();
        }
    }
});


// ══════════════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    // Initialize pitch ring
    const ring = document.getElementById('ring-fill');
    if (ring) {
        ring.style.strokeDasharray = CIRCUMFERENCE;
        ring.style.strokeDashoffset = '0';
    }

    // Load confidence data
    loadConfidence();

    // Load practice history
    updateHistoryRibbon();
});
