/*------------------------------
     chat_navigation.js 
     Se encargara de dibujar y mantener actualizado el menu lateral asi como de las notificaciones, 
     además sera el encargado de acceder a las salas de chat.
------------------------------*/
class NavigationManager
{
    static INSTANCE = null
    constructor(current_room, main_container, rooms_container, chats_container, loading_box, template, notification_audio)
    {
		this._current_page = 0;
		this._rooms_list = new Array();
		this._chats_list = new Array();
		this._sidebar = document.getElementById("side-navigation");
		this._current_room = current_room;
        this._rooms_container = document.getElementById(rooms_container);
        this._chats_container = document.getElementById(chats_container);
        this._main_container = document.getElementById(main_container);
		this._loading_box = document.getElementById(loading_box);
        this._template = template;
		this._last_rooms_datas = new Object();
        this._tab_title = document.title;
		this._notification = null;
        this._notification_audio = document.getElementById(notification_audio)

		//navigator.serviceWorker.ready.then((registration) =>{ this._registration = registration; });		

        NavigationManager.INSTANCE = this;
    }


    /*------------------------------
     METHODS
     ------------------------------*/
    //Necesario para que se ejecute el javascript recuperado por ajax.
	_add_script(content){
		const script = document.createElement("script");
		let text = document.createTextNode(content);
		script.appendChild(text);
		return script;
	}

	_add_script_src(src)
	{
		const script = document.createElement("script");
		script.src = src;
		return script;
	}

    //Establece los eventos al pulsar los elementos de menu
	_set_handlers(){
		let menu_items = document.querySelectorAll(".chat-room-link");
		menu_items.forEach((element)=>{
			element.addEventListener("click", (e)=>{
					e.stopPropagation(); 
					e.preventDefault(); 
						
					let current_active = document.querySelector(".chat-room-link.active")
					if (current_active){
						current_active.classList.remove("active");
					}
					element.classList.add("active");
					self.load_room(element.getAttribute("href"), element.getAttribute("data-room-code"));
					this._sidebar.classList.add("side-navigation-hidden-xs");
			});
		});
		
	}
	
    
    _template_parse(list, icon)
    {
        let html =""
        for (let obj of list)
        {   let active = (obj.code == self._current_room) ? "active" : "";

            html+= self._template(obj.code, obj.name, active, obj.url, icon, "", "display:none", "");
        }
        return html;

    }
    _refresh_menu(rooms_list, chats_list, callback=null)
    {   
        
        self = this
        
        //rooms
        let rooms_html = self._template_parse(rooms_list, "hash");
        self._rooms_container.innerHTML=rooms_html;
        //chats
        let chats_html = self._template_parse(chats_list, "at-sign");
        self._chats_container.innerHTML=chats_html;
        
		self._set_handlers();
        if (callback!= null)
        {
            callback();
        }
    }

    //comprueba si los datos del objeto son iguales a la caché
    _same_in_cache(obj, cache)
    {
        if (cache != null)
        {
            let result = cache.filter(room=>{ 
                   return (room.pk == obj.pk &&  room.last_message.timestamp == obj.last_message.timestamp &&  room.user_last_connection == obj.user_last_connection)
            });
            return (result.length > 0 )
        }
        return false;
    }


    _check_updates(list, cache, callback=null)
    {

        let self = this;
        let unreaded = false;
        let sound = false
        list = list.filter(room => room.code != self._current_room);
        for (let room of list)
        {
            if (room.hasOwnProperty("last_message"))
            {
                let lmessage = room.last_message.timestamp;
                let element_icon = document.getElementById(`not_icon_room_${room.code}`);

                if (lmessage > room.user_last_connection)
                {
                    unreaded = true;
                    element_icon.style.display="inline-block";

                    if (!self._same_in_cache(room, cache))
                    {
                        sound = true;
                    }
                }else
                {
                    element_icon.style.display="none";
                }
            }
        }
        if (callback)
        {
            callback()
        }


        return [unreaded, sound];

    }

    _show_tab_notification()
    {
        let title = this._tab_title;
        let show_title = true
        if (this._tab_interval)
        {
            clearInterval(self._tab_interval);
        }
        
        this._tab_interval = setInterval(()=>{
            if (show_title) { document.title = title; } else { document.title = "● Nuevos Mensajes"}
            show_title  = !show_title
            
        }, 500);
    }


