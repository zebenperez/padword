/*---------------------
	chat_sende.js 
	Se encarga de enviar los mensajes al servidor, haciendo uso de una caché para evitar la perdida  de los mismos 
	en caso de que se cambie de sala antes de que el mensaje se haya enviado.
-
-------------------*/
class MessageSender
{
	
	static LISTENERS = {'form': null, 'input': null};
	constructor (form_selector_id, message_input ,messages_container_id, template , image_template)
	{
		this._form = document.getElementById(form_selector_id);
		this._input = document.getElementById(message_input);
        this._image_field = document.getElementById("id_image");
		this._response_to_field=document.getElementById("id_response_to");
		this._messages_container = document.getElementById(messages_container_id);
		this._template = template;
		this._image_template = image_template;
		this._response_template = (username, msg)=>`<div class="response_box"><p><i class="fas fa-at"></i>${username}</p><p>${msg}</p><div>`
		this._set_events_listeners();
	}

	//setter - getters
	set response_template (value) { this._response_template = value}


	//static
    static generate_msg_identifier()
	{
		let LENGTH = 10;
		let result  = '';
		let characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
		let charactersLength = characters.length;
		for ( let i = 0; i < LENGTH; i++ ) {
			result += characters.charAt(Math.floor(Math.random() * charactersLength));
		}

		return result;
	}

	static clean_listeners()
	{
		try{
			if (MessageSender.LISTENERS.form != null)
			{
				this._form.removeEventListener("submit", MessageSender.LISTENERS.form);
				delete MessageSender.LISTENERS.form
			}
		}catch(err){
			//console.error("[clean listener 1] "+err);
		}
		try{
			if (MessageSender.LISTENERS.input != null){
				this._input.removeEventListener("keydown", MessageSender.LISTENERS.input);
				delete MessageSender.LISTENERS.input
			}
		}catch(err){
			//console.log("[clean listener 2] "+err);
		}
    	try{
			if (MessageSender.LISTENERS.image != null){
				this._image_field.removeEventListener("change", MessageSender.LISTENERS.image);
				delete MessageSender.LISTENERS.image
			}
		}catch(err){
			//console.log("[clean listener 2] "+err);
		}
	}

	_set_events_listeners()
	{ 
		MessageSender.clean_listeners()	
		let self = this
		const submit_listener = (e)=> self._submit(e)
		this._form.addEventListener("submit", submit_listener) //el uso de self es para no perder el contexto en el metodo _cache_add
		MessageSender.LISTENERS['form'] = submit_listener

		const enter_listener = (e)=> self._press_return(e)
		this._input.addEventListener("keydown", enter_listener);
		MessageSender.LISTENERS['input']= enter_listener;


        const image_listener = (e)=> self._submit(e)
        this._image_field.addEventListener("change", image_listener);
        MessageSender.LISTENERS['image'] = image_listener

		const reply_listener = (e)=> self._reply_listener(e)
		this._messages_container.addEventListener("click", reply_listener);

	}
	
	_get_response_template()
	{
		let self = this;
	}

	//FIXME: El metodo template deberia encargarse no solo de devolver una plantilla sino de dar el html que es insertado 
	// recibiendo en dos parametros (content, y msg_id) los datos que necesite
	_print_message(content, msg_id, response_obj)
	{
		let response_tmp="";
		if (response_obj)
		{
			response_tmp = this._response_template(response_obj.reply_user, escape_html(response_obj.reply_content));
		}
		this._messages_container.innerHTML += this._template(escape_html(content), msg_id, response_tmp);
	}

	_press_return(e){
		if (e.ctrlKey && e.keyCode == 13) 
   		{
			e.target.value += "\n"
			return;
   		}
		if (e.keyCode==13)
		{
			e.preventDefault();
			if (e.target.value.trim().length > 0);
			{
				this._submit(e);
			}
		}
	}

	_submit(ev){
		ev.stopPropagation();
		ev.preventDefault();

		let self = this;
		if (self._input.value.length > 0 || self._image_field.value.length > 0)
		{
			self._send();
		}
	}

	_send()
	{
		let self = this;
		let form_data = new FormData(self._form)
		let content = escape_html(self._input.value);

		let msg_id = MessageSender.generate_msg_identifier();
		let response_obj = null
		if (self._reply_user)
		{
			response_obj = new Object();
			response_obj.reply_user = self._reply_user;
			response_obj.reply_content = self._reply_content;
		}
		self._print_message(content,  msg_id, response_obj);
		go_bottom(self._messages_container, 0)
		self._reset_form();
		form_data.append("message_identifier", msg_id);
		
		let url = this._form.getAttribute("action")
		fetch (url , 
			{ 
			  method : "POST",
			  body: form_data
			}
		).then(res => res.json())
		.then(data=> {
			 self._update_image(data);
			 self._update_timestamp(data);
			 self._update_datasets(data);
             
		})
        //.then(data=>go_bottom(self._messages_container, 0))
		.catch(error => console.error(error));
	}
	
	//FIXME : Refactorizar y unir con update_datasets
	_update_timestamp(data)
	{
		//El id del mensaje sirve exclusivamente para identificar al mensaje dentro del DOM por eso 
		// Una vez actualizada la marca de tiempo, el id desaparecerá (seleccionando el padre y borrado el elemento que tiene el id)
		let element = document.getElementById(`id_time_${data.message_identifier}`).parentElement
		element.innerHTML= data.messages[0].date;	
		document.getElementById(`msg__container__${data.message_identifier}`).setAttribute("id",`msg__container__${data.messages[0].pk}` );

	}
	_update_datasets(data)
	{
		let msg_pk = data.messages[0].pk;
		let msg_selector = `msg__container__${msg_pk}`;
		let user = data.messages[0].user
		let element = document.getElementById(msg_selector);
		element.dataset.message_id = msg_pk
		element.dataset.message_user = user;
		let reply_btn = element.querySelector(".reply_btn");
		reply_btn.dataset.target=msg_selector;
	}
	_update_image(data)
	{
		let self = this;
		let message = data.messages[0]
		let element = $(`#id_time_${data.message_identifier}`)
		if (message.image)
		{
			$(self._image_template(message.image)).insertAfter(element.closest("div"));
		}
	}

	_reply_listener(e)
	{
		let self = this;	
		let clicked_btn = e.target.closest(".reply_btn");
		if (clicked_btn)
		{
			let msg_container = e.target.closest(".message_container");
			let msg_pk = msg_container.dataset.message_id;
			let container = document.getElementById("preview-container")
			self._reply_user = msg_container.dataset.message_user;
			self._reply_content = msg_container.querySelector(".message-content").textContent;

			let response_box = self._response_template(self._reply_user, escape_html(self._reply_content), "");
			container.innerHTML= response_box;
			container.closest("#preview-container-box").style.display="block";
			self._response_to_field.value=msg_pk;
			self._input.focus();
		}			
	}

	_reset_form()
	{
		this._reply_user = null;
		this._reply_content = null;
		this._input.value="";
        this._image_field.value =""
		this._response_to_field.value=""
		try{
			document.getElementById("preview-container-box").style.display="none";
		}catch{};
	}


}

