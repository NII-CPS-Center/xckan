var api_base = '/api';

$(document).ready(function() {
  $("#btn_query").click(function() {
    var q_str = $("#query").val()
    $.ajax({
      url: api_base + '/package_search',
      data: {
        "q":$("#query").val(),
	"fq":$("#fq").val(),
	"start": $("#start").val(),
	"rows": $("#rows").val()
      },
      method: 'POST',
      dataType: 'json',
      success: function(data) {
        console.log(data);
	result = data['result'];
	
	var html = "<ul>\n";
	for (i in result['results']) {
	  var dataset = result['results'][i];
	  var show_url = api_base + '/package_show?id=' + dataset['xckan_id'];
	  var title = dataset['xckan_title'];
	  html += '<li><a href="' + show_url + '"'
	       + ' target="_blank">' + title + "<a>";
	  html += '<a href="' + dataset['xckan_site_url'] + '" target="_blank"> [' + dataset['xckan_site_name'] + ']</a></li>' + "\n";
	}
	html += "</ul>\n<hr />\n";
	
	html += '<table id="search_result">';
	html += "<tr><th>Count</th><td>" + result['count'] + "</td></tr>\n";
	html += "<tr><th>Facets</th></td></td></tr>\n";
	for (key in result['facets']['facet_fields']) {
	  html += '<tr><th>' + key + '</th><td>';
	  val = result['facets']['facet_fields'][key];
	  for (i = 0; i < val.length; i += 2) {
	    if (i > 0) html += ', ';
	    html += val[i] + ':' + val[i + 1];
	  }
	  html += "</td></tr>\n";
	}

        html += "</table>\n";
        $("#results").html(html);
      }
    });
    return false;
  });
  
});

      