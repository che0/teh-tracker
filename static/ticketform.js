function refresh_description()
{
	var topic_id = $('#id_topic').val();
	if (topic_id == '')
	{
		$('#topic_desc').hide();
		$('#mediainfo-group').hide();
		$('#expediture-group').hide();
		$('#preexpediture-group').hide();
		$('#id_tag').html("<option value selected>---------</option>");
		return;
	}

	var topic = topics_table[topic_id];
	$('#topic_desc').html(topic['form_description']).toggle(topic['form_description'] != "");
	$('#mediainfo-group').toggle(topic['ticket_media']);
	$('#expediture-group').toggle(topic['ticket_expenses']);
	$('#preexpediture-group').toggle(topic['ticket_preexpenses']);
	var tagsHtml = "<option value selected>---------</option>";
	for(var i = 0; i < topic.tag_set.length; i++)
	{
		var tag = topic.tag_set[i];
		tagsHtml += '<option value="' + tag.id + '">' + tag.display_name + '</option>';
	}
	$('#id_tag').html(tagsHtml);
	if($('#id_tag').html().includes(window.originallyCheckedTag))
		$('#id_tag').val(window.originallyCheckedTag);
	else
		$('#id_tag').val("");
}

$(document).ready(function() {
	$('#id_topic').change(refresh_description);
	window.originallyCheckedTag = $('#id_tag').val();
	refresh_description();
});
