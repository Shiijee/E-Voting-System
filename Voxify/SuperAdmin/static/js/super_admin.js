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

  // ── Live Clock (12-hour AM/PM) ─────────────────────────────────────
  const clockEl = document.getElementById('topbarTime');
  if (clockEl) {
    const tick = () => {
      clockEl.textContent = new Date().toLocaleTimeString('en-US', {
        hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true
      });
    };
    tick();
    setInterval(tick, 1000);
  }

  // ── Format all DB timestamps to 12-hour AM/PM ───────────────────────
  // Any element with class "db-ts" or data-ts attribute will be formatted.
  // We also auto-detect plain text nodes inside .text-muted-sm <td> cells
  // that look like a MySQL datetime (YYYY-MM-DD HH:MM:SS).
  function formatDbTimestamp(raw) {
    if (!raw) return raw;
    // MySQL datetime: "2026-05-02 23:37:53"  →  "May 02, 2026, 11:37:53 PM"
    const m = raw.trim().match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})/);
    if (!m) return raw;
    const dt = new Date(m[1], m[2]-1, m[3], m[4], m[5], m[6]);
    if (isNaN(dt)) return raw;
    return dt.toLocaleString('en-US', {
      year: 'numeric', month: 'short', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true
    });
  }

  // Walk all <td> and <span> elements and reformat any raw MySQL timestamps
  document.querySelectorAll('td, span, .activity-time, code').forEach(el => {
    // Only leaf-level text nodes (no child elements except <i>)
    const children = Array.from(el.childNodes);
    const hasElementChildren = children.some(n => n.nodeType === 1 && n.tagName !== 'I');
    if (hasElementChildren) return;
    const txt = el.textContent.trim();
    const formatted = formatDbTimestamp(txt);
    if (formatted !== txt) el.textContent = formatted;
  });

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