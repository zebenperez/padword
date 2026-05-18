from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, reverse
from .models import *
from bookings.models import Form 
import json, os, time, datetime
from padword.decorators import group_required
from padword.commons import show_exc, get_float, get_or_none, get_param, new_ui_slug, translate
from .forms import ImageUploadForm

# Create your views here.

@group_required("admins")
def index(request):
    try:
        categories = Category.objects.all()
        return JsonResponse({'results':len(categories), 'error':0})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

'''
    Categories
'''
@group_required("admins", "projects")
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

@group_required("admins", "projects")
def categories_by_project(request, project_id):
        project = Project.objects.get(uuid=project_id)
        categories = Category.objects.filter(project_uuid=project_id, parent__isnull =True).order_by('position')
        return render(request, "contents/categories.html", {'project':project, 'items':categories})

@group_required("admins", "projects", "categories")
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

        if obj.parent is not None:
            parents_options = Category.objects.filter(pk=obj.parent.pk)
        else:
            parents_options = Category.objects.none()
        parents_options = parents_options.union(Category.objects.filter(project_uuid = obj.project_uuid, parent = obj.parent))
        return render(request, "contents/category-form.html", {'obj': obj, 'new_item':new_item, 'parents_options':parents_options })
        #return render(request, "contents/category-form.html", {'obj': obj, 'company_id': project.company.uuid, 'new_item':new_item, 'parents_options':parents_options })
    except Exception as e:
        return render(request, "error_exception.html", {'exc': show_exc(e)})

@group_required("admins", "projects", "categories")
def category_tree(request, category_id):
    try:
        category = Category.objects.get(uuid=category_id)
        old_parent = request.GET.get('old_parent',0)
        if old_parent != 0:
            old_parent = get_or_none(Category, old_parent)
            return render(request, 'contents/items-list.html', {'cat':category, 'old_parent':old_parent, 'move':True})
        else:
            return render(request, 'contents/items-list.html', {'cat':category, 'move':False})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins", "projects", "categories")
def category_change_active(request, category_id):
    try:
        category = Category.objects.get(uuid=category_id)
        category.is_active = (category.is_active + 1) % 2
        category.save()
        return render(request, "contents/category-row.html", {'item':category})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins", "projects")
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

@group_required("admins", "projects")
def category_clone(request):
    try:
        category_id = request.GET['objId'] if 'objId' in request.GET else None
        target = get_or_none(Project, request.GET['toProjectUuid'], 'uuid') if 'toProjectUuid' in request.GET else None
        category = Category.objects.get(uuid=category_id)
        projects = Project.objects.filter(active=1)
        projects = sorted(projects, key=lambda x: x.name.upper())
        if target is None:
            project_uuid = category.project_uuid
            return render(request, "contents/category-clone.html", {'category':category, 'projects':projects, 'target':target})
        else:
            tree = [[category, None]]
            while len(tree) > 0:
                [current, parent] = tree.pop(0)
                uuid_cat = current.uuid
                items = current.get_items
                for children in current.get_childrens:
                    tree.append([children, current])

                cat_features = CategoryFeature.objects.filter(category = current)
                cat_images = CategoryImage.objects.filter(category = current)
                cat_forms = Form.objects.filter(category = uuid_cat)

                cat_item = current
                cat_item.pk = None
                if cat_item.project_uuid == target.uuid and category.uuid == cat_item.uuid:
                    cat_item.name = '0000 {}'.format(translate(request, cat_item.name))
                cat_item.uuid = new_ui_slug(Category)
                cat_item.project_uuid = target.uuid
                cat_item.is_active = current.is_active
                cat_item.parent = parent
                cat_item.updated_at = datetime.datetime.now()
                cat_item.created_at = datetime.datetime.now()
                cat_item.save()
                for idx,item in enumerate(items):
                    item.pk = None
                    item.uuid = new_ui_slug(Item)
                    item.save()
                    item_in_cat = ItemInCat(position=idx, category=cat_item, item=item)
                    item_in_cat.save()

                for cat_feature in cat_features:
                    cat_feature.pk = None
                    cat_feature.category = cat_item
                    cat_feature.save()

                for cat_image in cat_images:
                    cat_image.pk = None
                    cat_image.category = cat_item
                    cat_image.save()
                
                for cat_form in cat_forms:
                    blocks = cat_form.blocks
                    cat_form.pk = None
                    cat_form.category = cat_item.uuid
                    cat_form.save()
