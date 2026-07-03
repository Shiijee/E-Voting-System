// ── Election Selector Dropdown ──────────────────────────
(function () {
  const searchInput = document.getElementById('election-search');
  const currentId = searchInput ? searchInput.dataset.currentId || '' : '';
  if (currentId) {
    document.querySelectorAll('.election-opt').forEach(opt => {
      if (opt.dataset.value === currentId) {
        document.getElementById('election-search').value = opt.dataset.label || opt.textContent.trim();
      }
    });
  }
})();

function positionDropdown() {
  const input = document.getElementById('election-search');
  const dd = document.getElementById('election-dropdown');
  const rect = input.getBoundingClientRect();
  dd.style.top = (rect.bottom + 4) + 'px';
  dd.style.left = rect.left + 'px';
  dd.style.width = rect.width + 'px';
}

function openDropdown() {
  positionDropdown();
  document.getElementById('election-dropdown').style.display = 'block';
  filterElections(document.getElementById('election-search').value);
}

function filterElections(query) {
  const q = query.toLowerCase().trim();
  const opts = document.querySelectorAll('.election-opt');
  let visible = 0;
  opts.forEach(opt => {
    const label = (opt.dataset.label || opt.textContent).toLowerCase();
    const show = !q || label.includes(q);
    opt.style.display = show ? '' : 'none';
    if (show && opt.dataset.value) visible++;
  });
  document.getElementById('election-no-results').style.display = (visible === 0 && q) ? 'block' : 'none';
  positionDropdown();
  document.getElementById('election-dropdown').style.display = 'block';
}

function selectElection(id, label) {
  document.getElementById('election-id-input').value = id;
  document.getElementById('election-search').value = id ? label : '';
  document.getElementById('election-dropdown').style.display = 'none';
  if (id) document.getElementById('election-form').submit();
}

document.addEventListener('click', function (e) {
  const dd = document.getElementById('election-dropdown');
  const input = document.getElementById('election-search');
  if (!dd || !input) return;
  if (!dd.contains(e.target) && e.target !== input) {
    dd.style.display = 'none';
  }
});

window.addEventListener('scroll', function () {
  const dd = document.getElementById('election-dropdown');
  if (dd && dd.style.display === 'block') {
    positionDropdown();
  }
}, true);

document.querySelectorAll('.election-opt').forEach(opt => {
  opt.addEventListener('mouseenter', () => opt.style.background = 'var(--paper)');
  opt.addEventListener('mouseleave', () => opt.style.background = '');
});

