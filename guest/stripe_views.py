from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, translate, set_session, update_cron, get_int, translate2, get_random_str

from connector.libstripe import *
from connector.models import ProjectStripeUser
from .models import Guest, GuestStripe

@group_required("admins")
def stripe_alta_client(reqeuest, uuid_guest):
    guest = get_or_none(Guest, uuid_guest, "UUID")
    if guest is None:
        return render(request, 'error_exception.html', {'exc': 'Guest not found!'})

    email = guest.UUID + "@padword.es"  # Email ficticio, para identificar al cliente
    name = f'{guest.name} {guest.surname}'

    psu = ProjectStripeUser.objects.filter(project_uuid=guest.project_id).first()
    if psu is None:
        return render(request, 'error_exception.html', {'exc': 'Api Key not found!'})

    st = ShStripe(psu.api_key)
    session = st.alta_client(email, name)
    return redirect(session.url, code=303)

#        API_KEY = "sk_test_51PAwwh14EEiK5wo0fArBnn5kkPbri8PkDCTyiqcC2jknwqwYqjjSwHP8NQQmtVESzuIJ95TPukiN5m509SptMRAN00mmKFNDkW"
#        customer_data = {
#            "email": email,
#            "name": name,
#        }
#        obj_id = create_stripe_customer(API_KEY, customer_data)
#        session = stripe.checkout.Session.create(
#            customer = obj_id,
#            line_items=[{
#                'price_data': {
#                    'currency': 'eur',
#                    'product_data': {
#                        'name': 'Precarga',
#                    },
#                    'unit_amount': 100,
#                },
#                'quantity': 1,
#            }],
#            mode='payment', 
#            payment_method_options = {'card': {'setup_future_usage': 'off_session'}},
#            success_url='https://padword.shidix.es/web/stripe/store-payment/{CHECKOUT_SESSION_ID}',
#            cancel_url=f'https://padword.shidix.es/guest/guests/details/{guest.pk}/',
#        )
#        return redirect(session.url, code=303)

@group_required("admins")
def stripe_store_payment(request, session_id):
    try:
        #API_KEY = "sk_test_51PAwwh14EEiK5wo0fArBnn5kkPbri8PkDCTyiqcC2jknwqwYqjjSwHP8NQQmtVESzuIJ95TPukiN5m509SptMRAN00mmKFNDkW"
        session = stripe.checkout.Session.retrieve(session_id)
        payment_intent = stripe.PaymentIntent.retrieve(session.payment_intent)
        customer = stripe.Customer.retrieve(session.customer)
        email = customer.email
        guest = Guest.objects.get(UUID=email.split("@")[0])
        if payment_intent.status == "succeeded":
            try:
                guest_stripe = GuestStripe.objects.get(guest=guest)
            except:
                guest_stripe = GuestStripe(guest=guest)
            guest_stripe.stripe_id = session.customer
            guest_stripe.payment_method = payment_intent.payment_method
            guest_stripe.save()

            return redirect(reverse('guest-details', kwargs={'obj_id': guest.pk}))
        else:
            return HttpResponse("Payment KO")
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def stripe_error_payment(request):
    return HttpResponse("Error")

#@csrf_exempt
#def stripe_payment(request):
#    # wristband code = 4038674227
#    try:
#        if request.method == "POST":
#            key_value = request.POST["key_value"]
#            if key_value != "cH4Va?9qZSM_cFM!Kdo-hhmvENfqluOMbjxH-lDCMjhleaqCrCB?my8jMYl-?u!!JevHI2InZF!PFHXzZht_1Qkkxagaj?UPYuAvk3pEp-7LoDLPmUV9xRefYSedY!ba":
#                return HttpResponse("Error")
#            wristband_code = request.POST["wb_code"]
#            amount = request.POST["amount"]
#            wristband = Wristband.objects.get(code=wristband_code)
#            guest = wristband.guest
#            guest_stripe = GuestStripe.objects.get(guest=guest)
#            API_KEY = "sk_test_51PAwwh14EEiK5wo0fArBnn5kkPbri8PkDCTyiqcC2jknwqwYqjjSwHP8NQQmtVESzuIJ95TPukiN5m509SptMRAN00mmKFNDkW"
#            obj_id = create_stripe_payment_intent(API_KEY, guest_stripe.stripe_id, guest_stripe.payment_method, int(amount), "123", "eur")
#            if obj_id != "":
#                return HttpResponse("OK")
#            else:
#                return HttpResponse("Error")
#        else:
#            return HttpResponse("Error")
#    except Exception as e:
#        print (show_exc(e))
#        return HttpResponse("Error")