#                     for block in blocks:
#                         block.pk = None
#                         block.form = cat_form
#                         block.save()

            return render(request, "contents/category-clone.html", {'category':Category.objects.get(uuid=category_id), 'projects':projects, 'target':target})

    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins", "projects")
def category_links(request):
    try:
        open_url = ""
        qr_url = ""
        pwa_url = ""
        obj = get_or_none(Category, request.GET["objId"], 'uuid') if "objId" in request.GET else None
        if obj != None:
            f = get_or_none(Form, obj.uuid, 'category')
            if f != None:
                open_url = "https://%s%s?device_imei={device.imei}&room_number={room.number}&guest_name={guest.name}&guest_surname={guest.surname}" % (request.get_host(), reverse('guest-access', kwargs={'form_uuid': f.uuid}))
                qr_url = "https://{}{}".format(request.get_host(), reverse('guest-access', kwargs={'form_uuid': f.uuid}))
            #pwa_url = "https://{}{}".format(request.get_host(), reverse('guest-access-pwa', kwargs={'project_uuid': obj.project.uuid}))
            pwa_url = "https://{}{}".format(request.get_host(), reverse('guest-access-pwa', kwargs={'category_uuid': obj.uuid}))
        return render(request, "contents/category-links.html", {'open_url': open_url, 'qr_url': qr_url, 'pwa_url': pwa_url})
    except Exception as e:
        return render(request, "error_exception.html", {'exc': show_exc(e)})

@group_required("admins", "projects", "project_manager")
def category_add_image(request):
    try:
        obj_id = request.POST["obj_id"]
        image = request.FILES["file"]

        cat = get_or_none(Category, obj_id)
        if cat != None:
            cat.image = image
            cat.save()
        return render(request, "contents/category-img.html", {"obj": cat,})
    except Exception as e:
        print(e)
        #logger.error("[bookings-form_add_image]" + str(e))
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("admins", "projects")
def category_remove_image(request):
    try:
        obj_id = request.GET["obj_id"]
        obj = get_or_none(Category, obj_id) 
        if Category.objects.filter(image=obj.image).count() > 1:
            obj.image = None
            obj.save()
        else:
            obj.image.delete(save=True)

        return render(request, "contents/category-img.html", {"obj": obj,})
    except Exception as e:
        print(e)
        #logger.error("[remove_file]" + str(e))
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("admins", "projects", "categories")
def category_add_image_gallery(request):
    try:
        obj_id = request.POST["obj_id"]
        image = request.FILES["file"]

        cat = get_or_none(Category, obj_id)
        if cat != None:
            ci = CategoryImage.objects.create(image=image, category=cat)
        return render(request, "contents/category-gallery.html", {"obj": cat,})
    except Exception as e:
        print(e)
        #logger.error("[bookings-form_add_image]" + str(e))
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("admins", "projects", "categories")
def category_remove_image_gallery(request):
    try:
        obj_id = request.GET["obj_id"]
        obj = get_or_none(CategoryImage, obj_id) 
        cat = obj.category
        obj.image.delete(save=True)
        obj.delete()
        return render(request, "contents/category-gallery.html", {"obj": cat,})
    except Exception as e:
        print(e)
        #logger.error("[remove_file]" + str(e))
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("admins", "projects", "categories")
def category_add_file(request):
    try:
        obj_id = request.POST["obj_id"]
        f = request.FILES["file"]

        cat = get_or_none(Category, obj_id)
        if cat != None:
            cf = CategoryFile.objects.create(file=f, category=cat)
        return render(request, "contents/category-files.html", {"obj": cat,})
    except Exception as e:
        print(e)
        #logger.error("[bookings-form_add_image]" + str(e))
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("admins", "projects", "categories")
def category_remove_file(request):
    try:
        obj_id = request.GET["obj_id"]
        obj = get_or_none(CategoryFile, obj_id) 
        cat = obj.category
        obj.file.delete(save=True)
        obj.delete()
        return render(request, "contents/category-files.html", {"obj": cat,})
    except Exception as e:
        print(e)
        #logger.error("[remove_file]" + str(e))
        return render(request, 'error_exception.html', {'msg': str(e)})


