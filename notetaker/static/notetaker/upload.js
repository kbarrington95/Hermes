// upload.js — recording upload, transcription trigger, status polling

Auth.requireAuth();

const token = localStorage.getItem('access_token');
const authHeaders = { 'Authorization': `JWT ${token}` };
const jsonHeaders = { ...authHeaders, 'Content-Type': 'application/json' };

// Pre-select campaign from query param if coming from campaign detail
const params = new URLSearchParams(window.location.search);
const preselectedCampaign = params.get('campaign');

// ── Load campaigns into dropdown ─────────────────────────────

async function loadCampaigns() {
    const res = await fetch('/notetaker/campaigns/', { headers: jsonHeaders });
    if (!res.ok) return;

    const data = await res.json();
    const campaigns = data.results ?? data;
    const select = document.getElementById('campaign-select');

    select.innerHTML = '<option value="">Select a campaign…</option>' +
        campaigns.map(c => `<option value="${c.id}">${c.name}</option>`).join('');

    if (preselectedCampaign) select.value = preselectedCampaign;
}

// ── Step state helpers ───────────────────────────────────────

function setStep(id, state) {
    const el = document.getElementById(id);
    const icon = el.querySelector('.step-icon');
    if (state === 'done')    { el.classList.add('step-done');    icon.textContent = '✅'; }
    if (state === 'active')  { el.classList.add('step-active');  icon.textContent = '🔄'; }
    if (state === 'error')   { el.classList.add('step-error');   icon.textContent = '❌'; }
}

function showProcessing(title, sub) {
    document.getElementById('upload-section').style.display = 'none';
    document.getElementById('processing-section').style.display = 'block';
    document.getElementById('processing-title').textContent = title;
    document.getElementById('processing-sub').textContent = sub;
}

// ── Upload handler ───────────────────────────────────────────

document.getElementById('upload-btn').addEventListener('click', async () => {
    const campaignId = document.getElementById('campaign-select').value;
    const title = document.getElementById('session-title').value.trim();
    const date = document.getElementById('session-date').value;
    const fileInput = document.getElementById('audio-file');
    const errEl = document.getElementById('upload-error');

    errEl.style.display = 'none';

    if (!campaignId) {
        errEl.textContent = 'Please select a campaign.';
        errEl.style.display = 'block';
        return;
    }
    if (!fileInput.files[0]) {
        errEl.textContent = 'Please select an audio file.';
        errEl.style.display = 'block';
        return;
    }

    // Build multipart form
    const formData = new FormData();
    formData.append('audio_file', fileInput.files[0]);
    formData.append('campaign_id', campaignId);
    if (title) formData.append('title', title);
    if (date)  formData.append('date', date);

    // Show processing UI
    showProcessing('Uploading recording…', 'Please keep this page open.');
    setStep('step-upload', 'active');

    // 1. Upload recording
    let recording;
    try {
        const res = await fetch('/notetaker/recordings/', {
            method: 'POST',
            headers: authHeaders,  // no Content-Type — let browser set multipart boundary
            body: formData
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(Object.values(err).flat().join(' '));
        }
        const uploadData = await res.json();
        // UploadRecordingSerializer doesn't return session — fetch full recording to get it
        const recRes = await fetch(`/notetaker/recordings/${uploadData.id}/`, { headers: jsonHeaders });
        recording = await recRes.json();
    } catch (e) {
        setStep('step-upload', 'error');
        document.getElementById('processing-title').textContent = 'Upload failed';
        document.getElementById('processing-sub').textContent = e.message;
        return;
    }

    setStep('step-upload', 'done');
    setStep('step-transcribe', 'active');
    showProcessing('Transcribing audio…', 'This may take a few minutes.');

    // 2. Trigger transcription
    try {
        const res = await fetch(`/notetaker/recordings/${recording.id}/transcribe/`, {
            method: 'POST',
            headers: jsonHeaders
        });
        if (!res.ok) throw new Error('Failed to start transcription.');
    } catch (e) {
        setStep('step-transcribe', 'error');
        document.getElementById('processing-title').textContent = 'Transcription failed';
        document.getElementById('processing-sub').textContent = e.message;
        return;
    }

    // 3. Poll transcription status
    let transcriptionId;
    try {
        transcriptionId = await pollTranscription(recording.id);
    } catch (e) {
        setStep('step-transcribe', 'error');
        document.getElementById('processing-title').textContent = 'Transcription failed';
        document.getElementById('processing-sub').textContent = e.message;
        return;
    }

    setStep('step-transcribe', 'done');
    setStep('step-summary', 'active');
    showProcessing('Generating summary…', 'Almost there!');

    // 4. Poll for summary (auto-generated by webhook)
    try {
        await pollSummary(transcriptionId);
    } catch (e) {
        setStep('step-summary', 'error');
        document.getElementById('processing-title').textContent = 'Summary generation failed';
        document.getElementById('processing-sub').textContent = e.message;
        return;
    }

    setStep('step-summary', 'done');

    // 5. Redirect to session detail
    window.location.href = `/notetaker/session/${recording.session}/`;
});

// ── Polling helpers ──────────────────────────────────────────

function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

async function pollTranscription(recordingId) {
    for (let i = 0; i < 120; i++) {  // max 10 minutes
        await wait(5000);
        const res = await fetch(`/notetaker/transcriptions/?recording_id=${recordingId}`, { headers: jsonHeaders });
        if (!res.ok) throw new Error('Could not check transcription status.');

        const data = await res.json();
        const results = data.results ?? data;
        if (results.length === 0) continue;

        const t = results[0];
        if (t.status === 'COMPLETED') return t.id;
        if (t.status === 'FAILED') throw new Error('AssemblyAI transcription failed.');
    }
    throw new Error('Transcription timed out.');
}

async function pollSummary(transcriptionId) {
    for (let i = 0; i < 60; i++) {  // max 5 minutes
        await wait(5000);
        const res = await fetch(`/notetaker/summaries/?transcription_id=${transcriptionId}`, { headers: jsonHeaders });
        if (!res.ok) throw new Error('Could not check summary status.');

        const data = await res.json();
        const results = data.results ?? data;
        if (results.length > 0) return results[0];
    }
    throw new Error('Summary generation timed out.');
}

// ── Init ─────────────────────────────────────────────────────
loadCampaigns();
