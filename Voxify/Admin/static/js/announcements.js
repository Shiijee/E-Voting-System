/* announcements.js — Voxify Admin */

document.addEventListener('DOMContentLoaded', function () {

  /* ── Search + Filter ──────────────────────────────── */
  const searchInput    = document.getElementById('annSearchInput');
  const typeFilter     = document.getElementById('annTypeFilter');
  const statusFilter   = document.getElementById('annStatusFilter');
  const rows           = () => document.querySelectorAll('#annTableBody .ann-row');

  function filterTable() {
    const q      = (searchInput?.value || '').toLowerCase();
    const type   = typeFilter?.value || '';
    const status = statusFilter?.value || '';

    rows().forEach(row => {
      const matchText   = !q      || row.dataset.text.includes(q);
      const matchType   = !type   || row.dataset.type === type;
      const matchStatus = !status || row.dataset.status === status;
      row.style.display = (matchText && matchType && matchStatus) ? '' : 'none';
    });
  }

  searchInput?.addEventListener('input', filterTable);
  typeFilter?.addEventListener('change', filterTable);
  statusFilter?.addEventListener('change', filterTable);

  /* ── Char counter ─────────────────────────────────── */
  const bodyTA   = document.getElementById('annFormBody');
  const charCnt  = document.getElementById('annCharCount');
  if (bodyTA && charCnt) {
    bodyTA.addEventListener('input', () => {
      charCnt.textContent = bodyTA.value.length;
    });
  }

  /* ── Create/Edit Modal ────────────────────────────── */
  const annModal    = document.getElementById('announcementModal');
  const annForm     = document.getElementById('annForm');
  const annFormId   = document.getElementById('annFormId');
  const annFormTitle = document.getElementById('annFormTitle');
  const annFormType  = document.getElementById('annFormType');
  const annFormBody  = document.getElementById('annFormBody');
  const annModalTitle = document.getElementById('annModalTitle');
  const annFormSubmit = document.getElementById('annFormSubmit');

  // Reset modal when opened fresh via "New Announcement" button
  annModal?.addEventListener('show.bs.modal', function (event) {
    // Only reset if triggered by the "New Announcement" button (not edit)
    if (!event.relatedTarget || event.relatedTarget.classList.contains('btn-edit-ann')) return;
    annModalTitle.textContent = 'New Announcement';
    annForm.action = '/admin/announcements/create';
    annFormId.value = '';
    annFormTitle.value = '';
    annFormType.value = 'general';
    annFormBody.value = '';
    if (charCnt) charCnt.textContent = '0';
    document.getElementById('statusDraft').checked = true;
  });

  // Edit buttons
  document.querySelectorAll('.btn-edit-ann').forEach(btn => {
    btn.addEventListener('click', function () {
      const id     = this.dataset.id;
      const title  = this.dataset.title;
      const type   = this.dataset.type;
      const body   = this.dataset.body;
      const status = this.dataset.status;

      annModalTitle.textContent = 'Edit Announcement';
      annForm.action = `/admin/announcements/${id}/edit`;
      annFormId.value = id;
      annFormTitle.value = title;
      annFormType.value = type;
      annFormBody.value = body;
      if (charCnt) charCnt.textContent = body.length;
      document.getElementById(status === 'published' ? 'statusPublished' : 'statusDraft').checked = true;

      bootstrap.Modal.getOrCreateInstance(annModal).show();
    });
  });

  // Submit form
  annFormSubmit?.addEventListener('click', function () {
    if (!annFormTitle.value.trim() || !annFormBody.value.trim()) {
      alert('Please fill in the title and message.');
      return;
    }
    annForm.submit();
  });

  /* ── View Modal ───────────────────────────────────── */
  const viewModal      = document.getElementById('annViewModal');
  const viewTitle      = document.getElementById('annViewTitle');
  const viewBody       = document.getElementById('annViewBody');
  const viewTypeBadge  = document.getElementById('annViewTypeBadge');
  const viewStatusBadge = document.getElementById('annViewStatusBadge');

  const typeIconMap = {
    general: 'bi-info-circle',
    election: 'bi-calendar2-event',
    winner: 'bi-trophy',
    reminder: 'bi-bell'
  };

  document.querySelectorAll('.btn-view-ann').forEach(btn => {
    btn.addEventListener('click', function () {
      const title  = this.dataset.title;
      const body   = this.dataset.body;
      const type   = this.dataset.type;
      const status = this.dataset.status;

      viewTitle.textContent = title;
      viewBody.textContent  = body;

      const icon = typeIconMap[type] || 'bi-megaphone';
      viewTypeBadge.className  = `ann-type-badge ann-type-${type}`;
      viewTypeBadge.innerHTML  = `<i class="bi ${icon}"></i> ${type.charAt(0).toUpperCase() + type.slice(1)}`;

      viewStatusBadge.className = `ann-status-badge ann-status-${status}`;
      viewStatusBadge.textContent = status.charAt(0).toUpperCase() + status.slice(1);

      bootstrap.Modal.getOrCreateInstance(viewModal).show();
    });
  });

  /* ── Auto-Announce Winner ─────────────────────────── */
  const autoAnnBtn       = document.getElementById('autoAnnounceBtn');
  const autoAnnModal     = document.getElementById('autoAnnModal');
  const electionSelect   = document.getElementById('autoAnnElectionSelect');
  const previewDiv       = document.getElementById('autoAnnPreview');
  const previewTitleEl   = document.getElementById('autoAnnPreviewTitle');
  const previewBodyEl    = document.getElementById('autoAnnPreviewBody');
  const autoAnnSaveBtn   = document.getElementById('autoAnnSaveBtn');

  autoAnnBtn?.addEventListener('click', function () {
    bootstrap.Modal.getOrCreateInstance(autoAnnModal).show();
  });

  electionSelect?.addEventListener('change', function () {
    const electionId = this.value;
    if (!electionId) {
      previewDiv.classList.add('d-none');
      autoAnnSaveBtn.disabled = true;
      return;
    }

    // Fetch winner data from the server
    fetch(`/admin/announcements/winner-preview?election_id=${electionId}`)
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          previewDiv.classList.add('d-none');
          autoAnnSaveBtn.disabled = true;
          alert(data.error);
          return;
        }
        previewTitleEl.textContent = data.title;
        previewBodyEl.textContent  = data.body;
        previewDiv.classList.remove('d-none');
        autoAnnSaveBtn.disabled = false;
      })
      .catch(() => {
        alert('Failed to load winner data. Please try again.');
      });
  });

  autoAnnSaveBtn?.addEventListener('click', function () {
    const electionId = electionSelect.value;
    if (!electionId) return;

    fetch(`/admin/announcements/winner-create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ election_id: electionId })
    })
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          window.location.reload();
        } else {
          alert(data.error || 'Failed to create announcement.');
        }
      })
      .catch(() => alert('Request failed. Please try again.'));
  });
});
