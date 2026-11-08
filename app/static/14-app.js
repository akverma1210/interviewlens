const root = document.getElementById('app');
const pageLabel = document.getElementById('page-label');
const engineStatus = document.getElementById('engine-status');
const state = { dashboard: null, session: null };

const icons = {
  arrow: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14m-5-5 5 5-5 5"/></svg>',
  plus: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>',
  sessions: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h10v4H7zM5 5H3v16h14v-2M7 11h10M7 15h7M7 7h14v14H7z"/></svg>',
  answers: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m4 13 4 4L20 5M4 5h9M4 9h6M12 13h8v8H4v-4"/></svg>',
  score: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a9 9 0 1 0 9 9M12 7v5l3 2M16 3h5v5"/></svg>',
  bulb: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 18h6M10 21h4M8.5 15.5A7 7 0 1 1 15.5 15.5c-.7.6-.5 2.5-.5 2.5H9s.2-1.9-.5-2.5Z"/></svg>',
  empty: '<svg viewBox="0 0 64 64" aria-hidden="true"><path d="M15 12h29a5 5 0 0 1 5 5v35H20a5 5 0 0 1-5-5V12Z"/><path d="M20 52V17a5 5 0 0 1 5-5h24M26 27h13M26 34h13M26 41h8"/><path d="m43 43 9 9m-9 0 9-9"/></svg>'
};

function escapeHtml(value = '') {
  return String(value).replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
}
function titleCase(value) { return value ? value.charAt(0).toUpperCase() + value.slice(1).replaceAll('_', ' ') : ''; }
function formatDate(value) {
  const normalized = typeof value === 'string' && !value.endsWith('Z') && !/[+-]\d\d:\d\d$/.test(value) ? `${value}Z` : value;
  const date = new Date(normalized);
  return new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }).format(date);
}
function setPage(label, route) {
  pageLabel.textContent = label;
  document.querySelectorAll('.nav-item').forEach(button => button.classList.toggle('active', button.dataset.route === route));
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
function toast(message) {
  const element = document.getElementById('toast');
  element.textContent = message;
  element.classList.add('visible');
  setTimeout(() => element.classList.remove('visible'), 4000);
}
async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(body.detail) ? body.detail[0]?.msg : body.detail;
    throw new Error(detail || 'Something went wrong. Please try again.');
  }
  return body;
}
function ring(score, size = 138) {
  const value = score || 0;
  const radius = 53;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - value / 100);
  return `<div class="score-ring" style="width:${size}px;height:${size}px">
    <svg width="${size}" height="${size}" viewBox="0 0 120 120" aria-hidden="true">
      <circle class="ring-track" cx="60" cy="60" r="${radius}"/>
      <circle class="ring-value" cx="60" cy="60" r="${radius}" stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"/>
    </svg>
    <div class="score-ring-label"><strong>${score === null ? '–' : value}</strong><span>${score === null ? 'NO SCORE YET' : 'OUT OF 100'}</span></div>
  </div>`;
}
function skillRows(scores) {
  const labels = { relevance: 'Relevance', structure: 'Structure', communication: 'Communication', technical_depth: 'Technical depth' };
  return `<div class="skill-list">${Object.entries(labels).map(([key, label]) => `
    <div class="skill-row"><div class="skill-row-top"><span>${label}</span><strong>${scores[key] || 0}</strong></div>
    <div class="skill-bar"><span style="width:${scores[key] || 0}%"></span></div></div>`).join('')}</div>`;
}
function statCard(label, value, suffix, foot, icon) {
  return `<article class="stat-card"><div class="stat-top"><span class="stat-label">${label}</span><span class="stat-icon">${icon}</span></div>
    <div class="stat-value">${value}${suffix ? `<small>${suffix}</small>` : ''}</div><div class="stat-foot">${foot}</div></article>`;
}

