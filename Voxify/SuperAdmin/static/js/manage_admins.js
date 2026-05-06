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

function normalizeName(name) {
  return name.trim().replace(/\s+/g, ' ');
}

function formatName(name) {
  return normalizeName(name)
    .split(' ')
    .filter(function(word) { return word.length > 0; })
    .map(function(word) {
      return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
    })
    .join(' ');
}

function mValidateName(name) {
  var normalized = normalizeName(name);
  if (normalized.length < 2) return false;
  var parts = normalized.split(' ');
  return parts.every(function(part) {
    return /^[A-Za-zÀ-ÖØ-öø-ÿ]{2,}$/.test(part);
  });
}

function mValidateEmail(email) {
  var trimmed = email.trim();
  if (!trimmed.includes('@')) return false;
  if (trimmed !== trimmed.toLowerCase()) return false; // must be lowercase
  var local = trimmed.split('@')[0];
  if (local.length < 3) return false;
  var domain = trimmed.split('@')[1].toLowerCase();
  var allowedDomains = [
    'gmail.com', 'yahoo.com', 'ymail.com', 'rocketmail.com',
    'outlook.com', 'hotmail.com', 'live.com', 'msn.com', 'icloud.com',
    'me.com', 'mac.com', 'proton.me', 'protonmail.com', 'zoho.com',
    'zoho.eu', 'aol.com', 'fastmail.com', 'gmx.com', 'mail.com', 'yandex.com',
    'pldtmail.com', 'pldtdsl.net', 'globe.com.ph', 'smart.com.ph'
  ];
  var isAllowed = allowedDomains.includes(domain) ||
                  domain.endsWith('.edu') ||
                  domain.endsWith('.ph') ||
                  domain.endsWith('.edu.ph') ||
                  domain.endsWith('.gov.ph') ||
                  domain.endsWith('.microsoft.com');
  return isAllowed;
}

function mSetErr(id, msg) {
  var el = document.getElementById(id + '-err');
  var inp = document.getElementById(id);
  if (el) el.textContent = msg;
  if (inp) inp.classList.toggle('form-control-error', !!msg);
}
function mClearErr(id) { mSetErr(id, ''); }

function mValidateForm() {
  var ok = true;
  var firstnameEl = document.getElementById('addAdminForm').elements['firstname'];
  var surnameEl = document.getElementById('addAdminForm').elements['surname'];
  var emailEl = document.getElementById('addAdminForm').elements['email'];
  var firstname = firstnameEl ? normalizeName(firstnameEl.value) : '';
  var surname = surnameEl ? normalizeName(surnameEl.value) : '';
  var email = emailEl ? emailEl.value.trim() : '';

  if (!firstname) {
    mSetErr('m-firstname', 'First name is required.');
    ok = false;
  } else if (!mValidateName(firstname)) {
    mSetErr('m-firstname', 'First name must be at least 2 letters and contain only letters and spaces.');
    ok = false;
  } else {
    mClearErr('m-firstname');
  }

  if (!surname) {
    mSetErr('m-surname', 'Last name is required.');
    ok = false;
  } else if (!mValidateName(surname)) {
    mSetErr('m-surname', 'Last name must be at least 2 letters and contain only letters and spaces.');
    ok = false;
  } else {
    mClearErr('m-surname');
  }

  if (!email) {
    mSetErr('m-email', 'Email is required.');
    ok = false;
  } else if (!mValidateEmail(email)) {
    mSetErr('m-email', 'Email must be lowercase, have at least 3 characters before @, and come from an accepted provider (e.g., Gmail, Outlook, Yahoo, or .edu/.ph domains).');
    ok = false;
  } else {
    mClearErr('m-email');
  }

  return ok;
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
  var pwChecks = mEvaluatePw(pw);
  var pwAllMet = Object.values(pwChecks).every(Boolean);
  var formValid = mValidateForm();
  btn.disabled = !(pwAllMet && pw === cpw && cpw.length > 0 && formValid);
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
  ['m-firstname','m-surname','m-email'].forEach(function(id){ mClearErr(id); });
  document.getElementById('createAdminBtn').disabled = true;
});

// Add input listeners for validation
document.addEventListener('DOMContentLoaded', function() {
  var form = document.getElementById('addAdminForm');
  if (form) {
    ['firstname', 'surname', 'email'].forEach(function(name) {
      var el = form.elements[name];
      if (el) {
        el.addEventListener('input', function() { mClearErr('m-' + name); mSyncBtn(); });
        if (name !== 'email') {
          el.addEventListener('blur', function() { el.value = formatName(el.value); });
        }
      }
    });
  }
});
