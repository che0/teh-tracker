function show_hidden() {
	$(this).hide();
	$(this).parent().find('.hidden').show();
}

function process_hidden(index) {
	switch_div = $(this);
	switch_div.find('.hidden').hide();
	switch_div.find('a.unhide').click(show_hidden).show();
}

$(document).ready(function() {
	$('.hide-switch').each(process_hidden);
});