async function showHome() {
  setPage('Overview', 'home');
  root.innerHTML = '<div class="loading-screen"><div><span class="spinner"></span>Loading your workspace</div></div>';
  try {
    state.dashboard = await api('/api/dashboard');
    const data = state.dashboard;
    root.innerHTML = `
      <section class="page-heading">
        <div><div class="eyebrow">YOUR INTERVIEW WORKSPACE</div><h1>Practice with purpose.</h1><p>Turn every answer into clear, useful progress.</p></div>
        <button class="primary-button" data-route="new">${icons.plus} New practice</button>
      </section>
      <section class="stats-grid">
        ${statCard('Practice sessions', data.session_count, '', data.session_count ? 'Sessions created in this workspace' : 'Your first session is one click away', icons.sessions)}
        ${statCard('Answers reviewed', data.answer_count, '', data.answer_count ? 'Each review is saved to your progress' : 'Submit an answer to get detailed feedback', icons.answers)}
        ${statCard('Average score', data.average_score ?? '–', data.average_score !== null ? '<small> / 100</small>' : '', data.average_score !== null ? 'Across all reviewed answers' : 'Your scores will appear here', icons.score)}
      </section>
      <section class="dashboard-grid">
        <article class="card">
          <div class="card-header"><h2>Recent practice</h2><span>${data.session_count} total</span></div>
          ${data.recent_sessions.length ? `<div class="session-list">${data.recent_sessions.map(sessionRow).join('')}</div>` : emptyState()}
        </article>
        <article class="card">
          <div class="card-header"><h2>Skill snapshot</h2><span>ALL TIME</span></div>
          <div class="progress-card-body">
            <div class="score-ring-wrap">${ring(data.average_score)}</div>
            ${skillRows(data.skill_averages)}
            <div class="progress-note">Scores are coaching signals, not a hiring prediction. Use them to choose what to practice next.</div>
          </div>
        </article>
      </section>`;
  } catch (error) { toast(error.message); root.innerHTML = emptyState(); }
}
function emptyState() {
  return `<div class="empty-state"><div class="empty-illustration">${icons.empty}</div><h3>Your progress starts here</h3>
    <p>Choose a role, answer a few tailored questions, and get specific feedback on what to improve.</p>
    <button class="secondary-button" data-route="new">Create your first practice ${icons.arrow}</button></div>`;
}
function sessionRow(session) {
  const progress = session.question_count ? session.answered_count / session.question_count * 100 : 0;
  return `<button class="session-row" data-session-id="${session.id}">
    <div><div class="session-role">${escapeHtml(session.role)}</div><div class="session-meta">${escapeHtml(session.level)} · ${formatDate(session.created_at)}</div></div>
    <div><div class="session-progress"><span style="width:${progress}%"></span></div><div class="session-progress-label">${session.answered_count}/${session.question_count} answered</div></div>
    <div class="session-score">${session.average_score ?? '–'}<small>AVG SCORE</small></div><span class="chevron">›</span>
  </button>`;
}

