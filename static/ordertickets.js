$( document ).ready(function() {
	$( "i" ).each(function() {
		if( $( this ).parent().attr("onclick").split("'")[1] == getUrlParameter("order") && getUrlParameter("state") == "1") {
			$( this ).addClass("fa-caret-up");
			console.log("state 1")
		} else if( $( this).parent().attr("onclick").split("'")[1] == getUrlParameter("order") && getUrlParameter("state") == "2") {
			$( this ).addClass("fa-caret-down");
		} else {
			$( this ).addClass("fa-sort");
		}
	});
})
var getUrlParameter = function getUrlParameter(sParam) {
    var sPageURL = decodeURIComponent(window.location.search.substring(1)),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : sParameterName[1];
        }
    }
};

var state = 0;
function order(by) {
    state = getUrlParameter('state');
    if (state == '0') {state = 0;}
    if (state == '1') {state = 1;}
    if (state == '2') {state = 2;}
    if (state == undefined) {
    	state = 0;
    }
    var tmp = getUrlParameter('order'); 
    if (by != tmp && tmp != undefined) {
        state = 0;
    } else if (tmp == undefined) {
     	tmp = by;
	state = 1;
    } else {
	state += 1;
        if (state > 2) {
            state = 0;
        }
    }
    var target = window.location.href.split('?')[0];
    if(state == 1) {
        window.location = target + "?order=" + tmp + "&descasc=asc&state=" + state;
    } else if(state == 2) {
        window.location = target + "?order=" + tmp + "&descasc=desc&state=" + state;
    } else {
        window.location = target;
    }
}
