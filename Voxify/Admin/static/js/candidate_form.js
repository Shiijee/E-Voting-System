function previewPhoto(input) {
  const preview = document.getElementById('photoPreview');
  const placeholder = document.getElementById('uploadPlaceholder');
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = e => {
      preview.src = e.target.result;
      preview.classList.remove('d-none');
      placeholder.classList.add('d-none');
    };
    reader.readAsDataURL(input.files[0]);
  }
}

document.addEventListener('DOMContentLoaded', function() {
  const uploadArea = document.getElementById('uploadArea');
  const photoInput = document.getElementById('photoInput');

  if (!uploadArea || !photoInput) return;

  function filterPositions(autoSelect) {
    const electionSelect = document.getElementById('electionSelect');
    const positionSelect = document.getElementById('positionSelect');
    if (!electionSelect || !positionSelect) return;

    const electionId = electionSelect.value;
    Array.from(positionSelect.options).forEach(option => {
      if (!option.value) {
        option.hidden = false;
        option.disabled = false;
        return;
      }
      const optionElectionId = option.dataset.electionId || '';
      const show = !electionId || optionElectionId === electionId;
      option.hidden = !show;
      option.disabled = !show;
    });

    if (autoSelect && electionSelect.value) {
      const firstVisible = Array.from(positionSelect.options).find(o => !o.disabled && o.value);
      positionSelect.value = firstVisible ? firstVisible.value : '';
    }
  }

  const electionSelect = document.getElementById('electionSelect');
  const positionSelect = document.getElementById('positionSelect');
  if (electionSelect && positionSelect) {
    electionSelect.addEventListener('change', function() { filterPositions(true); });
    filterPositions(false);
  }

  uploadArea.addEventListener('click', () => photoInput.click());
  photoInput.addEventListener('change', function() { previewPhoto(this); });

  uploadArea.addEventListener('dragover', e => {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
    uploadArea.style.backgroundColor = '#f8f9fa';
  });

  uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('drag-over');
    uploadArea.style.backgroundColor = '';
  });

  uploadArea.addEventListener('drop', e => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    uploadArea.style.backgroundColor = '';
    const files = e.dataTransfer.files;
    if (files.length) {
      photoInput.files = files;
      previewPhoto(photoInput);
    }
  });
});