from contextlib import suppress
from decimal import Decimal

from accounts.models import Account
from django.contrib.auth import get_user_model
from rest_framework import mixins
from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from transactions.constants import ACCEPTABLE_TRANSACTION
from transactions.constants import CREDIT_TRANSACTION
from transactions.constants import INVOICE_TRANSACTION
from transactions.constants import SIMPLE_TRANSACTION
from transactions.exceptions import BadRequest
from transactions.models import Transaction
from transactions.serializers import CreateTransactionSerializer


class TransactionViewSet(GenericViewSet, mixins.CreateModelMixin):
    authentication_classes = [
        SessionAuthentication,
        BasicAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def _get_account(self, account_id):
        with suppress(Account.DoesNotExist):
            return Account.objects.filter(pk=account_id, is_active=True).first()
        return None

    def _get_user(self, user_id):
        with suppress(get_user_model().DoesNotExist):
            return get_user_model().objects.get(pk=user_id)
        return None

    def _get_transaction_queryset(self, pk):
        return (
            Transaction.objects.select_related("from_account")
            .select_related("to_account")
            .select_for_update()
            .filter(pk=pk)
        )

    def _move_money(from_acc, to_acc, amount):
        from_acc.balance = from_acc.balance - amount
        to_acc.balance = to_acc.balance + amount

    def _accept_transaction(self, pk):
        transaction = self._get_transaction_queryset(pk)
        if transaction.from_account.balance < transaction.amount:
            return
        self._move_money(
            transaction.from_account, transaction.to_account, transaction.amount
        )
        transaction.processed = True
        transaction.save()

    def _cancel_transaction(self, pk):
        transaction = self._get_transaction_queryset(pk)
        if transaction.to_account.balance < transaction.amount:
            return
        self._move_money(
            transaction.to_account, transaction.from_account, transaction.amount
        )
        transaction.canceled = True
        transaction.save()

    def _delete_transaction(self, pk):
        Transaction.objects.filter(pk=pk).delete()

    def create(self, request, *args, **kwargs):
        """
        Create transaction
        """
        serializer = CreateTransactionSerializer(data=request.data)
        if not serializer.is_valid():
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
            self._accept_transaction(transaction.pk)
        return Response(
            data={"transaction_id": transaction.pk}, status=status.HTTP_202_ACCEPTED
        )

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        transaction = get_object_or_404(Transaction.objects.filter(), pk=pk)
        if transaction.type_of_transaction not in ACCEPTABLE_TRANSACTION:
            raise BadRequest("Transcation cant be accept")
        if transaction.processed:
            raise BadRequest("Transcation allready processed")
        self._accept_transaction(pk)
        return Response(status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        transaction = get_object_or_404(Transaction.objects.filter(), pk=pk)
        if transaction.processed:
            raise BadRequest("Transcation allready processed")
        if (
            transaction.type_of_transaction in [SIMPLE_TRANSACTION, INVOICE_TRANSACTION]
            and transaction.to_account.holder == request.user
        ):
            self._cancel_transaction(pk)
        if (
            transaction.type_of_transaction == CREDIT_TRANSACTION
            and transaction.from_account.holder == request.user
        ):
            self._cancel_transaction(pk)
            self._delete_transaction(pk)

        self._cancel_transaction(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
