from django.core.exceptions import ValidationError
from django.utils import timezone

from rest_framework import serializers

from wallet.models import WalletAccount, WalletTransaction, WalletUser


class ObtainTokenSerializer(serializers.Serializer):
    customer_xid = serializers.CharField()


class WalletAccountSerializer(serializers.ModelSerializer):
    owned_by = serializers.ReadOnlyField(source="owned_by.customer_xid")
    is_disabled = serializers.BooleanField(required=False, write_only=True)
    status = serializers.ReadOnlyField(source="parse_status")

    class Meta:
        model = WalletAccount
        fields = [
            "id",
            "owned_by",
            "status",
            "balance",
            "is_disabled",
        ]
        read_only_fields = [
            "id",
        ]

    def to_representation(self, instance):
        representation = super(WalletAccountSerializer, self).to_representation(instance)
        if instance.status:
            representation["enabled_at"] = instance.enabled_at
        else:
            representation["disabled_at"] = instance.disabled_at

        return representation

    def validate(self, attrs):
        if "is_disabled" in attrs:
            today = timezone.localtime(timezone.now())
            if attrs.pop("is_disabled"):
                status = False
                attrs["disabled_at"] = today
            else:
                status = True
                attrs["enabled_at"] = today

            attrs["status"] = status
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        wallet = getattr(request.user, "wallet", None)
        if wallet and wallet.status:
            raise ValidationError("Wallet enabled")
        else:
            if wallet.status == "disabled" and not validated_data["status"]:
                raise ValidationError("Wallet already disabled")

            wallet, _ = WalletAccount.objects.update_or_create(
                owned_by_id=request.user.id,
                defaults={
                    "status": True,
                    "enabled_at": timezone.localtime(timezone.now())
                },
            )

        return wallet


class WalletUserSerializer(serializers.Serializer):
    customer_xid = serializers.CharField(required=True)

    def create(self, validated_data):
        user, _ = WalletUser.objects.get_or_create(customer_xid=validated_data["customer_xid"])
        if user:
            WalletAccount.objects.create(owned_by=user)


class WalletTransactionSerializer(serializers.ModelSerializer):
    amount = serializers.IntegerField(required=True)
    status = serializers.ReadOnlyField(source="parse_status")

    class Meta:
        model = WalletTransaction
        fields = [
            "id",
            "status",
            "type",
            "reference_id",
            "amount",
        ]
        read_only_fields = [
            "id",
            "type",
        ]

    def to_representation(self, instance):
        action_type = self.context.get("action_type")
        representation = super(WalletTransactionSerializer, self).to_representation(instance)
        if action_type:
            if action_type == "deposits":
                representation["deposited_by"] = instance.action_by.customer_xid
                representation["deposited_at"] = instance.action_at
            else:
                representation["withdrawn_by"] = instance.action_by.customer_xid
                representation["withdrawn_at"] = instance.action_at
        else:
            representation["transacted_at"] = instance.action_at

        return representation

    def create(self, validated_data):
        request = self.context.get("request")
        wallet_account = WalletAccount.objects.filter(owned_by=request.user, status=True).first()
        if not wallet_account:
            raise ValidationError("Wallet not found or disabled")

        action_type = self.context.get("action_type")
        type = ""

        if action_type == "deposits":
            wallet_account.balance += validated_data["amount"]
            type = "deposit"
        elif action_type == "withdrawals":
            if wallet_account.balance <= 0:
                raise ValidationError("Balance insufficient")

            wallet_account.balance -= validated_data["amount"]
            type = "withdrawal"
        else:
            raise ValidationError("Unknown action")

        wallet_account.save()
        validated_data["wallet_id"] = str(wallet_account.id)
        validated_data["type"] = type
        validated_data["action_by"] = request.user
        validated_data["action_at"] = timezone.localtime(timezone.now())
        return WalletTransaction.objects.create(**validated_data)
