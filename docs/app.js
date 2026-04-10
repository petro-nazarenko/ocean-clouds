/**
 * Ocean Clouds — Landing page JS
 * Handles search form (redirects to GitHub Issues search or shows a note),
 * alert subscription via Formspree, and vacancy card rendering.
 */

// ---------------------------------------------------------------------------
// Search form
// ---------------------------------------------------------------------------
function handleSearch(event) {
  event.preventDefault();
  const form = event.target;
  const rank   = form.querySelector('#rank').value;
  const vessel = form.querySelector('#vessel').value;
  const region = form.querySelector('#region').value;
  const email  = form.querySelector('#email').value;

  // Build query string for display
  const parts = [];
  if (rank)   parts.push(rank);
  if (vessel) parts.push(vessel);
  if (region) parts.push(region);
  const query = parts.join(' · ') || 'All vacancies';

  // If email provided, subscribe first
  if (email) {
    subscribeEmail(email, rank);
  }

  // Show a "how to get results" notice since this is a static page
  showSearchGuide(query, rank, vessel, region);
}

function showSearchGuide(query, rank, vessel, region) {
  const resultsSection = document.getElementById('results');
  const resultsList    = document.getElementById('results-list');
  const countBadge     = document.getElementById('results-count');
  const metaEl         = document.getElementById('results-meta');

  // Build CLI command
  const rankArg   = rank   ? `--rank "${rank}" `   : '';
  const vesselArg = vessel ? `--vessel "${vessel}" ` : '';
  const regionArg = region ? `--region "${region}" ` : '';
  const cliCmd = `/ocean-clouds:search ${rankArg}${vesselArg}${regionArg}`.trim();

  resultsList.innerHTML = `
    <div class="search-guide-card">
      <div class="guide-icon">🔍</div>
      <div class="guide-body">
        <h3>Searching for: <em>${escapeHtml(query)}</em></h3>
        <p>
          Ocean Clouds is a backend scraper — results are fetched fresh each time.
          To run a live search, use one of the options below:
        </p>
        <div class="guide-options">
          <div class="guide-option">
            <span class="guide-num">1</span>
            <div>
              <strong>Claude Code plugin (recommended)</strong>
              <pre><code>${escapeHtml(cliCmd)}</code></pre>
            </div>
          </div>
          <div class="guide-option">
            <span class="guide-num">2</span>
            <div>
              <strong>Python CLI</strong>
              <pre><code>python -m scraper.cli search ${rankArg}${vesselArg}${regionArg}</code></pre>
            </div>
          </div>
          <div class="guide-option">
            <span class="guide-num">3</span>
            <div>
              <strong>Get notified by email</strong>
              <p>Fill in the alert form below and we'll send matching jobs to your inbox.</p>
            </div>
          </div>
        </div>
        <a class="btn-gh" href="https://github.com/petro-nazarenko/ocean-clouds#readme" target="_blank" rel="noopener">
          Setup guide →
        </a>
      </div>
    </div>
  `;

  countBadge.textContent = '';
  metaEl.textContent = '';
  resultsSection.classList.remove('hidden');
  resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ---------------------------------------------------------------------------
// Alert / email subscription (Formspree)
// ---------------------------------------------------------------------------
function handleAlertSubmit(event) {
  event.preventDefault();
  const form = event.target;

  // Check Formspree ID is configured
  if (form.action.includes('YOUR_FORM_ID')) {
    showAlertMessage('To enable email alerts, replace YOUR_FORM_ID in index.html with your Formspree form ID. Get one free at formspree.io', 'warn');
    return;
  }

  const data = new FormData(form);
  fetch(form.action, {
    method: 'POST',
    body: data,
    headers: { 'Accept': 'application/json' },
  })
    .then(res => {
      if (res.ok) {
        form.reset();
        document.getElementById('alert-success').classList.remove('hidden');
        form.classList.add('hidden');
      } else {
        showAlertMessage('Submission failed. Please try again or open a GitHub issue.', 'error');
      }
    })
    .catch(() => showAlertMessage('Network error. Check your connection.', 'error'));
}

function subscribeEmail(email, rank) {
  // Silently attempt subscription via Formspree if configured
  const alertForm = document.querySelector('.alert-form');
  if (!alertForm || alertForm.action.includes('YOUR_FORM_ID')) return;
  const data = new FormData();
  data.append('email', email);
  data.append('rank', rank || 'Any');
  data.append('_subject', 'Ocean Clouds — Quick Alert Signup');
  fetch(alertForm.action, { method: 'POST', body: data, headers: { Accept: 'application/json' } })
    .catch(() => {}); // silent fail for background subscription
}

function showAlertMessage(msg, type) {
  const el = document.getElementById('alert-success');
  el.textContent = msg;
  el.style.background = type === 'warn' ? 'rgba(251,191,36,0.1)' : 'rgba(239,68,68,0.1)';
  el.style.borderColor = type === 'warn' ? 'rgba(251,191,36,0.3)' : 'rgba(239,68,68,0.3)';
  el.style.color = type === 'warn' ? '#fbbf24' : '#f87171';
  el.classList.remove('hidden');
}

// ---------------------------------------------------------------------------
// Vacancy card renderer (for future API integration)
// ---------------------------------------------------------------------------
function renderVacancy(v) {
  const urgentTag = v.is_urgent ? '<span class="tag-urgent">Urgent</span>' : '';
  return `
    <div class="vacancy-card ${v.is_urgent ? 'urgent' : ''}">
      <div>
        <div class="vacancy-title">${escapeHtml(v.title)} ${urgentTag}</div>
        <div class="vacancy-meta">
          <span>${escapeHtml(v.rank)}</span>
          <span>${escapeHtml(v.vessel_type)}</span>
          <span>${escapeHtml(v.company)}</span>
          <span>${escapeHtml(v.salary)}</span>
          <span>${escapeHtml(v.duration)}</span>
          <span>${escapeHtml(v.region)}</span>
        </div>
      </div>
      <div class="vacancy-actions">
        <a href="${escapeHtml(v.url)}" target="_blank" rel="noopener" class="btn-view">View →</a>
        <div class="source-tag">${escapeHtml(v.source)}</div>
      </div>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Inline guide card styles (injected)
// ---------------------------------------------------------------------------
const guideStyles = `
  .search-guide-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 32px;
    display: flex;
    gap: 20px;
  }
  .guide-icon { font-size: 2rem; flex-shrink: 0; margin-top: 4px; }
  .guide-body h3 { font-size: 1.1rem; margin-bottom: 10px; }
  .guide-body h3 em { color: var(--accent); font-style: normal; }
  .guide-body > p { color: var(--text-muted); margin-bottom: 24px; font-size: 0.9rem; }
  .guide-options { display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px; }
  .guide-option { display: flex; gap: 14px; align-items: flex-start; }
  .guide-num {
    background: var(--ocean-blue);
    border-radius: 50%;
    color: white;
    font-weight: 700;
    font-size: 0.8rem;
    min-width: 28px;
    height: 28px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    margin-top: 2px;
  }
  .guide-option strong { display: block; font-size: 0.9rem; margin-bottom: 6px; }
  .guide-option p { font-size: 0.85rem; color: var(--text-muted); }
  .btn-gh {
    display: inline-block;
    background: var(--ocean-blue);
    border-radius: var(--radius-sm);
    color: white;
    font-weight: 600;
    font-size: 0.9rem;
    padding: 9px 20px;
    text-decoration: none;
    transition: background 0.2s;
  }
  .btn-gh:hover { background: var(--ocean-light); }
`;

const styleTag = document.createElement('style');
styleTag.textContent = guideStyles;
document.head.appendChild(styleTag);

// ---------------------------------------------------------------------------
// Utils
// ---------------------------------------------------------------------------
function escapeHtml(str) {
  if (!str) return '—';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
