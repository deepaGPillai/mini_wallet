import logging
from time import sleep

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from transaction.models import Transaction
from wallet.models import Wallet

logger = logging.getLogger('walletmanager.logger')
JSON_PARAMS = {'indent': 2}


@csrf_exempt
@api_view(['POST', 'GET', 'PATCH', ])
@permission_classes([IsAuthenticated])
def wallet_view(request):
    response_data = {'status': '', 'data': {}, 'message': []}
    customer = request.user
    wallet = None
    try:
        wallet = Wallet.objects.get(customer=customer)
    except ObjectDoesNotExist as e:
        response_data['status'] = 'FAILED'
        response_data['message'].append('Unable to Find Wallet For Customer')
        return JsonResponse(response_data, json_dumps_params=JSON_PARAMS)

    if request.method == 'POST':
        if wallet.status is True:
            response_data['status'] = 'FAILED'
            response_data['message'].append('Wallet Already Enabled')
        else:
            wallet.status = True
            wallet.enabled_at = timezone.now()
            try:
                wallet.save()
                response_data['status'] = 'SUCCESS'
                response_data['data'] = {'wallet': wallet.get_dict()}
                response_data['message'].append('Wallet Enabled')
            except ValueError as e:
                logger.error('Error in Save : DB Error' + str(e.args[0]))
                response_data['status'] = 'FAILED'
                response_data['message'].append('Database Error')
        return JsonResponse(response_data, json_dumps_params=JSON_PARAMS)
    if request.method == 'PATCH':
        is_disabled_flag = request.data.get('is_disabled', '')
        if is_disabled_flag and is_disabled_flag.lower() == 'true':
            if wallet.status is False:
                response_data['status'] = 'FAILED'
                response_data['message'].append('Wallet Already Disabled')
            else:
                wallet.status = False
                try:
                    wallet.save()
                    response_data['status'] = 'SUCCESS'
                    response_data['data'] = {'wallet': wallet.get_dict()}
                    response_data['message'].append('Wallet Disabled')
                except ValueError as e:
                    logger.error('Error in Save : DB Error' + str(e.args[0]))
                    response_data['status'] = 'FAILED'
                    response_data['message'].append('Database Error')
        else:
            response_data['status'] = 'FAILED'
            response_data['message'].append('Form Data (is_disabled) Missing/Invalid')
        return JsonResponse(response_data, json_dumps_params=JSON_PARAMS)
    if request.method == 'GET':
        if wallet.status is False:
            response_data['status'] = 'FAILED'
            response_data['message'].append('Operation Not permitted. Wallet is Disabled')
        else:
            response_data['status'] = 'SUCCESS'
            response_data['data'] = {'wallet': wallet.get_dict()}
        return JsonResponse(response_data, json_dumps_params=JSON_PARAMS)


@csrf_exempt
@api_view(['GET', ])
@permission_classes([IsAuthenticated])
def reference_view(request):
    response_data = {'status': '', 'data': {}, 'message': []}
    customer = request.user
    wallet = None
    try:
        wallet = Wallet.objects.get(customer=customer)
    except ObjectDoesNotExist as e:
        response_data['status'] = 'FAILED'
        response_data['message'].append('Unable to Generate ReferenceID. No Wallet Found.')
        return JsonResponse(response_data, json_dumps_params=JSON_PARAMS)

    if wallet.status is False:
        response_data['status'] = 'FAILED'
        response_data['message'].append('Wallet is Disabled. Transaction not Permitted.')
    else:
        transaction = Transaction(wallet=wallet)
        try:
            transaction.save()
            response_data['status'] = 'SUCCESS'
            response_data['data'] = transaction.get_dict()
            response_data['message'].append('Reference ID Generated for Transaction.')
        except ValueError as e:
            logger.error('Error in Save : DB Error' + str(e.args[0]))
            response_data['status'] = 'FAILED'
            response_data['message'].append('Database Error')
    return JsonResponse(response_data, json_dumps_params=JSON_PARAMS)


