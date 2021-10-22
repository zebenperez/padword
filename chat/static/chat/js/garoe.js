/* garoe-framework v 0.0.1 copyright 2018 */

/* TEMPLATES */
const ConfirmModal = ({message, modal_id, button_id })  => `
<div class="modal fade" tabindex="-1" id="${modal_id}" role="dialog">
  <div class="modal-dialog" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title text-warning"> <i class="fa fa-exclamation-triangle"></i> Confirmación necesaria</h5>
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
     </div>
     <div class="modal-body" style="color:gray">
          ${message}
      </div>
      <div class="modal-footer text-right">
        <button type="button" class="btn btn-default col-5 offset-1 " data-dismiss="modal">No</button>
        <button type="button" class="btn btn-danger col-5 offset-1" id="${button_id}">Sí</button>
      </div>
    </div><!-- /.modal-content -->
  </div><!-- /.modal-dialog -->
</div><!-- /.modal -->
`;


const Modal = ({modal_title, modal_content, modal_id})  => `
<div class="modal fade" tabindex="-1" id="${modal_id}" role="dialog">
  <div class="modal-dialog modal-lg" style=""  role="document">
    <div class="modal-content" style="width:130%; margin-left:-10%;">
      <div class="modal-header">

        <h5 class="modal-title text-primary" style=""> ${modal_title}</h5>
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
      </div>
      <div class="modal-body" style="color:gray" >
	  	<div class="row">
			<div class="col-12" id="body_${modal_id}">
          		${modal_content}
		  	</div>
		</div>
      </div>
      <div class="modal-footer text-right">
      </div>
    </div><!-- /.modal-content -->
  </div><!-- /.modal-dialog -->
</div><!-- /.modal -->
`;



const DivDanger = ({message}) => `<div class="alert alert-danger fade in col-12"><i class="fa fa-times"></i> ${message} </div>`;
const DivLoading= ({message}) => `<div class="alert alert-info col-12"><h5><i class="fa fa-spinner fa-spin" 
												style="animation:fa-spin 0.6s infinite linear!important; 
													   -webkit-animation: fa-spin 0.6s infinite linear !important;"></i> ${message}</h5></div>'`;
// ------------------------------------
/* GENERAL UTILITIES  */
// from https://stackoverflow.com/questions/3452546/how-do-i-get-the-youtube-video-id-from-a-url
function youtube_parser(url){
    var regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#\&\?]*).*/;
    var match = url.match(regExp);
     return (match&&match[7].length==11)? match[7] : false;
}


function param_is_true(dic, param_name, def=false)
{
	if (param_name in dic)
	{
		if (dic[param_name] == "true"  || dic[param_name] == true){ return true;}
		return false;
	}
	return def;
}


function get_attribute(element ,name, def=null)
{
	var attr = element.attr(name);
	if (typeof attr !== typeof undefined && attr !== false) {
		return attr
	}
	return def;
}


function get_data(element, name, def=null)
{
	try{
		var attr = element.data(name);
		if (typeof attr !== typeof undefined){
			return attr;
		}
	}catch(err){
		console.error('[ get-data-fail] '+name)
	}
	return def
}


function bottom_scroll(element)
{
    element.scrollTo(0,element.scrollHeight -element.clientHeight);
}

function is_scroll_at_top(element, offset=30){
    return (element.scrollTop < offset)
}


function is_scroll_at_bottom(element, offset=10)
{
   return element.scrollTop >= (element.scrollHeight - (element.offsetHeight + offset))  
}

/* DEPRECATED
function get_random_string(len)
{
	return Math.random().toString(36).substring(len);
}
*/

function get_random_string(len){
	var result  = '';
	var characters       = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
	var charactersLength = characters.length;
	for ( var i = 0; i < len; i++ ) {
		result += characters.charAt(Math.floor(Math.random() * charactersLength));
	}
	return result;

}

function set_cookie(key, value, minutes) {
   var now = new Date();
   now.setTime(now.getTime() + (minutes * 60 * 1000));
   value = escape(value)
   cookie_str = `${key}=${value}; expires=${now.toUTCString()};`
   document.cookie = cookie_str
   
}

