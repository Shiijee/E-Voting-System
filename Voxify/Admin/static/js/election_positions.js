function openCandidateModal() {
  var el = document.getElementById('candidateDetailModal');
  if (!el) return;
  el.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeCandidateModal() {
  var el = document.getElementById('candidateDetailModal');
  if (!el) return;
  el.classList.remove('open');
  document.body.style.overflow = '';
}

document.addEventListener('DOMContentLoaded', function() {
  var modalOverlay = document.getElementById('candidateDetailModal');
  if (modalOverlay) {
    modalOverlay.addEventListener('click', function(e) {
      if (e.target === this) closeCandidateModal();
    });
  }

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeCandidateModal();
  });

  var contentDiv = document.getElementById('candidateDetailContent');
  if (!contentDiv) return;

  document.querySelectorAll('.view-candidate-info').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var fullname  = this.dataset.fullname;
      var studentId = this.dataset.studentId;
      var platform  = this.dataset.platform;
      var photo     = this.dataset.photo;

      var photoHtml = '';
      if (photo) {
        photoHtml = '<img src="/admin/static/uploads/candidates/' + photo + '" alt="' + fullname + '"'
                  + ' style="width:150px;height:150px;border-radius:50%;object-fit:cover;margin-bottom:15px;"/>';
      } else {
        photoHtml = '<div style="width:150px;height:150px;border-radius:50%;background:#e9ecef;'
                  + 'display:flex;align-items:center;justify-content:center;margin:0 auto 15px;'
                  + 'font-size:3rem;color:#6c757d;">'
                  + (fullname ? fullname[0].toUpperCase() : '?')
                  + '</div>';
      }

      var platformHtml = platform
        ? '<div class="mt-3"><p><strong>Platform/Campaign Statement:</strong></p><p style="color:var(--muted)">' + platform + '</p></div>'
        : '<div class="mt-3"><p style="color:var(--muted)">No platform statement provided.</p></div>';

      contentDiv.innerHTML = '
        <div>
          ' + photoHtml + '
          <h5 class="mb-1">' + fullname + '</h5>
          <p style="color:var(--muted);margin-bottom:12px;">Student ID: ' + studentId + '</p>
          ' + platformHtml + '
        </div>
      ';

      openCandidateModal();
    });
  });
});
