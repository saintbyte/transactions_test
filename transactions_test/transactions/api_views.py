from contextlib import suppress
from decimal import Decimal

from accounts.models import Account
from django.contrib.auth import get_user_model
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from transactions.constants import ACCEPTABLE_TRANSACTION
from transactions.constants import SIMPLE_TRANSACTION
from transactions.exceptions import BadRequest
from transactions.models import Transaction
from transactions.serializers import CreateTransactionSerializer
from transactions.tasks import accept_transaction
from transactions.tasks import cancel_transaction


class TransactionViewSet(GenericViewSet, mixins.CreateModelMixin):
    def _get_account(self, account_id):
        with suppress(Account.DoesNotExist):
            return Account.objects.filter(pk=account_id, is_active=True).first()
        return None

    def _get_user(self, user_id):
        with suppress(get_user_model().DoesNotExist):
            return get_user_model().objects.get(pk=user_id)
        return None

    def create(self, request, *args, **kwargs):
        """
        Create transaction
        """
        serializer = CreateTransactionSerializer(data=request.data)
        if not serializer.is_valid():
            print(serializer.errors)
            raise BadRequest("cant pass serilizer")
        data = serializer.validated_data
        from_account_obj = self._get_account(data.get("from_account"))
        to_account_obj = self._get_account(data.get("to_account"))
        creator_obj = request.user
        if not all([from_account_obj, to_account_obj, creator_obj]):
            raise BadRequest("from_account, to_account, creator is not valid")
        if from_account_obj.holder != creator_obj:
            raise BadRequest("from_account is not ownded by creator")
        if from_account_obj.balance < Decimal(data.get("amount")):
            raise BadRequest("amount more balance")
        transaction = Transaction(
            from_account=from_account_obj,
            to_account=to_account_obj,
            request_id=data.get("request_id"),
            amount=data.get("amount"),
            creator=creator_obj,
            type_of_transaction=data.get("transaction_type"),
        )
        transaction.save()
        if transaction.type_of_transaction == SIMPLE_TRANSACTION:
            accept_transaction.delay(transaction.pk)
        return Response(
            data={"transaction_id": transaction.pk}, status=status.HTTP_202_ACCEPTED
        )

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        """
        Для аккредитива и выставленного счета;
        """
        # transaction
        transaction = get_object_or_404(Transaction.objects.filter(), pk=pk)
        if transaction not in ACCEPTABLE_TRANSACTION:
            raise BadRequest("Transcation cant be accept")
        if transaction.processed:
            raise BadRequest("Transcation allready processed")
        accept_transaction.delay(pk)
        return Response(status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        transaction = get_object_or_404(Transaction.objects.filter(), pk=pk)
        if transaction.processed:
            raise BadRequest("Transcation allready processed")
        cancel_transaction.delay(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
