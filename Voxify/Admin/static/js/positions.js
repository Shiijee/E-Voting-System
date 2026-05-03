/* ── Quick Add Management ─────────────────── */
var DEFAULT_QUICK_POSITIONS = [
  { title: 'President',              desc: 'Leads the Student Council and represents the student body.',          icon: 'bi-person-badge',        maxVotes: 1, displayOrder: 1 },
  { title: 'Vice President',         desc: 'Assists the President and presides in their absence.',               icon: 'bi-person-badge-fill',    maxVotes: 1, displayOrder: 2 },
  { title: 'Secretary',              desc: 'Manages records, minutes, and official correspondence.',             icon: 'bi-journal-text',         maxVotes: 1, displayOrder: 3 },
  { title: 'Treasurer',              desc: 'Oversees the budget and financial management.',                      icon: 'bi-cash-coin',            maxVotes: 1, displayOrder: 4 },
  { title: 'Auditor',                desc: 'Reviews financial records and ensures accountability.',              icon: 'bi-clipboard-check',      maxVotes: 1, displayOrder: 5 },
  { title: 'P.R.O.',                 desc: 'Handles communications and public relations.',                       icon: 'bi-megaphone',            maxVotes: 1, displayOrder: 6 },
  { title: 'Senator',                desc: 'Represents the student body in legislative matters.',                icon: 'bi-people',               maxVotes: 3, displayOrder: 7 },
  { title: 'Rep.',                   desc: 'Advocates for student concerns at the council.',                     icon: 'bi-person-raised-hand',   maxVotes: 2, displayOrder: 8 },
  { title: 'Bus. Manager',           desc: 'Manages organizational resources and business affairs.',             icon: 'bi-briefcase',            maxVotes: 1, displayOrder: 9 },
  { title: 'Press Officer',          desc: 'Documents and publicizes council events and activities.',            icon: 'bi-newspaper',            maxVotes: 1, displayOrder: 10 },
  { title: 'Sgt.-at-Arms',           desc: 'Maintains order and enforces rules during council meetings.',        icon: 'bi-shield-check',         maxVotes: 1, displayOrder: 11 },
  { title: 'Beadle',                 desc: 'Liaises between students and faculty, manages class records.',       icon: 'bi-person-workspace',     maxVotes: 1, displayOrder: 12 },
  { title: 'Muse',                   desc: 'Represents the grace and spirit of the student council.',           icon: 'bi-stars',                maxVotes: 1, displayOrder: 13 },
  { title: 'SSG Rep.',               desc: 'Represents the school in inter-school student governance.',         icon: 'bi-award',                maxVotes: 1, displayOrder: 14 }
];

var STORAGE_KEY = 'svQuickPositions';

function loadQuickPositions() {
  try {
    var stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : JSON.parse(JSON.stringify(DEFAULT_QUICK_POSITIONS));
  } catch(e) {
    return JSON.parse(JSON.stringify(DEFAULT_QUICK_POSITIONS));
  }
}

function saveQuickPositions(arr) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(arr)); } catch(e) {}
}

function renderQuickGrid() {
  var positions = loadQuickPositions();
  var grid = document.getElementById('quickAddGrid');
  if (!grid) return;
  grid.innerHTML = '';
  positions.forEach(function(p, idx) {
    var item = document.createElement('div');
    item.className = 'quick-add-item';

    var prefillBtn = document.createElement('button');
    prefillBtn.className = 'quick-add-btn';
    prefillBtn.type = 'button';
    prefillBtn.innerHTML = '<i class="bi ' + p.icon + '"></i><span>' + p.title + '</span>';
    prefillBtn.addEventListener('click', function() {
      prefill(p.title, p.desc, p.maxVotes, p.displayOrder || 0);
    });

    var deleteBtn = document.createElement('button');
    deleteBtn.className = 'quick-delete-btn';
    deleteBtn.type = 'button';
    deleteBtn.title = 'Remove';
    deleteBtn.innerHTML = '<i class="bi bi-x"></i>';
    deleteBtn.addEventListener('click', function() {
      deleteQuickPosition(idx);
    });

    item.appendChild(prefillBtn);
    item.appendChild(deleteBtn);
    grid.appendChild(item);
  });
}

function deleteQuickPosition(idx) {
  var positions = loadQuickPositions();
  positions.splice(idx, 1);
  saveQuickPositions(positions);
  renderQuickGrid();
}

function openAddQuickModal() {
  document.getElementById('quickTitle').value = '';
  document.getElementById('quickDesc').value = '';
  document.getElementById('quickMaxVotes').value = 1;
  document.getElementById('quickDisplayOrder').value = 0;
  document.getElementById('addQuickModal').style.display = 'flex';
  document.body.style.overflow = 'hidden';
  setTimeout(function(){ document.getElementById('quickTitle').focus(); }, 50);
}

function closeAddQuickModal() {
  document.getElementById('addQuickModal').style.display = 'none';
  document.body.style.overflow = '';
}

function saveQuickPosition() {
  var title = document.getElementById('quickTitle').value.trim();
  if (!title) { document.getElementById('quickTitle').focus(); return; }
  var desc         = document.getElementById('quickDesc').value.trim();
  var maxVotes     = parseInt(document.getElementById('quickMaxVotes').value) || 1;
  var displayOrder = parseInt(document.getElementById('quickDisplayOrder').value) || 0;
  var positions = loadQuickPositions();
  positions.push({ title: title, desc: desc, icon: 'bi-person-fill', maxVotes: maxVotes, displayOrder: displayOrder });
  saveQuickPositions(positions);
  renderQuickGrid();
  closeAddQuickModal();
}

document.getElementById('addQuickModal').addEventListener('click', function(e) {
  if (e.target === this) closeAddQuickModal();
});

function prefill(title, desc, maxVotes, displayOrder) {
  document.getElementById('addTitle').value = title;
  document.getElementById('addDescription').value = desc;
  document.getElementById('addMaxVotes').value = maxVotes;
  var doEl = document.querySelector('#addPositionForm input[name="display_order"]');
  if (doEl) doEl.value = displayOrder || 0;
  document.getElementById('addTitle').focus();
}

function openEditModal(id, electionId, title, description, maxVotes, displayOrder) {
  document.getElementById('editTitle').value = title;
  document.getElementById('editDescription').value = description;
  document.getElementById('editMaxVotes').value = maxVotes;
  document.querySelector('#editPositionForm select[name="election_id"]').value = electionId;
  document.getElementById('editPositionForm').action = '/admin/positions/' + id + '/edit';
  document.getElementById('editModal').style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeEditModal() {
  document.getElementById('editModal').style.display = 'none';
  document.body.style.overflow = '';
}

document.getElementById('editModal').addEventListener('click', function(e) {
  if (e.target === this) closeEditModal();
});

var _posCurrentElection = 'all';
var _posPaginator = null;

document.addEventListener('DOMContentLoaded', function () {
  renderQuickGrid();
  _posPaginator = new SvPaginator({
    tableId:     'positionsTable',
    rowSelector: 'tbody tr',
    perPage:     10,
    infoId:      'posPagInfo',
    listId:      'posPagList',
    wrapId:      'posPagWrap',
    onFilter:    function(row) {
      return _posCurrentElection === 'all' || row.dataset.electionId === _posCurrentElection;
    }
  });
});

function filterByElection(id, btn) {
  document.querySelectorAll('.election-tab').forEach(function(t){ t.classList.remove('active'); });
  btn.classList.add('active');
  _posCurrentElection = id;
  if (_posPaginator) _posPaginator.applyFilter();
}
