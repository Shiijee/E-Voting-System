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

var nameRe  = /^[A-Za-zÀ-ÖØ-öø-ÿ' \-]+$/;
var gmailRe = /^[a-zA-Z0-9._%+\-]+@gmail\.com$/i;

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
  var fn = document.getElementById('av-firstname').value.trim();
  if (!fn) { setErr('av-firstname-err', 'First name is required.'); ok = false; }
  else if (!nameRe.test(fn)) { setErr('av-firstname-err', 'Letters only (no numbers or special characters).'); ok = false; }
  else clearErr('av-firstname-err');

  var mn = document.getElementById('av-middlename').value.trim();
  if (mn && !nameRe.test(mn)) { setErr('av-middlename-err', 'Letters only (no numbers or special characters).'); ok = false; }
  else clearErr('av-middlename-err');

  var sn = document.getElementById('av-surname').value.trim();
  if (!sn) { setErr('av-surname-err', 'Surname is required.'); ok = false; }
  else if (!nameRe.test(sn)) { setErr('av-surname-err', 'Letters only (no numbers or special characters).'); ok = false; }
  else clearErr('av-surname-err');

  var sid = document.getElementById('av-studentid').value.trim();
  if (!sid) { setErr('av-studentid-err', 'Student ID number is required.'); ok = false; }
  else if (isNaN(sid) || parseInt(sid) < 1 || !Number.isInteger(parseFloat(sid))) {
    setErr('av-studentid-err', 'Must be a whole number (e.g. 3).'); ok = false;
  } else clearErr('av-studentid-err');

  var em = document.getElementById('av-email').value.trim();
  if (!em) { setErr('av-email-err', 'Email is required.'); ok = false; }
  else if (!gmailRe.test(em)) { setErr('av-email-err', 'Only Gmail addresses are allowed (e.g. name@gmail.com).'); ok = false; }
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
      if (el) el.addEventListener('input', function () { clearErr(id + '-err'); });
    });
  }
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

// Auto-open Add Voter modal and restore strength if there was a create error
var votersPageData = document.getElementById('votersPageData');
if (votersPageData && votersPageData.dataset.createVoterRestore === 'true') {
  openModal('addVoterModal');
  var avPw = document.getElementById('av-password');
  if (avPw && avPw.value) { avUpdateStrength(); }
}
