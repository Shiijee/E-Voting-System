document.addEventListener('DOMContentLoaded', function () {
  window._candPaginator = new SvPaginator({
    tableId:     'candidatesTable',
    rowSelector: 'tbody tr',
    perPage:     10,
    infoId:      'candPagInfo',
    listId:      'candPagList',
    wrapId:      'candPagWrap'
  });
});
