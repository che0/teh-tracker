$(document).ready(function() {
	var language = $('meta[http-equiv="Content-Language"]').attr('content');
    var fullLanguage = "English";
	switch(language) {
		case "cs":
			fullLanguage = "Czech";
	}
    var url = "https://cdn.datatables.net/plug-ins/9dcbecd42ad/i18n/" + fullLanguage + ".json";
    var ordering = $('#custom-ordering-datatables').text();
    if(ordering == "")
    {
        ordering = [[ 0, "asc "]];
    }
    else
    {
        ordering = JSON.parse(ordering)
    }
	$('table').DataTable({
		"order": ordering,
		"language": {
			"url": url,
		}
	});
} );