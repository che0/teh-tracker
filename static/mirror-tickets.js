async function downloadTicket(id)
{
    console.log(id);
    $.getJSON('/ticket/json/' + id + '/', function(data){
        localStorage.setItem('ticket_' + id, JSON.stringify(data));
    });
    // FIXME: Do not throw error when it is 404, it is normal, IDs are quazisequent.
}

async function deleteDeletedTickets()
{
    for(var id = Number(localStorage.ticket_highest); id > 0; id--)
    {
        if('ticket_' + id in localStorage)
        {
            $.getJSON('/ticket/json/deleted/' + id, function(data) {
                if(data.deleted) { localStorage.removeItem('ticket_' + data.pk) }
            });
        }
    }
}

async function checkAndDownloadTickets() {
    $.getJSON('/tickets/json/highest/', function(data){
        var start_id = 1;
        if(Number(localStorage.ticket_highest) < data.id) { start_id = Number(localStorage.ticket_highest)}
        if(Number(localStorage.ticket_highest) == data.id) { return; }
        for(var id = data.id; id >= start_id; id--)
        {
            downloadTicket(id);
            localStorage.ticket_highest = data.id;
        }
    });
}

function displayTickets()
{
    var timeout = 0;
    if(localStorage.length == 0) timeout = 100;
    setTimeout(function() {
        var data = [];
        for(var id = Number(localStorage.ticket_highest); id > 0; id--)
        {
            if('ticket_' + id in localStorage)
            {
                var ticket = JSON.parse(localStorage['ticket_' + id]);
                
                data.push([
                    ticket.pk,
                    ticket.event_date,
                    ticket.summary,
                    ticket.grant, // Grant
                    ticket.topic, // Topic
                    ticket.requested_by, // Requestor
                    ticket.requested_expeditures, // Requested expeditures
                    ticket.accepted_expeditures, // Accepted exp
                    ticket.paid_expeditures, // Paid exp
                    ticket.state, // State
                    ticket.changed // Changed

                ])
            }
            
        }
        var language = $('meta[http-equiv="Content-Language"]').attr('content');
        var fullLanguage = "English";
        switch(language) {
            case "cs":
                fullLanguage = "Czech";
        }
        var url = "https://cdn.datatables.net/plug-ins/9dcbecd42ad/i18n/" + fullLanguage + ".json";
        var table = $('table').DataTable({
            "data": data,
            "order": [[0, "desc"]],
            "language": {
                    "url": url,
                }
        });
    }, timeout);
}

checkAndDownloadTickets();