// session_detail.js — display recording, transcription, and summary

Auth.requireAuth();

const token = localStorage.getItem('access_token');
const headers = { 'Authorization': `JWT ${token}`, 'Content-Type': 'application/json' };

// Get session ID from URL: /notetaker/sessions/<id>/
const sessionId = window.location.pathname.split('/').filter(Boolean).pop();

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
    const section = document.getElementById('summary-section');
    const meta = document.getElementById('summary-meta');
    const content = document.getElementById('summary-content');

    meta.textContent = `${summary.summary_type} · ${summary.model_used} · ${new Date(summary.created_at).toLocaleDateString()}`;
    content.textContent = summary.content;  // plain text for now; Phase 5 adds markdown rendering
    section.style.display = 'block';
}

loadSession();
