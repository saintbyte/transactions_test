from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from transactions.constants import DECIMAL_MAX_DIGITS
from transactions.constants import DECIMAL_PLACES
from transactions.constants import TYPE_OF_TRANSACTION


class CreateTransactionSerializer(serializers.Serializer):
    from_account = serializers.IntegerField(required=True)
    to_account = serializers.IntegerField(required=True)
    request_id = serializers.CharField(required=True)
    transaction_type = serializers.CharField(required=True)
    amount = serializers.DecimalField(
        max_digits=DECIMAL_MAX_DIGITS, decimal_places=DECIMAL_PLACES
    )

    def validate(self, data):
        validated_data = super().validate(data)
        if data.get("from_account") == data.get("to_account"):
            raise ValidationError("cant from_account == to_account")
        if data.get("transaction_type") not in TYPE_OF_TRANSACTION:
            raise ValidationError(
                "transaction_type not in" + ",".join(TYPE_OF_TRANSACTION)
            )
        return validated_data
