/*------------------------------
     chat_subscriber.js 
 	 Se encargara de suscribirse a los eventos del servidor y de enviar las notificaciones 
	 al modulo correspondiente.
 
 ------------------------------*/
// Permite subscribirse a una URL que envie SSE 
// todos los manejadores de eventos, recibiran como parametros el propio objeto y  los datos que devuelve la petición 
class NotificationSubscriber
{
	static INSTANCE = null;
	constructor(url, error_handler=null)
	{
		this.__url = url;
		this.__error_handler = error_handler;
		this.__subscriber = new EventSource(this.__url);
		//this.__subscriber.onmessage =  (resp)=> { message_handler(this, JSON.parse(resp.data))};
		this.__subscriber.onerror = (error_handler == null ) ? (resp)=>{console.log(resp); this.restart()} : (resp)=>error_handler(this, JSON.parse(resp.data));

		if (NotificationSubscriber.INSTANCE != null && typeof NotificationSubscriber.INSTANCE != undefined)
		{
			NotificationSubscriber.kill_subscriber(NotificationSubscriber.INSTANCE);
		}
		
		NotificationSubscriber.INSTANCE = this;
	}
	
	static kill_subscriber( subscriber )
	{
		if (subscriber != null && typeof subscriber != undefined)
		{
			if (subscriber.is_connected)
			{
				subscriber.kill()
			}
		}
	}
	
	kill ()
	{
		console.log("matando hilo");
		this.__subscriber.close();
	}

	restart()
	{
		this.kill();
		this.__subscriber = new EventSource(this.__url);
	}

	get is_connected()
	{
		this.__subscriber.readyState == 1;
	}

	get ready_state()
	{
		this.__subscriber.readyState;
	}

	get url()
	{
		return this.__url;
	}

    set message_handler(handler)
    {
        let self = this
        self.__subscriber.onmessage = (resp)=> handler(self, JSON.parse(resp.data))
    }

	register_event(event_name, handler)
	{
		let self = this;
		this.__subscriber.addEventListener(event_name, (e) => {handler(self,JSON.parse(e.data))});
	}
}
