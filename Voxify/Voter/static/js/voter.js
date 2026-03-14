// ── Sidebar toggle ───────────────────────────────────
const sidebar      = document.getElementById('sidebar');
const mainWrapper  = document.getElementById('mainWrapper');
const sidebarToggle = document.getElementById('sidebarToggle');

if (sidebarToggle) {
  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
  });
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', (e) => {
  if (window.innerWidth <= 900 &&
      sidebar && sidebar.classList.contains('open') &&
      !sidebar.contains(e.target) &&
      !sidebarToggle.contains(e.target)) {
    sidebar.classList.remove('open');
  }
});

// ── Live clock ────────────────────────────────────────
function updateClock() {
  const el = document.getElementById('topbarTime');
  if (!el) return;
  const now = new Date();
  el.textContent = now.toLocaleTimeString('en-US', {
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  });
}
updateClock();
setInterval(updateClock, 1000);

// ── Candidate selection (ballot page) ────────────────
document.addEventListener('DOMContentLoaded', () => {
  const cards = document.querySelectorAll('.candidate-card');
  cards.forEach(card => {
    card.addEventListener('click', () => {
      const group = card.dataset.group;
      if (group) {
        document.querySelectorAll(`.candidate-card[data-group="${group}"]`)
          .forEach(c => c.classList.remove('selected'));
      }
      card.classList.toggle('selected');
      updateConfirmBar();
    });
  });

  function updateConfirmBar() {
    const bar   = document.getElementById('voteConfirmBar');
    const count = document.getElementById('selectedCount');
    if (!bar || !count) return;
    const selected = document.querySelectorAll('.candidate-card.selected').length;
    count.textContent = selected;
    bar.style.display = selected > 0 ? 'flex' : 'none';
  }
});