'''
    Items
    FIXME: Hacer una gestión de items para los usuarios de tipo categories
'''
@group_required("admins", "projects", "categories")
def item_form (request):
    try:
        obj = get_or_none(Item, request.GET["objId"], 'uuid') if "objId" in request.GET else None
        cat = get_or_none(Category, request.GET["catId"], 'uuid') if "catId" in request.GET else None
        if cat is not None:
            lang = request.GET['lang'] if 'lang' in request.GET else request.LANGUAGE_CODE
            lang = lang.split('-')[0]
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

@group_required("admins", "projects", "categories")
def item_change_active(request, item_id):
    try:
        item = Item.objects.get(uuid=item_id)
        item.is_active = (item.is_active + 1) % 2
        item.save()
        return render(request, "contents/item-row.html", {'item':item})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins", "projects", "categories")
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

@group_required("admins", "projects", "categories")
def item_change_image(request):
    if request.method == "POST":
        try:
            form = ImageUploadForm(request.POST, request.FILES)
            if form.is_valid():
                cat = Category.objects.get(pk = request.POST.get('cat_id','0'))
                item = Item.objects.get(pk = request.POST.get('obj_id','0'))
                item.image = form.cleaned_data['image']
                item.save()
                return HttpResponse(item.image.url)
            else:
                print("NO")
        except Exception as e:
            print (show_exc(e))
            return HttpResponse(show_exc(e))
    else:
        return (HttpResponse("Lo sentimos, pero ha ocurrido un error. "))

@group_required("admins", "projects", "categories")
def item_add_image(request):
    try:
        obj_id = request.POST["obj_id"]
        image = request.FILES["file"]

        item = get_or_none(Item, obj_id)
        if item != None:
            item.image = image
            item.save()
        return render(request, "contents/item-img.html", {"obj": item,})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("admins", "projects", "categories")
def item_remove_image(request):
    try:
        obj_id = request.GET["obj_id"]
        obj = get_or_none(Item, obj_id) 
        obj.image.delete(save=True)
        if Item.objects.filter(image=obj.image).count() > 1:
            obj.image = None
            obj.save()
        else:
            obj.image.delete(save=True)

        return render(request, "contents/item-img.html", {"obj": obj,})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("admins", "projects", "categories")
def item_add_image_gallery(request):
    try:
        obj_id = request.POST["obj_id"]
        image = request.FILES["file"]

        item = get_or_none(Item, obj_id)
        if item != None:
            ii = ItemImage.objects.create(image=image, item=item)
        return render(request, "contents/item-gallery.html", {"obj": item,})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("admins", "projects", "categories")
def item_remove_image_gallery(request):
    try:
        obj_id = request.GET["obj_id"]
        obj = get_or_none(ItemImage, obj_id) 
        item = obj.item
        obj.image.delete(save=True)
        obj.delete()
        return render(request, "contents/item-gallery.html", {"obj": item,})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})


@group_required("admins", "projects", "categories")
def save_allergen(request):
    try:
        obj = get_or_none(Item, request.GET["obj_id"])
        allergen = get_or_none(Allergen, request.GET["allergen_id"])
        add = request.GET["add"]
        
        if add == "True":
            ItemAllergen.objects.create(item=obj, allergen=allergen)
        else:
            ItemAllergen.objects.filter(item=obj, allergen=allergen).delete()
        return render(request, "contents/allergens.html", {"obj": obj, "item_list": Allergen.objects.all()})
    except Exception as e:
        return render(request, "error_exception.html", {'exc': show_exc(e)})

@group_required("admins", "projects", "categories")
def new_extra(request):
    try:
        obj = get_or_none(Item, request.GET["obj_id"])
        ItemExtra.objects.create(item=obj)
        return render(request, "contents/extras.html", {"obj": obj,})
    except Exception as e:
        return render(request, "error_exception.html", {'exc': show_exc(e)})

