function checkCronEnable(state, className){
    if (state == "-1"){
        $("."+className).prop("disabled", "disabled"); 
        $("."+className+"-head").removeClass("bg-success")
    }
}

$(document).ready(()=>{
    $("body").on("change", ".toggleCron", function(e){
        var fields = $(this).data("fields").split(",");
        var className = "."+$(this).data("class-name");
        var head = className+"-head" ;
        if (!$(this).is(":checked")) {
            for (i in fields){
                $("."+fields[i]).val("-1"); 
                $("."+fields[i]).change();
            };
            $(className).prop("disabled", "disabled");
            $(head).removeClass("bg-success");
        } else {
            for (i in fields){
                $("."+fields[i]).val("1"); 
                $("."+fields[i]).change();    
            };
            $(className).prop("disabled", "");
            $(head).addClass("bg-success");
        }
    });
});
