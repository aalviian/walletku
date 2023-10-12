import uuid

from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        get_latest_by = "created_at"


class WalletUser(BaseModel):
    customer_xid = models.CharField(
        max_length=50,
        unique=True,
        error_messages={
            "unique": "A user with that ID already exists.",
        },
    )

    class Meta:
        db_table = "wallet_users"

    def save(self, *args, **kwargs):
        self.customer_xid = self.customer_xid
        super(WalletUser, self).save(*args, **kwargs)


class WalletAccount(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owned_by = models.OneToOneField(
        "WalletUser",
        related_name="wallet",
        on_delete=models.CASCADE
    )
    status = models.BooleanField(default=True)
    balance = models.PositiveBigIntegerField(default=0)
    enabled_at = models.DateTimeField(blank=True, null=True)
    disabled_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "wallet_account"

    @property
    def parse_status(self):
        return "enabled" if self.status else "disabled"


class WalletTransaction(BaseModel):
    TRANSACTION_TYPES = {
        "deposit": "Deposit",
        "withdrawal": "Withdrawal",
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_id = models.CharField(
        max_length=50,
        unique=True,
        error_messages={
            "unique": "A reference with that ID already exists.",
        },
    )
    wallet = models.ForeignKey('WalletAccount', related_name="transactions", on_delete=models.CASCADE)
    status = models.BooleanField(default=True)
    type = models.CharField(max_length=10, blank=True, null=True, choices=TRANSACTION_TYPES.items())
    action_by = models.ForeignKey(
        "WalletUser",
        related_name="user_transactions",
        on_delete=models.CASCADE
    )
    action_at = models.DateTimeField(blank=True, null=True)
    amount = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "wallet_transactions"
        ordering = ("action_at",)

    @property
    def parse_status(self):
        return "success" if self.status else "failed"
