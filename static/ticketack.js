(function($) {
	function find_parent(el, condition)
	{
		while(true)
		{
			if (el.is(condition))
			{
				return el;
			}
			el = el.parent();
		}
	}
	
	function add_ack(target, set)
	{
		var block = find_parent(target, 'li');
		set.data('prev', block.html());
		$.ajax({
			type: 'GET',
			url: set.attr('data-add-handler'),
			dataType: 'json',
			success: function(data) {
				block.html(data['form']);
			},
		});
	}
	
	function submit_ack(target, set)
	{
		var form_data = find_parent(target, 'form').serialize();
		$.ajax({
			type: 'POST',
			data: form_data,
			url: set.attr('data-add-handler'),
			dataType: 'json',
			success: function(data) {
				var item = find_parent(target, '.add-block');
				if (data['form'] != undefined)
				{
					item.html(data['form']);
				}
				if (data['success'])
				{
					var next = item.clone();
					next.html(set.data('prev'));
					item.removeClass('add-block');
					item.addClass('newly-added');
					item.attr('data-id', data['id']);
					item.after(next);
				}
			},
		});
	}
	
	function remove_ack(target, set)
	{
		var ack_line = find_parent(target, 'li');
		var block = find_parent(target, '.remove-block');
		if (block.hasClass('really'))
		{
			ack_line.addClass('removing');
			$.ajax({
				type: 'POST',
				data: {id: ack_line.attr('data-id'), csrfmiddlewaretoken: set.attr('data-token')},
				url: set.attr('data-remove-handler'),
				dataType: 'json',
				success: function(data) {
					if (data['success'])
					{
						ack_line.remove();
					}
					else
					{
						ack_line.addClass('failed');
					}
				},
			});
		}
		else
		{
			block.addClass('really');
		}
	}
	
	$(document).ready(function()
	{
		$('.ack-set').click(function(event) {
			var target = $(event.target);
			var set = $(this);
			if (target.hasClass('add-ack')) { add_ack(target, set); return false; }
			if (target.hasClass('submit-ack')) { submit_ack(target, set); return false; }
			if (target.hasClass('remove-ack')) { remove_ack(target, set); return false; }
		});
	});
})(django.jQuery);
