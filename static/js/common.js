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

function ajaxGetRemove(url, datas, target)
{
    $.ajax({
        url : url,
        type : 'GET',
        data : datas,
        dataType : 'html',
        beforeSend : function(){},
        success : function(data){
            if(data != "")
                $('#'+target).html(data);
            else
                $('#'+target).remove();
        },
        error : function(e){alert("Error: "+e.responseText);},
        complete : function(){}
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

	$("body").on("change", ".autosearch_change", function(e){
		var obj = $(this);
		autoSearch(obj);
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

    $("body").on("change", ".ark_change", function(e){
        var obj = $(this);
        if (((obj.data("confirm")) && confirm(obj.data("confirm"))) || !(obj.data("confirm")))
        {
            var url = obj.data("url");
            var value = obj.val();
            var target = "";
            var target_modal = "";
            if (obj.data("target"))
                target = obj.data("target");
            if (obj.data("target-modal"))
                target_modal = obj.data("target-modal");

            var datas = {'value': value};
            var args = obj.data();
            for(var i in args)
                if (i != "url")
                    datas[i] = args[i]
            ajaxGet(url, datas, target, target_modal);

            if (obj.data("clear"))
                clearHtml($("#" + obj.data("clear")));
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
        if (obj.data("ref-field"))
            ref_field = obj.data("ref-field");
        else
            ref_field = "pk";

        if (obj.data("bool"))
            if (obj.is(':checked'))
                value = "True";
            else
                value = "False";
        else
            value = obj.val();

        datas = {'model_name': model_name, 'obj_id': obj_id, 'field': field, 'value': value, "ref_field":ref_field};
        ajaxGetAutosave(url, datas, target);
        e.preventDefault();
    });

    $("body").on("click", ".autoremove", function(e){
        if (confirm("Esta seguro/a de que desea borrar el elemento?"))
        {
            model_name = $(this).data("model-name");
            obj_id = $(this).data("obj-id");
            url = $(this).data("url");
            target = $(this).data("target");
            datas = {'model_name': model_name, 'obj_id': obj_id};
            ajaxGetRemove(url, datas, target);
            if ($(this).data("hide"))
                $("#" + $(this).data("hide")).hide();
            e.preventDefault();
        }
    });

});