function get_cookie(key){
    var name = `${key}=`;
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for(var i = 0; i <ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
          c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
          return c.substring(name.length, c.length);
        }
    }
    return null;

}

function check_cookie(key) {
  var username = get_cookie(key);
  if (username != null) {
      return true
  }else {
      return false;
  }
}


/*-----------------------------*/
/* DOM UTILS */
/*-----------------------------*/

function ga_show_loading(container, message="Cargando ...")
{
	try{
		container.empty();
		container.html([{ message: message}].map(DivLoading));
		

	}catch(err)
	{
		console.error("[show_loading] ERROR"+err);
	}
}

function ga_confirm_modal(message, callback)
{
	$_modal_id = get_random_string(7);
	button_id = "accept_"+$_modal_id
		
	$('body').undelegate('#'+button_id,'click').delegate('#'+button_id,'click', function () {
		callback();
		$('body').undelegate('#'+button_id,'click', $(this));
		$('#'+$_modal_id).modal('hide');
			
	});

	$('body').append([{ message: message, modal_id: $_modal_id, button_id:button_id}].map(ConfirmModal));
	$('#'+$_modal_id).modal('show');


}


function ga_show_modal(modal_title, modal_content, modal_id=null)
{
	if (modal_id == null){ modal_id = get_random_string(7);}
	if (modal_title == null){ modal_title ="";}
	$('body').append([{ modal_title: modal_title, modal_content: modal_content, modal_id:modal_id}].map(Modal));
	$('#'+modal_id).modal('show');
	$('#'+modal_id).off('hidden.bs.modal').on('hidden.bs.modal', function (e) {
            $(this).html("").empty();
  			modal_element = document.getElementById(modal_id);
			
            modal_element.parentNode.removeChild(modal_element);
	});
}



