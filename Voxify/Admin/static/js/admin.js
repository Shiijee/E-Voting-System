// Minimal admin JS placeholder
// This file is referenced by admin templates for basic UI interactivity.

window.addEventListener('DOMContentLoaded', () => {
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const mainWrapper = document.getElementById('mainWrapper');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
      mainWrapper.classList.toggle('collapsed');
    });
  }

  // Confirmation modal for destructive actions
  const confirmModal = document.getElementById('confirmModal');
  if (confirmModal) {
    const bsModal = new bootstrap.Modal(confirmModal);
    const confirmBtn = document.getElementById('confirmModalBtn');
    let pendingAction = null;

    document.querySelectorAll('[data-confirm]').forEach(el => {
      el.addEventListener('click', event => {
        event.preventDefault();
        const title = el.dataset.confirmTitle || 'Confirm Action';
        const message = el.dataset.confirmMessage || 'Are you sure?';

        document.getElementById('confirmModalTitle').textContent = title;
        document.getElementById('confirmModalBody').textContent = message;

        pendingAction = () => {
          if (el.tagName.toLowerCase() === 'a' && el.href) {
            window.location.href = el.href;
          } else if (el.tagName.toLowerCase() === 'button') {
            const form = el.closest('form');
            if (form) form.submit();
          }
        };

        bsModal.show();
      });
    });

    if (confirmBtn) {
      confirmBtn.addEventListener('click', () => {
        bsModal.hide();
        if (pendingAction) {
          pendingAction();
          pendingAction = null;
        }
      });
    }
  }
});
