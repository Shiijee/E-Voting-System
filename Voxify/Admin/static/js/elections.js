document.addEventListener('DOMContentLoaded', function () {
  window._elecPaginator = new SvPaginator({
    tableId:     'electionsTable',
    rowSelector: 'tbody tr',
    perPage:     10,
    infoId:      'electionsPagInfo',
    listId:      'electionsPagList',
    wrapId:      'electionsPagWrap'
  });

  const modalLabel   = document.getElementById('electionPositionsModalLabel');
  const modalContent = document.getElementById('electionPositionsModalContent');
  const pageData     = document.getElementById('electionPageData');
  const uploadsBase  = pageData ? pageData.dataset.uploadsUrl : '/admin/static/uploads/candidates/';

  // ── Inline candidate detail panel ────────────────────────────
  function showCandidateDetail(candidate, positionTitle) {
    const detailView    = document.getElementById('posModalDetailView');
    const detailContent = document.getElementById('candidateDetailContent');
    const posLabel      = document.getElementById('detailPositionLabel');

    if (posLabel) posLabel.textContent = positionTitle || '';

    const name    = (candidate.fullname || 'Candidate').trim();
    const initial = name[0].toUpperCase();

    const photoHtml = candidate.photo
      ? '<img src="' + uploadsBase + candidate.photo + '" '
        + 'style="width:100px;height:100px;border-radius:12px;object-fit:cover;border:2px solid var(--border);display:block;margin:0 auto 16px;">'
      : '<div style="width:100px;height:100px;border-radius:12px;background:var(--navy);color:var(--gold);display:flex;align-items:center;justify-content:center;font-family:\'Playfair Display\',serif;font-weight:700;font-size:2.2rem;margin:0 auto 16px;">' + initial + '</div>';

    detailContent.innerHTML =
      '<div style="text-align:center;">'
      + photoHtml
      + '<h5 style="font-family:\'Playfair Display\',serif;font-weight:700;margin:0 0 4px;">' + name + '</h5>'
      + '<p style="color:var(--muted);font-size:0.83rem;margin-bottom:20px;">Student ID: ' + (candidate.student_id || '—') + '</p>'
      + '</div>'
      + '<div style="border-top:1px solid var(--border);padding-top:16px;">'
      + '<p style="font-weight:600;font-size:0.88rem;margin-bottom:6px;">Platform / Campaign Statement</p>'
      + '<p style="color:var(--muted);font-size:0.87rem;line-height:1.6;margin:0;">' + (candidate.platform || 'No platform statement provided.') + '</p>'
      + '</div>';

    if (detailView) detailView.style.transform = 'translateX(0)';
  }

  window.closeCandidateDetail = function() {
    var detailView = document.getElementById('posModalDetailView');
    if (detailView) detailView.style.transform = 'translateX(100%)';
  };

  var posModal = document.getElementById('electionPositionsModal');
  if (posModal) {
    posModal.addEventListener('hidden.bs.modal', function() {
      var detailView = document.getElementById('posModalDetailView');
      if (detailView) detailView.style.transform = 'translateX(100%)';
    });
  }

  // ── Quick View: populate positions modal ─────────────────────
  document.querySelectorAll('.view-positions-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var electionId    = this.dataset.electionId;
      var electionTitle = this.dataset.electionTitle;

      if (modalLabel)   modalLabel.textContent = electionTitle || 'Election Positions';
      if (!modalContent) return;

      // Reset detail panel
      window.closeCandidateDetail();

      var dataContainer = document.getElementById('positions-data-' + electionId);
      if (!dataContainer) { modalContent.innerHTML = '<p style="color:var(--muted);padding:16px;">No positions found.</p>'; return; }

      var positionItems = dataContainer.querySelectorAll('.position-item');
      if (!positionItems.length) { modalContent.innerHTML = '<p style="color:var(--muted);padding:16px;">No positions found.</p>'; return; }

      var html = '';
      positionItems.forEach(function(item) {
        var title      = item.dataset.title || 'Unnamed Position';
        var candidates = [];
        try { candidates = JSON.parse(item.dataset.candidates || '[]'); } catch(e) {}

        html += '<div style="border:1px solid var(--border);border-radius:10px;overflow:hidden;margin-bottom:4px;">';
        html += '  <div style="background:var(--navy);padding:10px 16px;display:flex;align-items:center;justify-content:space-between;">';
        html += '    <span style="font-family:\'Playfair Display\',serif;font-weight:700;color:#fff;font-size:0.95rem;">' + title + '</span>';
        html += '    <span style="font-size:0.75rem;color:rgba(255,255,255,0.55);">' + candidates.length + ' candidate' + (candidates.length !== 1 ? 's' : '') + '</span>';
        html += '  </div>';

        if (candidates.length) {
          html += '  <div style="padding:8px 12px;display:flex;flex-direction:column;gap:4px;">';
          candidates.forEach(function(c) {
            var name    = ((c.firstname || '') + (c.middlename ? ' ' + c.middlename : '') + ' ' + (c.surname || '')).trim();
            var initial = (c.firstname || '?')[0].toUpperCase();
            var photo   = c.photo
              ? '<img src="' + uploadsBase + c.photo + '" style="width:36px;height:36px;border-radius:7px;object-fit:cover;border:1.5px solid var(--border);flex-shrink:0;">'
              : '<div style="width:36px;height:36px;border-radius:7px;background:var(--navy);color:var(--gold);display:flex;align-items:center;justify-content:center;font-family:\'Playfair Display\',serif;font-weight:700;font-size:0.9rem;flex-shrink:0;">' + initial + '</div>';

            html += '<div class="vx-cand-row" style="display:flex;align-items:center;gap:10px;padding:8px;border-radius:8px;cursor:pointer;transition:background 0.15s;"'
                  + ' data-position="' + title + '"'
                  + ' data-fullname="' + name + '"'
                  + ' data-student-id="' + (c.student_id || '') + '"'
                  + ' data-platform="' + ((c.platform || '').replace(/"/g, '&quot;')) + '"'
                  + ' data-photo="' + (c.photo || '') + '"'
                  + ' onmouseover="this.style.background=\'var(--paper)\'" onmouseout="this.style.background=\'transparent\'">'
                  + photo
                  + '<div style="flex:1;min-width:0;">'
                  + '  <div style="font-weight:600;font-size:0.88rem;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + name + '</div>'
                  + (c.partylist ? '<div style="font-size:0.75rem;color:var(--muted);">' + c.partylist + '</div>' : '')
                  + '</div>'
                  + '<i class="bi bi-chevron-right" style="font-size:0.72rem;color:var(--muted);flex-shrink:0;"></i>'
                  + '</div>';
          });
          html += '  </div>';
        } else {
          html += '  <div style="padding:12px 16px;font-size:0.85rem;color:var(--muted);">No candidates assigned.</div>';
        }
        html += '</div>';
      });

      modalContent.innerHTML = html;

      // Bind clicks — open inline detail panel, NOT a second modal
      modalContent.querySelectorAll('.vx-cand-row').forEach(function(row) {
        row.addEventListener('click', function() {
          showCandidateDetail({
            fullname:   this.dataset.fullname,
            student_id: this.dataset.studentId,
            platform:   this.dataset.platform,
            photo:      this.dataset.photo
          }, this.dataset.position);
        });
      });
    });
  });

});

(function() {
  var updateElement = document.getElementById('electionPageData');
  var updateUrl = updateElement ? updateElement.dataset.autoUpdateUrl : null;
  if (!updateUrl) return;

  function autoUpdate() {
    fetch(updateUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' } })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.opened > 0 || data.closed > 0) window.location.reload();
      })
      .catch(function() {});
  }

  setInterval(autoUpdate, 30000);
})();