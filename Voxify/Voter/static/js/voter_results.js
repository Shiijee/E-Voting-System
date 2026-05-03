function submitElectionForm(selectElement) {
  selectElement.form.submit();
}

/* ── Position Tab Switching ──────────────────────────── */
function switchTab(btn) {
  document.querySelectorAll('.results-tab').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');

  const target = btn.dataset.target;
  const cards = document.querySelectorAll('.result-position-card');

  cards.forEach(card => {
    if (target === 'all') {
      card.style.display = '';
    } else {
      card.style.display = card.id === target ? '' : 'none';
    }
  });

  // Re-run search filter if active
  const searchVal = document.getElementById('candidateSearch');
  if (searchVal && searchVal.value.trim()) filterResults();
}

/* ── Candidate Search ────────────────────────────────── */
function filterResults() {
  const input = document.getElementById('candidateSearch');
  const clearBtn = document.getElementById('searchClearBtn');
  const query = input.value.trim().toLowerCase();

  clearBtn.style.display = query ? 'block' : 'none';

  const cards = document.querySelectorAll('.result-position-card');
  let anyVisible = false;

  // Respect active tab
  const activeTab = document.querySelector('.results-tab.active');
  const tabTarget = activeTab ? activeTab.dataset.target : 'all';

  cards.forEach(card => {
    // If tab is filtering, skip hidden cards
    if (tabTarget !== 'all' && card.id !== tabTarget) {
      card.style.display = 'none';
      return;
    }

    if (!query) {
      card.style.display = '';
      card.querySelectorAll('.result-row').forEach(row => row.style.display = '');
      anyVisible = true;
      return;
    }

    const rows = card.querySelectorAll('.result-row');
    let cardHasMatch = false;

    rows.forEach(row => {
      const name = row.dataset.candidateName || '';
      if (name.includes(query)) {
        row.style.display = '';
        cardHasMatch = true;
      } else {
        row.style.display = 'none';
      }
    });

    card.style.display = cardHasMatch ? '' : 'none';
    if (cardHasMatch) anyVisible = true;
  });

  const noResults = document.getElementById('noSearchResults');
  if (noResults) noResults.style.display = anyVisible ? 'none' : '';
}

function clearSearch() {
  const input = document.getElementById('candidateSearch');
  input.value = '';
  filterResults();
  input.focus();
}