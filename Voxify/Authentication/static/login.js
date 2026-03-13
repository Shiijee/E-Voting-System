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