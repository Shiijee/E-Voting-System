function closeFlashMessage(button) {
  button.parentElement.remove();
}

function confirmDelete() {
  return confirm('Delete this college? This cannot be undone.');
}