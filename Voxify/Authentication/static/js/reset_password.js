/* ── Toggle show/hide password ──────────────────────────────────── */
function togglePassword(fieldId, iconId) {
  const field = document.getElementById(fieldId);
  const icon  = document.getElementById(iconId);
  if (field.type === 'password') {
    field.type = 'text';
    icon.src = icon.getAttribute('data-show');
  } else {
    field.type = 'password';
    icon.src = icon.getAttribute('data-hide');
  }
}

/* ── DOM refs ────────────────────────────────────────────────────── */
const npField   = document.getElementById('new_password');
const cpField   = document.getElementById('confirm_password');
const matchMsg  = document.getElementById('match-msg');
const submitBtn = document.getElementById('submit-btn');
const wrapper   = document.getElementById('strength-wrapper');
const label     = document.getElementById('strength-label');
const segs      = ['seg1','seg2','seg3'].map(id => document.getElementById(id));
const reqs = {
  len:     document.getElementById('req-len'),
  upper:   document.getElementById('req-upper'),
  lower:   document.getElementById('req-lower'),
  num:     document.getElementById('req-num'),
  special: document.getElementById('req-special'),
};

/* ── Check each requirement ─────────────────────────────────────── */
function evaluate(pw) {
  return {
    len:     pw.length >= 8,
    upper:   /[A-Z]/.test(pw),
    lower:   /[a-z]/.test(pw),
    num:     /[0-9]/.test(pw),
    special: /[^A-Za-z0-9]/.test(pw),
  };
}

/* ── Update strength bar + requirement dots ─────────────────────── */
function updateStrength() {
  const pw = npField.value;

  if (!pw) {
    wrapper.style.display = 'none';
    segs.forEach(s => { s.className = 'seg'; });
    label.className = 'strength-label';
    label.textContent = '';
    Object.values(reqs).forEach(r => r.classList.remove('met'));
    syncButton();
    return;
  }

  wrapper.style.display = 'block';

  const checks = evaluate(pw);
  const score  = Object.values(checks).filter(Boolean).length; // 0-5

  // Tick/untick requirement dots
  Object.keys(checks).forEach(k => reqs[k].classList.toggle('met', checks[k]));

  // Strength level
  let level, text;
  if (score <= 2)      { level = 'weak';   text = 'Weak'; }
  else if (score <= 3) { level = 'medium'; text = 'Medium'; }
  else                  { level = 'strong'; text = 'Very strong'; }

  const activeBars = level === 'weak' ? 1 : level === 'medium' ? 2 : 3;
  segs.forEach((s, i) => {
    s.className = 'seg';
    if (i < activeBars) s.classList.add(level);
  });

  label.className = 'strength-label ' + level;
  label.textContent = text;

  syncButton();
}

/* ── Confirm password match feedback ───────────────────────────── */
function updateMatch() {
  const pw  = npField.value;
  const cpw = cpField.value;

  if (!cpw) {
    matchMsg.textContent = '';
  } else if (pw === cpw) {
    matchMsg.style.color = '#2e7d32';
    matchMsg.textContent = '\u2713 Passwords match';
  } else {
    matchMsg.style.color = '#c62828';
    matchMsg.textContent = '\u2717 Passwords do not match';
  }

  syncButton();
}

/* ── Enable button ONLY when all 5 rules + match are satisfied ─── */
function syncButton() {
  const pw     = npField.value;
  const cpw    = cpField.value;
  const checks = evaluate(pw);
  const allMet = Object.values(checks).every(Boolean);  // all 5 must be true
  const matches = pw === cpw && cpw.length > 0;

  submitBtn.disabled = !(allMet && matches);
}

/* ── Listeners ──────────────────────────────────────────────────── */
npField.addEventListener('input', updateStrength);
cpField.addEventListener('input', updateMatch);