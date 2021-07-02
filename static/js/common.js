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
});


