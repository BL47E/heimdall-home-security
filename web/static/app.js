'use strict';
const $ = (id) => document.getElementById(id);
let csrf = '',
  alerts = [],
  selectedId = null,
  selectedSignature = '',
  configDirty = false,
  selectedConnection = null,
  connectionSnapshot = null;
let sessionVersion = 0,
  inspectionVersion = 0;
const page =
  {
    '/': 'overview',
    '/overview': 'overview',
    '/investigations': 'investigations',
    '/activity': 'activity',
    '/connections': 'connections',
    '/settings': 'settings'
  }[location.pathname] || 'overview';
document.title =
  {
    overview: 'Overview',
    investigations: 'Investigations',
    activity: 'Activity',
    connections: 'Connections',
    settings: 'Settings'
  }[page] + ' · Heimdall';
$(page).hidden = false;
for (const a of document.querySelectorAll('nav a'))
  if (a.getAttribute('href') === '/' + page)
    a.setAttribute('aria-current', 'page');
const label = (s) => (s === 'needs_review' ? 'Needs review' : 'Reviewed');
const providerState = (state) => ({
  disabled: 'disabled',
  configured: 'configured',
  needs_configuration: 'needs configuration',
  fixture_destination_mismatch: 'requires a test destination',
  rate_limited: 'rate limited',
  delivery_error: 'delivery error',
  pending: 'pending delivery',
  delivered: 'delivered'
})[state] || 'unknown';
function notice(s) {
  $('message').textContent = s;
}
function node(tag, text, cls) {
  const e = document.createElement(tag);
  e.textContent = text ?? 'Unknown';
  if (cls) e.className = cls;
  return e;
}
function date(t) {
  return t == null ? 'Time unavailable' : new Date(t * 1000).toLocaleString();
}
function emptyDetail() {
  const empty = node('div', '', 'empty');
  empty.append(
    node('span', '┌─ ▥ ─┐'),
    node('h3', 'Follow the evidence'),
    node('p', 'Choose an alert to inspect its timeline and review history.')
  );
  $('detail').replaceChildren(empty);
}
function showLogin(message = '') {
  sessionVersion++;
  inspectionVersion++;
  csrf = '';
  alerts = [];
  selectedId = null;
  selectedSignature = '';
  configDirty = false;
  $('config').querySelector('button').disabled = false;
  $('app').hidden = true;
  $('login').hidden = false;
  $('logout').hidden = true;
  $('alerts').replaceChildren();
  $('events').replaceChildren();
  $('ssh-connections').replaceChildren();
  $('connection-detail').replaceChildren();
  $('connection-detail').hidden = true;
  selectedConnection = null;
  connectionSnapshot = null;
  $('metrics').replaceChildren();
  emptyDetail();
  $('config').reset();
  $('config-state').textContent = '';
  $('status').textContent = '';
  $('monitor-badge').textContent = 'Unknown';
  $('mode-label').textContent = 'Checking source';
  $('provider-label').textContent = '';
  $('freshness').textContent = 'Waiting for status';
  $('token').value = '';
  notice(message);
}
const currentSession = (version) => Boolean(csrf) && version === sessionVersion;
async function api(path, opts = {}) {
  const headers = {},
    version = sessionVersion;
  if (opts.method === 'POST') {
    headers['Content-Type'] = 'application/json';
    headers['X-CSRF-Token'] = csrf;
    opts.body = JSON.stringify(opts.body || {});
  }
  const controller = new AbortController(),
    timer = setTimeout(() => controller.abort(), 12000);
  try {
    const r = await fetch(path, {
      ...opts,
      headers,
      signal: controller.signal
    });
    if (r.status === 401 && currentSession(version))
      showLogin('Your session expired. Sign in again.');
    if (!r.ok) {
      let e = {};
      try {
        e = await r.json();
      } catch {}
      throw Error(e.error || 'Request failed');
    }
    return await r.json();
  } finally {
    clearTimeout(timer);
  }
}
function render() {
  const root = $('alerts');
  root.replaceChildren();
  const list = alerts.filter(
    (a) => $('filter').value === 'all' || a.review_status === $('filter').value
  );
  if (!list.length)
    root.append(
      node(
        'p',
        'No alerts match this filter. New rule matches will appear here.'
      )
    );
  for (const a of list) {
    const b = node('button', '', a.id === selectedId ? 'selected' : '');
    b.setAttribute('aria-pressed', String(a.id === selectedId));
    const head = node('span', '', 'alert-head');
    head.append(
      node('span', a.source_ip || 'Unknown source', 'alert-source'),
      node('span', a.severity, 'badge')
    );
    b.append(
      head,
      node(
        'span',
        a.failure_count + ' failures / ' + a.rule.window_seconds + 's rule',
        'alert-summary'
      ),
      node(
        'span',
        label(a.review_status) +
          ' / ' +
          (a.provenance === 'fixture' ? 'Sample data' : 'Journal'),
        'alert-status'
      )
    );
    b.onclick = () => inspect(a.id);
    root.append(b);
  }
}
async function inspect(id) {
  const version = sessionVersion,
    request = ++inspectionVersion;
  try {
    const a = await api('/api/alerts/' + encodeURIComponent(id));
    if (!currentSession(version) || request !== inspectionVersion) return;
    selectedId = id;
    selectedSignature = JSON.stringify(alerts.find((item) => item.id === id));
    render();
    const d = $('detail');
    d.replaceChildren(
      node('h3', a.source_ip),
      node(
        'p',
        a.severity +
          ' / ' +
          label(a.review_status) +
          ' / ' +
          (a.provenance === 'fixture' ? 'Synthetic sample' : 'SSH journal')
      ),
      node('p', a.explanation),
      node('p', a.recommendation),
      node('p', date(a.first_seen) + ' – ' + date(a.last_seen)),
      node('h3', 'VirusTotal reputation')
    );
    const reputation = a.reputation;
    if (reputation) {
      const provenance = reputation.provenance === 'simulated'
        ? ' / Simulated'
        : reputation.from_cache ? ' / Cached' : '';
      d.append(node('p', reputation.label + provenance + ' / Checked ' + date(reputation.checked_at)));
      d.append(node('p', reputation.flags === null
        ? reputation.reason
        : `${reputation.flags} flagging vendors (malicious or suspicious)`));
      if (reputation.flags >= 10) {
        d.append(node('p', 'Severity raised to High because at least 10 vendors flagged the IP.'));
      }
    } else {
      d.append(node('p', 'Unknown / No lookup recorded'));
    }
    d.append(node('h3', 'Evidence timeline'));
    for (const e of a.events || []) {
      const item = node('div', '', 'timeline-item');
      item.append(
        node('time', date(e.timestamp)),
        node('div', e.message, 'original')
      );
      for (const note of e.notes || []) item.append(node('div', note, 'note'));
      d.append(item);
    }
    d.append(node('h3', 'Review history'));
    if (!(a.review_history || []).length)
      d.append(node('p', 'This alert has not been reviewed yet.'));
    for (const h of a.review_history || [])
      d.append(
        node(
          'p',
          date(h.timestamp) +
            ' / ' +
            label(h.status || h.review_status) +
            ' / ' +
            (h.reason === 'new_failure'
              ? 'New failure reopened this alert'
              : 'Owner action')
        )
      );
    const b = node(
      'button',
      a.review_status === 'reviewed' ? 'Reopen alert' : 'Mark reviewed',
      'primary'
    );
    b.onclick = async () => {
      b.disabled = true;
      try {
        await api(
          '/api/alerts/' +
            encodeURIComponent(id) +
            '/' +
            (a.review_status === 'reviewed' ? 'reopen' : 'review'),
          { method: 'POST' }
        );
        if (!currentSession(version)) return;
        await refresh();
        await inspect(id);
      } catch (e) {
        if (currentSession(version)) {
          notice(e.message);
          b.disabled = false;
        }
      }
    };
    const link = node('a', 'Download report', 'report-link');
    link.href = '/api/alerts/' + encodeURIComponent(id) + '/report';
    d.append(b, link);
  } catch (e) {
    if (currentSession(version)) notice(e.message);
  }
}
function reputationFor(address, findings) {
  return findings
    .filter((alert) => alert.source_ip === address && alert.reputation)
    .map((alert) => alert.reputation)
    .sort((a, b) => (b.checked_at || 0) - (a.checked_at || 0))[0] || null;
}
function connectionAssessment(reputation) {
  if (!reputation || !Number.isInteger(reputation.flags) || reputation.flags < 0)
    return ['unknown', 'Unknown'];
  if (reputation.flags === 0) return ['active', 'No flags found'];
  if (reputation.flags < 7) return ['previous', reputation.label];
  return ['bad', reputation.label];
}
function showConnection(address, findings) {
  const detail = $('connection-detail');
  const reputation = reputationFor(address, findings);
  const [state, label] = connectionAssessment(reputation);
  const heading = node('h2', address);
  const summary = node('p', '', 'connection-reputation');
  const dot = node('span', '', 'connection-dot ' + state);
  dot.setAttribute('aria-hidden', 'true');
  const provenance = reputation && reputation.provenance === 'simulated' ? ' / Simulated' : '';
  summary.append(dot, document.createTextNode('VirusTotal / ' + label + provenance));
  detail.replaceChildren(heading, summary);
  if (reputation && Number.isInteger(reputation.flags))
    detail.append(node('p', reputation.flags + ' vendors flagged this IP / Checked ' + date(reputation.checked_at)));
  else detail.append(node('p', 'No available VirusTotal result for this IP.'));
  detail.append(node('p', 'Actions would apply to this IP address and can affect multiple people or systems.'));
  const actions = node('div', '', 'connection-actions');
  for (const label of ['Block', 'Time out', 'Limit access']) {
    const button = node('button', label);
    button.type = 'button';
    button.disabled = true;
    actions.append(button);
  }
  detail.append(node('h3', 'Access controls / Planned'), actions,
    node('p', 'These controls are not active. Firewall design review and console recovery testing are required before they can change access.'));
  detail.hidden = false;
}
function connectionRow(title, detail, state, findings) {
  const row = node('button', '', 'connection-row');
  row.type = 'button';
  row.dataset.address = title;
  row.setAttribute('aria-pressed', String(selectedConnection === title));
  const dot = node('span', '', 'connection-dot ' + state);
  dot.setAttribute('aria-hidden', 'true');
  const info = node('span', '', 'connection-detail');
  const reputation = reputationFor(title, findings);
  const [assessment, label] = connectionAssessment(reputation);
  const reputationLine = node('span', '', 'connection-reputation');
  const reputationDot = node('span', '', 'connection-dot ' + assessment);
  reputationDot.setAttribute('aria-hidden', 'true');
  const provenance = reputation && reputation.provenance === 'simulated' ? ' / Simulated' : '';
  reputationLine.append(reputationDot, document.createTextNode('VirusTotal / ' + label + provenance));
  info.append(node('span', detail), reputationLine);
  row.append(dot, node('strong', title, 'connection-name'), info);
  row.onclick = () => {
    selectedConnection = title;
    for (const button of $('ssh-connections').querySelectorAll('button'))
      button.setAttribute('aria-pressed', String(button.dataset.address === title));
    showConnection(title, findings);
  };
  return row;
}
function renderConnections(data, findings) {
  const ssh = $('ssh-connections');
  ssh.replaceChildren();
  for (const item of data.ssh.history)
    ssh.append(connectionRow(item.address, 'Successful login / ' + (item.username || 'Unknown user') + ' / ' + date(item.timestamp), 'previous', findings));
  if (data.ssh.history_message) ssh.append(node('p', data.ssh.history_message));
  if (!data.ssh.history.length && !data.ssh.history_message)
    ssh.append(node('p', 'No retained successful password logins have been recorded.'));
  if (selectedConnection && data.ssh.history.some((item) => item.address === selectedConnection))
    showConnection(selectedConnection, findings);
  else {
    selectedConnection = null;
    $('connection-detail').replaceChildren();
    $('connection-detail').hidden = true;
  }
}
async function refresh() {
  const version = sessionVersion;
  if (!csrf) return;
  try {
    if (page === 'overview') {
      const s = await api('/api/status');
      if (!currentSession(version)) return;
      const healthy =
        s.monitor.state === 'running' && s.monitor.coverage === 'available';
      $('monitor-badge').textContent = healthy
        ? 'Monitoring'
        : s.monitor.state === 'paused'
          ? 'Paused'
          : s.monitor.state === 'error'
          ? 'Needs attention'
          : 'Not monitoring';
      $('status').textContent =
        s.monitor.last_error ||
        (s.monitor.state === 'paused'
          ? 'Monitoring is paused. SSH activity during this pause is skipped.'
          : healthy
          ? 'Watching the SSH journal for password authentication activity.'
          : 'Live journal coverage is unavailable. Start the monitor on Ubuntu to watch new activity.');
      $('metrics').replaceChildren(
        ...[
          ['events', 'Events recorded'],
          ['alerts', 'Alerts raised'],
          ['needs_review', 'Need review']
        ].map(([key, text]) => {
          const n = node('div', '', 'metric');
          n.append(node('strong', s.counts[key]), node('span', text));
          return n;
        })
      );
      $('mode-label').textContent =
        s.mode === 'fixture'
          ? 'Synthetic samples / no live coverage'
          : 'SSH journal / ' + s.monitor.coverage + ' coverage';
      $('provider-label').textContent =
        'Discord ' + providerState(s.providers.discord) + ' / VirusTotal ' + providerState(s.providers.virustotal);
      $('freshness').textContent = 'Updated ' + new Date().toLocaleTimeString();
    } else if (page === 'investigations') {
      const latest = await api('/api/alerts');
      if (!currentSession(version)) return;
      alerts = latest;
      render();
      if (selectedId) {
        const selected = alerts.find((a) => a.id === selectedId);
        if (!selected) {
          selectedId = null;
          selectedSignature = '';
          inspectionVersion++;
          emptyDetail();
        } else if (
          JSON.stringify(selected) !== selectedSignature &&
          !$('detail').contains(document.activeElement)
        )
          await inspect(selectedId);
      }
    } else if (page === 'connections') {
      const [data, findings] = await Promise.all([api('/api/connections'), api('/api/alerts')]);
      if (!currentSession(version)) return;
      const snapshot = JSON.stringify([data, findings]);
      if (snapshot !== connectionSnapshot && !$('ssh-connections').contains(document.activeElement) && !$('connection-detail').contains(document.activeElement)) {
        connectionSnapshot = snapshot;
        renderConnections(data, findings);
      }
    } else if (page === 'activity') {
      const events = await api('/api/events');
      if (!currentSession(version)) return;
      $('events').replaceChildren(
        ...events.map((e) => {
          const n = node('div', '', 'event');
          n.append(
            node('time', date(e.timestamp)),
            node('span', e.source_ip || 'Source unavailable'),
            node('span', e.message, 'event-message')
          );
          if (e.outcome === 'success')
            n.append(
              node(
                'span',
                'Preceding matching failures: ' +
                  (e.preceding_failures ?? 'Unknown'),
                'event-message'
              )
            );
          for (const note of e.notes || [])
            n.append(node('span', note, 'event-message'));
          return n;
        })
      );
      if (!events.length)
        $('events').append(node('p', 'No events recorded yet.', 'event'));
    } else if (!configDirty) {
      const c = await api('/api/config');
      if (!currentSession(version) || configDirty) return;
      for (const k of ['threshold', 'window_seconds', 'retention_days'])
        $('config').elements[k].value = c[k];
    }
  } catch (e) {
    if (currentSession(version)) {
      if (page === 'connections') {
        $('ssh-connections').replaceChildren(node('p', 'Connection data unavailable.'));
        $('connection-detail').replaceChildren();
        $('connection-detail').hidden = true;
        connectionSnapshot = null;
      }
      if (page === 'overview')
        $('freshness').textContent =
          'Connection unavailable / data may be stale';
      notice(e.message);
    }
  }
}
function signed() {
  $('login').hidden = true;
  $('app').hidden = false;
  $('logout').hidden = false;
  refresh();
}
$('login-form').onsubmit = async (e) => {
  e.preventDefault();
  const version = sessionVersion;
  try {
    const r = await api('/api/login', {
      method: 'POST',
      body: { token: $('token').value }
    });
    if (version !== sessionVersion) return;
    sessionVersion++;
    csrf = r.csrf;
    $('token').value = '';
    notice('');
    signed();
  } catch (e) {
    if (version === sessionVersion) notice(e.message);
  }
};
$('logout').onclick = async () => {
  if (configDirty && !confirm('Discard unsaved settings and sign out?')) return;
  const version = sessionVersion;
  try {
    await api('/api/logout', { method: 'POST' });
    if (version === sessionVersion) showLogin();
  } catch (e) {
    if (currentSession(version)) notice(e.message);
  }
};
$('filter').onchange = render;
for (const action of ['start', 'stop'])
  $(action).onclick = async () => {
    if (!confirm((action === 'start' ? 'Resume SSH monitoring?' : 'Pause SSH monitoring? Activity during the pause will be skipped.')))
      return;
    const version = sessionVersion;
    try {
      await api('/api/monitor/' + action, { method: 'POST' });
      if (currentSession(version)) await refresh();
    } catch (e) {
      if (currentSession(version)) notice(e.message);
    }
  };
