
var script_tag = document.getElementById('searcher')
var search_term = script_tag.getAttribute("data-search");

for (i = 0; i < search_term.length; i++) {
    var tr = document.createElement('TR');
    for (j = 0; j < stock[i].length; j++) {
        var td = document.createElement('TD')
        td.appendChild(document.createTextNode(search_term.name));
        tr.appendChild(td)
    }
    tableBody.appendChild(tr);
}
