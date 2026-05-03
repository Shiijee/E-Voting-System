function togglePw(inputId, iconId) {
  var inp = document.getElementById(inputId);
  var ico = document.getElementById(iconId);
  if (!inp) return;
  if (inp.type === 'password') {
    inp.type = 'text';
    if (ico) { ico.classList.replace('bi-eye-fill','bi-eye-slash-fill'); }
  } else {
    inp.type = 'password';
    if (ico) { ico.classList.replace('bi-eye-slash-fill','bi-eye-fill'); }
  }
}

function evaluatePw(pw) {
  return {
    len:     pw.length >= 8,
    upper:   /[A-Z]/.test(pw),
    lower:   /[a-z]/.test(pw),
    num:     /[0-9]/.test(pw),
    special: /[^A-Za-z0-9]/.test(pw),
  };
}

function updateStrength() {
  var pw      = document.getElementById('new_pw').value;
  var wrapper = document.getElementById('strengthWrapper');
  var label   = document.getElementById('strengthLabel');
  var segs    = ['seg1','seg2','seg3'].map(function(id){ return document.getElementById(id); });
  var reqMap  = {
    len:     document.getElementById('req-len'),
    upper:   document.getElementById('req-upper'),
    lower:   document.getElementById('req-lower'),
    num:     document.getElementById('req-num'),
    special: document.getElementById('req-special'),
  };

  if (!pw) {
    wrapper.style.display = 'none';
    segs.forEach(function(s){ s.className = 'seg'; });
    label.className = 'strength-label'; label.textContent = '';
    Object.values(reqMap).forEach(function(r){ r.classList.remove('met'); });
    syncPwBtn(); return;
  }

  wrapper.style.display = 'block';
  var checks = evaluatePw(pw);
  var score  = Object.values(checks).filter(Boolean).length;
  Object.keys(checks).forEach(function(k){ reqMap[k].classList.toggle('met', checks[k]); });

  var level  = score <= 2 ? 'weak' : score <= 3 ? 'medium' : 'strong';
  var text   = level === 'weak' ? 'Weak' : level === 'medium' ? 'Medium' : 'Very Strong';
  var active = level === 'weak' ? 1 : level === 'medium' ? 2 : 3;
  segs.forEach(function(s,i){ s.className = 'seg'; if (i < active) s.classList.add(level); });
  label.className = 'strength-label ' + level; label.textContent = text;

  updateMatch();
}

function updateMatch() {
  var pw   = document.getElementById('new_pw').value;
  var cpw  = document.getElementById('conf_pw').value;
  var hint = document.getElementById('hintMatch');
  if (!cpw) { hint.textContent = ''; hint.className = 'pform-hint'; }
  else if (pw === cpw) { hint.innerHTML = '&#10003; Passwords match.'; hint.className = 'pform-hint ok'; }
  else { hint.innerHTML = '&#10007; Passwords do not match.'; hint.className = 'pform-hint error'; }
  syncPwBtn();
}

function syncPwBtn() {
  var btn = document.getElementById('pwSubmitBtn');
  var cur = document.getElementById('cur_pw').value;
  var pw  = document.getElementById('new_pw').value;
  var cpw = document.getElementById('conf_pw').value;
  var checks = evaluatePw(pw);
  var allMet = Object.values(checks).every(Boolean);
  btn.disabled = !(cur.length > 0 && allMet && pw === cpw && cpw.length > 0);
}

(function init() {
  var newPw = document.getElementById('new_pw');
  if (newPw && newPw.value) { updateStrength(); }
  syncPwBtn();
})();