@group_required("admins")
def stripe_test_payment(request, test_type=-1):
    #import stripe

    API_KEY = "sk_test_51PAwwh14EEiK5wo0fArBnn5kkPbri8PkDCTyiqcC2jknwqwYqjjSwHP8NQQmtVESzuIJ95TPukiN5m509SptMRAN00mmKFNDkW"
    st = ShStripe(API_KEY)
    payment_method_data = {
            # "type": "card",
            "card": {
                "number": "4242424242424242",
                "exp_month": 12,
                "exp_year": 2029,
                "cvc": "123",
            }
        }

    if type(test_type) == str:
        print (test_type)
        session = stripe.checkout.Session.retrieve(test_type)
        return HttpResponse(f'{session}<hr>')

    elif test_type == -1:
        print (test_type)
        return HttpResponse("OK")
    elif test_type == 0:
        import random
        st = ShStripe(API_KEY) 
        obj_id = st.create_stripe_payment_intent("cus_Q9LsDjy8eXJZX6", "pm_1PJ3GL14EEiK5wo03ZnybHBz", int(random.randint(1,100000)), "123", "eur")
        #obj_id = create_stripe_payment_intent(API_KEY, "cus_Q9LsDjy8eXJZX6", "pm_1PJ3GL14EEiK5wo03ZnybHBz", int(random.randint(1,100000)), "123", "eur")

    elif test_type == 1:

        customer_data = {
            "email": "none@shidix.com",
            "name": "Shidix",
            "description": "Shidix Customer",
            "phone": "123456789",
            "address": {
                "city": "Finca España",
                "country": "ES",
                "line1": "Avenida Las Palmeras",
                "line2": "19",
                "postal_code": "38230",
                "state": "Santa Cruz de Tenerife"
            }
        }
        obj_id = st.create_stripe_customer(customer_data)
        #obj_id = create_stripe_customer(API_KEY, customer_data)
    elif test_type == 2:
        customer_data = {
            "email": "none@shidix.com",
            "name": "Shidix",
        }
        obj_id = st.create_stripe_customer(customer_data)
        #obj_id = create_stripe_customer(API_KEY, customer_data)
        intents = stripe.PaymentIntent.list(customer=obj_id, limit=1)
        for intent in intents:
            break
        import random
        obj_id = create_stripe_payment_intent(API_KEY, obj_id, intent.payment_method, random.randint(1,100000), "123", "eur")

    elif test_type == 4:
        stripe.api_key = API_KEY
        customer_data = {
            "email": "none@shidix.com",
            "name": "Shidix",
        }
        obj_id = st.create_stripe_customer(customer_data)
        #obj_id = create_stripe_customer(API_KEY, customer_data)

        session = stripe.checkout.Session.create(
            customer = obj_id,
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': 'Precarga',
                    },
                    'unit_amount': 100,
                },
                'quantity': 1,
            }],
            mode='payment',
            payment_method_options = {'card': {'setup_future_usage': 'off_session'}},
            success_url='https://padword.shidix.es/web/stripe/test-payment/{CHECKOUT_SESSION_ID}',
            cancel_url='https://padword.shidix.es/web/stripe/test-payment/',
        )
        return redirect(session.url, code=303)

    return HttpResponse(f'{obj_id}<hr>')

