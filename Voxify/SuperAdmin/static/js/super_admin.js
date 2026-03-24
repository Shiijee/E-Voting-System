/* ─── Voxify Super Admin JS ───────────────────────── */

// Sidebar toggle
const sidebar      = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
if (sidebarToggle && sidebar) {
  sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  document.addEventListener('click', e => {
    if (window.innerWidth <= 900 && !sidebar.contains(e.target) && e.target !== sidebarToggle) {
      sidebar.classList.remove('open');
    }
  });
}

// Live clock in topbar
function updateClock () {
  const el = document.getElementById('topbarTime');
  if (!el) return;
  el.textContent = new Date().toLocaleTimeString('en-US', {
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  });
}
updateClock();
setInterval(updateClock, 1000);

// Generic confirm modal wiring
const confirmModal = document.getElementById('confirmModal');
if (confirmModal) {
  const bsModal = new bootstrap.Modal(confirmModal);
  const confirmBtn = document.getElementById('confirmModalBtn');
  let pendingCallback = null;

  document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', () => {
      const title   = btn.dataset.confirmTitle   || 'Confirm Action';
      const message = btn.dataset.confirmMessage || 'Are you sure?';
      document.getElementById('confirmModalTitle').textContent = title;
      document.getElementById('confirmModalBody').textContent  = message;
      pendingCallback = () => {
        const form = btn.closest('form');
        if (form) form.submit();
        else if (btn.dataset.href) window.location.href = btn.dataset.href;
      };
      bsModal.show();
    });
  });

  if (confirmBtn) {
    confirmBtn.addEventListener('click', () => {
      bsModal.hide();
      if (pendingCallback) { pendingCallback(); pendingCallback = null; }
    });
  }
}

// Flash message auto-dismiss
document.querySelectorAll('.alert').forEach(alert => {
  setTimeout(() => {
    alert.style.transition = 'opacity 0.5s';
    alert.style.opacity = '0';
    setTimeout(() => alert.remove(), 500);
  }, 4000);
});