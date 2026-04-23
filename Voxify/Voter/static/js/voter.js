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
  if (group) {
    // Remove selected from other candidates in same position
    document.querySelectorAll(`.candidate-card[data-group="${group}"]`)
      .forEach(c => c.classList.remove('selected'));
  }
  // Mark this card as selected
  cardElement.classList.add('selected');
  
  // Set the form input value
  const input = cardElement.querySelector(`input[name="position_${positionId}"]`);
  if (input) {
    input.value = candidateId;
  }
  
  updateConfirmBar();
}

function clearAllSelections() {
  document.querySelectorAll('.candidate-card.selected').forEach(c => {
    c.classList.remove('selected');
    // Clear form inputs
    const inputs = c.querySelectorAll('input[name^="position_"]');
    inputs.forEach(input => input.value = '');
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
  // Form submission handler
  const ballotForm = document.getElementById('ballotForm');
  if (ballotForm) {
    ballotForm.addEventListener('submit', (e) => {
      // Collect selected candidates
      const selected = document.querySelectorAll('.candidate-card.selected');
      if (selected.length === 0) {
        e.preventDefault();
        alert('Please select at least one candidate before submitting.');
        return;
      }
      // Form will submit normally with the selected candidates
    });
  }
});
