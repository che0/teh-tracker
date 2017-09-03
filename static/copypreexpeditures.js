function cloneRow() {
  //event.preventDefault();
  var table = $('*[id^="preexpediture"].dynamic-preexpediture');
  console.log(table.rows);
  for (var i = 0, row; row = table[i]; i++) {
    var desc = row.cells[1].children[0].value;
    var amount = row.cells[2].children[0].value;
    var wage = row.cells[3].children[0].checked;
    var tmp = document.getElementById('expediture');
    tmp.children[i+1].children[0].children[0].click();
    if (i != 0) {
      var tt = i + 1
      var exp_row = document.getElementById('expediture-' + tt);
    } else {
      var exp_row = document.getElementById('expediture-' + 1);
    }
    exp_row.cells[1].children[0].value = desc;
    exp_row.cells[2].children[0].value = amount;
    exp_row.cells[3].children[0].checked = wage;
  }
}
