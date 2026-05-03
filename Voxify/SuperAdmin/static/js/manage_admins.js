function mTogglePw(inputId, iconId) {
  var inp = document.getElementById(inputId);
  var ico = document.getElementById(iconId);
  if (!inp) return;
  if (inp.type === 'password') {
    inp.type = 'text';
    if (ico) ico.classList.replace('bi-eye-fill', 'bi-eye-slash-fill');
  } else {
    inp.type = 'password';
    if (ico) ico.classList.replace('bi-eye-slash-fill', 'bi-eye-fill');
  }
}

function mEvaluatePw(pw) {
  return {
    len:     pw.length >= 8,
    upper:   /[A-Z]/.test(pw),
    lower:   /[a-z]/.test(pw),
    num:     /[0-9]/.test(pw),
    special: /[^A-Za-z0-9]/.test(pw),
  };
}

function mUpdateStrength() {
  var pw      = document.getElementById('m_new_pw').value;
  var wrapper = document.getElementById('mStrengthWrapper');
  var label   = document.getElementById('mStrengthLabel');
  var segs    = ['mseg1','mseg2','mseg3'].map(function(id){ return document.getElementById(id); });
  var reqMap  = {
    len:     document.getElementById('mreq-len'),
    upper:   document.getElementById('mreq-upper'),
    lower:   document.getElementById('mreq-lower'),
    num:     document.getElementById('mreq-num'),
    special: document.getElementById('mreq-special'),
  };

  if (!pw) {
    wrapper.style.display = 'none';
    segs.forEach(function(s){ s.className = 'mseg'; });
    label.className = 'modal-strength-label'; label.textContent = '';
    Object.values(reqMap).forEach(function(r){ r.classList.remove('met'); });
    mSyncBtn(); return;
  }

  wrapper.style.display = 'block';
  var checks = mEvaluatePw(pw);
  var score  = Object.values(checks).filter(Boolean).length;
  Object.keys(checks).forEach(function(k){ reqMap[k].classList.toggle('met', checks[k]); });

  var level  = score <= 2 ? 'weak' : score <= 3 ? 'medium' : 'strong';
  var text   = level === 'weak' ? 'Weak' : level === 'medium' ? 'Medium' : 'Very Strong';
  var active = level === 'weak' ? 1 : level === 'medium' ? 2 : 3;
  segs.forEach(function(s,i){ s.className = 'mseg'; if (i < active) s.classList.add(level); });
  label.className = 'modal-strength-label ' + level; label.textContent = text;
  mUpdateMatch();
}

function mUpdateMatch() {
  var pw   = document.getElementById('m_new_pw').value;
  var cpw  = document.getElementById('m_conf_pw').value;
  var hint = document.getElementById('mHintMatch');
  if (!cpw) { hint.textContent = ''; hint.className = 'modal-pform-hint'; }
  else if (pw === cpw) { hint.innerHTML = '&#10003; Passwords match.'; hint.className = 'modal-pform-hint ok'; }
  else { hint.innerHTML = '&#10007; Passwords do not match.'; hint.className = 'modal-pform-hint error'; }
  mSyncBtn();
}

function mSyncBtn() {
  var btn    = document.getElementById('createAdminBtn');
  var pw     = document.getElementById('m_new_pw').value;
  var cpw    = document.getElementById('m_conf_pw').value;
  var checks = mEvaluatePw(pw);
  var allMet = Object.values(checks).every(Boolean);
  btn.disabled = !(allMet && pw === cpw && cpw.length > 0);
}

document.getElementById('addAdminModal').addEventListener('hidden.bs.modal', function () {
  document.getElementById('addAdminForm').reset();
  document.getElementById('mStrengthWrapper').style.display = 'none';
  document.getElementById('mStrengthLabel').textContent = '';
  document.getElementById('mHintMatch').textContent = '';
  ['mseg1','mseg2','mseg3'].forEach(function(id){ document.getElementById(id).className = 'mseg'; });
  ['mreq-len','mreq-upper','mreq-lower','mreq-num','mreq-special'].forEach(function(id){
    document.getElementById(id).classList.remove('met');
  });
  document.getElementById('createAdminBtn').disabled = true;
});
