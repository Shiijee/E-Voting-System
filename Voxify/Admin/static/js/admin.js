// Admin JS — sidebar toggle + clock

window.addEventListener('DOMContentLoaded', () => {
  // ── Sidebar Toggle ──────────────────────────────────────────────────
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar       = document.getElementById('sidebar');
  const mainWrapper   = document.getElementById('mainWrapper');

  if (sidebarToggle && sidebar) {
    let backdrop = null;

    function isMobile() { return window.innerWidth <= 768; }

    function closeBackdrop() {
      document.body.style.overflow = '';
      if (backdrop) {
        backdrop.remove();
        backdrop = null;
      }
    }

    // ── Restore collapsed state from localStorage on page load ──────
    if (!isMobile() && localStorage.getItem('sidebarCollapsed') === 'true') {
      sidebar.classList.add('collapsed');
      if (mainWrapper) mainWrapper.classList.add('sidebar-collapsed');
    }
    // Remove the pre-paint no-transition helper class now that JS has taken over
    document.documentElement.classList.remove('sidebar-init-collapsed');
    // Re-enable transitions after the instant state is painted (no flash)
    requestAnimationFrame(() => {
      sidebar.style.transition = '';
      if (mainWrapper) mainWrapper.style.transition = '';
    });

    sidebarToggle.addEventListener('click', () => {
      if (isMobile()) {
        const isOpen = sidebar.classList.toggle('open');
        if (mainWrapper) mainWrapper.classList.toggle('open', isOpen);

        if (isOpen) {
          document.body.style.overflow = 'hidden';
          backdrop = document.createElement('div');
          backdrop.className = 'sidebar-backdrop';
          backdrop.addEventListener('click', () => {
            sidebar.classList.remove('open');
            if (mainWrapper) mainWrapper.classList.remove('open');
            closeBackdrop();
          });
          document.body.appendChild(backdrop);
        } else {
          closeBackdrop();
        }
      } else {
        sidebar.classList.add('transitioning');
        const isCollapsed = sidebar.classList.toggle('collapsed');
        setTimeout(() => sidebar.classList.remove('transitioning'), 250);
        if (mainWrapper) mainWrapper.classList.toggle('sidebar-collapsed', isCollapsed);
        // ── Persist state so nav clicks don't reset it ──────────────
        localStorage.setItem('sidebarCollapsed', isCollapsed ? 'true' : 'false');
      }
    });

    window.addEventListener('resize', () => {
      if (!isMobile()) {
        sidebar.classList.remove('open');
        if (mainWrapper) mainWrapper.classList.remove('open');
        closeBackdrop();
      } else {
        sidebar.classList.remove('collapsed');
        if (mainWrapper) mainWrapper.classList.remove('sidebar-collapsed');
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
  document.querySelectorAll('[data-bs-toggle="modal"]').forEach(btn => {
    btn.addEventListener('click', () => {
      if (!document.querySelector('.modal.show')) {
        document.querySelectorAll('.modal-backdrop').forEach(b => b.remove());
        document.body.classList.remove('modal-open');
        document.body.style.removeProperty('overflow');
        document.body.style.removeProperty('padding-right');
      }
    });
  });
});