function togglePw(inputId, iconId) {
  var inp = document.getElementById(inputId);
  var ico = document.getElementById(iconId);
  if (!inp) return;
  if (inp.type === 'password') {
    inp.type = 'text';
    if (ico) { ico.classList.remove('bi-eye-fill'); ico.classList.add('bi-eye-slash-fill'); }
  } else {
    inp.type = 'password';
    if (ico) { ico.classList.remove('bi-eye-slash-fill'); ico.classList.add('bi-eye-fill'); }
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

function isValidName(name, required) {
  var normalized = normalizeName(name);
  if (!normalized) return !required;
  if (normalized.length < 2) return false;
  return normalized.split(' ').every(function(part) {
    return /^[A-Za-zÀ-ÖØ-öø-ÿ]{2,}$/.test(part);
  });
}

// ── EMAIL DOMAIN VALIDATION ───────────────────────────────────────────
var authorizedExplicit = [
  "gmail.com", "googlemail.com", "yahoo.com", "ymail.com", "rocketmail.com",
  "outlook.com", "hotmail.com", "live.com", "msn.com", "icloud.com",
  "me.com", "mac.com", "proton.me", "protonmail.com", "zoho.com",
  "zoho.eu", "aol.com", "fastmail.com", "gmx.com", "mail.com", "yandex.com",
  "pldtmail.com", "pldtdsl.net", "globe.com.ph", "smart.com.ph",
  "aspmx.l.google.com", "alt1.aspmx.l.google.com", "alt2.aspmx.l.google.com",
  "alt3.aspmx.l.google.com", "alt4.aspmx.l.google.com",
  "mail.protection.outlook.com", "mx.zoho.com", "mx2.zoho.com", "mx3.zoho.com",
  "mail.protonmail.ch", "mailsec.protonmail.ch", "mta5.am0.yahoodns.net",
  "mta6.am0.yahoodns.net", "mta7.am0.yahoodns.net",
  "in1-smtp.messagingengine.com", "in2-smtp.messagingengine.com",
  "inbound-smtp.us-east-1.amazonaws.com", "inbound-smtp.us-west-2.amazonaws.com",
  "mail.domain.com", "smtp.domain.com", "mx.domain.com"
];

function isValidEmail(email) {
  var trimmed = email.trim();
  var basicRe = /^[a-z0-9._%+\-]{3,}@[a-z0-9.\-]+\.[a-z]{2,}$/;
  if (!basicRe.test(trimmed)) return false;
  if (trimmed !== trimmed.toLowerCase()) return false;
  var domain = trimmed.split('@')[1].toLowerCase();
  var isExplicitMatch = authorizedExplicit.indexOf(domain) !== -1;
  var isEduOrPh = domain.endsWith('.edu') ||
                  domain.endsWith('.ph') ||
                  domain.endsWith('.edu.ph') ||
                  domain.endsWith('.gov.ph');
  return isExplicitMatch || isEduOrPh;
}
// ─────────────────────────────────────────────────────────────────────

function setErr(id, msg) {
  var el = document.getElementById(id);
  var inp = document.getElementById(id.replace('-err', ''));
  if (!el) return;
  el.textContent = msg;
  if (inp) inp.classList.toggle('vform-input-error', !!msg);
}

function clearErr(id) { setErr(id, ''); }

function avEvalPw(pw) {
  return {
    len:     pw.length >= 8,
    upper:   /[A-Z]/.test(pw),
    lower:   /[a-z]/.test(pw),
    num:     /[0-9]/.test(pw),
    special: /[^A-Za-z0-9]/.test(pw),
  };
}

function avUpdateStrength() {
  var pw      = document.getElementById('av-password').value;
  var wrapper = document.getElementById('av-strength-wrapper');
  var label   = document.getElementById('av-strength-label');
  var segs    = ['av-seg1','av-seg2','av-seg3'].map(function(id){ return document.getElementById(id); });
  var reqIds  = { len:'av-req-len', upper:'av-req-upper', lower:'av-req-lower', num:'av-req-num', special:'av-req-special' };

  if (!pw) {
    wrapper.style.display = 'none';
    segs.forEach(function(s){ s.style.background = '#ddd'; });
    label.textContent = '';
    label.style.color = '';
    Object.values(reqIds).forEach(function(rid){
      var r = document.getElementById(rid);
      if (r) { r.style.color = '#999'; var dot = r.querySelector('.av-dot'); if (dot) dot.style.background = '#ddd'; }
    });
    avUpdateMatch();
    return;
  }

  wrapper.style.display = 'block';
  var checks = avEvalPw(pw);
  var score  = Object.values(checks).filter(Boolean).length;

  Object.keys(checks).forEach(function(k){
    var r = document.getElementById(reqIds[k]);
    if (!r) return;
    var dot = r.querySelector('.av-dot');
    if (checks[k]) {
      r.style.color = '#2e7d32';
      if (dot) dot.style.background = '#2e7d32';
    } else {
      r.style.color = '#999';
      if (dot) dot.style.background = '#ddd';
    }
  });

  var level = score <= 2 ? 'weak' : score <= 3 ? 'medium' : 'strong';
  var text  = level === 'weak' ? 'Weak' : level === 'medium' ? 'Medium' : 'Very Strong';
  var color = level === 'weak' ? '#e53935' : level === 'medium' ? '#f9a825' : '#2e7d32';
  var activeBars = level === 'weak' ? 1 : level === 'medium' ? 2 : 3;

  segs.forEach(function(s, i){
    s.style.background = i < activeBars ? color : '#ddd';
  });
  label.textContent = text;
  label.style.color = color;
  avUpdateMatch();
}

function avUpdateMatch() {
  var pw   = document.getElementById('av-password').value;
  var cpw  = document.getElementById('av-confirm-password').value;
  var hint = document.getElementById('av-match-hint');
  if (!hint) return;
  if (!cpw) {
    hint.textContent = '';
    hint.style.color = '';
  } else if (pw === cpw) {
    hint.textContent = '✓ Passwords match.';
    hint.style.color = '#2e7d32';
  } else {
    hint.textContent = '✗ Passwords do not match.';
    hint.style.color = '#c62828';
  }
}

function validateAddVoterForm() {
  var ok = true;
  var fnEl = document.getElementById('av-firstname');
  var fn = fnEl ? formatName(fnEl.value) : '';
  if (fnEl) fnEl.value = fn;
  if (!isValidName(fn, true)) { setErr('av-firstname-err', 'First name is required and must be letters only, at least 2 characters long.'); ok = false; }
  else clearErr('av-firstname-err');

  var mnEl = document.getElementById('av-middlename');
  var mn = mnEl ? formatName(mnEl.value) : '';
  if (mnEl) mnEl.value = mn;
  if (!isValidName(mn, false)) { setErr('av-middlename-err', 'Middle name must be letters only and at least 2 characters if provided.'); ok = false; }
  else clearErr('av-middlename-err');

  var snEl = document.getElementById('av-surname');
  var sn = snEl ? formatName(snEl.value) : '';
  if (snEl) snEl.value = sn;
  if (!isValidName(sn, true)) { setErr('av-surname-err', 'Surname is required and must be letters only, at least 2 characters long.'); ok = false; }
  else clearErr('av-surname-err');

  var sid = document.getElementById('av-studentid').value.trim();
  if (!sid) { setErr('av-studentid-err', 'Student ID number is required.'); ok = false; }
  else if (isNaN(sid) || parseInt(sid) < 1 || !Number.isInteger(parseFloat(sid))) {
    setErr('av-studentid-err', 'Must be a whole number (e.g. 3).'); ok = false;
  } else clearErr('av-studentid-err');

  var em = document.getElementById('av-email').value.trim();
  if (!em) { setErr('av-email-err', 'Email is required.'); ok = false; }
  else if (!isValidEmail(em)) { setErr('av-email-err', 'Please enter a valid lowercase email with at least 3 characters before @ from an accepted provider (e.g. Gmail, Outlook, Yahoo, or a .ph / .edu email).'); ok = false; }
  else clearErr('av-email-err');

  var pw = document.getElementById('av-password').value;
  if (!pw) { setErr('av-password-err', 'Password is required.'); ok = false; }
  else {
    var checks = avEvalPw(pw);
    var allMet = Object.values(checks).every(Boolean);
    if (!allMet) { setErr('av-password-err', 'Password must meet all requirements above.'); ok = false; }
    else clearErr('av-password-err');
  }

  var cpw = document.getElementById('av-confirm-password').value;
  if (!cpw) { setErr('av-confirm-password-err', 'Please confirm the password.'); ok = false; }
  else if (pw !== cpw) { setErr('av-confirm-password-err', 'Passwords do not match.'); ok = false; }
  else clearErr('av-confirm-password-err');

  return ok;
}

document.addEventListener('DOMContentLoaded', function () {
  var form = document.getElementById('addVoterForm');
  if (form) {
    form.addEventListener('submit', function (e) {
      if (!validateAddVoterForm()) e.preventDefault();
    });

    ['av-firstname','av-middlename','av-surname','av-studentid','av-email','av-password','av-confirm-password'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) {
        el.addEventListener('input', function () { clearErr(id + '-err'); });
        if (['av-firstname','av-middlename','av-surname'].includes(id)) {
          el.addEventListener('blur', function() { el.value = formatName(el.value); });
        }
      }
    });
  }

  document.querySelectorAll('[id^="editVoterForm"]').forEach(function(form) {
    var vid = form.id.replace('editVoterForm', '');
    form.addEventListener('submit', function(e) {
      if (!validateEditVoterForm(vid)) e.preventDefault();
    });
    ['firstname','middlename','surname','email','password','confirm-password'].forEach(function(field) {
      var el = document.getElementById('ev-' + vid + '-' + field);
      if (el) {
        el.addEventListener('input', function () { evClearErr(vid, field); });
        if (['firstname','middlename','surname'].includes(field)) {
          el.addEventListener('blur', function() { el.value = formatName(el.value); });
        }
      }
    });
  });
});

