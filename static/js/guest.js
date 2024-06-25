function checkGuestDates(obj, msg) {
    var checkIn = new Date($("#check_in").val()+" "+$("#check_in_time").val());
    var checkOut = new Date($("#check_out").val()+" "+$("#check_out_time").val());
    $("#btn-date").data(obj.attr("id"), obj.val());
    if(checkOut < checkIn)
        $("#check_out__msg").html(msg);
    else {
        $("#check_out__msg").html("");
        $("#btn-date").click();
    }
}

function setGuestFields(id){
    if (confirm("Are you sure to modify the name, surname and phone?")){
        var room = $("#s-room").val();
        $("#name").val("Guest "+room);
        $("#name").change();
        setTimeout(function(){
            $("#surname").val(id);
            $("#surname").change();
        }, 500);
        setTimeout(function(){
            var str = "";
            for (var i=0; i < 6; i++)
                str += Math.floor(Math.random() * 6);
            $("#mobile").val(str);
            $("#mobile").change();
        }, 1000);
    }
}

function setGuestSurname(id){
    if (confirm("Are you sure to modify the surname?")){
        $("#surname").val(id);
        $("#surname").change();
    }
}

$(document).ready(()=>{});

