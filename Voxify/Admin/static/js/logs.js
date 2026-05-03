(function () {
  'use strict';

  const ROWS_PER_PAGE = 10;
  let currentPage = 1;
  let filteredRows = [];

  const allRows        = Array.from(document.querySelectorAll('.log-table-row'));
  const searchInput    = document.getElementById('logSearchInput');
  const actionSelect   = document.getElementById('logActionSelect');
  const filterBtn      = document.getElementById('logFilterBtn');
  const paginationList = document.getElementById('paginationList');
  const paginationInfo = document.getElementById('paginationInfo');
  const eventCount     = document.getElementById('logEventCount');

  function applyFilters() {
    const q      = (searchInput  ? searchInput.value.trim().toLowerCase()  : '');
    const action = (actionSelect ? actionSelect.value.trim().toLowerCase() : '');

    filteredRows = allRows.filter(row => {
      const matchAction = !action || row.dataset.action === action;
      const matchSearch = !q      || row.dataset.text.includes(q);
      return matchAction && matchSearch;
    });

    currentPage = 1;
    renderPage();
    renderPagination();
    if (eventCount) {
      eventCount.innerHTML = '<i class="bi bi-journal-text"></i> ' + filteredRows.length + ' Event' + (filteredRows.length !== 1 ? 's' : '');
    }
  }

  function renderPage() {
    const start = (currentPage - 1) * ROWS_PER_PAGE;
    const end   = start + ROWS_PER_PAGE;

    allRows.forEach(r => r.style.display = 'none');
    filteredRows.slice(start, end).forEach(r => r.style.display = '');

    if (paginationInfo) {
      const from = filteredRows.length ? start + 1 : 0;
      const to   = Math.min(end, filteredRows.length);
      paginationInfo.textContent = 'Showing ' + from + '–' + to + ' of ' + filteredRows.length + ' entries';
    }
  }

  function renderPagination() {
    if (!paginationList) return;
    const totalPages = Math.ceil(filteredRows.length / ROWS_PER_PAGE);
    paginationList.innerHTML = '';

    function makeLi(label, page, disabled, active, isEllipsis) {
      const li = document.createElement('li');
      if (isEllipsis) {
        li.className = 'ellipsis';
        li.innerHTML = '<span>…</span>';
        return li;
      }
      if (active) li.classList.add('active');
      if (disabled) li.classList.add('disabled');
      const a = document.createElement('a');
      a.href = '#';
      a.innerHTML = label;
      if (!disabled && !active) {
        a.addEventListener('click', function(e) { e.preventDefault(); currentPage = page; renderPage(); renderPagination(); });
      }
      li.appendChild(a);
      return li;
    }

    paginationList.appendChild(makeLi('<i class="bi bi-chevron-left"></i>', currentPage - 1, currentPage === 1, false));

    var pages = buildPageRange(currentPage, totalPages);
    pages.forEach(function(p) {
      if (p === '...') {
        paginationList.appendChild(makeLi('', null, true, false, true));
      } else {
        paginationList.appendChild(makeLi(p, p, false, p === currentPage));
      }
    });

    paginationList.appendChild(makeLi('<i class="bi bi-chevron-right"></i>', currentPage + 1, currentPage === totalPages || totalPages === 0, false));
  }

  function buildPageRange(cur, total) {
    if (total <= 7) {
      var arr = [];
      for (var i = 1; i <= total; i++) arr.push(i);
      return arr;
    }
    var pages = [];
    if (cur <= 4) {
      for (var i = 1; i <= 5; i++) pages.push(i);
      pages.push('...');
      pages.push(total);
    } else if (cur >= total - 3) {
      pages.push(1);
      pages.push('...');
      for (var i = total - 4; i <= total; i++) pages.push(i);
    } else {
      pages.push(1);
      pages.push('...');
      for (var i = cur - 1; i <= cur + 1; i++) pages.push(i);
      pages.push('...');
      pages.push(total);
    }
    return pages;
  }

  if (filterBtn)   filterBtn.addEventListener('click', applyFilters);
  if (searchInput) searchInput.addEventListener('keydown', function(e) { if (e.key === 'Enter') applyFilters(); });
  if (actionSelect) actionSelect.addEventListener('change', applyFilters);

  applyFilters();
})();