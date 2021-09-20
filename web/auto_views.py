from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from padword.commons import get_or_none_str, set_obj_field, show_exc

#import logging
#logger = logging.getLogger(__name__)


#@login_required
def autosave_field(request):
    try:
        app = request.GET["model_name"].split(".")[0]
        model = request.GET["model_name"].split(".")[1]
        obj_id = request.GET["obj_id"]

        lang = request.GET['lang'] if 'lang' in request.GET else request.LANGUAGE_CODE
        lang = lang.split('-')[0]
        field = request.GET["field"]
        try:
            reffield = request.GET["ref_field"]
        except:
            reffield = "pk"
        try:
            value = request.GET["value"]
        except:
            value = request.GET.getlist("value[]")

        obj = get_or_none_str(app, model, obj_id, field=reffield)
        if "lang" in request.GET: 
            try:
                value_json = json.loads(getattr(obj,field))
            except Exception as e:
                print (show_exc(e))
                value_json = {}
            value_json[lang.upper()] = value
            value = json.dumps(value_json)

        if obj != None:
            set_obj_field(obj, field, value)
            obj.save()
            return HttpResponse("Saved!")
        return HttpResponse("Not saved, object not found!")
    except Exception as e:
        #logger.error("[autosave_field]: %s" % e)
        print(show_exc(e))
        return render(request, 'simple-error-plane.html', {'msg': str(e)})
        return render(request, 'simple-error.html', {'msg': str(e)})

#@login_required
def autoremove_obj(request):
    try:
        app = request.GET["model_name"].split(".")[0]
        model = request.GET["model_name"].split(".")[1]
        obj_id = request.GET["obj_id"]

        obj = get_or_none_str(app, model, obj_id)
        if obj != None:
            obj.delete()
            return HttpResponse("")
        return HttpResponse("Not deleted, object not found!")
    except Exception as e:
        #logger.error("[autoremove_obj] %s" % e)
        return render(request, 'simple-error.html', {'msg': str(e)})


