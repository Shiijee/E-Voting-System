function setRole(btn, role) {
  document.querySelectorAll('.role-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  const label = document.getElementById('id-label');
  const input = document.getElementById('id-input');

  if (role === 'admin') {
    label.textContent = 'Admin Username';
    input.placeholder = 'Enter admin username';
  } else {
    label.textContent = 'Voter ID / Email';
    input.placeholder = 'Enter your voter ID or email';
  }
}

function togglePassword(passwordId, iconId) {
  const pwd = document.getElementById(passwordId);
  const icon = document.getElementById(iconId);
  if (!pwd || !icon) return;

  const showSrc = icon.dataset.show;
  const hideSrc = icon.dataset.hide;

  if (pwd.type === 'password') {
    pwd.type = 'text';
    icon.src = showSrc || icon.src;
    icon.alt = 'Hide password';
  } else {
    pwd.type = 'password';
    icon.src = hideSrc || icon.src;
    icon.alt = 'Show password';
  }
}

// Check if user is logged in when page loads
window.addEventListener('load', function() {
    // You can add a check here if needed
});

// Prevent form resubmission on page refresh
if (window.history.replaceState) {
    window.history.replaceState(null, null, window.location.href);
}
