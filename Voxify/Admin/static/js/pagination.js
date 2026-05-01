/* ═══════════════════════════════════════════════════════
   SecureVote Admin — Shared Pagination Utility
   Usage: new SvPaginator({ tableId, rowSelector, perPage, infoId, listId, countId, countText })
═══════════════════════════════════════════════════════ */

function SvPaginator(opts) {
  var tableId     = opts.tableId     || null;
  var rowSel      = opts.rowSelector || 'tbody tr';
  var perPage     = opts.perPage     || 10;
  var infoId      = opts.infoId      || null;
  var listId      = opts.listId      || null;
  var countId     = opts.countId     || null;
  var countText   = opts.countText   || function(n){ return n + ' item' + (n !== 1 ? 's' : ''); };
  var onFilter    = opts.onFilter    || null;   // optional extra filter fn(row) → bool
  var wrapId      = opts.wrapId      || null;   // pagination wrapper element id

  var root        = tableId ? document.getElementById(tableId) : document;
  var allRows     = root    ? Array.from(root.querySelectorAll(rowSel)) : [];
  var currentPage = 1;
  var filteredRows= [];

  var paginationList = listId ? document.getElementById(listId) : null;
  var paginationInfo = infoId ? document.getElementById(infoId) : null;
  var countEl        = countId ? document.getElementById(countId) : null;

  function applyFilter(filterFn) {
    onFilter = filterFn || onFilter;
    filteredRows = onFilter ? allRows.filter(onFilter) : allRows.slice();
    currentPage = 1;
    render();
    renderPagination();
    updateCount();
  }

  function render() {
    var start = (currentPage - 1) * perPage;
    var end   = start + perPage;
    allRows.forEach(function(r){ r.style.display = 'none'; });
    filteredRows.slice(start, end).forEach(function(r){ r.style.display = ''; });
    if (paginationInfo) {
      var from = filteredRows.length ? start + 1 : 0;
      var to   = Math.min(end, filteredRows.length);
      paginationInfo.textContent = 'Showing ' + from + '\u2013' + to + ' of ' + filteredRows.length + ' entries';
    }
  }

  function renderPagination() {
    if (!paginationList) return;
    var totalPages = Math.max(1, Math.ceil(filteredRows.length / perPage));
    paginationList.innerHTML = '';

    // Hide wrapper when 1 page
    if (wrapId) {
      var wrap = document.getElementById(wrapId);
      if (wrap) wrap.style.display = filteredRows.length > perPage ? '' : 'none';
    }

    function makeLi(label, page, disabled, active, isEllipsis) {
      var li = document.createElement('li');
      if (isEllipsis) { li.className = 'ellipsis'; li.innerHTML = '<span>\u2026</span>'; return li; }
      if (active)   li.classList.add('active');
      if (disabled) li.classList.add('disabled');
      var a = document.createElement('a');
      a.href = '#';
      a.innerHTML = label;
      if (!disabled && !active) {
        a.addEventListener('click', function(e) {
          e.preventDefault();
          currentPage = page;
          render();
          renderPagination();
        });
      }
      li.appendChild(a);
      return li;
    }

    paginationList.appendChild(makeLi('<i class="bi bi-chevron-left"></i>', currentPage - 1, currentPage === 1, false));
    buildPageRange(currentPage, totalPages).forEach(function(p) {
      if (p === '...') paginationList.appendChild(makeLi('', null, true, false, true));
      else paginationList.appendChild(makeLi(p, p, false, p === currentPage));
    });
    paginationList.appendChild(makeLi('<i class="bi bi-chevron-right"></i>', currentPage + 1, currentPage >= totalPages, false));
  }

  function buildPageRange(cur, total) {
    if (total <= 7) {
      var arr = []; for (var i = 1; i <= total; i++) arr.push(i); return arr;
    }
    var pages = [];
    if (cur <= 4) {
      for (var i = 1; i <= 5; i++) pages.push(i);
      pages.push('...'); pages.push(total);
    } else if (cur >= total - 3) {
      pages.push(1); pages.push('...');
      for (var i = total - 4; i <= total; i++) pages.push(i);
    } else {
      pages.push(1); pages.push('...');
      for (var i = cur - 1; i <= cur + 1; i++) pages.push(i);
      pages.push('...'); pages.push(total);
    }
    return pages;
  }

  function updateCount() {
    if (countEl) countEl.innerHTML = countText(filteredRows.length);
  }

  function refresh() {
    root    = tableId ? document.getElementById(tableId) : document;
    allRows = root ? Array.from(root.querySelectorAll(rowSel)) : [];
    applyFilter();
  }

  // Init
  applyFilter();

  return {
    applyFilter: applyFilter,
    refresh: refresh,
    getPage: function() { return currentPage; },
    getFiltered: function() { return filteredRows; }
  };
}
