// session_detail.js — display recording, transcription, and summary

Auth.requireAuth();

const token = localStorage.getItem('access_token');
const headers = { 'Authorization': `JWT ${token}`, 'Content-Type': 'application/json' };

// Get session ID from URL: /notetaker/sessions/<id>/
const sessionId = window.location.pathname.split('/').filter(Boolean).pop();

let summaryId = null;
let summaryRawContent = '';

async function loadSession() {
    const res = await fetch(`/notetaker/sessions/${sessionId}/`, { headers });
    if (res.status === 401) { Auth.requireAuth(); return; }
    if (!res.ok) return;

    const session = await res.json();
    document.getElementById('session-title').textContent = session.title;
    document.getElementById('session-date').textContent = session.date_played;
    document.title = `${session.title} — Hermes`;

    // Back link to campaign detail
    document.getElementById('back-link').href = `/notetaker/campaign/${session.campaign}/`;

    document.getElementById('loading-msg').remove();
    document.getElementById('delete-btn').style.display = 'block';
    document.getElementById('edit-session-btn').style.display = 'block';

    if (session.recording) {
        showRecording(session.recording);
        await loadTranscription(session.recording.id);
    } else {
        document.getElementById('loading-msg').textContent = 'No recording for this session.';
    }
}

function showRecording(recording) {
    const section = document.getElementById('recording-section');
    const meta = document.getElementById('recording-meta');
    const mins = recording.duration_minutes
        ? `${parseFloat(recording.duration_minutes).toFixed(1)} minutes`
        : 'Duration unknown';
    meta.textContent = `Uploaded ${new Date(recording.uploaded_at).toLocaleDateString()} · ${mins}`;
    section.style.display = 'block';
}

async function loadTranscription(recordingId) {
    const res = await fetch(`/notetaker/transcriptions/?recording_id=${recordingId}`, { headers });
    if (!res.ok) return;

    const data = await res.json();
    const results = data.results ?? data;
    if (results.length === 0) return;

    const t = results[0];
    const section = document.getElementById('transcription-section');
    const meta = document.getElementById('transcription-meta');

    const duration = t.processing_duration
        ? ` · Processed in ${t.processing_duration}`
        : '';
    meta.textContent = `Status: ${t.status}${duration}`;

    if (t.status === 'COMPLETED' && t.raw_text) {
        document.getElementById('transcription-text').textContent = t.raw_text;
        section.style.display = 'block';
        await loadSummary(t.id);
    } else if (t.status === 'FAILED') {
        meta.textContent = 'Transcription failed.';
        section.style.display = 'block';
    }
}

async function loadSummary(transcriptionId) {
    const res = await fetch(`/notetaker/summaries/?transcription_id=${transcriptionId}`, { headers });
    if (!res.ok) return;

    const data = await res.json();
    const results = data.results ?? data;
    if (results.length === 0) return;

    const summary = results[0];
    summaryId = summary.id;
    summaryRawContent = summary.content;

    const section = document.getElementById('summary-section');
    const meta = document.getElementById('summary-meta');
    const content = document.getElementById('summary-content');

    meta.textContent = `${summary.summary_type} · ${summary.model_used} · ${new Date(summary.created_at).toLocaleDateString()}`;
    content.innerHTML = marked.parse(summary.content);
    section.style.display = 'block';
}

// ── Session title edit ──────────────────────────────────────
function startSessionEdit() {
    document.getElementById('edit-title').value = document.getElementById('session-title').textContent;
    document.getElementById('session-view').style.display = 'none';
    document.getElementById('session-edit').style.display = 'block';
    document.getElementById('edit-session-btn').style.display = 'none';
    document.getElementById('save-session-btn').style.display = 'block';
    document.getElementById('cancel-session-btn').style.display = 'block';
    document.getElementById('edit-title').focus();
}

function cancelSessionEdit() {
    document.getElementById('session-edit').style.display = 'none';
    document.getElementById('session-view').style.display = 'block';
    document.getElementById('edit-session-btn').style.display = 'block';
    document.getElementById('save-session-btn').style.display = 'none';
    document.getElementById('cancel-session-btn').style.display = 'none';
}

async function saveSessionEdit() {
    const title = document.getElementById('edit-title').value.trim();
    if (!title) { alert('Title is required.'); return; }

    const res = await fetch(`/notetaker/sessions/${sessionId}/`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({ title }),
    });
    if (!res.ok) { alert('Failed to save. Please try again.'); return; }

    const updated = await res.json();
    document.getElementById('session-title').textContent = updated.title;
    document.title = `${updated.title} — Hermes`;
    cancelSessionEdit();
}

// ── Summary edit ────────────────────────────────────────────
function startSummaryEdit() {
    const textarea = document.getElementById('summary-textarea');
    textarea.value = summaryRawContent;
    textarea.style.display = 'block';
    // Auto-size to content height
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';

    document.getElementById('summary-content').style.display = 'none';
    document.getElementById('edit-summary-btn').style.display = 'none';
    document.getElementById('save-summary-btn').style.display = 'block';
    document.getElementById('cancel-summary-btn').style.display = 'block';
    textarea.focus();
}

function cancelSummaryEdit() {
    document.getElementById('summary-textarea').style.display = 'none';
    document.getElementById('summary-content').style.display = 'block';
    document.getElementById('edit-summary-btn').style.display = 'block';
    document.getElementById('save-summary-btn').style.display = 'none';
    document.getElementById('cancel-summary-btn').style.display = 'none';
}

async function saveSummaryEdit() {
    const content = document.getElementById('summary-textarea').value;

    const res = await fetch(`/notetaker/summaries/${summaryId}/`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({ content }),
    });
    if (!res.ok) { alert('Failed to save. Please try again.'); return; }

    const updated = await res.json();
    summaryRawContent = updated.content;
    document.getElementById('summary-content').innerHTML = marked.parse(updated.content);
    cancelSummaryEdit();
}

async function deleteSession() {
    const title = document.getElementById('session-title').textContent;
    const campaignHref = document.getElementById('back-link').href;
    if (!confirm(`Delete "${title}"? This will also remove its recording, transcription, and summary. This cannot be undone.`)) return;

    const res = await fetch(`/notetaker/sessions/${sessionId}/`, { method: 'DELETE', headers });
    if (res.ok || res.status === 204) {
        window.location.href = campaignHref;
    } else {
        alert('Failed to delete session. Please try again.');
    }
}

loadSession();
