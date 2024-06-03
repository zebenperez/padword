from django.conf import settings

import stripe

#def create_stripe_customer(api_key, customer_data):
#    stripe.api_key = api_key
#
#    try:
#        query = stripe.Customer.search(limit=1, query=f"email:'{customer_data['email']}' AND name:'{customer_data['name']}'")
#        if len(query.data) > 0:
#            return query.data[0].id
#        
#        customer = stripe.Customer.create(
#            email=customer_data['email'],
#            name=customer_data['name'],
#            # phone=customer_data['phone'],
#            # address={
#            #     'line1': customer_data['address']['line1'],
#            #     'line2': customer_data['address']['line2'],
#            #     'city': customer_data['address']['city'],
#            #     'state': customer_data['address']['state'],
#            #     'postal_code': customer_data['address']['postal_code'],
#            #     'country': customer_data['address']['country']
#            # }
#        )
#        return customer.id
#    except stripe.error.StripeError as e:
#        # Handle any errors that occur during the API request
#        print(f"Error creating Stripe customer: {e}")
#        return None

#def get_stripe_payment_method(api_key, customer_id):
#    stripe.api_key = api_key
#    try:
#        intents = stripe.PaymentIntent.list(customer=customer_id, limit=1)
#        for intent in intents:
#            break
#        return intent.payment_method
#    except stripe.error.StripeError as e:
#        # Handle any errors that occur during the API request
#        print(f"Error creating Stripe payment method: {e}")
#        return None
    
#def create_stripe_payment_intent(api_key, customer_id, payment_method_id, amount, cvc, currency="eur", return_url="https://padword.shidix.es/"):
#    stripe.api_key = api_key
#
#    try:
#        cvc_token = stripe.Token.create(cvc_update={"cvc": cvc})
#        payment_intent = stripe.PaymentIntent.create(
#            amount=amount,
#            currency=currency,
#            customer=customer_id,
#            payment_method=payment_method_id,
#            automatic_payment_methods={ 'enabled': True, },
#            setup_future_usage='off_session',
#            # payment_method_options={'card':{'cvc_token':cvc_token}},
#            return_url=return_url,
#            confirm=True
#        )
#        return payment_intent.id
#    except stripe.error.StripeError as e:
#        # Handle any errors that occur during the API request
#        print(f"Error creating Stripe payment intent: {e}")
#        return None


class ShStripe:
    def __init__(self, api_key=""):
        self.api_key = api_key
        self.return_url = settings.STRIPE_RETURN_URL
        self.success_url = settings.STRIPE_SUCCESS_URL
        self.cancel_url = settings.STRIPE_CANCEL_URL

    def alta_client(self, email, name):
        customer_data = { "email": email, "name": name, }
        obj_id = self.create_stripe_customer(customer_data)
        #obj_id = self.create_stripe_customer(self.api_key, customer_data)
        session = stripe.checkout.Session.create(
            customer = obj_id,
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': { 'name': 'Precarga', },
                    'unit_amount': 100,
                },
                'quantity': 1,
            }],
            mode='payment', 
            payment_method_options = {'card': {'setup_future_usage': 'off_session'}},
            success_url = self.success_url,
            cancel_url = self.cancel_url,
        )
        return session

    #def create_stripe_customer(api_key, customer_data):
    def create_stripe_customer(self, customer_data):
        stripe.api_key = self.api_key

        try:
            query = stripe.Customer.search(limit=1, query=f"email:'{customer_data['email']}' AND name:'{customer_data['name']}'")
            if len(query.data) > 0:
                return query.data[0].id
            
            customer = stripe.Customer.create(email=customer_data['email'], name=customer_data['name'])
            return customer.id
        except stripe.error.StripeError as e:
            print(f"Error creating Stripe customer: {e}")
            return None

    #def create_stripe_payment_intent(api_key, customer_id, payment_method_id, amount, cvc, currency="eur", return_url="https://padword.shidix.es/"):
    def create_stripe_payment_intent(self, customer_id, payment_method_id, amount, cvc, currency="eur"):
        stripe.api_key = self.api_key

        try:
            cvc_token = stripe.Token.create(cvc_update={"cvc": cvc})
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                customer=customer_id,
                payment_method=payment_method_id,
                automatic_payment_methods={ 'enabled': True, },
                setup_future_usage='off_session',
                return_url=self.return_url,
                confirm=True
            )
            return payment_intent.id
        except stripe.error.StripeError as e:
            print(f"Error creating Stripe payment intent: {e}")
            return None


