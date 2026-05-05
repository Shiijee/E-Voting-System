function selectCandidate(card, positionId, candidateId) {
  var group = card.getAttribute('data-group');
  var positionInput = document.getElementById('position_input_' + positionId);
  var cards = document.querySelectorAll('.candidate-card[data-group="' + group + '"]');
  var selectedCount = 0;
  var isAlreadySelected = card.classList.contains('selected');

  cards.forEach(function(c) {
    c.classList.remove('selected');
  });

  if (isAlreadySelected) {
    positionInput.value = '';
  } else {
    card.classList.add('selected');
    positionInput.value = candidateId;
  }

  // Update selected count
  var allInputs = document.querySelectorAll('input[type="hidden"][name^="position_"]');
  allInputs.forEach(function(inp) {
    if (inp.value) selectedCount++;
  });

  document.getElementById('selectedCount').textContent = selectedCount;
  document.getElementById('voteConfirmBar').style.display = selectedCount > 0 ? 'flex' : 'none';
}

function clearAllSelections() {
  var cards = document.querySelectorAll('.candidate-card.selected');
  var inputs = document.querySelectorAll('input[type="hidden"][name^="position_"]');

  cards.forEach(function(c) { c.classList.remove('selected'); });
  inputs.forEach(function(inp) { inp.value = ''; });

  document.getElementById('selectedCount').textContent = '0';
  document.getElementById('voteConfirmBar').style.display = 'none';
}
function toggleInstructions(btn) {
  const body = document.getElementById('instructionsBody');
  const isCollapsed = body.classList.toggle('collapsed');
  btn.classList.toggle('collapsed', isCollapsed);
}