function openModal(id) {
  var el = document.getElementById(id);
  if (el) { el.style.display = 'flex'; document.body.style.overflow = 'hidden'; }
}

function closeModal(id) {
  var el = document.getElementById(id);
  if (el) { el.style.display = 'none'; document.body.style.overflow = ''; }
  if (id === 'addVoterModal') {
    var form = document.getElementById('addVoterForm');
    if (form) { form.reset(); }
    ['av-firstname','av-middlename','av-surname','av-studentid','av-email','av-password','av-confirm-password'].forEach(function (fid) {
      clearErr(fid + '-err');
      var inp = document.getElementById(fid);
      if (inp) inp.classList.remove('vform-input-error');
    });
    var sw = document.getElementById('av-strength-wrapper');
    if (sw) sw.style.display = 'none';
    var mh = document.getElementById('av-match-hint');
    if (mh) { mh.textContent = ''; }
  }
}

function overlayClose(e, id) {
  if (e.target === e.currentTarget) closeModal(id);
}

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    document.querySelectorAll('.vmodal-overlay').forEach(function(m) { m.style.display = 'none'; });
    document.body.style.overflow = '';
  }
});

function switchTab(tab) {
  var panels = { active: document.getElementById('panel-active'), archived: document.getElementById('panel-archived') };
  var tabs = { active: document.getElementById('tab-active'), archived: document.getElementById('tab-archived') };
  Object.keys(panels).forEach(function(k) {
    panels[k].style.display = k === tab ? 'block' : 'none';
    tabs[k].classList.toggle('voter-tab-active', k === tab);
  });
  sessionStorage.setItem('voterTab', tab);
}

