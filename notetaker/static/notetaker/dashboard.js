// dashboard.js — campaigns list + quota usage

Auth.requireAuth();

const token = localStorage.getItem('access_token');
const headers = { 'Authorization': `JWT ${token}`, 'Content-Type': 'application/json' };

let subscriptionId = null;

async function loadDashboard() {
    await loadQuota();   // must run first to get subscriptionId
    await loadCampaigns();
}

// ── Campaigns ────────────────────────────────────────────────

async function loadCampaigns() {
    const res = await fetch('/notetaker/campaigns/', { headers });
    if (res.status === 401) { Auth.requireAuth(); return; }

    const data = await res.json();
    const campaigns = data.results ?? data;

    const list = document.getElementById('campaigns-list');
    document.getElementById('loading-msg')?.remove();

    if (campaigns.length === 0) {
        list.innerHTML = `<p class="text-muted">No campaigns yet. Create one to get started.</p>`;
        return;
    }

    list.innerHTML = campaigns.map(c => `
        <a href="/notetaker/campaign/${c.id}/" class="campaign-card card">
            <div class="campaign-card-header">
                <h3 class="campaign-name">${c.name}</h3>
                <span class="session-count">${c.sessions_count ?? 0} session${c.sessions_count !== 1 ? 's' : ''}</span>
            </div>
            ${c.description ? `<p class="campaign-desc text-muted">${c.description}</p>` : ''}
        </a>
    `).join('');
}

// ── Quota ────────────────────────────────────────────────────

async function loadQuota() {
    const res = await fetch('/notetaker/subscription/me/', { headers });
    if (!res.ok) return;

    const sub = await res.json();
    if (!sub) return;

    subscriptionId = sub.id;

    const used = parseFloat(sub.monthly_audio_minutes_used) || 0;
    const limit = sub.audio_minutes_limit || 60;
    const pct = Math.min((used / limit) * 100, 100).toFixed(0);

    const card = document.getElementById('quota-card');
    card.style.display = 'block';
    document.getElementById('quota-bar').style.width = `${pct}%`;
    document.getElementById('quota-text').textContent =
        `${used.toFixed(1)} / ${limit} minutes used (${sub.plan_tier} plan)`;
}

// ── New campaign form ────────────────────────────────────────

document.getElementById('new-campaign-btn').addEventListener('click', () => {
    document.getElementById('new-campaign-form').style.display = 'block';
    document.getElementById('campaign-name').focus();
});

document.getElementById('cancel-campaign-btn').addEventListener('click', () => {
    document.getElementById('new-campaign-form').style.display = 'none';
    document.getElementById('campaign-name').value = '';
    document.getElementById('campaign-desc').value = '';
    document.getElementById('campaign-error').style.display = 'none';
});

document.getElementById('create-campaign-btn').addEventListener('click', async () => {
    const name = document.getElementById('campaign-name').value.trim();
    const description = document.getElementById('campaign-desc').value.trim();
    const errEl = document.getElementById('campaign-error');

    if (!name) {
        errEl.textContent = 'Campaign name is required.';
        errEl.style.display = 'block';
        return;
    }

    if (!subscriptionId) {
        errEl.textContent = 'Could not load subscription. Please refresh and try again.';
        errEl.style.display = 'block';
        return;
    }

    const btn = document.getElementById('create-campaign-btn');
    btn.disabled = true;
    btn.textContent = 'Creating…';
    errEl.style.display = 'none';

    const res = await fetch('/notetaker/campaigns/', {
        method: 'POST',
        headers,
        body: JSON.stringify({ name, description, subscription: subscriptionId })
    });

    if (!res.ok) {
        const err = await res.json();
        errEl.textContent = Object.values(err).flat().join(' ');
        errEl.style.display = 'block';
        btn.disabled = false;
        btn.textContent = 'Create';
        return;
    }

    const campaign = await res.json();
    window.location.href = `/notetaker/campaigns/${campaign.id}/`;
});

// ── Init ─────────────────────────────────────────────────────
loadDashboard();
