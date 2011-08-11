function refresh_description()
{
	$('#topic_desc').html(topics_table[$('#id_topic').val()]['desc']);
}

$(document).ready(function() {
	$('#id_topic').change(refresh_description);
	refresh_description();
});