new SvPaginator({
  tableId:     'activeVotersTable',
  rowSelector: 'tbody tr',
  perPage:     10,
  infoId:      'activePagInfo',
  listId:      'activePagList',
  wrapId:      'activePagWrap'
});
new SvPaginator({
  tableId:     'archivedVotersTable',
  rowSelector: 'tbody tr',
  perPage:     10,
  infoId:      'archivedPagInfo',
  listId:      'archivedPagList',
  wrapId:      'archivedPagWrap'
});

var saved = sessionStorage.getItem('voterTab');
if (saved) switchTab(saved);

var votersPageData = document.getElementById('votersPageData');
if (votersPageData && votersPageData.dataset.createVoterRestore === 'true') {
  openModal('addVoterModal');
  var avPw = document.getElementById('av-password');
  if (avPw && avPw.value) { avUpdateStrength(); }
}

// ── EDIT VOTER VALIDATION ─────────────────────────────────────────────

function evSetErr(vid, field, msg) {
  var el  = document.getElementById('ev-' + vid + '-' + field + '-err');
  var inp = document.getElementById('ev-' + vid + '-' + field);
  if (el)  el.textContent = msg;
  if (inp) inp.classList.toggle('vform-input-error', !!msg);
}

function evClearErr(vid, field) { evSetErr(vid, field, ''); }

