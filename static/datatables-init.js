$(document).ready(function() {
	var language = $('meta[http-equiv="Content-Language"]').attr('content');
	var fullLanguage = "English";
	switch(language) {
		case "cs":
			fullLanguage = "Czech";
	}
	var url = "https://cdn.datatables.net/plug-ins/9dcbecd42ad/i18n/" + fullLanguage + ".json";
	$('.ticket_list').DataTable({
		"order": [[ 0, "desc "]],
		"language": {
			"url": url,
		}
	});
} );