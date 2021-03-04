import json
import logging

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from customer.forms import CreateCustomerForm
from customer.models import Customer
from wallet.models import Wallet

logger = logging.getLogger('walletmanager.logger')
JSON_PARAMS = {'indent': 2}


def validate_form(request_data):
    errors = []
    if "username" not in request_data.keys():
        errors.append("username")
    if "email" not in request_data.keys():
        errors.append("email")
    if "password" in request_data.keys():
        request_data["password1"] = request_data["password"]
    else:
        errors.append("password")
    return request_data, errors


@csrf_exempt
@api_view(['POST', ])
def register_view(request):
    try:
        request_data = json.loads(request.body)
        logger.info("Register API Accessed: /")
        validations = validate_form(request_data)
        if validations[1]:
            raise ValidationError(validations[1])
        form = CreateCustomerForm(request_data)
        customer = form.save()
        wallet = Wallet(customer=customer)
        wallet.save()
        dto = {'username': customer.username, 'email': customer.email, 'customer_id': str(customer.cxid),
               'wallet_id': str(wallet.wxid)}
        return JsonResponse(dto, json_dumps_params=JSON_PARAMS)
    except json.decoder.JSONDecodeError as e:
        logger.error('Error in Registration : Malformed Request Body ' + str(e.args[0]))
        return JsonResponse({"Message": 'Malformed request body ' + str(e.args[0])}, json_dumps_params=JSON_PARAMS)
    except ValidationError as e:
        logger.error('Form Validation Failed. Fields = ' + str(e))
        return JsonResponse({"Message": 'Missing Field: ' + str(e)}, json_dumps_params=JSON_PARAMS)
    except ValueError as e:
        logger.error('Error in Save : DB Error' + str(e.args[0]))
        return JsonResponse({"Message": 'Error in DB Save. ' + str(e.args[0])}, json_dumps_params=JSON_PARAMS)


class JWTTokenSerializer(TokenObtainSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields['password']
        del self.fields['username']

    def get_token(self, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        response_data = {}
        try:
            request = self.context["request"]
        except KeyError:
            response_data['code'] = 500
            response_data['message'] = 'Internal Server Error'
            return response_data

        if request.method == 'POST':
            try:
                cxid = request.data['customer_xid']
                customer = Customer.objects.get(cxid=cxid)
                refresh = self.get_token(user=customer)
                token = {'token': str(refresh.access_token)}
                response_data['status'] = "success"
                response_data['code'] = "200"
                response_data['data'] = token
            except KeyError:
                response_data['code'] = 400
                response_data['message'] = 'customer_xid is mandatory'
            except Customer.DoesNotExist:
                response_data['code'] = 400
                response_data['message'] = 'Customer Not Found With XID= {}'.format(str(cxid))
        else:
            response_data['code'] = 400
            response_data['message'] = "{} Method not supported".format(str(request.method))

        return response_data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = JWTTokenSerializer