(function( $ ){

   $.fn.ajax_send_file_form = function (response_container, form_element,  options){
   
  			if (response_container != "modal" ){
				response_container= $(response_container);
			}else{
				mtitle = ""
				if ('modal_title' in options)
				{
					mtitle = options['modal_title'];
				}
			}
			form_selector=$(this);
			response_container= $(response_container);
			url = form_selector.attr('action');
			method = get_attribute(form_selector, 'method', 'POST');
			load_indicator = param_is_true(options, 'loading', true);
			show_error = param_is_true(options, 'ga-show-errors');

		  	$.ajax({
    			url: url,
    			type: method,
				data: new FormData(form_element),
				cache: false,
				contentType:false,
				processData:false,
				beforeSend: function(data){
					if (load_indicator && response_container != 'modal') {
						ga_show_loading(response_container, 'Procesando datos, por favor espere ...');
					}
				},
    			success: function(data) {
						if (response_container=="modal"){
							ga_show_modal(mtitle, data);
						}else{
							$(response_container).html(data);	
						}

				},
				error: function(data){
					if (show_error){
							if (response_container == "modal"){
								ga_show_modal(mtitle, [{message:'Ha habido un error al cargar los datos de esta sección'}].map(DivDanger));
							}else{
	
								$(response_container).html([{ message: 'Ha habido un error al cargar los datos de esta sección'}].map(DivDanger));
							}

					}

					console.error("[ajax-send-for] "+data.toString());
				},
				complete: function(data){
				}
  			});
	}



   $.fn.ajax_send_form = function(response_container, options) {
			if (response_container != "modal" ){
				response_container= $(response_container);
			}else{
				mtitle = ""
				if ('modal_title' in options)
				{
					mtitle = options['modal_title'];
				}
			}
			form_selector=$(this);
			response_container= $(response_container);
			url = form_selector.attr('action');
			method = get_attribute(form_selector, 'method', 'POST');
			load_indicator = param_is_true(options, 'loading', true);
			show_error = param_is_true(options, 'ga-show-errors');

		  	$.ajax({
    			url: url,
    			type: method,
				data: $(form_selector).serialize(),
				beforeSend: function(data){
					if (load_indicator && response_container != 'modal') {
						ga_show_loading(response_container, 'Procesando datos, por favor espere ...');
					}
				},
    			success: function(data) {
						if (response_container=="modal"){
							ga_show_modal(mtitle, data);
						}else{
							$(response_container).html(data);	
						}
				},
				error: function(data){
					if (show_error){
							if (response_container == "modal"){
								ga_show_modal(mtitle, [{message:'Ha habido un error al cargar los datos de esta sección'}].map(DivDanger));
							}else{
	
								$(response_container).html([{ message: 'Ha habido un error al cargar los datos de esta sección'}].map(DivDanger));
							}

					}

					console.error("[ajax-send-for] "+data.toString());
				},
				complete: function(data){
				}
  			});
	};

	$.fn.ajax_load = function(response_container, options) {
			if (response_container != "modal" ){
				response_container= $(response_container);
			}else{
				mtitle = ""
				if ('modal_title' in options)
				{
					mtitle = options['modal_title'];
				}
			}
			
			url = $(this).attr('href');
				
			if (typeof url == typeof undefined || url == false) {
				url = options['url']; 
			}
			
			method = "GET"
			
			if ('method' in options)
			{
				method = options['method'];
			}
			modal_id = null;
			if ('modal_id' in options)
			{
				modal_id = options['modal_id'];
			}
			if ( !url || url === ""  )
			{
				if (response_container == "modal"){
					ga_show_modal(mtitle, [{message:'Ha habido un error al cargar los datos falta url '}].map(DivDanger));
				}else{
					$(response_container).html([{ message: 'Ha habido un error al cargar los datos falta url'}].map(DivDanger));
				}

			}else{
				load_indicator = param_is_true(options, 'loading', false);
				show_error = param_is_true(options, 'ga-show-errors',true);
					
				$.ajax({
					url: url,
					type: method,
					beforeSend: function(data){
						if (load_indicator && response_container != "modal") {
							ga_show_loading(response_container);
						}
					},
					success: function(data) {
						if (response_container=="modal"){
							
							ga_show_modal(mtitle, data, modal_id);
						}else{
							$(response_container).html(data);	
						}
					},
					error: function(data){
						if (show_error){
							
							if (response_container == "modal"){
								ga_show_modal(mtitle, [{message:'Ha habido un error al cargar los datos de esta sección'}].map(DivDanger));
							}else{
	
								$(response_container).html([{ message: 'Ha habido un error al cargar los datos de esta sección'}].map(DivDanger));
							}
						}
						console.error("[ajax-load] "+data.toString());

					},
					complete: function(data){
						
					}
				});
			}
	};

	$.fn.scroll_to = function(target) {
		$('html, body').animate({
			scrollTop:$(target).offset().top - 100
		}, 500);
	}


})( jQuery )


/* Validar formularios */

