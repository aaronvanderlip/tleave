

$(function(){
    $('#route').select(function(){
        selectedroute = $('#route :selected').val();
        $.get( '${tg.url("/stationlist")}',
        {tg_format:'json',route:selectedroute},
        function(data){
            updateStationList(data);
            })
    })
}
) 

function updateStationList(data){
    alert(data);
}
 
