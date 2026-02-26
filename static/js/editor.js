/* ═══════════════════════════════════════════════════════════
   Hibbs Institute — Prep Tool — Editor JS
   Handles: tab switching, dynamic form building, CRUD via API
   ═══════════════════════════════════════════════════════════ */

// SESSION, SESSION_ID, API_URL are injected by the template

// ── Tab switching ────────────────────────────────────────
function showEditorTab(tab, btn) {
    document.querySelectorAll('.editor-tab').forEach(t => t.classList.remove('active'));
    if (btn) btn.classList.add('active');
    document.querySelectorAll('.editor-panel').forEach(p => p.classList.remove('visible'));
    const panel = document.getElementById('editor-' + tab);
    if (panel) panel.classList.add('visible');
}

// ── Toast ────────────────────────────────────────────────
function showToast() {
    const toast = document.getElementById('save-toast');
    if (!toast) return;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2000);
}

// ── API helper ───────────────────────────────────────────
async function apiSave(data) {
    const resp = await fetch(API_URL, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    if (resp.ok) showToast();
    return resp;
}

// ══════════════════════════════════════════════════════════
// BASICS
// ══════════════════════════════════════════════════════════
function saveBasics() {
    apiSave({
        title:    document.getElementById('ed-title').value,
        subtitle: document.getElementById('ed-subtitle').value,
        date:     document.getElementById('ed-date').value,
        format:   document.getElementById('ed-format').value,
    });
}


// ══════════════════════════════════════════════════════════
// STATS BANNER
// ══════════════════════════════════════════════════════════
function renderStats() {
    const list = document.getElementById('stats-list');
    if (!list) return;
    list.innerHTML = '';
    (SESSION.stats_banner || []).forEach((s, i) => {
        list.innerHTML += `
        <div class="ed-item">
            <div class="ed-item-header">
                <span class="ed-item-num">Stat ${i + 1}</span>
                <button class="ed-remove" onclick="removeStat(${i})" title="Remove"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Value</label>
                    <input class="ed-field stat-val" value="${escHtml(s.value || '')}">
                </div>
                <div class="form-group">
                    <label>Label</label>
                    <input class="ed-field stat-lbl" value="${escHtml(s.label || '')}">
                </div>
            </div>
        </div>`;
    });
}
function addStat() {
    SESSION.stats_banner = SESSION.stats_banner || [];
    SESSION.stats_banner.push({ value: '', label: '' });
    renderStats();
}
function removeStat(i) {
    SESSION.stats_banner.splice(i, 1);
    renderStats();
}
function saveStats() {
    const items = document.getElementById('stats-list').querySelectorAll('.ed-item');
    SESSION.stats_banner = [];
    items.forEach(item => {
        SESSION.stats_banner.push({
            value: item.querySelector('.stat-val').value,
            label: item.querySelector('.stat-lbl').value,
        });
    });
    apiSave({ stats_banner: SESSION.stats_banner });
}


// ══════════════════════════════════════════════════════════
// TALKING POINTS
// ══════════════════════════════════════════════════════════
function renderTalkingPoints() {
    const list = document.getElementById('tp-list');
    if (!list) return;
    list.innerHTML = '';
    (SESSION.talking_points || []).forEach((tp, i) => {
        list.innerHTML += `
        <div class="ed-item">
            <div class="ed-item-header">
                <span class="ed-item-num">Point ${i + 1}</span>
                <button class="ed-remove" onclick="removeTP(${i})" title="Remove"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Topic ID</label>
                    <input class="ed-field tp-id" value="${escHtml(tp.id || '')}">
                </div>
                <div class="form-group">
                    <label>Label</label>
                    <input class="ed-field tp-label" value="${escHtml(tp.label || '')}">
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Number/Tag</label>
                    <input class="ed-field tp-number" value="${escHtml(tp.number || '')}">
                </div>
                <div class="form-group">
                    <label>Timing</label>
                    <input class="ed-field tp-timing" value="${escHtml(tp.timing || '')}">
                </div>
            </div>
            <div class="form-group">
                <label>Question / Prompt</label>
                <input class="ed-field tp-question" value="${escHtml(tp.question || '')}">
            </div>
            <div class="form-group">
                <label>Speaker Notes (HTML)</label>
                <textarea class="ed-textarea tp-note" rows="6">${escHtml(tp.note || '')}</textarea>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Do Say (tip)</label>
                    <input class="ed-field tp-tipdo" value="${escHtml(tp.tip_do || '')}">
                </div>
                <div class="form-group">
                    <label>Avoid (tip)</label>
                    <input class="ed-field tp-tipdont" value="${escHtml(tp.tip_dont || '')}">
                </div>
            </div>
            <div class="form-group">
                <label>Source</label>
                <input class="ed-field tp-source" value="${escHtml(tp.source || '')}">
            </div>
        </div>`;
    });
}
function addTalkingPoint() {
    SESSION.talking_points = SESSION.talking_points || [];
    SESSION.talking_points.push({
        id: '', label: '', number: '', timing: '',
        question: '', note: '', tip_do: '', tip_dont: '', source: ''
    });
    renderTalkingPoints();
}
function removeTP(i) {
    SESSION.talking_points.splice(i, 1);
    renderTalkingPoints();
}
function saveTalkingPoints() {
    const items = document.getElementById('tp-list').querySelectorAll('.ed-item');
    SESSION.talking_points = [];
    items.forEach(item => {
        SESSION.talking_points.push({
            id:       item.querySelector('.tp-id').value,
            label:    item.querySelector('.tp-label').value,
            number:   item.querySelector('.tp-number').value,
            timing:   item.querySelector('.tp-timing').value,
            question: item.querySelector('.tp-question').value,
            note:     item.querySelector('.tp-note').value,
            tip_do:   item.querySelector('.tp-tipdo').value,
            tip_dont: item.querySelector('.tp-tipdont').value,
            source:   item.querySelector('.tp-source').value,
        });
    });
    apiSave({ talking_points: SESSION.talking_points });
}


// ══════════════════════════════════════════════════════════
// PRACTICE QUESTIONS
// ══════════════════════════════════════════════════════════
function renderPracticeQuestions() {
    const list = document.getElementById('pq-list');
    if (!list) return;
    list.innerHTML = '';
    (SESSION.practice_questions || []).forEach((pq, i) => {
        const pointsText = (pq.points || []).join('\n');
        list.innerHTML += `
        <div class="ed-item">
            <div class="ed-item-header">
                <span class="ed-item-num">Question ${i + 1}</span>
                <button class="ed-remove" onclick="removePQ(${i})" title="Remove"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="form-group">
                <label>Question</label>
                <input class="ed-field pq-q" value="${escHtml(pq.q || '')}">
            </div>
            <div class="form-group">
                <label>Key Points (one per line)</label>
                <textarea class="ed-textarea pq-pts" rows="4">${escHtml(pointsText)}</textarea>
            </div>
        </div>`;
    });
}
function addPracticeQuestion() {
    SESSION.practice_questions = SESSION.practice_questions || [];
    SESSION.practice_questions.push({ q: '', points: [] });
    renderPracticeQuestions();
}
function removePQ(i) {
    SESSION.practice_questions.splice(i, 1);
    renderPracticeQuestions();
}
function savePracticeQuestions() {
    const items = document.getElementById('pq-list').querySelectorAll('.ed-item');
    SESSION.practice_questions = [];
    items.forEach(item => {
        SESSION.practice_questions.push({
            q: item.querySelector('.pq-q').value,
            points: item.querySelector('.pq-pts').value.split('\n').filter(l => l.trim()),
        });
    });
    apiSave({ practice_questions: SESSION.practice_questions });
}


// ══════════════════════════════════════════════════════════
// CHEAT SHEET
// ══════════════════════════════════════════════════════════
function renderCheatsheet() {
    const list = document.getElementById('cs-list');
    if (!list) return;
    list.innerHTML = '';
    (SESSION.cheatsheet_cards || []).forEach((card, i) => {
        const itemsText = (card.items || []).map(it => {
            if (it[1]) return it[0] + ' | ' + it[1];
            return it[0];
        }).join('\n');
        list.innerHTML += `
        <div class="ed-item">
            <div class="ed-item-header">
                <span class="ed-item-num">Card ${i + 1}</span>
                <button class="ed-remove" onclick="removeCS(${i})" title="Remove"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Icon (emoji)</label>
                    <input class="ed-field cs-icon" value="${escHtml(card.icon || '')}" style="max-width:80px">
                </div>
                <div class="form-group">
                    <label>Title</label>
                    <input class="ed-field cs-title" value="${escHtml(card.title || '')}">
                </div>
            </div>
            <div class="form-group">
                <label>Items (one per line, use | to separate label and value)</label>
                <textarea class="ed-textarea cs-items" rows="5">${escHtml(itemsText)}</textarea>
            </div>
        </div>`;
    });
}
function addCheatsheetCard() {
    SESSION.cheatsheet_cards = SESSION.cheatsheet_cards || [];
    SESSION.cheatsheet_cards.push({ icon: '📊', title: '', items: [] });
    renderCheatsheet();
}
function removeCS(i) {
    SESSION.cheatsheet_cards.splice(i, 1);
    renderCheatsheet();
}
function saveCheatsheet() {
    const items = document.getElementById('cs-list').querySelectorAll('.ed-item');
    SESSION.cheatsheet_cards = [];
    items.forEach(item => {
        const lines = item.querySelector('.cs-items').value.split('\n').filter(l => l.trim());
        SESSION.cheatsheet_cards.push({
            icon: item.querySelector('.cs-icon').value,
            title: item.querySelector('.cs-title').value,
            items: lines.map(l => {
                const parts = l.split('|').map(s => s.trim());
                return [parts[0] || '', parts[1] || ''];
            })
        });
    });
    apiSave({ cheatsheet_cards: SESSION.cheatsheet_cards });
}


// ══════════════════════════════════════════════════════════
// TIPS
// ══════════════════════════════════════════════════════════
function renderTips() {
    const list = document.getElementById('tips-list');
    if (!list) return;
    list.innerHTML = '';
    (SESSION.tips || []).forEach((tip, i) => {
        list.innerHTML += `
        <div class="ed-item" style="padding: 0.5rem 1rem; display: flex; align-items: center; gap: 0.5rem;">
            <input class="ed-field tip-text" value="${escHtml(tip)}" style="flex:1">
            <button class="ed-remove" onclick="removeTip(${i})" title="Remove"><i class="fa-solid fa-xmark"></i></button>
        </div>`;
    });
}
function addTip() {
    SESSION.tips = SESSION.tips || [];
    SESSION.tips.push('');
    renderTips();
}
function removeTip(i) {
    SESSION.tips.splice(i, 1);
    renderTips();
}
function saveTips() {
    const inputs = document.getElementById('tips-list').querySelectorAll('.tip-text');
    SESSION.tips = [];
    inputs.forEach(el => {
        if (el.value.trim()) SESSION.tips.push(el.value.trim());
    });
    apiSave({ tips: SESSION.tips });
}


// ══════════════════════════════════════════════════════════
// PITCH DATA (pitch type only)
// ══════════════════════════════════════════════════════════
function renderKeyMessages() {
    const list = document.getElementById('km-list');
    if (!list) return;
    list.innerHTML = '';
    (SESSION.key_messages || []).forEach((msg, i) => {
        list.innerHTML += `
        <div class="ed-item" style="padding: 0.5rem 1rem; display: flex; align-items: center; gap: 0.5rem;">
            <input class="ed-field km-text" value="${escHtml(msg)}" style="flex:1">
            <button class="ed-remove" onclick="removeKM(${i})" title="Remove"><i class="fa-solid fa-xmark"></i></button>
        </div>`;
    });
}
function addKeyMessage() {
    SESSION.key_messages = SESSION.key_messages || [];
    SESSION.key_messages.push('');
    renderKeyMessages();
}
function removeKM(i) {
    SESSION.key_messages.splice(i, 1);
    renderKeyMessages();
}

function renderObjections() {
    const list = document.getElementById('obj-list');
    if (!list) return;
    list.innerHTML = '';
    (SESSION.objections || []).forEach((obj, i) => {
        list.innerHTML += `
        <div class="ed-item">
            <div class="ed-item-header">
                <span class="ed-item-num">Objection ${i + 1}</span>
                <button class="ed-remove" onclick="removeObj(${i})" title="Remove"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="form-group">
                <label>Question / Objection</label>
                <input class="ed-field obj-q" value="${escHtml(obj.objection || '')}">
            </div>
            <div class="form-group">
                <label>Your Response</label>
                <textarea class="ed-textarea obj-a" rows="3">${escHtml(obj.response || '')}</textarea>
            </div>
        </div>`;
    });
}
function addObjection() {
    SESSION.objections = SESSION.objections || [];
    SESSION.objections.push({ objection: '', response: '' });
    renderObjections();
}
function removeObj(i) {
    SESSION.objections.splice(i, 1);
    renderObjections();
}

function savePitchData() {
    const data = {};
    // Pitch variants
    const p30 = document.getElementById('pitch-30');
    const p60 = document.getElementById('pitch-60');
    const p120 = document.getElementById('pitch-120');
    if (p30 || p60 || p120) {
        data.pitch_variants = {
            '30sec': p30 ? p30.value : '',
            '60sec': p60 ? p60.value : '',
            '2min':  p120 ? p120.value : '',
        };
    }
    // Key messages
    const kmInputs = document.getElementById('km-list')?.querySelectorAll('.km-text') || [];
    data.key_messages = [];
    kmInputs.forEach(el => {
        if (el.value.trim()) data.key_messages.push(el.value.trim());
    });
    // Objections
    const objItems = document.getElementById('obj-list')?.querySelectorAll('.ed-item') || [];
    data.objections = [];
    objItems.forEach(item => {
        data.objections.push({
            objection: item.querySelector('.obj-q').value,
            response:  item.querySelector('.obj-a').value,
        });
    });
    apiSave(data);
}


// ══════════════════════════════════════════════════════════
// UTILITY
// ══════════════════════════════════════════════════════════
function escHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}


// ══════════════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    renderStats();
    renderTalkingPoints();
    renderPracticeQuestions();
    renderCheatsheet();
    renderTips();
    if (SESSION.type === 'pitch') {
        renderKeyMessages();
        renderObjections();
    }
});
