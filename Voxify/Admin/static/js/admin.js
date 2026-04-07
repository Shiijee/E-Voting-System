// Admin JS — sidebar toggle + clock

window.addEventListener('DOMContentLoaded', () => {
  // ── Sidebar Toggle ──────────────────────────────────────────────────
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar       = document.getElementById('sidebar');
  const mainWrapper   = document.getElementById('mainWrapper');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
      if (mainWrapper) mainWrapper.classList.toggle('collapsed');
    });
  }

  // ── Live Clock ──────────────────────────────────────────────────────
  const clockEl = document.getElementById('topbarTime');
  if (clockEl) {
    const tick = () => {
      const now = new Date();
      clockEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };
    tick();
    setInterval(tick, 1000);
  }

  // ── Clean up stale modal state on any modal-trigger click ──────────
  // (handles edge cases where a previous modal closed abnormally)
  document.querySelectorAll('[data-bs-toggle="modal"]').forEach(btn => {
    btn.addEventListener('click', () => {
      // Only clean up if no modal is currently shown
      if (!document.querySelector('.modal.show')) {
        document.querySelectorAll('.modal-backdrop').forEach(b => b.remove());
        document.body.classList.remove('modal-open');
        document.body.style.removeProperty('overflow');
        document.body.style.removeProperty('padding-right');
      }
    });
  });
});