function evUpdateStrength(vid) {
  var pw      = document.getElementById('ev-' + vid + '-password');
  var wrapper = document.getElementById('ev-' + vid + '-strength-wrapper');
  var label   = document.getElementById('ev-' + vid + '-strength-label');
  var segs    = [1,2,3].map(function(n){ return document.getElementById('ev-' + vid + '-seg' + n); });
  if (!pw || !wrapper) return;
  var val = pw.value;
  if (!val) {
    wrapper.style.display = 'none';
    segs.forEach(function(s){ if(s) s.style.background = '#ddd'; });
    if (label) { label.textContent = ''; label.style.color = ''; }
    evUpdateMatch(vid);
    return;
  }
  wrapper.style.display = 'block';
  var checks = avEvalPw(val);
  var score  = Object.values(checks).filter(Boolean).length;
  ['len','upper','lower','num','special'].forEach(function(k) {
    var r = document.getElementById('ev-' + vid + '-req-' + k);
    if (!r) return;
    var dot = r.querySelector('.av-dot');
    if (checks[k]) { r.style.color = '#2e7d32'; if (dot) dot.style.background = '#2e7d32'; }
    else            { r.style.color = '#999';    if (dot) dot.style.background = '#ddd';    }
  });
  var level = score <= 2 ? 'weak' : score <= 3 ? 'medium' : 'strong';
  var color = level === 'weak' ? '#e53935' : level === 'medium' ? '#f9a825' : '#2e7d32';
  var bars  = level === 'weak' ? 1 : level === 'medium' ? 2 : 3;
  var text  = level === 'weak' ? 'Weak' : level === 'medium' ? 'Medium' : 'Very Strong';
  segs.forEach(function(s, i){ if(s) s.style.background = i < bars ? color : '#ddd'; });
  if (label) { label.textContent = text; label.style.color = color; }
  evUpdateMatch(vid);
}

function evUpdateMatch(vid) {
  var pw   = document.getElementById('ev-' + vid + '-password');
  var cpw  = document.getElementById('ev-' + vid + '-confirm-password');
  var hint = document.getElementById('ev-' + vid + '-match-hint');
  if (!pw || !cpw || !hint) return;
  if (!cpw.value) { hint.textContent = ''; hint.style.color = ''; }
  else if (pw.value === cpw.value) { hint.textContent = '✓ Passwords match.'; hint.style.color = '#2e7d32'; }
  else { hint.textContent = '✗ Passwords do not match.'; hint.style.color = '#c62828'; }
}

function validateEditVoterForm(vid) {
  var ok = true;

  var fnEl = document.getElementById('ev-' + vid + '-firstname');
  if (!fnEl) return true;
  var fnVal = formatName(fnEl.value);
  fnEl.value = fnVal;
  if (!isValidName(fnVal, true)) { evSetErr(vid, 'firstname', 'First name is required and must be letters only, at least 2 characters long.'); ok = false; }
  else evClearErr(vid, 'firstname');

  var mnEl  = document.getElementById('ev-' + vid + '-middlename');
  var mnVal = mnEl ? formatName(mnEl.value) : '';
  if (mnEl) mnEl.value = mnVal;
  if (!isValidName(mnVal, false)) { evSetErr(vid, 'middlename', 'Middle name must be letters only and at least 2 characters if provided.'); ok = false; }
  else evClearErr(vid, 'middlename');

  var snEl  = document.getElementById('ev-' + vid + '-surname');
  var snVal = snEl ? formatName(snEl.value) : '';
  if (snEl) snEl.value = snVal;
  if (!isValidName(snVal, true)) { evSetErr(vid, 'surname', 'Surname is required and must be letters only, at least 2 characters long.'); ok = false; }
  else evClearErr(vid, 'surname');

  var emEl  = document.getElementById('ev-' + vid + '-email');
  var emVal = emEl ? emEl.value.trim() : '';
  if (!emVal) { evSetErr(vid, 'email', 'Email is required.'); ok = false; }
  else if (!isValidEmail(emVal)) { evSetErr(vid, 'email', 'Please enter a valid lowercase email with at least 3 characters before @ from an accepted provider (e.g. Gmail, Outlook, Yahoo, or a .ph / .edu email).'); ok = false; }
  else evClearErr(vid, 'email');

  var pwEl   = document.getElementById('ev-' + vid + '-password');
  var cpwEl  = document.getElementById('ev-' + vid + '-confirm-password');
  var pwVal  = pwEl  ? pwEl.value  : '';
  var cpwVal = cpwEl ? cpwEl.value : '';

  if (pwVal) {
    var checks = avEvalPw(pwVal);
    if (!Object.values(checks).every(Boolean)) {
      evSetErr(vid, 'password', 'Password must meet all requirements above.'); ok = false;
    } else evClearErr(vid, 'password');

    if (!cpwVal) { evSetErr(vid, 'confirm-password', 'Please confirm the new password.'); ok = false; }
    else if (pwVal !== cpwVal) { evSetErr(vid, 'confirm-password', 'Passwords do not match.'); ok = false; }
    else evClearErr(vid, 'confirm-password');
  } else {
    evClearErr(vid, 'password');
    if (cpwVal) { evSetErr(vid, 'confirm-password', 'Enter a new password first.'); ok = false; }
    else evClearErr(vid, 'confirm-password');
  }

  return ok;
}