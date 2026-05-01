/* ═══════════════════════════════════════════════════════
   SecureVote Admin — Enhancements JS
   Notifications · Toasts
   Candidate Cards View · Election Inline Search/Filter
═══════════════════════════════════════════════════════ */

(function() {
  'use strict';

  /* ── 1. NOTIFICATIONS ────────────────────────────── */
  const notifBtn      = document.getElementById('notifBtn');
  const notifDropdown = document.getElementById('notifDropdown');
  const notifBadge    = document.getElementById('notifBadge');
  const notifList     = document.getElementById('notifList');
  const notifClearAll = document.getElementById('notifClearAll');

  let notifications = loadNotifications();

  renderNotifications();

  if (notifBtn) {
    notifBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      notifDropdown.classList.toggle('open');
      if (notifDropdown.classList.contains('open')) {
        markAllRead();
      }
    });
  }

  document.addEventListener('click', (e) => {
    if (notifDropdown && !notifDropdown.contains(e.target) && e.target !== notifBtn) {
      notifDropdown.classList.remove('open');
    }
  });

  if (notifClearAll) {
    notifClearAll.addEventListener('click', () => {
      notifications = [];
      saveNotifications();
      renderNotifications();
    });
  }

  function loadNotifications() {
    try {
      const stored = localStorage.getItem('sv_notifications');
      return stored ? JSON.parse(stored) : getDefaultNotifications();
    } catch { return getDefaultNotifications(); }
  }

  function getDefaultNotifications() {
    return [
      { id: 1, text: 'New voter registered and awaiting approval', icon: 'bi-person-plus-fill', type: 'blue', time: '2 min ago', read: false },
      { id: 2, text: 'Election "Student Council" is starting soon', icon: 'bi-calendar-event-fill', type: 'amber', time: '15 min ago', read: false },
      { id: 3, text: 'Audit log: Admin login detected', icon: 'bi-shield-check', type: 'green', time: '1 hr ago', read: true },
    ];
  }

  function saveNotifications() {
    localStorage.setItem('sv_notifications', JSON.stringify(notifications));
  }

  function markAllRead() {
    notifications.forEach(n => n.read = true);
    saveNotifications();
    updateBadge();
  }

  function updateBadge() {
    const unread = notifications.filter(n => !n.read).length;
    if (notifBadge) {
      notifBadge.textContent = unread;
      notifBadge.style.display = unread > 0 ? 'flex' : 'none';
    }
  }

  function renderNotifications() {
    if (!notifList) return;
    updateBadge();
    if (!notifications.length) {
      notifList.innerHTML = '<div class="notif-empty"><i class="bi bi-bell-slash"></i><span>All caught up!</span></div>';
      return;
    }
    notifList.innerHTML = '';
    notifications.forEach(n => {
      const item = document.createElement('div');
      item.className = 'notif-item' + (n.read ? '' : ' unread');
      item.innerHTML = `
        <div class="notif-item-icon notif-icon-${n.type}"><i class="bi ${n.icon}"></i></div>
        <div class="notif-item-body">
          <div class="notif-item-text">${escHtml(n.text)}</div>
          <div class="notif-item-time"><i class="bi bi-clock me-1"></i>${n.time}</div>
        </div>
        <button class="notif-item-dismiss" data-id="${n.id}" title="Dismiss"><i class="bi bi-x"></i></button>
      `;
      item.querySelector('.notif-item-dismiss').addEventListener('click', (e) => {
        e.stopPropagation();
        notifications = notifications.filter(x => x.id !== n.id);
        saveNotifications();
        renderNotifications();
      });
      notifList.appendChild(item);
    });
  }

  // Expose so Flask flash messages can create notifications
  window.svAddNotification = function(text, type = 'blue', icon = 'bi-info-circle-fill') {
    const n = { id: Date.now(), text, icon, type, time: 'Just now', read: false };
    notifications.unshift(n);
    if (notifications.length > 20) notifications.pop();
    saveNotifications();
    renderNotifications();
  };

  /* ── 2. TOAST SYSTEM ─────────────────────────────── */
  const toastStack = document.getElementById('toastStack');

  window.showToast = function(message, type = 'info', duration = 4000) {
    if (!toastStack) return;
    const icons = { success: 'bi-check-circle-fill', error: 'bi-x-circle-fill', warning: 'bi-exclamation-triangle-fill', info: 'bi-info-circle-fill' };
    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;
    toast.innerHTML = `
      <i class="bi ${icons[type] || icons.info} toast-icon"></i>
      <span class="toast-msg">${escHtml(message)}</span>
      <button class="toast-close"><i class="bi bi-x"></i></button>
    `;
    toast.querySelector('.toast-close').addEventListener('click', () => dismissToast(toast));
    toastStack.prepend(toast);
    setTimeout(() => dismissToast(toast), duration);
  };

  function dismissToast(toast) {
    toast.classList.add('toast-out');
    setTimeout(() => toast.remove(), 300);
  }

  /* ── 3. CANDIDATE CARD VIEW TOGGLE ───────────────── */
  initCandidateViewToggle();

  function initCandidateViewToggle() {
    const tableWrap = document.querySelector('.table-responsive');
    if (!tableWrap) return;
    const pageHeading = document.querySelector('.page-heading');
    if (!pageHeading || !pageHeading.textContent.toLowerCase().includes('candidate')) return;

    // Build toolbar
    const toolbar = document.createElement('div');
    toolbar.className = 'candidates-toolbar';

    // Count display
    const rows = document.querySelectorAll('.table-custom tbody tr');
    const countEl = document.createElement('div');
    countEl.className = 'candidates-count';
    countEl.innerHTML = `<span>${rows.length}</span> candidate${rows.length !== 1 ? 's' : ''}`;

    // Inline search
    const searchWrap = document.createElement('div');
    searchWrap.className = 'candidates-search-wrap';
    searchWrap.innerHTML = `
      <i class="bi bi-search"></i>
      <input type="text" class="candidates-search-input" placeholder="Search candidates…" id="candidateInlineSearch"/>
    `;

    // View toggle
    const savedView = localStorage.getItem('sv_candidate_view') || 'table';
    const viewToggle = document.createElement('div');
    viewToggle.className = 'view-toggle';
    viewToggle.innerHTML = `
      <button class="view-toggle-btn ${savedView === 'table' ? 'active' : ''}" data-view="table" title="Table view"><i class="bi bi-list-ul"></i></button>
      <button class="view-toggle-btn ${savedView === 'cards' ? 'active' : ''}" data-view="cards" title="Card view"><i class="bi bi-grid-3x3-gap-fill"></i></button>
    `;

    toolbar.appendChild(countEl);
    toolbar.appendChild(searchWrap);
    toolbar.appendChild(viewToggle);

    const cardPanel = tableWrap.closest('.card-panel');
    if (cardPanel) cardPanel.insertBefore(toolbar, tableWrap);

    // Build cards grid from table data
    const cardsGrid = document.createElement('div');
    cardsGrid.className = 'candidate-cards-grid';
    cardsGrid.style.display = 'none';

    rows.forEach(row => {
      const cells = row.querySelectorAll('td');
      const photoCell = cells[0];
      const nameCell  = cells[1];
      const posCell   = cells[2];
      const elecCell  = cells[3];
      const actCell   = cells[4];

      const imgEl = photoCell.querySelector('img');
      const letter = photoCell.querySelector('.candidate-avatar-placeholder')?.textContent?.trim() || '?';
      const name    = nameCell.querySelector('.fw-600')?.textContent?.trim() || '';
      const pos     = posCell?.textContent?.trim() || '';
      const elec    = elecCell?.textContent?.trim() || '';
      const editBtn = actCell?.querySelector('.btn-action-edit')?.outerHTML || '';
      const delBtn  = actCell?.querySelector('.btn-action-delete')?.outerHTML || '';

      const card = document.createElement('div');
      card.className = 'candidate-card';
      card.dataset.name = name.toLowerCase();
      card.dataset.position = pos.toLowerCase();
      card.dataset.election = elec.toLowerCase();
      card.innerHTML = `
        <div class="candidate-card-photo">${imgEl ? `<img src="${imgEl.src}" alt="${name}"/>` : letter}</div>
        <div class="candidate-card-body">
          <div class="candidate-card-name" title="${name}">${name}</div>
          <div class="candidate-card-position">${pos}</div>
          <div class="candidate-card-election">${elec}</div>
          <div class="candidate-card-actions">${editBtn}${delBtn}</div>
        </div>
      `;
      cardsGrid.appendChild(card);
    });

    if (cardPanel) cardPanel.appendChild(cardsGrid);

    // Switch views
    if (savedView === 'cards') { tableWrap.style.display = 'none'; cardsGrid.style.display = 'grid'; }

    viewToggle.querySelectorAll('.view-toggle-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const view = btn.dataset.view;
        viewToggle.querySelectorAll('.view-toggle-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        localStorage.setItem('sv_candidate_view', view);
        if (view === 'cards') { tableWrap.style.display = 'none'; cardsGrid.style.display = 'grid'; }
        else { tableWrap.style.display = ''; cardsGrid.style.display = 'none'; }
      });
    });

    // Inline search
    const inlineSearch = document.getElementById('candidateInlineSearch');
    if (inlineSearch) {
      inlineSearch.addEventListener('input', () => {
        const q = inlineSearch.value.toLowerCase().trim();
        let visCount = 0;

        // Filter table rows
        rows.forEach(row => {
          const text = row.textContent.toLowerCase();
          const visible = !q || text.includes(q);
          row.style.display = visible ? '' : 'none';
          if (visible) visCount++;
        });

        // Filter cards
        cardsGrid.querySelectorAll('.candidate-card').forEach(card => {
          const matches = !q || card.dataset.name.includes(q) || card.dataset.position.includes(q) || card.dataset.election.includes(q);
          card.style.display = matches ? '' : 'none';
        });

        countEl.innerHTML = `<span>${q ? visCount : rows.length}</span> candidate${rows.length !== 1 ? 's' : ''}${q ? ` matching "<strong>${escHtml(q)}</strong>"` : ''}`;
      });
    }
  }

  /* ── 4. ELECTION INLINE SEARCH & STATUS FILTER ───── */
  initElectionFilters();

  function initElectionFilters() {
    const tableWrap = document.querySelector('.table-responsive');
    if (!tableWrap) return;
    const pageHeading = document.querySelector('.page-heading');
    if (!pageHeading || !pageHeading.textContent.toLowerCase().includes('election')) return;

    const cardPanel = tableWrap.closest('.card-panel');
    if (!cardPanel) return;

    const searchBar = document.createElement('div');
    searchBar.className = 'election-search-bar';
    searchBar.innerHTML = `
      <div class="election-search-wrap">
        <i class="bi bi-search"></i>
        <input type="text" class="election-search-input" placeholder="Search elections…" id="electionInlineSearch"/>
      </div>
      <div class="status-filter-btns">
        <button class="status-filter-btn active" data-filter="all">All</button>
        <button class="status-filter-btn" data-filter="upcoming">Upcoming</button>
        <button class="status-filter-btn" data-filter="active">Active</button>
        <button class="status-filter-btn" data-filter="closed">Closed</button>
      </div>
    `;
    cardPanel.insertBefore(searchBar, cardPanel.querySelector('.card-panel-body'));

    const rows = document.querySelectorAll('.table-custom tbody tr');
    let currentFilter = 'all';
    let currentSearch = '';

    function applyFilters() {
      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const statusBadge = row.querySelector('.badge-status');
        const status = statusBadge ? statusBadge.textContent.trim().toLowerCase() : '';
        const matchSearch = !currentSearch || text.includes(currentSearch);
        const matchFilter = currentFilter === 'all' || status.includes(currentFilter);
        row.style.display = (matchSearch && matchFilter) ? '' : 'none';
      });
    }

    document.getElementById('electionInlineSearch')?.addEventListener('input', (e) => {
      currentSearch = e.target.value.toLowerCase().trim();
      applyFilters();
    });

    searchBar.querySelectorAll('.status-filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        currentFilter = btn.dataset.filter;
        searchBar.querySelectorAll('.status-filter-btn').forEach(b => {
          b.classList.remove('active', 'btn-active-active', 'btn-active-upcoming', 'btn-active-closed');
        });
        btn.classList.add('active');
        if (currentFilter !== 'all') btn.classList.add(`btn-active-${currentFilter}`);
        applyFilters();
      });
    });

    // Add duration badge to each row
    rows.forEach(row => {
      const cells = row.querySelectorAll('td');
      const startTd = cells[3];
      const endTd   = cells[4];
      if (!startTd || !endTd) return;
      const start = new Date(startTd.textContent.trim());
      const end   = new Date(endTd.textContent.trim());
      if (isNaN(start) || isNaN(end)) return;
      const diff = Math.round((end - start) / (1000*60*60*24));
      const titleCell = cells[1];
      if (titleCell) {
        const dur = document.createElement('span');
        dur.className = 'election-duration';
        dur.innerHTML = `<i class="bi bi-clock me-1"></i>${diff === 1 ? '1 day' : diff + ' days'}`;
        titleCell.appendChild(dur);
      }
    });
  }

  /* ── 5. CONFIRM DELETE MODAL ENHANCEMENT ─────────── */
  // Intercept all delete links and use the modal instead of browser confirm
  document.querySelectorAll('.btn-action-delete[href]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const href = link.getAttribute('href');
      const modalEl = document.getElementById('confirmModal');
      const modalBtn = document.getElementById('confirmModalBtn');
      if (!modalEl || !modalBtn) return;
      const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
      const titleEl = document.getElementById('confirmModalTitle');
      const bodyEl  = document.getElementById('confirmModalBody');
      if (titleEl) titleEl.innerHTML = '<i class="bi bi-exclamation-triangle-fill text-danger me-2"></i>Delete Confirmation';
      if (bodyEl)  bodyEl.textContent = 'This action is permanent and cannot be undone. Are you sure you want to delete this record?';
      modalBtn.className = 'btn btn-danger fw-600';
      modalBtn.textContent = 'Yes, Delete';
      const onConfirm = () => { window.location.href = href; modalBtn.removeEventListener('click', onConfirm); };
      modalBtn.addEventListener('click', onConfirm);
      modal.show();
    });
  });

  /* ── 6. TIPS ──────────────────── */
  // Show hint on first visit
  if (!localStorage.getItem('sv_hint_shown')) {
    setTimeout(() => {
      showToast('💡 Welcome to SecureVote Admin!', 'info', 4000);
      localStorage.setItem('sv_hint_shown', '1');
    }, 1800);
  }

  /* ── 7. AUTO-REFRESH ACTIVE ELECTIONS BADGE ─────── */
  function checkElectionStatus() {
    const badges = document.querySelectorAll('.badge-status.badge-active');
    if (badges.length > 0) {
      // Could ping a status endpoint; for now just pulse active badges
      badges.forEach(b => { b.style.animation = 'none'; setTimeout(() => b.style.animation = '', 10); });
    }
  }
  setInterval(checkElectionStatus, 30000);

})();
