// Admin JS — sidebar toggle + clock

window.addEventListener('DOMContentLoaded', () => {
  // ── Sidebar Toggle ──────────────────────────────────────────────────
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar       = document.getElementById('sidebar');
  const mainWrapper   = document.getElementById('mainWrapper');

  if (sidebarToggle && sidebar) {
    let backdrop = null;
    sidebarToggle.addEventListener('click', () => {
      const isOpen = sidebar.classList.toggle('open');
      if (mainWrapper) mainWrapper.classList.toggle('open');
      
      if (window.innerWidth <= 768) {
        if (isOpen) {
          document.body.style.overflow = 'hidden';
          backdrop = document.createElement('div');
          backdrop.className = 'sidebar-backdrop';
          backdrop.style.cssText = `
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 199;
          `;
          backdrop.addEventListener('click', () => {
            sidebar.classList.remove('open');
            if (mainWrapper) mainWrapper.classList.remove('open');
            document.body.style.overflow = '';
            if (backdrop) {
              document.body.removeChild(backdrop);
              backdrop = null;
            }
          });
          document.body.appendChild(backdrop);
        } else {
          document.body.style.overflow = '';
          if (backdrop) {
            document.body.removeChild(backdrop);
            backdrop = null;
          }
        }
      }
    });

    window.addEventListener('resize', () => {
      if (window.innerWidth > 768 && backdrop) {
        sidebar.classList.remove('open');
        if (mainWrapper) mainWrapper.classList.remove('open');
        document.body.removeChild(backdrop);
        backdrop = null;
      }
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