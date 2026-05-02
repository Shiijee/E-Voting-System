// ── OTP Expiry Countdown (server-backed) ───────────────────────────
(function () {
  const EXPIRY_SECONDS = 5 * 60;
  const storageKey = 'voxify_otp_expiry';
  const expiryInput = document.getElementById('otp-expiry');
  const serverExpiry = expiryInput ? Date.parse(expiryInput.value) : NaN;

  const countdownEl = document.getElementById('countdown');
  const timerBox    = document.getElementById('otp-timer-box');
  const verifyBtn   = document.getElementById('verify-btn');
  const linkEl      = document.getElementById('resend-link');

  function disableResend() {
    linkEl.classList.remove('active');
    linkEl.style.pointerEvents = 'none';
  }

  function enableResend() {
    linkEl.classList.add('active');
    linkEl.style.pointerEvents = 'auto';
  }

  function setExpiry(value) {
    sessionStorage.setItem(storageKey, String(value));
    timerBox.classList.remove('expired');
    verifyBtn.disabled      = false;
    verifyBtn.style.opacity = '';
    verifyBtn.style.cursor  = 'pointer';
    disableResend();
  }

  function initializeExpiry() {
    if (!Number.isNaN(serverExpiry)) {
      setExpiry(serverExpiry);
      return;
    }

    const savedValue = parseInt(sessionStorage.getItem(storageKey), 10);
    if (!Number.isNaN(savedValue) && savedValue > Date.now()) {
      timerBox.classList.remove('expired');
      verifyBtn.disabled      = false;
      verifyBtn.style.opacity = '';
      verifyBtn.style.cursor  = 'pointer';
      disableResend();
      return;
    }

    setExpiry(Date.now() + EXPIRY_SECONDS * 1000);
  }

  function expireOtp() {
    timerBox.classList.add('expired');
    timerBox.querySelector('span').innerHTML = '⚠ OTP has <span id="countdown">Expired</span>. Please resend.';
    verifyBtn.disabled      = true;
    verifyBtn.style.opacity = '0.5';
    verifyBtn.style.cursor  = 'not-allowed';
    enableResend();
  }

  function updateTimer() {
    const expiry = parseInt(sessionStorage.getItem(storageKey), 10);
    if (Number.isNaN(expiry)) {
      return;
    }

    const remaining = expiry - Date.now();
    if (remaining <= 0) {
      countdownEl.textContent = '00:00';
      expireOtp();
      clearInterval(timerInterval);
      return;
    }

    const seconds = Math.floor(remaining / 1000);
    const m = String(Math.floor(seconds / 60)).padStart(2, '0');
    const s = String(seconds % 60).padStart(2, '0');
    countdownEl.textContent = `${m}:${s}`;
  }

  initializeExpiry();

  const timerInterval = setInterval(updateTimer, 1000);
  updateTimer();

  window.resendOTP = function (e) {
    e.preventDefault();
    if (!linkEl.classList.contains('active')) return;

    const resendUrl = linkEl.dataset.resendUrl;
    if (resendUrl) {
      sessionStorage.removeItem(storageKey);
      window.location.href = resendUrl;
    }
  };

})();

// ── Auto-focus & numeric-only input ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  const otpInput = document.querySelector('input[name="otp"]');
  if (otpInput) otpInput.focus();
});

document.querySelector('input[name="otp"]').addEventListener('input', function () {
  this.value = this.value.replace(/[^0-9]/g, '');
});

// Prevent form resubmission on refresh
if (window.history.replaceState) {
  window.history.replaceState(null, null, window.location.href);
}