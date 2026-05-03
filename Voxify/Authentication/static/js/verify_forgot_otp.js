(function () {
  const expiryStr = "{{ otp_expiry | default('') }}";
  const countdownEl = document.getElementById('countdown');
  const timerBox = document.getElementById('timer-box');
  const resendLink = document.getElementById('resend-link');
  const resendCooldown = document.getElementById('resend-cooldown');

  if (!expiryStr || !countdownEl) return;

  const expiry = new Date(expiryStr);

  // Resend is available only after 30 s from page load
  let resendUnlockAt = Date.now() + 30000;

  function tick() {
    const now = Date.now();
    const diff = Math.max(0, Math.floor((expiry - now) / 1000));
    const m = Math.floor(diff / 60).toString().padStart(2, '0');
    const s = (diff % 60).toString().padStart(2, '0');
    countdownEl.textContent = `${m}:${s}`;

    if (diff === 0 && timerBox) {
      timerBox.classList.add('expired');
      countdownEl.textContent = 'Expired';
    }

    // Resend cooldown
    if (resendLink) {
      const resendRemaining = Math.max(0, Math.ceil((resendUnlockAt - now) / 1000));
      if (resendRemaining > 0) {
        resendLink.classList.remove('active');
        resendCooldown.textContent = `(${resendRemaining}s)`;
      } else {
        resendLink.classList.add('active');
        resendCooldown.textContent = '';
      }
    }
  }

  tick();
  setInterval(tick, 1000);
})();