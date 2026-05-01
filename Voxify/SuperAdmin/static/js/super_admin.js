/* ─── Voxify Super Admin JS ───────────────────────── */

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
      if (backdrop) { backdrop.remove(); backdrop = null; }
    }

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
        const isCollapsed = sidebar.classList.toggle('collapsed');
        if (mainWrapper) mainWrapper.classList.toggle('sidebar-collapsed', isCollapsed);
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
      clockEl.textContent = new Date().toLocaleTimeString('en-US', {
        hour: '2-digit', minute: '2-digit', second: '2-digit'
      });
    };
    tick();
    setInterval(tick, 1000);
  }

  // ── Generic confirm modal wiring ────────────────────────────────────
  const confirmModal = document.getElementById('confirmModal');
  if (confirmModal) {
    const bsModal   = new bootstrap.Modal(confirmModal);
    const confirmBtn = document.getElementById('confirmModalBtn');
    let pendingCallback = null;

    document.querySelectorAll('[data-confirm]').forEach(btn => {
      btn.addEventListener('click', e => {
        e.preventDefault();
        const title   = btn.dataset.confirmTitle   || 'Confirm Action';
        const message = btn.dataset.confirmMessage || 'Are you sure?';
        document.getElementById('confirmModalTitle').textContent = title;
        document.getElementById('confirmModalBody').textContent  = message;
        pendingCallback = () => {
          const form = btn.closest('form');
          if (form) form.submit();
          else if (btn.dataset.href) window.location.href = btn.dataset.href;
          else if (btn.tagName === 'A' && btn.href && btn.href !== '#') window.location.href = btn.href;
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

  // ── Clean up stale modal state ──────────────────────────────────────
  document.querySelectorAll('[data-bs-toggle="modal"]').forEach(btn => {
    btn.addEventListener('click', () => {
      if (!document.querySelector('.modal.show')) {
        document.querySelectorAll('.modal-backdrop').forEach(b => b.remove());
        document.body.classList.remove('modal-open');
      }
    });
  });

  // ── Focus first input in modal when shown ───────────────────────────
  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('shown.bs.modal', () => {
      const firstInput = modal.querySelector('input:not([type="hidden"]), select, textarea');
      if (firstInput) firstInput.focus();
    });
  });

  // ── Flash message auto-dismiss ──────────────────────────────────────
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 500);
    }, 4000);
  });

}); // end DOMContentLoaded