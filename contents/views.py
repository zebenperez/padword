from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from .models import *
import json, os, time, datetime
from padword.commons import show_exc, get_or_none, get_param

# Create your views here.

@login_required
def index(request):
    try:
        categories = Category.objects.all()
        return JsonResponse({'results':len(categories), 'error':0})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@login_required
def category_search(request):
    try:
        project_id = get_param(request.GET, "project_id")
        name = get_param(request.GET, "s-name")
        filters_to_search = ["name__icontains"]
        items = Channel.objects.none()
        print ("DEB", project_id)
        for myfilter in filters_to_search:
            kwargs = {}
            if project_id != "":
                kwargs["project_uuid"] = project_id
            if name != "":
                kwargs[myfilter] = name
            items = items.union(Category.objects.filter(**kwargs))
        return render(request, "contents/categories-list.html", {'items': items, })
    except Exception as e:
        print (show_exc(e))
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@login_required
def categories_by_project(request, project_id):
    try:
        project = Project.objects.get(uuid=project_id)
        categories = Category.objects.filter(project_uuid=project_id, parent__isnull =True, is_active=1).order_by('position')
        return render(request, "contents/categories.html", {'project':project, 'items':categories})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@login_required
def category_form(request):
    obj = get_or_none(Category, request.GET["obj_id"]) if "obj_id" in request.GET else Category.objects.create()
    project_id = get_param(request.GET, "project_id")
    if project_id != "":
        project = get_or_none(Project, project_id)
        if project != None:
            obj.project = project
            obj.save()

    return render(request, "contents/category-form.html", {'obj': obj, 'company_id': company_id})

@login_required
def category_tree(request, category_id):
    try:
        category = Category.objects.get(uuid=category_id)
        return render(request, 'contents/items-list.html', {'cat':category})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

class Node:
    def __init__(self, json_data, languages):
        self.data = json_data
        self.next = None
        self.languages = languages

    @property
    def uuid(self):
        return self.data['uuid'].strip()

    @property
    def parent(self):
        try:
            if self.data['parent_id'] is not None:
                return [self.data['parent_id'].strip()]
            return [None]
        except:
            aux = [k.strip() for k,v in self.data['order_indexes'].items()]
            for i in self.data['categories']:
                if i.strip() not in aux:
                    aux.append(i.strip())
            return aux

    @property
    def price(self):
        try:
            return self.data['price']
        except:
            return 0.

    @property
    def description(self):
        if 'parent_id' in self.data.keys():
            return ''
        aux = {}
        for idx,name_str in enumerate(self.data['descriptions']):
            if self.languages[idx] != '':
                aux[self.languages[idx]] = name_str.strip()
        return json.dumps(aux)

    @property
    def subtitle(self):
        if 'parent_id' in self.data.keys():
            return ''
        aux = {}
        for idx,name_str in enumerate(self.data['subtitles']):
            if self.languages[idx] != '':
                aux[self.languages[idx]] = name_str.strip()
        return json.dumps(aux)

    @property
    def icon(self):
        try:
            return self.data['image']
        except:
            return ''

    @property
    def name(self):
        aux = {}
        for idx,name_str in enumerate(self.data['names']):
            if self.languages[idx] != '':
                aux[self.languages[idx]] = name_str.strip()
        return json.dumps(aux)
#         if 'parent_id' in self.data.keys():
#             return '| [CAT] {}'.format(str(aux))
#         return '{}'.format(self.data['names'][0].strip())



@login_required
def import_categories(request, project_uuid = 'UNKNOWN'):
    json_tree = None

    try:
        json_tree = json.load(open(os.path.join(settings.BASE_DIR,'contents','{}.json'.format(project_uuid)),'r'))
    except Exception as e:
        return HttpResponse(show_exc(e))
    languages = json_tree['languages']
    aux = ['' for i in range(30)]
    for item in languages:
        aux[item['language_index']] = item['cartrawler_lang']
    languages = aux

    tree = []
    for category in json_tree['menucategories']:
        node = Node(category, languages)
        tree.append(node)
        category = Category(
                            uuid = node.uuid.strip(), 
                            parent = None,
                            project_uuid = project_uuid, 
                            place_uuid = node.data['place_id'], 
                            name = node.name,
                            description = node.description,
                            allow_reservation = 'yes',
                            minimum_reservation = 0,
                            icon = node.icon,
                            is_active = 1,
                            created_at = datetime.datetime.now(),
                            updated_at = datetime.datetime.now(),
                            reservation_form_active = 0,
                            position = node.data['position'])
        category.save()

    for node in tree:
        category = Category.objects.get(uuid = node.uuid)
        for parent_uuid in node.parent:
            if parent_uuid is not None:
                parent = Category.objects.get(uuid=parent_uuid)
                category.parent = parent
                category.save()

    leafs = []
    for item in json_tree['menuitems']:
        leaf = Node(item, languages)
        if not Item.objects.filter(uuid=leaf.uuid).exists():
            item = Item(uuid = leaf.uuid,
                        name = leaf.name,
                        title = leaf.subtitle,
                        description = leaf.description,
                        price = leaf.price,
                        gallery = leaf.icon,
                        is_active = 1,
                        created_at = datetime.datetime.now(),
                        updated_at = datetime.datetime.now(),
                        reservation_form_active = 0)
            item.save()
        leafs.append(leaf)


    for leaf in leafs:
        item = Item.objects.get(uuid=leaf.uuid)
        for parent_uuid in leaf.parent:
            cat = Category.objects.get(uuid=parent_uuid)
            try:
                item_in_cat = ItemInCat(position=leaf.data["order_indexes"][parent_uuid], category = cat, item=item)
                item_in_cat.save()
            except Exception as e:
                try:
                    item_in_cat = ItemInCat(position=0, category = cat, item=item)
                    item_in_cat.save()
                except Exception as e:
                    print ('{}. {}'.format(parent_uuid, show_exc(e)))
    return HttpResponse("OK")

    categories = json_tree['menucategories']
    for item in categories:
        category = Category(uuid=item['uuid'], )
    return HttpResponse("OK")