    _hide_tab_notification()
    {
        let self = this;
        if(self._tab_interval)
        {
            clearInterval(self._tab_interval);
        }
        document.title = self._tab_title;
    }

    _show_browser_notification()
	{
		if (Notification.permission === "granted" && this._notification == null )
		{
			var options = {
  				body: 'Tienes mensajes sin leer',
 				vibrate: [200, 100, 200],
				icon : "/static/images/logo-shidix.png",
			}
		    //navigator.serviceWorker.ready.then(function(registration) {
      		//	registration.showNotification('Shidix Channels', options);
    		//});
			this._registration.getNotifications().then(nlist=>{
				if (nlist.length < 1)
				{	
					this._registration.showNotification("Shidix Channels", options);
				}
			});
			
			
			//this._notification = new Notification("Shidix Channels", options);
		}
	}

	loading_show()
	{
		this._main_container.style.visibility="hidden";
		this._loading_box.style.display="flex";
	}

	loading_hide(){
		this._loading_box.style.display="none";
		this._main_container.style.visibility="visible";
	}

    check_status(full_list, callback=null)
    {
        let self = this;
		let last_room = full_list.current_room 
		full_list = full_list.rooms
        let rooms_list = full_list.filter(room => room.private == false);
        let chats_list = full_list.filter(room => room.private == true);

        
        self._refresh_menu(rooms_list, chats_list, callback)
        let room_results = self._check_updates(rooms_list, self._rooms_list, ()=>{ self._rooms_list = rooms_list});
        let chats_results = self._check_updates(chats_list, self._chats_list, ()=>{ self._chats_list = chats_list});
		if (room_results[0] || chats_results[0]){ 
			self._show_tab_notification();
			self._show_browser_notification();} 
		else { 
			self._hide_tab_notification();
			if (self._notification != null)
			{
				self._notification.close()
				self._notification = null
			}
		}
        if (room_results[1] || chats_results[1]){ self._notification_audio.play()}
		
		
		//si nos han echado de la sala actual , redirigimos al usuario.
		let current_room = full_list.filter(room => room.code == self._current_room)
		if (current_room.length < 1) { 
			document.getElementById("chat_room_screen").remove();
			if (last_room)
			{
				self._current_room = last_room.code
				document.getElementById(`a__room__${last_room.code}`).click();
			}
		}
        if(callback) { callback() }

    }


	initialize(full_list, callback=null, notify=false)
	{
        
        let self = this;
		full_list = full_list.rooms
        self._rooms_list = full_list.filter(room => room.private == false);
        self._chats_list = full_list.filter(room => room.private == true);

		self._refresh_menu(self._rooms_list, self._chats_list, callback)
        self._check_updates(self._rooms_list, null, null);
        self._check_updates(self._chats_list, null, null);
       
	}



    //Marca la sala como la sala activa en el menu y la almacena como "sala actual", cargando su contenido en el panel principal.
    load_room(url, room_code)
    {
		let self = this;
		self.loading_show();
		self._current_room=room_code;
        let element_icon = document.getElementById(`not_icon_room_${room_code}`);
        element_icon.style.display="none";


		fetch (url)
		.then(res => res.text())
		.then((data)=>{
			console.log("Sala descargada")
			let parser = new DOMParser();
            
			self._main_container.innerHTML="";
        	let doc = parser.parseFromString(data, "text/html");
			
			let chat_screen = doc.getElementById("chat_room_screen");
			self._main_container.appendChild(chat_screen);
			
			let scripts = doc.querySelectorAll("script");
			scripts.forEach(element=>{
				if (element.hasAttribute("src")){
					self._main_container.appendChild(self._add_script_src(element.getAttribute("src")));
				}else{
					self._main_container.appendChild(self._add_script(element.textContent));
				}
			});
			
			//let logic = doc.getElementById("chatroom_logic").textContent;
			//let initial = doc.getElementById("chatroom_initial_data").textContent;
			
			
			//fixme: reemplazar todo este codigo por un json 	
			//self._main_container.appendChild(self._add_script(logic));
			//self._main_container.appendChild(self._add_script(initial));

			self.loading_hide();})
		.catch((error) => {
			console.error(error); 
			self.loading_hide();
		});

    }
	
    clear(){
       NavigationManager.INSTANCE = null;
    }

    

}
