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
    $("body").on("change", ".toggleCronLock", function(e){
        var field = $(this).data("field");
        var fieldTime = $(this).data("field-time");
        var className = "."+$(this).data("class-name");
        if (!$(this).is(":checked")) {
            $("#"+fieldTime).val("00:00"); 
            $("#"+field).data("time", "-1"); 
            $("#"+field).click();
            $(className).prop("disabled", "disabled");
        } else {
            $("#"+fieldTime).val("12:00"); 
            $("#"+field).val("12:00"); 
            $("#"+field).click();    
            $(className).prop("disabled", "");
        }
    });

    $("body").on("click", ".btnLock", function(e){
        var obj = $(this)
        var input = "#ch_"+obj.data("id");
        var activeClass = "btn-info";
        if (obj.hasClass(activeClass)) {
            obj.removeClass(activeClass);
            $(input).val("");
        } else {
            obj.addClass(activeClass);
            $(input).val(obj.data("id"));
        }
    });
});