@group_required("admins", "projects", "categories")
def remove_extra(request):
    try:
        obj = get_or_none(ItemExtra, request.GET["obj_id"])
        item = obj.item
        obj.delete()
        return render(request, "contents/extras.html", {"obj": item,})
    except Exception as e:
        return render(request, "error_exception.html", {'exc': show_exc(e)})

@group_required("admins", "projects", "categories")
def save_feature(request):
    try:
        obj = get_or_none(Category, request.GET["obj_id"])
        feature = get_or_none(Feature, request.GET["feature_id"])
        add = request.GET["add"]
        
        if add == "True":
            CategoryFeature.objects.create(category=obj, feature=feature)
        else:
            CategoryFeature.objects.filter(category=obj, feature=feature).delete()
        return render(request, "contents/features.html", {"obj": obj, "item_list": Feature.objects.all()})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc': show_exc(e)})

@group_required("admins", "projects", "categories")
def save_payment_type(request):
    try:
        obj = get_or_none(Category, request.GET["obj_id"])
        pt = get_or_none(PaymentType, request.GET["payment_type_id"])
        add = request.GET["add"]
        
        if add == "True":
            CategoryPaymentType.objects.create(category=obj, payment_type=pt)
        else:
            CategoryPaymentType.objects.filter(category=obj, payment_type=pt).delete()
        return render(request, "contents/payment-types.html", {"obj": obj, "item_list": PaymentType.objects.all()})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc': show_exc(e)})

@group_required("admins", "projects", "categories")
def new_promo(request):
    try:
        obj = get_or_none(Item, request.GET["obj_id"])
        ItemPromo.objects.create(item=obj)
        return render(request, "contents/promos.html", {"obj": obj,})
    except Exception as e:
        return render(request, "error_exception.html", {'exc': show_exc(e)})

@group_required("admins", "projects", "categories")
def remove_promo(request):
    try:
        obj = get_or_none(ItemPromo, request.GET["obj_id"])
        item = obj.item
        obj.delete()
        return render(request, "contents/promos.html", {"obj": item,})
    except Exception as e:
        return render(request, "error_exception.html", {'exc': show_exc(e)})

@group_required("admins", "projects", "categories")
def item_add_banner(request):
    try:
        obj_id = request.POST["obj_id"]
        image = request.FILES["file"]

        item = get_or_none(ItemPromo, obj_id)
        if item != None:
            item.banner = image
            item.save()
        return render(request, "contents/promos.html", {"obj": item.item,})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("admins", "projects", "categories")
def item_remove_banner(request):
    try:
        obj_id = request.GET["obj_id"]
        obj = get_or_none(ItemPromo, obj_id) 
        obj.banner.delete(save=True)
        return render(request, "contents/promos.html", {"obj": obj.item,})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("admins", "projects", "categories")
def item_change_price(request):
    try:
        obj_id = request.GET["obj_id"]
        code = request.GET["regime_code"]
        pos = request.GET["pos"]
        value = request.GET["value"]

        obj = get_or_none(Item, obj_id) 
        ItemPrice.objects.filter(item=obj, regime_code=code, pos=pos).delete()
        ip, created = ItemPrice.objects.get_or_create(item=obj, regime_code=code, pos=pos)
        ip.price = get_float(value.replace(",", "."))
        ip.save()

        return HttpResponse("Saved!")
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})


'''
    Category Users
'''
@group_required("categories")
def categories_by_categories(request):
    if request.category_user == None:
        return render(request, 'error_exception.html', {'msg': "User not found!"})
    return render(request,"contents/categories.html",{'project':request.category_user.categories[0].project,'items':request.category_user.categories})


'''
    Import
'''
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



@group_required("admins", "projects")
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

@group_required("admins", "projects")
def import_categories_by_file(request):
    json_tree = None

    try:
        project_uuid = request.POST["project_uuid"]
        content = request.FILES["file"].read().decode("utf-8")
        json_tree = json.loads(content)
        #json_tree = json.load(open(os.path.join(settings.BASE_DIR,'contents','{}.json'.format(project_uuid)),'r'))
    except Exception as e:
        print(e)
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
        try:
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
        except Exception as e:
            print(e)

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
            try:
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
            except Exception as e:
                print(e)
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

def item_get_img(request, item_id):
    return HttpResponse("OK")
