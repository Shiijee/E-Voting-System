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
      const now = new Date();
      clockEl.textContent = now.toLocaleTimeString('en-US', {
        hour: '2-digit', minute: '2-digit', second: '2-digit'
      });
    };
    tick();
    setInterval(tick, 1000);
  }

}); // end DOMContentLoaded

// ── Candidate selection (ballot page) ────────────────
function selectCandidate(cardElement, positionId, candidateId) {
  const group = cardElement.dataset.group;
  const input = document.getElementById(`position_input_${positionId}`);
  const isAlreadySelected = cardElement.classList.contains('selected');

  if (group) {
    // Deselect all cards in the same position group
    document.querySelectorAll(`.candidate-card[data-group="${group}"]`)
      .forEach(c => c.classList.remove('selected'));
  }

  if (isAlreadySelected) {
    // Toggle OFF — unselect this candidate
    cardElement.classList.remove('selected');
    if (input) input.value = '';
  } else {
    // Select this candidate
    cardElement.classList.add('selected');
    if (input) input.value = candidateId;
  }

  updateConfirmBar();
}

function clearAllSelections() {
  document.querySelectorAll('.candidate-card.selected').forEach(c => {
    c.classList.remove('selected');
  });
  document.querySelectorAll('input[id^="position_input_"]').forEach(input => {
    input.value = '';
  });
  document.getElementById('voteConfirmBar').style.display = 'none';
}

function updateConfirmBar() {
  const bar   = document.getElementById('voteConfirmBar');
  const count = document.getElementById('selectedCount');
  if (!bar || !count) return;
  const selected = document.querySelectorAll('.candidate-card.selected').length;
  count.textContent = selected;
  bar.style.display = selected > 0 ? 'flex' : 'none';
}

document.addEventListener('DOMContentLoaded', () => {
  const ballotForm = document.getElementById('ballotForm');
  if (ballotForm) {
    ballotForm.addEventListener('submit', (e) => {
      const selected = document.querySelectorAll('.candidate-card.selected').length;
      if (selected === 0) {
        e.preventDefault();
        alert('Please select at least one candidate before submitting.');
      }
      // If at least 1 is selected, allow submit — unselected positions are simply skipped
    });
  }
});