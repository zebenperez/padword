from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, reverse
from .models import *
import json, os, time, datetime
from padword.commons import show_exc, get_or_none, get_param, new_ui_slug

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
        categories = Category.objects.filter(project_uuid=project_id, parent__isnull =True).order_by('position')
        return render(request, "contents/categories.html", {'project':project, 'items':categories})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@login_required
def category_form(request):
    try:
        obj = get_or_none(Category, request.GET["objId"], 'uuid') if "objId" in request.GET else None
        lang = request.GET['lang'] if 'lang' in request.GET else request.LANGUAGE_CODE
        if obj is None:
            new_item = True
            if 'projectId' in request.GET:
                project_id = get_param(request.GET, "projectId")
                project = Project.objects.get(uuid=project_id)
                parent = None
            else:
                parent_id = get_param(request.GET, "parentId")
                parent = Category.objects.get(uuid=parent_id)
                project = parent.project
            obj = Category.objects.create(  uuid=new_ui_slug(Category), 
                                                project_uuid = project.uuid, 
                                                is_active = 1,
                                                parent = parent,
                                                updated_at = datetime.datetime.now(),
                                                created_at = datetime.datetime.now())
        else:
            new_item = False
            project = obj.project

        return render(request, "contents/category-form.html", {'obj': obj, 'company_id': project.company.uuid, 'new_item':new_item })
    except Exception as e:
        return render(request, "error_exception.html", {'exc': show_exc(e)})

@login_required
def category_tree(request, category_id):
    try:
        category = Category.objects.get(uuid=category_id)
        return render(request, 'contents/items-list.html', {'cat':category})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@login_required
def category_change_active(request, category_id):
    try:
        category = Category.objects.get(uuid=category_id)
        category.is_active = (category.is_active + 1) % 2
        category.save()
        return render(request, "contents/category-row.html", {'item':category})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@login_required
def category_remove(request, category_id):
    try:
        category = Category.objects.get(uuid=category_id)
        project_uuid = category.project_uuid
        parent = category.parent
        category.delete()
        if parent is None:
            categories = Category.objects.filter(project_uuid=project_uuid, parent__isnull =True).order_by('position')
            return render(request, "contents/categories-list.html", {'items': categories, })
        else:
            return redirect(reverse('items-by-category', kwargs={'category_id':parent.uuid}))
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@login_required
def item_form (request):
    try:
        obj = get_or_none(Item, request.GET["objId"], 'uuid') if "objId" in request.GET else None
        cat = get_or_none(Category, request.GET["catId"], 'uuid') if "catId" in request.GET else None
        if cat is not None:
            lang = request.GET['lang'] if 'lang' in request.GET else request.LANGUAGE_CODE
            if obj is None:
                new_item = True
                obj = Item.objects.create(  uuid=new_ui_slug(Item), 
                                            is_active = 1,
                                            is_event = 0,
                                            price = "0.0",
                                            updated_at = datetime.datetime.now(),
                                            created_at = datetime.datetime.now())
                obj.save()
                if ItemInCat.objects.filter(category=cat).exists():
                    new_position = ItemInCat.objects.filter(category = cat).order_by('position').last().position + 1
                else:
                    new_position = 0
                item_in_cat = ItemInCat(position=new_position, category=cat, item=obj)
                item_in_cat.save()
            else:
                new_item = False

        return render(request, "contents/item-form.html", {'obj': obj, 'new_item':new_item, 'cat':cat })
    except Exception as e:
        return render(request, "error_exception.html", {'exc': show_exc(e)})


@login_required
def item_change_active(request, item_id):
    try:
        item = Item.objects.get(uuid=item_id)
        item.is_active = (item.is_active + 1) % 2
        item.save()
        return render(request, "contents/item-row.html", {'item':item})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@login_required
def item_remove(request):
    try:
        obj = get_or_none(Item, request.GET["objId"], 'uuid') if "objId" in request.GET else None
        cat = get_or_none(Category, request.GET["catId"], 'uuid') if "catId" in request.GET else None
        if obj:
            categories = ItemInCat.objects.filter(item=obj)
            for cat_item in categories:
                cat_item.delete()
            obj.delete()
        return redirect(reverse('items-by-category', kwargs={'category_id':cat.uuid}))
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})




##### IMPORT #####
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
