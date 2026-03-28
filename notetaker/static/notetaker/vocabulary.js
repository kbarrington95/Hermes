// vocabulary.js — manage custom D&D vocabulary per campaign

Auth.requireAuth();

const token = localStorage.getItem('access_token');
const headers = { 'Authorization': `JWT ${token}`, 'Content-Type': 'application/json' };

// Get campaign ID from URL: /notetaker/campaign/<id>/vocabulary/
const campaignId = window.location.pathname.split('/').filter(Boolean)[2];

async function loadCampaign() {
    const res = await fetch(`/notetaker/campaigns/${campaignId}/`, { headers });
    if (!res.ok) return;
    const campaign = await res.json();
    document.getElementById('campaign-name').textContent = `${campaign.name} — Vocabulary`;
    document.getElementById('back-link').href = `/notetaker/campaign/${campaignId}/`;
    document.title = `${campaign.name} Vocabulary — Hermes`;
}

async function loadVocabulary() {
    const res = await fetch(`/notetaker/vocabulary/?campaign_id=${campaignId}`, { headers });
    if (!res.ok) return;

    const data = await res.json();
    const terms = data.results ?? data;
    const list = document.getElementById('vocab-list');
    document.getElementById('loading-msg')?.remove();

    if (terms.length === 0) {
        list.innerHTML = `<p class="text-muted">No terms yet. Add D&amp;D-specific words to improve transcription accuracy.</p>`;
        return;
    }

    renderTerms(terms);
}

function renderTerms(terms) {
    const list = document.getElementById('vocab-list');
    list.innerHTML = `
        <div class="card">
            <table class="vocab-table">
                <thead>
                    <tr>
                        <th>Term</th>
                        <th>Note</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    ${terms.map(t => `
                    <tr data-id="${t.id}">
                        <td class="vocab-term">${t.term}</td>
                        <td class="text-muted">${t.note || '—'}</td>
                        <td><button class="btn btn-danger btn-sm delete-btn" data-id="${t.id}">Delete</button></td>
                    </tr>`).join('')}
                </tbody>
            </table>
        </div>`;

    list.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', () => deleteTerm(btn.dataset.id));
    });
}

async function deleteTerm(id) {
    const res = await fetch(`/notetaker/vocabulary/${id}/`, { method: 'DELETE', headers });
    if (res.ok) {
        document.querySelector(`tr[data-id="${id}"]`).remove();
    }
}

document.getElementById('add-term-btn').addEventListener('click', async () => {
    const term = document.getElementById('term-input').value.trim();
    const note = document.getElementById('note-input').value.trim();
    const errEl = document.getElementById('vocab-error');

    errEl.style.display = 'none';

    if (!term) {
        errEl.textContent = 'Term is required.';
        errEl.style.display = 'block';
        return;
    }

    const btn = document.getElementById('add-term-btn');
    btn.disabled = true;

    const res = await fetch('/notetaker/vocabulary/', {
        method: 'POST',
        headers,
        body: JSON.stringify({ term, note, campaign: campaignId })
    });

    btn.disabled = false;

    if (!res.ok) {
        const err = await res.json();
        errEl.textContent = Object.values(err).flat().join(' ');
        errEl.style.display = 'block';
        return;
    }

    document.getElementById('term-input').value = '';
    document.getElementById('note-input').value = '';

    // Reload the full list to stay in sync
    const data = await fetch(`/notetaker/vocabulary/?campaign_id=${campaignId}`, { headers }).then(r => r.json());
    const terms = data.results ?? data;
    renderTerms(terms);
});

loadCampaign();
loadVocabulary();
