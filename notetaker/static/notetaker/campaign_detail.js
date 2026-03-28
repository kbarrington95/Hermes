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
        <div class="campaign-card card" id="session-card-${s.id}">
            <div class="campaign-card-header">
                <a href="/notetaker/session/${s.id}/" style="flex:1; text-decoration:none; color:inherit;">
                    <h3 class="campaign-name">${s.title}</h3>
                </a>
                ${statusBadge}
                <button class="btn btn-danger" style="margin-left:12px; font-size:12px; padding:4px 10px;" onclick="deleteSession(${s.id}, '${s.title.replace(/'/g, "\\'")}')">Delete</button>
            </div>
            <p class="campaign-desc text-muted">${s.date_played}</p>
        </div>`;
    }).join('');
}

function startEdit() {
    document.getElementById('edit-name').value = document.getElementById('campaign-name').textContent;
    const desc = document.getElementById('edit-desc');
    desc.value = document.getElementById('campaign-desc').textContent;
    desc.style.height = 'auto';
    desc.style.height = (desc.scrollHeight || 60) + 'px';
    document.getElementById('campaign-view').style.display = 'none';
    document.getElementById('campaign-edit').style.display = 'block';
    document.getElementById('edit-btn').style.display = 'none';
    document.getElementById('save-btn').style.display = 'block';
    document.getElementById('cancel-btn').style.display = 'block';
    document.getElementById('edit-name').focus();
}

function cancelEdit() {
    document.getElementById('campaign-edit').style.display = 'none';
    document.getElementById('campaign-view').style.display = 'block';
    document.getElementById('edit-btn').style.display = 'block';
    document.getElementById('save-btn').style.display = 'none';
    document.getElementById('cancel-btn').style.display = 'none';
}

async function saveEdit() {
    const name = document.getElementById('edit-name').value.trim();
    if (!name) { alert('Campaign name is required.'); return; }
    const description = document.getElementById('edit-desc').value.trim();

    const res = await fetch(`/notetaker/campaigns/${campaignId}/`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({ name, description }),
    });
    if (!res.ok) { alert('Failed to save changes. Please try again.'); return; }

    const updated = await res.json();
    document.getElementById('campaign-name').textContent = updated.name;
    document.getElementById('campaign-desc').textContent = updated.description || '';
    document.title = `${updated.name} — Hermes`;
    cancelEdit();
}

async function deleteCampaign() {
    const name = document.getElementById('campaign-name').textContent;
    if (!confirm(`Delete "${name}"? This will also remove all its sessions, recordings, transcriptions, and summaries. This cannot be undone.`)) return;

    const res = await fetch(`/notetaker/campaigns/${campaignId}/`, { method: 'DELETE', headers });
    if (res.ok || res.status === 204) {
        window.location.href = '/notetaker/dashboard/';
    } else {
        alert('Failed to delete campaign. Please try again.');
    }
}

async function deleteSession(sessionId, title) {
    if (!confirm(`Delete "${title}"? This cannot be undone.`)) return;

    const res = await fetch(`/notetaker/sessions/${sessionId}/`, { method: 'DELETE', headers });
    if (res.ok || res.status === 204) {
        document.getElementById(`session-card-${sessionId}`)?.remove();
        const list = document.getElementById('sessions-list');
        if (list && list.children.length === 0) {
            list.innerHTML = `<p class="text-muted">No sessions yet. Upload a recording to get started.</p>`;
        }
    } else {
        alert('Failed to delete session. Please try again.');
    }
}

loadCampaign();
loadSessions();
