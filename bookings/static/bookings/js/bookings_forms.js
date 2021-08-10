function ajaxGetAutosaveFormField(url, datas)
{
    $("body").css("cursor", "progress");
    $.ajax({
        url : url,
        type : 'GET',
        data : datas,
        dataType : 'html',
        beforeSend : function(){},
        success : function(data){
            var obj = JSON.parse(data);
            $(`#autosave-alert-${obj.q_id}`).html(obj.msg).fadeTo(5000, 500).slideUp(500, function(){
                $(`#autosave-alert-${obj.q_id}`).slideUp(500);
            });
        },
        error : function(e){alert("Error: "+e.responseText);},
        complete : function(){$("body").css("cursor", "default");}
    }); 
};

function addRow(url, datas, target)
{
    $("body").css("cursor", "progress");
    $.ajax({
        url : url,
        type : 'GET',
        data : datas,
        dataType : 'html',
        beforeSend : function(){},
        success : function(data){
            $(`#${target} tr:last`).after(data);
        },
        error : function(e){alert("Error: "+e.responseText);},
        complete : function(){$("body").css("cursor", "default");}
    }); 
};


function removeRow(url, datas, target)
{
    $("body").css("cursor", "progress");
    $.ajax({
        url : url,
        type : 'GET',
        data : datas,
        dataType : 'html',
        beforeSend : function(){},
        success : function(data){
            var obj = JSON.parse(data);
            $(`#${target}`).remove();
            var new_question_score = parseFloat(obj.q_score);
            var question_score = parseFloat($(`#autosave-question-score-${obj.q_id}`).html());
            var block_score = parseFloat($(`#autosave-block-score-${obj.b_id}`).html());
            var new_block_score = (block_score - question_score) + new_question_score;
            $(`#autosave-question-score-${obj.q_id}`).html(new_question_score.toFixed(2));
            $(`#autosave-block-score-${obj.b_id}`).html(new_block_score.toFixed(2));

        },
        error : function(e){alert("Error: "+e.responseText);},
        complete : function(){$("body").css("cursor", "default");}
    }); 
};

function uploadFile(obj, url, target, fi, question, field, index, token)
{
    var data = new FormData();
    data.append("file", obj[0].files[0]);
    data.append('fi', fi);
    data.append('question', question);
    data.append('field', field);
    data.append('index', index);
    data.append("csrfmiddlewaretoken", token);

    $.ajax({
        url: url,
        data: data,
        cache: false,
        contentType: false,
        processData: false,
        type: 'post',
        success: function (data) {
            $('#'+target).html(data);
        },
        error : function(e){alert("Error: "+e.responseText);},
    });
}


$(document).ready(()=>{
    $("body").on("change", ".autosave_form_field", function(e){
        var obj = $(this);
        msg_id = "#" + obj.attr("id") + "__msg";
        if (obj[0].checkValidity())
        {
            $(msg_id).html("");
            obj.removeClass("invalid");
            url = obj.data("url");
            fi = obj.data("fi");
            question = obj.data("question");
            field = obj.data("field");
            index = obj.data("index");
            value = obj.val();
            datas = {'fi':fi, 'question':question, 'field':field, 'index':index, 'value':value};
            ajaxGetAutosaveFormField(url, datas);
            checkEmpty(question); 
            e.preventDefault();
        }
        else
        {
            $(msg_id).html($(this).attr("title"));
            $(this).removeClass("valid").addClass("invalid");
        }
    });

    $("body").on("change", ".autoupload", function(e){
        var obj = $(this);
        msg_id = "#" + obj.attr("id") + "__msg";
        if (obj[0].checkValidity())
        {
            $(msg_id).html("");
            obj.removeClass("invalid");
            url = obj.data("url");
            target = obj.data("target");
            fi = obj.data("fi");
            question = obj.data("question");
            field = obj.data("field");
            index = obj.data("index");
            token = obj.data("csrf-token");
            uploadFile(obj, url, target, fi, question, field, index, token);
            checkEmpty(question); 
            e.preventDefault();
        }
        else
        {
            $(msg_id).html($(this).attr("title"));
            $(this).removeClass("valid").addClass("invalid");
        }
    });

    $("body").on("click", ".add_row", function(e){
        var obj = $(this);
        var url = obj.data("url");
        var target = obj.data("target");
            
        var datas = {};
        var args = obj.data();
        for(var i in args)
            if ((i != "url") && (i != "target"))
                datas[i] = args[i]

        addRow(url, datas, target);
        e.preventDefault();
    });

    $("body").on("click", ".remove_row", function(e){
        var obj = $(this);
        if (((obj.data("confirm")) && confirm(obj.data("confirm"))) || !(obj.data("confirm")))
        {
            var url = obj.data("url");
            var target = obj.data("target");
                
            var datas = {};
            var args = obj.data();
            for(var i in args)
                if ((i != "url") && (i != "target"))
                    datas[i] = args[i]

            removeRow(url, datas, target);
            e.preventDefault();
        }
    });

    $("body").on("click", ".set_multiselect", function(e){
        var obj = $(this);
        var multi_id = obj.data("multiselect-id");
        var id = obj.data("obj-id");
        var target = obj.data("target");
        if (obj.hasClass("multiselect_btn"))
        {
            var count = $("#"+multi_id+" :selected").length;
            if (count < 3)
            {
                $("#"+multi_id+" option[value='"+id+"']").prop("selected", true).change();
                obj.removeClass("multiselect_btn").addClass("multiselect_btn_act");
            }
            else
            {
                msg = "Se ha excedido el número de miembros de la comisión, solo se pueden seleccionar 3 miembros.";
                $("#"+target).html(msg).show().fadeTo(5000, 500).slideUp(500, function(){ $("#"+target).slideUp(500); });
            }
        }
        else
        {
            $("#"+multi_id+" option[value='"+id+"']").prop("selected", false).change();
            obj.removeClass("multiselect_btn_act").addClass("multiselect_btn");
        }
    });

});