let configRevision = 0;
$('config').oninput = () => {
  configRevision++;
  configDirty = true;
  $('config-state').textContent = 'Unsaved changes';
};
$('config').onsubmit = async (e) => {
  e.preventDefault();
  const save = e.target.querySelector('button');
  if (save.disabled) return;
  save.disabled = true;
  const revision = configRevision,
    body = {},
    version = sessionVersion;
  for (const k of ['threshold', 'window_seconds', 'retention_days'])
    body[k] = Number(e.target.elements[k].value);
  try {
    await api('/api/config', { method: 'POST', body });
    if (!currentSession(version) || revision !== configRevision) return;
    configDirty = false;
    $('config-state').textContent = 'Settings saved';
    await refresh();
  } catch (e) {
    if (currentSession(version)) notice(e.message);
  } finally {
    if (version === sessionVersion) save.disabled = false;
  }
};
async function restoreSession() {
  const version = sessionVersion;
  try {
    const s = await api('/api/session');
    if (version !== sessionVersion) return;
    if (s.authenticated) {
      csrf = s.csrf;
      signed();
    } else showLogin();
  } catch (e) {
    if (version === sessionVersion) showLogin(e.message);
  }
}
restoreSession();
setInterval(() => {
  if (csrf) refresh();
}, 15000);
window.addEventListener('beforeunload', (e) => {
  if (configDirty) {
    e.preventDefault();
    e.returnValue = '';
  }
});
window.addEventListener('pagehide', () => showLogin());
window.addEventListener('pageshow', (e) => {
  if (e.persisted) restoreSession();
});
