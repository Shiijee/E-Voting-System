document.addEventListener('DOMContentLoaded', function () {
  window._elecPaginator = new SvPaginator({
    tableId:     'electionsTable',
    rowSelector: 'tbody tr',
    perPage:     10,
    infoId:      'electionsPagInfo',
    listId:      'electionsPagList',
    wrapId:      'electionsPagWrap'
  });

  const modalLabel = document.getElementById('electionPositionsModalLabel');
  const modalContent = document.getElementById('electionPositionsModalContent');
  const candidateModal = new bootstrap.Modal(document.getElementById('candidateInfoModal'));
  const candidateInfoContent = document.getElementById('candidateInfoContent');
  const candidateInfoModalLabel = document.getElementById('candidateInfoModalLabel');

  function showCandidateInfo(candidate) {
    candidateInfoModalLabel.textContent = candidate.fullname || 'Candidate Information';

    let photoHtml = '';
    if (candidate.photo) {
      photoHtml = '<img src="/admin/static/uploads/candidates/' + candidate.photo + '" alt="' + candidate.fullname + '" '
                + 'style="width: 150px; height: 150px; border-radius: 50%; object-fit: cover; margin-bottom: 15px;"/>';
    } else {
      photoHtml = '<div style="width: 150px; height: 150px; border-radius: 50%; background: #e9ecef; '
                + 'display: flex; align-items: center; justify-content: center; margin: 0 auto 15px; font-size: 3rem; color: #6c757d;">'
                + (candidate.fullname ? candidate.fullname[0].toUpperCase() : '?')
                + '</div>';
    }

    const details = '<div class="text-start">'
                  + '  ' + photoHtml
                  + '  <h5 class="mb-1">' + (candidate.fullname || 'Candidate') + '</h5>'
                  + '  <p style="color:var(--muted);margin-bottom:12px;">Student ID: ' + (candidate.student_id || '—') + '</p>'
                  + '  <div class="mt-3"><p><strong>Platform/Campaign Statement:</strong></p><p style="color:var(--muted);">'
                  + (candidate.platform || 'No platform statement provided.') + '</p></div>'
                  + '</div>';

    if (candidateInfoContent) candidateInfoContent.innerHTML = details;
    candidateModal.show();
  }

  document.querySelectorAll('.view-candidate-info').forEach(function(btn) {
    btn.addEventListener('click', function() {
      const candidate = {
        fullname: this.dataset.fullname,
        student_id: this.dataset.studentId,
        platform: this.dataset.platform,
        photo: this.dataset.photo
      };
      showCandidateInfo(candidate);
    });
  });
});

(function() {
  const updateElement = document.getElementById('electionPageData');
  const updateUrl = updateElement ? updateElement.dataset.autoUpdateUrl : null;
  if (!updateUrl) return;

  function autoUpdate() {
    fetch(updateUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' } })
      .then(r => r.json())
      .then(data => {
        if (data.opened > 0 || data.closed > 0) {
          window.location.reload();
        }
      })
      .catch(() => {});
  }

  setInterval(autoUpdate, 30000);
})();