function validateEmail(email) {
    var re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

function validateSlug(text)
{
	var re = /^[A-Za-z0-9]+(._-[A-Za-z0-9]+)*$/
	return re.test(String(text));
}

function validatePassword(pass)
{
	if (str.length  > 7){
		return true
	}

	return false
}


$('body').delegate('.ga-val-input','input', function(){
	
	validatorType = $(this).data('ga-val-input');
	validated = false
	value = $(this).val();
	
	switch( validatorType )
	{
		case 'slug':
			validated = validateSlug(value);
			break;
		case 'email':
			validated = validateEmail(value);
			break;
		case 'password':
			validate = validatePassword(value);
			break;
		case 'match':
			match_field_name= $(this).data('ga-match');
			if($("input[name='"+match_field_name+"']").val() == $(this).val()) {validated=true;}
			break;
		case 'checkbox':
			validated = $(this).is(':checked');
			break;
	}

	if (validatorType != "checkbox")
	{
		if (validated || value == "")
		{
			$(this).removeClass('is-invalid');
		}else{
			$(this).addClass('is-invalid');
		}
	}else{
			submit_btn = $(this).closest('form').find(':submit');
			if (validated) {submit_btn.removeAttr("disabled")}
			else { submit_btn.attr("disabled", "disabled");}
	}

});

$('body').delegate('.ga-close-modal', 'click', function(){
    $('.modal').modal('hide');
});




$('body').delegate('input.ga-binded-field', 'input', function(){

	field = $(this);
	binded_to = $(field.data('ga-binded-to'));
	binded_to.val(field.val());

});

$('body').delegate('input[type=checkbox].ga-select-all', 'click', function(){
	selector = $(this).data('ga-target');
	value = $(this).is(':checked');
	$(selector).prop('checked', value);

});

/* AJAX */


$('body').delegate('.ga-ajax-form', 'submit', function(e){
	e.preventDefault();	
	e.stopPropagation();
	target = $(this).data('ga-target');
    method = get_attribute($(this), 'method', 'POST');

	$(this).ajax_send_form(target, {'loading': $(this).data('ga-loading'), 'method': method, 'show_errors': $(this).data('ga-show-errors')});	
	
});


$('body').delegate('.ga-ajax-file-form', 'submit', function(e){
	e.preventDefault();	
	e.stopPropagation();
	target = $(this).data('ga-target');
	$(this).ajax_send_file_form(target, e.target, {'loading': $(this).data('ga-loading'), 'show_errors': $(this).data('ga-show-errors')});	
	
});



$('body').undelegate('.ga-ajax-load', 'click').delegate('.ga-ajax-load', 'click', function(e){
	e.preventDefault();
	e.stopPropagation();
	let self = $(this);
	target = $(this).data('ga-target');
	
	if ( $(this).data('ga-scroll-to'))
	{
		$('body').scroll_to($(this).data('ga-scroll-to'));
	}

	$(this).ajax_load(target, {'loading' : $(this).data('ga-loading'), 
		'show_errors':$(this).data('ga-show-errors'), 
		'method': get_data(self, 'ga-method', 'GET'),
		'modal_title':get_data(self, 'ga-modal-title', null),
		'modal_id': get_data(self,'ga-modal-id', null),
		});
});


$('body').undelegate('.ga-ajax-load-confirm', 'click').delegate('.ga-ajax-load-confirm', 'click', function(e){
	e.preventDefault();
	e.stopPropagation();
    message = "¿Seguro que desea realizar esta acción?"
    let self = $(this)
    
	if (self.data('ga-confirm-message'))
    {
        message = self.data('ga-confirm-message')
    }
    
	ga_confirm_modal(message, function() {
			target = self.data('ga-target');
			self.ajax_load(target, {'loading' : self.data('ga-loading')})
	
	});

});

$('.ga-load-on-ready').on('load', function(e){
    
    target = $(this).data('ga-target');
    url = $(this).data('ga-url');
	$(this).ajax_load(target, {'loading' : $(this).data('ga-loading'), 'url': url });

});



/*$('body').delegate('.ga-click-on-load', 'click', function(e){
	e.preventDefault();
	e.stopPropagation();
	target = $(this).data('ga-target');
	$(this).ajax_load(target, {'loading' : $(this).data('ga-loading')})
	
});*/


$('body').delegate('.ga-input-search', 'input', function(e){
	e.preventDefault();
	e.stopPropagation();
	let self = $(this)
	form = self.closest("form");
	target = self.data('ga-target');
	allow_empty = get_data(self, 'ga-allow-empty', false);
	min_length = get_data(self, 'ga-min-length',3);
	
	val = self.val();
	if (val.length > min_length || (val.length == 0 && allow_empty )){
		var prev_length = val.length;
		setTimeout(function(){
			if (prev_length == val.length)
			{
				form.ajax_send_form(target, {'loading': self.data('ga-loading')});
			}
		},200)
	}else{
		if (val.length == 0) { $(target).empty(); }
		return false;
	}

});

$('body').delegate('.ga-select-load','change', function(e){
	e.preventDefault();
	e.stopPropagation();
	let self = $(this);
    key = $(this).attr('name');
	val = self.val()	
    if (val != "" && val != null)
    {
	    target = self.data('ga-target');
	    url_datas = self.data('ga-url').split("?")
        url = url_datas[0]+"?"+key+"="+val;
        try{
            url = url+"&"+url_datas[1];
        }catch(err){}
            
	    $(this).ajax_load(target, {'loading' : $(this).data('ga-loading'), 'url':url});
    }
});

$('body').delegate('.ga-limited-field', 'keyup', function(e){
    
    e.preventDefault();
    e.stopPropagation();
    try{
        limit = parseInt(get_attribute($(this), 'data-ga-limit', -1));
        length = $(this).val().length
        if (limit > 0){
            if ($(this).val().length > limit)
            {
                val  = $(this).val();
                $(this).val(val.substring(0,limit-1));
                return false;
            }
            return true;
        }
    }catch(e){
        console.error(e);
    }
});


/*--------------
 * Filtrao de elementos
---------------*/
$('body').delegate('.ga-search-filter', 'input', function(e){
    var search_term = $.trim($(this).val());
    search_selector = $(this).data('ga-search-items');
    if (search_term.length < 1)
    {
        $(search_selector).show();

    }else{
        $(search_selector).each(function(){
            $(this).toggle($(this).filter('[data-ga-search-term*="'+search_term+'"]').length > 0);
        });
    }

});

$('body').delegate('.ga-clean-search-filter', 'click', function(e){
    $('.ga-search-filter').val("");
    $('.ga-search-filter').trigger("input");
});


/*--------------
* OTROS
---------------*/
$('body').delegate('.ga-send-on-enter', 'keydown', function(e){
	
	if (e.ctrlKey && e.keyCode == 13) 
   	{
		let value = $(e.target).val()
		$(e.target).val(value+"<br/>"+'\n');
		return;
    }
	
	if (e.keyCode == 13)
	{
		e.preventDefault();
		$(this).closest('form').submit();
	}
});

function wait_for_confirm(e){
	
	e.preventDefault();
	message = "¿Seguro que desea realizar esta acción?"
	e.preventDefault();
	
    if ($(this).data('ga-confirm-message'))
    {
        message = $(this).data('ga-confirm-message')
    }

	let self =$(this);
	
	tag = self.prop("tagName");
	if (tag == "A")
		ga_confirm_modal(message, function(){ window.location.href=self.attr('href'); });
	if (tag == "BUTTON")
	{
		ga_confirm_modal(message, function(){ $(self.data('ga-form')).submit()  });
	}
}


$('body').delegate('a.ga-confirm', 'click', wait_for_confirm);
$('body').delegate('button[type="submit"].ga-confirm', 'click', wait_for_confirm);

$('body').delegate('.ga-clean', 'click', function(e){
	
	target = $(this).data('ga-target');
	$(target).empty();
		
});


/***********************
	WIDGETS
************************/

$('.ga-checkbox').each(function(e){

		id = get_attribute($(this), 'id', get_random_string(9));
		$(this).attr('id', id);
		html = '<label class="ga-checkbox-label" for="'+id+'"></label>';
		$(this).after(html);	
		
});

function sum(){
	$('.ga-sum').each(function(e){
		elements_selector = $(this).data('ga-sum');
		sum_value = 0.0;
		$(elements_selector).each(function(e){
			text = $(this).text().replace(",",".") 
			if (isNaN(text)) { return};
			sum_value += parseFloat(text);
		});

		$(this).text(""+sum_value.toFixed(1));


	});
}
/***********************
ON-LOAD METHODS
************************/
$(document).ready(function(){
/*	auto_loads = $('.ga-load-on-ready').length;
	if (auto_loads > 0)
	{
		$('.ga-load-on-ready').each(function(e){
			target = $(this).data('ga-target');
			url = $(this).data('ga-url');
			$(this).ajax_load(target, {'loading' : $(this).data('ga-loading'), 'url': url });
		});
	}
*/
    $('.ga-load-on-ready').trigger("load");
    $('.ga-click-on-load').each(function(){ $(this)[0].click();});
	sum();
})


