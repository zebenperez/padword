/*
    chat.js 
    Implementa las clases y características comunes del chat
    Creado : 10-05-2020 - brauliohrdz@gmail.com
    Modificaco : 10-05-2020 - brauliohrdz@gmail.com
*/

//---------------------------------
// CONSTANTS AND VARIABLES 
//---------------------------------
USER = null

//----------------------------
// UTILS 
//----------------------------

function strip_html(html){
   var doc = new DOMParser().parseFromString(html, 'text/html');
   return doc.body.textContent || "";
}


function escape_html(html_str) {
	let htmlEscapes = {
	  '<': '&lt;',
	  '>': '&gt;',
	  '"': '&quot;',
	  "'": '&#x27;',
	  '/': '&#x2F;'
	};

	var htmlEscaper = /[<>"'\/]/g;
	return html_str.replace(htmlEscaper, function(match){
		return htmlEscapes[match];
	});
}

function array_rm(arr, value) 
	{ return arr.filter(function(ele){ return ele != value; });}



function go_bottom(element, offset=0, callback=null)
{
    element.scrollTo(0,element.scrollHeight - element.clientHeight + offset);
	if (callback != null){ callback(); }
}

function capitalize(string)
{
    return string.charAt(0).toUpperCase() + this.slice(1);
}

function scroll_reaches(element, position='bottom', offset=100)
{
	if (position == "top" )
	{
		return (element.scrollTop < offset) ? true : false;
	}
	
	let distance = element.scrollTop + element.clientHeight;
	let height = element.scrollHeight - offset;
	return (distance >= height) ? true : false
}



//----------------------------
// CLASS DEFINITIONS 
//----------------------------
class User{
    static INSTANCE 
    constructor (username, pk, room)
    {
        this.__username = username;
        this.__pk = pk
        this.__room = room;
        User.INSTANCE = this
    }

    set_room(room)
    {
        this.__room = room;
    }
    
    get room()
    {
        return this.__room;
    }

    get username()
	{
        return this.__username
    }

    get pk()
	{
        return this.__pk
    }

	toString(){
		return `[${this.__pk}] ${this.__username} at ${this.__room}`;
	}
   
}

class IntervalsHandler
{
    static INTERVALS = new Object();
    constructor(func, code, timeout)
	{
        this.func = func
        this.code = code
        this.timeout = timeout
    }

    kill_interval_insatances()
	{
        if (IntervalsHandler.INTERVALS.hasOwnProperty(code))
	    {
		    for (i in IntervalsHandler.INTERVALS[code])
		    {
			    interval_id= IntervalsHandler.INTERVALS[code].shift();
			    clearInterval(interval_id);
		    }
	    }
    }

    initialize_intervals()
	{
        this.kill_interval_instances();
        IntervalsHandler.INTERVALS[this.code].push = setInterval(this.func, this.timeout);
    }
}


