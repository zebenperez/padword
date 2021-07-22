function ajaxGet(url, datas, target, modal_target)
{
	$("body").css("cursor", "progress");
	$.ajax({
		url : url,
		type : 'GET',
		data : datas,
		dataType : 'html',
		beforeSend : function(){},
		success : function(data){
			if (modal_target != "")
			{
				$('#'+modal_target+"-body").html(data);
				$('#'+modal_target).modal('show');
			}
			else
				if (target != "")
					$('#'+target).html(data);
		},
		error : function(e){alert("Error: "+e.responseText);},
		complete : function(){$("body").css("cursor", "default");}
	});
};

function ajaxGetAutosave(url, datas, target)
{
    $("body").css("cursor", "progress");
    $.ajax({
        url : url,
        type : 'GET',
        data : datas,
        dataType : 'html',
        beforeSend : function(){},
        success : function(data){
            $("#"+target).html(data).show().fadeTo(5000, 500).slideUp(500, function(){
                $("#"+target).slideUp(500);
            });
        },
        error : function(e){alert("Error: "+e.responseText);},
        complete : function(){$("body").css("cursor", "default");}
    }); 
};

function autoSearch(obj, num_rows=0)
{
	url = obj.data("url");
	target = obj.data("target");
	datas = {'num_rows': num_rows,};
	if (obj.data("related"))
	{
		related = obj.data("related").split(",");
		for(i in related)
		{
			key = $("#"+related[i]).attr('name');
			value = $("#"+related[i]).val();
			datas[key] = value;
		}
	}
	ajaxGet(url, datas, target, '');
}

$(document).ready(()=>{
	$("body").on("keyup", ".autosearch", function(e){
		var obj = $(this);
		setTimeout(function(){
			autoSearch(obj);
		}, 1000);
		e.preventDefault();
	});
    $("body").on("click", ".ark", function(e){
        var obj = $(this);
        if (((obj.data("confirm")) && confirm(obj.data("confirm"))) || !(obj.data("confirm")))
        {
            url = obj.data("url");
            var target = "";
            var target_modal = "";
            if (obj.data("target"))
                target = obj.data("target");
            if (obj.data("target-modal"))
                target_modal = obj.data("target-modal");

            var datas = {};
            var args = obj.data();
            for(var i in args)
                if (i != "url")
                    datas[i] = args[i]
            ajaxGet(url, datas, target, target_modal);
            if (obj.data("show"))
                $("#" + obj.data("show")).show();
            e.preventDefault();
        }
    });

    $("body").on("change", ".autosave", function(e){
        var obj = $(this);
        msg_id = "#" + obj.attr("id") + "__msg";
        if (obj[0].checkValidity())
        {
            $(msg_id).html("");
            obj.removeClass("invalid");
        }
        else
        {
            $(msg_id).html(obj.attr("title"));
            obj.removeClass("valid").addClass("invalid");
        }

        model_name = obj.data("model-name");
        obj_id = obj.data("obj-id");
        url = obj.data("url");
        target = obj.data("target");
        field = obj.attr("name");

        if (obj.data("bool"))
            if (obj.is(':checked'))
                value = "True";
            else
                value = "False";
        else
            value = obj.val();

        datas = {'model_name': model_name, 'obj_id': obj_id, 'field': field, 'value': value};
        ajaxGetAutosave(url, datas, target);
        e.preventDefault();
    });


});


