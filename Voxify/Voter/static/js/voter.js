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