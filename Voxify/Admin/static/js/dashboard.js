(function() {
  const widget = document.querySelector('.turnout-widget');
  if (!widget) return;

  const votes = parseInt(widget.dataset.totalVotes, 10) || 0;
  const total = parseInt(widget.dataset.totalVoters, 10) || 0;
  const pctEl = document.getElementById('turnoutPct');
  const arc = document.getElementById('turnoutArc');
  if (!arc || !pctEl) return;

  const pct = total > 0 ? Math.min((votes / total) * 100, 100) : 0;
  const circumference = 2 * Math.PI * 38;

  let current = 0;
  const target = (pct / 100) * circumference;
  const step = Math.max(target / 40, 0.3);

  function tick() {
    current = Math.min(current + step, target);
    arc.setAttribute('stroke-dasharray', current.toFixed(2) + ' ' + (circumference + 1).toFixed(2));
    const shown = total > 0 ? Math.round((current / circumference) * 100) : 0;
    pctEl.textContent = shown + '%';
    if (current < target) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
})();
