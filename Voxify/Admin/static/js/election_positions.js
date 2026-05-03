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

  var pageData    = document.getElementById('electionPosPageData');
  var uploadsBase = pageData ? pageData.dataset.uploadsUrl : '/admin/static/uploads/candidates/';

  document.querySelectorAll('.view-candidate-info').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var fullname  = this.dataset.fullname;
      var studentId = this.dataset.studentId;
      var platform  = this.dataset.platform;
      var photo     = this.dataset.photo;

      var photoHtml = photo
        ? '<img src="' + uploadsBase + photo + '" alt="' + fullname + '"'
          + ' style="width:110px;height:110px;border-radius:12px;object-fit:cover;display:block;margin:0 auto 14px;border:2px solid var(--border);">'
        : '<div style="width:110px;height:110px;border-radius:12px;background:var(--navy);color:var(--gold);'
          + 'display:flex;align-items:center;justify-content:center;margin:0 auto 14px;'
          + "font-family:'Playfair Display',serif;font-weight:700;font-size:2.4rem;"
          + '">'
          + (fullname ? fullname[0].toUpperCase() : '?')
          + '</div>';

      var platformHtml = platform
        ? '<div style="margin-top:14px;padding-top:14px;border-top:1px solid var(--border);">'
          + '<p style="font-weight:600;font-size:0.88rem;margin-bottom:6px;">Platform / Campaign Statement</p>'
          + '<p style="color:var(--muted);font-size:0.87rem;line-height:1.6;margin:0;">' + platform + '</p></div>'
        : '<div style="margin-top:14px;padding-top:14px;border-top:1px solid var(--border);">'
          + '<p style="color:var(--muted);font-size:0.87rem;margin:0;">No platform statement provided.</p></div>';

      contentDiv.innerHTML =
        '<div style="text-align:center;">'
        + photoHtml
        + '<h5 style="font-family:\'Playfair Display\',serif;font-weight:700;margin:0 0 4px;">' + fullname + '</h5>'
        + '<p style="color:var(--muted);font-size:0.83rem;margin:0;">Student ID: ' + studentId + '</p>'
        + '</div>'
        + platformHtml;

      openCandidateModal();
    });
  });
});