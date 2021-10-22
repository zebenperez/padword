/*------------------------------
     chat_receiver.js 
	 Se encarga de gestionar los mensajes recibidos del servidor.
	  	1) Comprueba que los mensajes son para la sala actual 
		2) Envia el aviso de lectura al servidor, Mientras el servidor responde, se almacenan los mensajes leidos 
		   en una cache local que evite que se repitan
 ------------------------------*/ 

class MessageReceiver
{
	static INSTANCE
	// ----
	// user : El usuario de la sesion actual instancia de la clae User de chat.js
	// mesages_container: id del contenedor de mensajes
	// confirmation_url : url donde debe enviarse el aviso de lectura, (listado de ids de los mensajes recibidos), si se deja a null, no se envia
	// user_template: function que recibirá un mensaje de usuario y se encargará de devolver el html para mostarlo
	// external_template : funcion que recibirá un mensaje de otros usuarios y se encargará de devolver el html para mostrarlo.
	constructor (user, messages_container, confirmation_url, pagination_url , user_template, external_template, image_template)
	{
		let self = this
		self._MARKER_ID ="last_readed_marker"
		self._user = user
		self._readed = new Array();
		self._confirmation_url = confirmation_url;
		self._pagination_url = pagination_url;
		self._container = document.getElementById(messages_container);
		self._user_template = user_template;
		self._external_template = external_template;
		self._last_scroll_position = this._container.scrollTop;
		self._image_template = image_template;
		self._unreaded_marker = `<div class='alert alert-info text-center mt-4' style="margin-top:3em!important" id='${self._MARKER_ID}'>&#11015; Mensajes Nuevos &#11015; </div>`
		self._last_readed_message = null;
		self._response_template = "";
		self._has_focus = true //permite indicar si la pestaña del navegador es la activa para definir el comportamiento
		MessageReceiver.INSTANCE = this;

		
		self._container.addEventListener("scroll", (e)=>{self._scroll_listener(e)});
		
	}

	
	set unreded_marker (value) { this._unreaded_marker = `<div id="${this._MARKER_ID}">${value}</div>` }
	set last_readed_message(value) {this._last_readed_message = value }
	set has_focus (value) { this._has_focus = value }
	set response_template (value) { this._response_template = value}


	_scroll_listener(ev)
	{
		let self = this;
		let offset = 120
		let scroll = self._container.scrollTop
		if (scroll_reaches(this._container, 'top', offset))
		{	
			//comprobamos si el scroll esta subiendo
			if (scroll < self._last_scroll_position){
				self._load_previous();
			}
		

		}
		if (scroll_reaches(this._container, 'bottom', offset))
		{	 
			//comprobamos si el scroll esta subiendo
			if ( scroll > self._last_scroll_position){
				self._load_next();
			}
		}

		self._last_scroll_position = scroll
	}

	_load_previous(){
		let self = this;
		let container = self._container;
		let first_message = container.dataset.first_message;
		let last_received = null; 
		if (first_message != "-1" && !self._previous_load_lock)
		{
			let body_obj = {"type": "previous", 'pk': first_message};
			self._previous_load_lock = true;
			fetch(self._pagination_url, {
				'method' : "POST",
				'body' : JSON.stringify(body_obj),
				"headers":{
					'Content-Type': "application/json",
				}
			}).then(res => res.json())
			.then((data)=>
			{
				//console.log(data)
				
				container.dataset.first_message = data.first_message.pk
				last_received = data.last_message.pk
				self.insert_messages(data.messages, true, last_received);
				self._previous_load_lock = false;
			})
			.catch(error=> console.error(error));

		}		
		
		//console.log(`${container.dataset.first_message}`)
	}
	_load_next(){
		//cargar la página siguiente
		let self = this;
		let container = self._container;
		//console.log(`${container.dataset.last_message}`)

    }

	
	//recibira la lista de mensajes que han sido marcados como leidos para poder liberar la memoria
	_update_readed_cache(data)
	{
		for (let i in data )
		{
			this._readed = array_rm(this._readed, data[i]);	
		}
	}


	
	_send_reading_confirmation()
	{
		let self = this
		if (self._confirmation_url != null)
		{
			let data = {'messages' : self._readed}

			fetch(this._confirmation_url, {
				'method' : "POST",
				'body' : JSON.stringify(data),
				"headers":{
					'Content-Type': "application/json",
				}
			}).then(res => res.json() )
			.then(data=>self._update_readed_cache(data.data))
			.catch(error=> console.error(error));
			//console.log("confirmación de lectura desctivada");
		}
	}

	insert_messages(messages_list, prepend=false, scroll_to=null)
	{
		let self = this
		let html ="";
		let last_message = null;
		for (let i in messages_list)
		{

			let message = messages_list[i];
			if (self._readed.indexOf(message.pk) != -1 )
			{
				continue;
			}

			if (message.room == self._user.room)
			{
				// Posicion del marcador cuando recibimos un mensaje con la sala activa en segundo plano (no es la pestaña activa)
				if (!self._has_focus && document.getElementById(self._MARKER_ID) == null)
				{
				
					html += self._unreaded_marker 
				}
				//console.log(message.response_to);

				let response_to =""
				if (message.response_to.pk)
				{
					response_to = self._response_template(message.response_to.user, message.response_to.content)
				}
				if (message.user_pk == self._user.pk)
				{	
					html += self._user_template(message, response_to);
				}
				else{
					html += self._external_template(message, response_to);
				}
				
				if (message.image)
            	{
                	html += self._image_template(message.image)                
            	}

				self._readed.push(message.pk);
			}

			//Posición del marcador cuando accedemos a la sala 
			if (message.pk == self._last_readed_message)
			{
				html+= self._unreaded_marker;
			}

			if (message.pk == scroll_to && scroll_to != null)
			{
				html += `<div id="_scroll_${scroll_to}" ></div>`
			}
			last_message = message
		}
		
		if (!prepend)
		{
			self._container.innerHTML += html;
			self._last_scroll_position = self._container.scrollHeight + 100;
			if (scroll_to == null){
				if (self._has_focus)
				{
					if (self._last_readed_message == null || self._last_readed_message == last_message.pk ){
						go_bottom(self._container, 150);
					}else{
						self.remove_marker_timeout(5000);
					}

				}else{
						
						self.remove_marker_timeout();
						// const unreaded_marker = document.getElementById(self._MARKER_ID)
						//  if (unreaded_marker)
						//  {
						//  	unreaded_marker.scrollIntoView();
						//  	setTimeout(()=>{ unreaded_marker.remove()}, 120000)
						//  }
					
				}
			}
		}
		else{
			self._container.innerHTML = html + self._container.innerHTML;
		}
		if (scroll_to){
			const scroll_marker = document.getElementById("_scroll_"+scroll_to)
			if (scroll_marker)
			{
				//scroll_marker.scrollIntoView();
				self._container.scrollTo(0, scroll_marker.scrollTop - element.clientHeight + 20);
				()=> setTimeout(scroll_marker.remove(), 200);
			}
		}
		self._send_reading_confirmation();
	}
	

	remove_marker_timeout(timeout=30000){
		
		const unreaded_marker = document.getElementById(this._MARKER_ID)
		//console.log(unreaded_marker);
		if (unreaded_marker!= null && !(typeof unreaded_marker === 'undefined'))
		{		
				unreaded_marker.scrollIntoView();
				this._marker_timeout = setTimeout(()=>{console.log("timeout-executed"); unreaded_marker.remove(), clearTimeout(this._marker_timeout)}, timeout)
		}

	}
	
}

