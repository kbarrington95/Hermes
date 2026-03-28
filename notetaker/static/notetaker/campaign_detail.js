// campaign_detail.js — sessions list for a campaign

Auth.requireAuth();

const token = localStorage.getItem('access_token');
const headers = { 'Authorization': `JWT ${token}`, 'Content-Type': 'application/json' };

// Get campaign ID from URL path: /notetaker/campaigns/<id>/
const campaignId = window.location.pathname.split('/').filter(Boolean).pop();

async function loadCampaign() {
    const res = await fetch(`/notetaker/campaigns/${campaignId}/`, { headers });
    if (res.status === 401) { Auth.requireAuth(); return; }
    if (!res.ok) return;

    const campaign = await res.json();
    document.getElementById('campaign-name').textContent = campaign.name;
    if (campaign.description) {
        document.getElementById('campaign-desc').textContent = campaign.description;
    }
    document.getElementById('upload-btn').href = `/notetaker/upload/?campaign=${campaignId}`;
    document.getElementById('vocab-btn').href = `/notetaker/campaign/${campaignId}/vocabulary/`;
    document.title = `${campaign.name} — Hermes`;
}

async function loadSessions() {
    const res = await fetch(`/notetaker/sessions/?campaign_id=${campaignId}`, { headers });
    if (!res.ok) return;

    const data = await res.json();
    const sessions = data.results ?? data;

    const list = document.getElementById('sessions-list');
    document.getElementById('loading-msg')?.remove();

    if (sessions.length === 0) {
        list.innerHTML = `<p class="text-muted">No sessions yet. Upload a recording to get started.</p>`;
        return;
    }

    list.innerHTML = sessions.map(s => {
        const hasRecording = !!s.recording;
        const statusBadge = hasRecording
            ? `<span class="badge badge-ok">Recording</span>`
            : `<span class="badge badge-muted">No recording</span>`;

        return `
        <a href="/notetaker/session/${s.id}/" class="campaign-card card">
            <div class="campaign-card-header">
                <h3 class="campaign-name">${s.title}</h3>
                ${statusBadge}
            </div>
            <p class="campaign-desc text-muted">${s.date_played}</p>
        </a>`;
    }).join('');
}

loadCampaign();
loadSessions();
