function show_hiddencomment() {
	$(this).hide();
	$(this).parent().find('.hiddencomment').show();
	return false;
}

function process_hiddencomment(index) {
	switch_div = $(this);
	switch_div.find('.hiddencomment').hide();
	switch_div.find('a.unhide').click(show_hiddencomment).show();
}

$(document).ready(function() {
	$('.hide-switch').each(process_hiddencomment);
});