// ── Tabs ─────────────────────────────────────────────────
function switchTab(tabId, btn) {
  document.querySelectorAll('.results-tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.results-tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + tabId).classList.add('active');
  btn.classList.add('active');
}

// ── Voter Table Search Filter ───────────────────────────
function filterTable(tableId, query) {
  const table = document.getElementById(tableId);
  if (!table) return;
  const rows = table.querySelectorAll('tbody tr');
  const q = query.toLowerCase();
  let visible = 0;
  rows.forEach(row => {
    const text = row.textContent.toLowerCase();
    const show = text.includes(q);
    row.style.display = show ? '' : 'none';
    if (show) visible++;
  });
}

// ── Export: Print / Save as PDF ─────────────────────────
function printResults() {
  closeExportMenu();
  window.print();
}

// ── Export: CSV (current tab only) ──────────────────────
// Move the menu to <body> so no ancestor (transforms, stacking
// contexts, overflow, etc.) can ever trap or clip it.
(function relocateExportMenu() {
  const menu = document.getElementById('export-menu');
  if (menu && menu.parentElement !== document.body) {
    document.body.appendChild(menu);
  }
})();

function positionExportMenu() {
  const btn = document.getElementById('export-btn');
  const menu = document.getElementById('export-menu');
  if (!btn || !menu) return;
  const rect = btn.getBoundingClientRect();
  menu.style.top = (rect.bottom + 6) + 'px';
  menu.style.left = 'auto';
  menu.style.right = (window.innerWidth - rect.right) + 'px';
}

function toggleExportMenu() {
  const menu = document.getElementById('export-menu');
  if (!menu) return;
  const willShow = !menu.classList.contains('show');
  if (willShow) {
    positionExportMenu();
  }
  menu.classList.toggle('show', willShow);
}
function closeExportMenu() {
  const menu = document.getElementById('export-menu');
  if (menu) menu.classList.remove('show');
}
document.addEventListener('click', function (e) {
  const menu = document.getElementById('export-menu');
  const btn = document.getElementById('export-btn');
  if (!menu || !btn) return;
  if (!menu.contains(e.target) && e.target !== btn && !btn.contains(e.target)) {
    closeExportMenu();
  }
});
window.addEventListener('scroll', function () {
  const menu = document.getElementById('export-menu');
  if (menu && menu.classList.contains('show')) positionExportMenu();
}, true);
window.addEventListener('resize', function () {
  const menu = document.getElementById('export-menu');
  if (menu && menu.classList.contains('show')) positionExportMenu();
});

function csvEscape(val) {
  val = String(val === undefined || val === null ? '' : val);
  if (/[",\r\n]/.test(val)) {
    val = '"' + val.replace(/"/g, '""') + '"';
  }
  return val;
}

function downloadCSV(rows, filename) {
  const csvContent = rows.map(r => r.map(csvEscape).join(',')).join('\r\n');
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(link.href);
}

function getElectionLabel() {
  const el = document.getElementById('election-search');
  return (el && el.value ? el.value : 'election').replace(/[\\/:*?"<>|]/g, '-');
}

function exportCSV() {
  const activePanel = document.querySelector('.results-tab-panel.active');
  if (!activePanel) return;
  const activeId = activePanel.id;
  const electionLabel = getElectionLabel();
  let rows = [];
  let filename = electionLabel + '.csv';

  if (activeId === 'tab-vote-results') {
    rows.push(['Position', 'Candidate', 'Partylist', 'Votes', 'Percentage']);
    document.querySelectorAll('#tab-vote-results .card-panel').forEach(panel => {
      const positionTitle = panel.querySelector('.card-panel-title');
      const position = positionTitle ? positionTitle.textContent.trim().replace(/\s+/g, ' ') : '';
      panel.querySelectorAll('.result-row').forEach(row => {
        const name = row.querySelector('.fw-600');
        const party = row.querySelector('.result-candidate .text-muted-sm');
        const votes = row.querySelector('.result-count');
        const pct = row.querySelector('.result-pct');
        rows.push([
          position,
          name ? name.textContent.trim() : '',
          party ? party.textContent.trim() : '',
          votes ? votes.textContent.trim() : '',
          pct ? pct.textContent.trim() : ''
        ]);
      });
    });
    filename = electionLabel + ' - vote results.csv';
  } else if (activeId === 'tab-voters-voted' || activeId === 'tab-voters-not-voted') {
    const tableId = activeId === 'tab-voters-voted' ? 'table-voted' : 'table-not-voted';
    const table = document.getElementById(tableId);
    if (!table) return;
    rows.push(['#', 'Voter Name', 'Email', 'Student ID', 'Status']);
    table.querySelectorAll('tbody tr').forEach(tr => {
      if (tr.style.display === 'none') return; // respect active search filter
      const cells = tr.querySelectorAll('td');
      const nameWrap = tr.querySelector('.voter-name-cell > div:last-child');
      const idx = cells[0] ? cells[0].textContent.trim() : '';
      const name = nameWrap && nameWrap.children[0] ? nameWrap.children[0].textContent.trim() : '';
      const email = nameWrap && nameWrap.children[1] ? nameWrap.children[1].textContent.trim() : '';
      const sid = cells[2] ? cells[2].textContent.trim() : '';
      const status = cells[3] ? cells[3].textContent.trim() : '';
      rows.push([idx, name, email, sid, status]);
    });
    filename = electionLabel + (activeId === 'tab-voters-voted' ? ' - voted.csv' : ' - not voted.csv');
  }

  if (rows.length <= 1) return;
  downloadCSV(rows, filename);
  closeExportMenu();
}