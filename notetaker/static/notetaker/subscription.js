// subscription.js — display plan, usage stats

Auth.requireAuth();

const token = localStorage.getItem('access_token');
const headers = { 'Authorization': `JWT ${token}`, 'Content-Type': 'application/json' };

const TIER_LABELS = { free: 'Free', basic: 'Basic', pro: 'Pro' };
const STATUS_LABELS = { active: 'Active', inactive: 'Inactive', trialing: 'Trialing', past_due: 'Past Due', canceled: 'Canceled', unpaid: 'Unpaid' };

async function loadSubscription() {
    const res = await fetch('/notetaker/subscription/me/', { headers });
    if (res.status === 401) { Auth.requireAuth(); return; }
    if (!res.ok) {
        document.getElementById('loading-msg').textContent = 'Could not load subscription.';
        return;
    }

    const sub = await res.json();

    document.getElementById('loading-msg').remove();
    document.getElementById('sub-content').style.display = 'block';

    // Plan name + status badge
    document.getElementById('plan-name').textContent = TIER_LABELS[sub.plan_tier] ?? sub.plan_tier;
    const badge = document.getElementById('plan-status');
    badge.textContent = STATUS_LABELS[sub.status] ?? sub.status;
    badge.classList.add(sub.status === 'active' || sub.status === 'trialing' ? 'badge-ok' : 'badge-muted');
    badge.classList.add('badge');

    // Audio minutes bar
    const minutesUsed = parseFloat(sub.monthly_audio_minutes_used) || 0;
    const minutesLimit = sub.audio_minutes_limit || 60;
    const minutesPct = Math.min((minutesUsed / minutesLimit) * 100, 100).toFixed(0);
    document.getElementById('minutes-bar').style.width = `${minutesPct}%`;
    document.getElementById('minutes-text').textContent = `${minutesUsed.toFixed(1)} of ${minutesLimit} minutes used`;

    // Summaries bar (no hard limit exposed — show count)
    const summariesCount = sub.summaries_generated_count || 0;
    document.getElementById('summaries-bar').style.width = `${Math.min(summariesCount * 5, 100)}%`;
    document.getElementById('summaries-text').textContent = `${summariesCount} summaries generated`;

    // Show upgrade CTA for free tier
    if (sub.plan_tier === 'free') {
        document.getElementById('upgrade-card').style.display = 'block';
    }
}

loadSubscription();
