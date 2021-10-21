
class DragAndDropFile
{
	constructor (element_id, field_target, trigger_element, click_trigger, icon="upload", text="Drop file here to upload", drop_callback=null)
	{
		this._element= document.getElementById(element_id);
		this._field = document.getElementById(field_target);
		this._field_id = field_target
		this._icon = icon;
		this._text = text;
		this._trigger_element = document.getElementById(trigger_element);
		this._click_trigger = document.getElementById(click_trigger);
		this._drop_callback = drop_callback;
		 
		
		this._initialize();
	}
	
	_template()  {
		let self = this;
		return `<label class="text-center v-100"  for="${self._field_id}" >
					<i data-feather="${self._icon}" style="display:inline-block; width:80px; height:80px; margin:auto;"></i>
					<h1 class="drag_area"> ${self._text} </h1>
				</label>`
	}

	_preview_template(){

	}

	
	_initialize()
	{
		this._denter_counter = 0;
		this._element.style.display="none";
		this._element.innerHTML = this._template();
		this._trigger_element.addEventListener("dragenter", (e)=>this._dragenter_parent(e))	;
		this._trigger_element.addEventListener("dragleave", (e)=>this._dragleave_parent(e)) ;
		this._trigger_element.addEventListener("dragover", (e)=>{ e.stopPropagation(); e.preventDefault();});
		this._element.addEventListener("dragover", (e)=>{ this._dragover(e)})
		this._element.addEventListener("drop", (e)=>{ this._drop(e)});				 
		this._element.addEventListener("dragenter", (e)=>this._dragenter(e));		
		//this._element.addEventListener("dragleave", (e)=>this._dragleave(e));					 
		this._click_trigger.addEventListener("click", (e)=>{this._click(e)});
	}

	_dragenter_parent(e)
	{
		this._denter_counter++; 
		this._element.style.display="block"; 

	}
	_dragleave_parent(e)
	{
		this._denter_counter--;
		if (this._denter_counter < 1) {
			this._element.style.display="none";
			this._element.classList.remove('uploadfile_dragover');
		}

	}


	_dragover(e){
		e.preventDefault();
		
		console.log("dragover");
	}
	
	_dragenter(e){
		e.preventDefault();
		console.log("dragenter");
		this._element.style="color:#2e2e2e"	
		this._element.classList.add('uploadfile_dragover');
	}

	_dragleave(e){
	}
	
	_drop(e){
		this._element.classList.remove('uploadfile_dragover');
		this._element.style.display="none";

		e.preventDefault();
		e.stopPropagation();
	
		let file = e.dataTransfer.files;
		this._field.files = file;
	
		this._drop_callback();
		
	}
	
	_click(e){
		this._field.click();	
	}

}
