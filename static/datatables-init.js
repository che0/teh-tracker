var dataTablesInit = function() {
    if($('#disabledatatables').text().length == 0)
    {
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
    }
}
$(document).ready(dataTablesInit);

if ('matchMedia' in window) {
    // Chrome, Firefox, and IE 10 support mediaMatch listeners
    window.matchMedia('print').addListener(function(media) {
        if (media.matches) {
            $('table').DataTable().destroy();
        } else {
            // Fires immediately, so wait for the first mouse movement
            $(document).one('mouseover', dataTablesInit);
        }
    });
};