@csrf_exempt
@api_view(['POST', ])
@permission_classes([IsAuthenticated])
def deposit_view(request):
    response_data = {'status': '', 'data': {}, 'message': []}
    customer = request.user

    amount = request.data.get('amount', None)
    reference_id = request.data.get('reference_id', None)
    if reference_id is None:
        response_data['status'] = 'FAILED'
        response_data['message'].append("reference_id Missing.")

    # Validate Amount
    if amount is None:
        response_data['status'] = 'FAILED'
        response_data['message'].append("amount Missing.")
    else:
        if not validate_int(amount):  # isinstance() not reliable, as isinstance("1") is false
            response_data['status'] = 'FAILED'
            response_data['message'].append("Invalid Amount Value. Should be Integer Value")
        else:
            if not int(amount) > 0:
                response_data['status'] = 'FAILED'
                response_data['message'].append("Amount should be greater than 0")

    if not response_data['message']:
        amount = int(amount)

        wallet = fetch_wallet(customer, response_data)
        if response_data['status'] == 'FAILED':
            return JsonResponse(response_data, json_dumps_params=JSON_PARAMS)

        transaction = fetch_transaction(wallet, reference_id, response_data)
        if response_data['status'] == 'FAILED':
            return JsonResponse(response_data, json_dumps_params=JSON_PARAMS)

        transaction.amount = amount
        transaction.type = 'DEPOSIT'
        transaction.status = 'IP'
        try:
            transaction.save()
            sleep(5)
        except ValueError as e:
            logger.error('Error in Deposit : DB Error <Attempted State = TRANSACTION_IN-PROGRESS>' + str(e.args[0]))
            response_data['status'] = 'FAILED'
            response_data['message'].append('Database Error')

        try:
            wallet.balance = wallet.balance + int(transaction.amount)
            wallet.save()
            try:
                transaction.type = 'DX'
                transaction.status = 'CMP'
                transaction.save()
                response_data['status'] = 'SUCCESS'
                deposit = { "status": "success",
                            "deposited_by": str(wallet.customer.cxid),
                            "amount": str(amount),
                            "reference_id": str(reference_id)
                            }
                response_data['data'] = deposit
            except ValueError as e:
                logger.error('Error in Deposit : DB Error <Attempted State = TRANSACTION_COMPLETE>' + str(e.args[0]))
                response_data['status'] = 'FAILED'
                response_data['message'].append('Database Error')
        except ValueError as e:
            logger.error('Error in Deposit : DB Error <Attempted State = WALLET_UPDATE>' + str(e.args[0]))
            response_data['status'] = 'FAILED'
            response_data['message'].append('Database Error')
            try:
                transaction.type = 'DEPOSIT'
                transaction.status = 'ABORTED'
                transaction.save()
            except ValueError as e:
                logger.error('Error in Deposit : DB Error <Attempted State = TRANSACTION_ABORT>' + str(e.args[0]))
                response_data['status'] = 'FAILED'
                response_data['message'].append('Database Error')

    return JsonResponse(response_data, json_dumps_params=JSON_PARAMS)


@csrf_exempt
@api_view(['POST', ])
@permission_classes([IsAuthenticated])
def withdrawal_view(request):
    response_data = {'status': '', 'data': {}}
    pass


def fetch_wallet(customer, response_data):
    wallet = None
    try:
        wallet = Wallet.objects.get(customer=customer)
    except ObjectDoesNotExist as e:
        response_data['status'] = 'FAILED'
        response_data['message'].append('Unable to Deposit. No Wallet Found.')
    if wallet.status is False:
        response_data['status'] = 'FAILED'
        response_data['message'].append('Wallet is Disabled. Deposit not Permitted.')
    return wallet


def fetch_transaction(wallet, reference_id, response_data):
    transaction = None
    try:
        transaction = Transaction.objects.get(wallet=wallet, reference_id=reference_id)
    except ObjectDoesNotExist as e:
        response_data['status'] = 'FAILED'
        response_data['message'].append('Unable to Fetch Transaction. Wallet & Reference ID Mismatch.')
    if transaction and not transaction.status == 'INIT':
        response_data['status'] = 'FAILED'
        response_data['message'].append('Transaction Attempted with Given Reference ID')
    return transaction


def validate_int(amount):
    try:
        val = int(amount)
    except ValueError as e:
        return False
    return True