function showSetup() {
  setPage('New practice', 'new');
  root.innerHTML = `<div class="setup-container">
    <section class="page-heading"><div><div class="eyebrow">A FOCUSED PRACTICE RUN</div><h1>What are you preparing for?</h1><p>Add a little context. We’ll build a balanced set of questions for you.</p></div></section>
    <div class="setup-grid">
      <form class="card setup-card" id="setup-form">
        <div class="form-row">
          <div class="field"><label for="role">Target role</label><input id="role" name="role" placeholder="e.g. Backend Developer" minlength="2" maxlength="160" required autofocus></div>
          <div class="field"><label for="level">Experience level</label><select id="level" name="level"><option>Student</option><option selected>Entry level</option><option>Mid level</option><option>Senior</option></select></div>
        </div>
        <div class="field"><span class="field-label">Interview style</span><div class="type-options">
          <div class="type-option"><input type="radio" name="interview_type" value="mixed" id="type-mixed" checked><label for="type-mixed">Mixed</label></div>
          <div class="type-option"><input type="radio" name="interview_type" value="technical" id="type-technical"><label for="type-technical">Technical</label></div>
          <div class="type-option"><input type="radio" name="interview_type" value="behavioral" id="type-behavioral"><label for="type-behavioral">Behavioral</label></div>
        </div></div>
        <div class="form-row">
          <div class="field"><label for="question_count">Number of questions</label><select id="question_count" name="question_count"><option value="3">3 questions · quick run</option><option value="5" selected>5 questions · balanced</option><option value="6">6 questions · deep dive</option><option value="8">8 questions · full practice</option></select></div>
        </div>
        <div class="field"><label for="job_description">Job description <span style="color:#9aa49e;font-weight:400">(optional)</span></label><textarea id="job_description" name="job_description" maxlength="5000" placeholder="Paste a few lines from the role. Key technologies will be used to make the first question more relevant."></textarea><div class="field-hint">Up to 5,000 characters. No job description is needed to begin.</div></div>
        <div class="setup-footer"><small>Your answers are saved as you go, so you can return to an unfinished session.</small><button class="primary-button" type="submit">Build my practice ${icons.arrow}</button></div>
      </form>
      <aside class="card guide-card"><div class="eyebrow">GET MORE FROM EACH ANSWER</div><h2>Specific beats perfect.</h2><p>A useful interview answer shows how you think, not just what you know.</p>
        <div class="guide-step"><span class="guide-number">01</span><div><strong>Set the scene briefly</strong><p>Give just enough context to understand the challenge.</p></div></div>
        <div class="guide-step"><span class="guide-number">02</span><div><strong>Own your decisions</strong><p>Explain what you did, why you chose it, and which trade-offs you considered.</p></div></div>
        <div class="guide-step"><span class="guide-number">03</span><div><strong>Land on evidence</strong><p>Finish with a result, a measurement, or a lesson you carried forward.</p></div></div>
      </aside>
    </div></div>`;
  document.getElementById('setup-form').addEventListener('submit', createSession);
}
async function createSession(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  button.innerHTML = '<span class="spinner"></span> Building questions';
  const formData = new FormData(form);
  const payload = {
    role: formData.get('role'), level: formData.get('level'), interview_type: formData.get('interview_type'),
    job_description: formData.get('job_description'), question_count: Number(formData.get('question_count'))
  };
  try {
    state.session = await api('/api/sessions', { method: 'POST', body: JSON.stringify(payload) });
    showPractice(0);
  } catch (error) {
    toast(error.message); button.disabled = false; button.innerHTML = `Build my practice ${icons.arrow}`;
  }
}
async function openSession(id) {
  root.innerHTML = '<div class="loading-screen"><div><span class="spinner"></span>Opening practice</div></div>';
  try {
    state.session = await api(`/api/sessions/${id}`);
    const firstUnanswered = state.session.questions.findIndex(question => !question.answer);
    if (firstUnanswered === -1) showSummary(); else showPractice(firstUnanswered);
  } catch (error) { toast(error.message); showHome(); }
}
function showPractice(index) {
  const session = state.session;
  const question = session.questions[index];
  setPage(session.role, 'new');
  root.innerHTML = `<section class="practice-top"><div class="practice-topline"><button class="back-button" data-route="home">← Back to overview</button><span class="practice-count">QUESTION ${index + 1} OF ${session.questions.length} · ${escapeHtml(session.role)}</span></div><div class="practice-progress"><span style="width:${(index + 1) / session.questions.length * 100}%"></span></div></section>
    <div class="practice-grid">
      <article class="card question-card"><span class="question-badge">${escapeHtml(question.category)} question</span><h2>${escapeHtml(question.text)}</h2><div class="focus-label">SIGNALS TO COVER</div><div class="focus-tags">${question.focus.slice(0,6).map(item => `<span>${escapeHtml(item)}</span>`).join('')}</div></article>
      <form class="card answer-card" id="answer-form"><div class="answer-card-header"><h3>Your answer</h3><span class="word-count" id="word-count">0 words</span></div>
        <textarea class="answer-input" id="answer-input" minlength="20" maxlength="15000" required placeholder="Start with the situation or your initial approach. Then explain the steps you would take, the decisions behind them, and how you would measure the result..."></textarea>
        <div class="answer-tip">${icons.bulb}<span>Aim for 100–250 words. Write as if you were speaking in the interview: clear, specific, and in your own voice.</span></div>
        <div class="answer-footer"><small>Minimum 20 characters · saved after review</small><button class="primary-button" type="submit">Review my answer ${icons.arrow}</button></div>
      </form>
    </div>`;
  const input = document.getElementById('answer-input');
  input.addEventListener('input', () => {
    const count = input.value.trim() ? input.value.trim().split(/\s+/).length : 0;
    document.getElementById('word-count').textContent = `${count} word${count === 1 ? '' : 's'}`;
  });
  input.focus();
  document.getElementById('answer-form').addEventListener('submit', event => submitAnswer(event, question));
}
async function submitAnswer(event, question) {
  event.preventDefault();
  const input = document.getElementById('answer-input');
  const button = event.currentTarget.querySelector('button[type="submit"]');
  if (input.value.trim().length < 20) { toast('Write at least 20 characters so there is enough to review.'); input.focus(); return; }
  button.disabled = true;
  button.innerHTML = '<span class="spinner"></span> Reviewing your answer';
  try {
    const answer = await api(`/api/questions/${question.id}/answer`, { method: 'POST', body: JSON.stringify({ response_text: input.value.trim() }) });
    question.answer = answer;
    const unanswered = state.session.questions.filter(item => !item.answer).length;
    if (!unanswered) state.session.status = 'completed';
    showFeedback(question, answer);
  } catch (error) { toast(error.message); button.disabled = false; button.innerHTML = `Review my answer ${icons.arrow}`; }
}
function showFeedback(question, answer) {
  setPage('Answer feedback', 'new');
  const currentIndex = state.session.questions.findIndex(item => item.id === question.id);
  const nextIndex = currentIndex + 1;
  root.innerHTML = `<section class="page-heading"><div><div class="eyebrow">ANSWER REVIEW · QUESTION ${currentIndex + 1}</div><h1>What worked. What to sharpen.</h1><p>${escapeHtml(question.text)}</p></div></section>
    <div class="feedback-layout">
      <article class="card feedback-score-card"><h2>Your answer score</h2><p>A coaching signal, not a grade</p><div class="score-ring-wrap">${ring(answer.overall_score, 154)}</div>
        ${skillRows(answer.scores)}<span class="analysis-label">● ${answer.analysis_mode === 'gemini' ? 'Gemini-enhanced review' : 'Built-in local rubric'}</span>
      </article>
      <div class="feedback-main">
        <article class="card feedback-summary"><div class="eyebrow">COACH'S SUMMARY</div><h2>${escapeHtml(answer.summary)}</h2></article>
        <div class="feedback-columns">
          <article class="card feedback-list-card"><h3><span>✓</span> What worked</h3><ul class="feedback-list">${answer.strengths.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul></article>
          <article class="card feedback-list-card improve"><h3><span>↗</span> Try next time</h3><ul class="feedback-list">${answer.improvements.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul></article>
        </div>
        <article class="card answer-review"><h3>Your original answer</h3><p>${escapeHtml(answer.response_text)}</p></article>
        <div class="feedback-actions"><button class="secondary-button" data-route="home">Save & finish later</button><button class="primary-button" id="next-question">${nextIndex < state.session.questions.length ? `Next question ${icons.arrow}` : `View session summary ${icons.arrow}`}</button></div>
      </div>
    </div>`;
  document.getElementById('next-question').addEventListener('click', () => nextIndex < state.session.questions.length ? showPractice(nextIndex) : showSummary());
}
function showSummary() {
  const session = state.session;
  const answers = session.questions.map(question => question.answer).filter(Boolean);
  const average = answers.length ? Math.round(answers.reduce((sum, answer) => sum + answer.overall_score, 0) / answers.length) : null;
  setPage('Session summary', 'new');
  root.innerHTML = `<div class="setup-container"><article class="card summary-hero"><div class="eyebrow">PRACTICE COMPLETE</div><h1>You showed up and did the work.</h1><p>${escapeHtml(session.role)} · ${answers.length} answers reviewed · ${formatDate(session.created_at)}</p><div class="score-ring-wrap">${ring(average, 160)}</div><p>Review your answer feedback while it is fresh, then run another practice to make the improvements stick.</p><div class="summary-actions"><button class="secondary-button" data-route="home">Back to overview</button><button class="primary-button" data-route="new">Practice another set ${icons.arrow}</button></div></article></div>`;
}
async function showProgress() {
  setPage('Your progress', 'progress');
  root.innerHTML = '<div class="loading-screen"><div><span class="spinner"></span>Loading progress</div></div>';
  try {
    const data = await api('/api/dashboard');
    root.innerHTML = `<section class="page-heading"><div><div class="eyebrow">LEARN FROM THE PATTERN</div><h1>Your progress, at a glance.</h1><p>Use the skill averages to decide what your next practice should focus on.</p></div><button class="primary-button" data-route="new">${icons.plus} New practice</button></section>
      <div class="dashboard-grid"><article class="card"><div class="card-header"><h2>All practice sessions</h2><span>${data.session_count} TOTAL</span></div>${data.recent_sessions.length ? `<div class="session-list">${data.recent_sessions.map(sessionRow).join('')}</div>` : emptyState()}</article>
      <article class="card"><div class="card-header"><h2>Skill snapshot</h2><span>${data.answer_count} ANSWERS</span></div><div class="progress-card-body"><div class="score-ring-wrap">${ring(data.average_score)}</div>${skillRows(data.skill_averages)}<div class="progress-note">Relevance checks question coverage. Structure looks for context, actions and outcomes. Communication rewards clear, focused answers. Technical depth looks for specific tools, evidence and trade-offs.</div></div></article></div>`;
  } catch (error) { toast(error.message); }
}

async function checkHealth() {
  try {
    const health = await api('/api/health');
    engineStatus.innerHTML = `<span></span>${health.gemini_configured ? 'Gemini enhanced' : 'Local rubric ready'}`;
    engineStatus.title = health.gemini_configured ? 'Gemini is configured for answer feedback' : 'Working without an API key using the built-in rubric';
  } catch (_) { engineStatus.textContent = 'Engine offline'; }
}
document.addEventListener('click', event => {
  const route = event.target.closest('[data-route]');
  if (route) {
    event.preventDefault();
    if (route.dataset.route === 'home') showHome();
    if (route.dataset.route === 'new') showSetup();
    if (route.dataset.route === 'progress') showProgress();
  }
  const sessionButton = event.target.closest('[data-session-id]');
  if (sessionButton) openSession(sessionButton.dataset.sessionId);
});
checkHealth();
showHome();
