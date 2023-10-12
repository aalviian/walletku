from django.utils import timezone

import factory

from wallet.models import WalletAccount, WalletUser


class WalletUserFactory(factory.django.DjangoModelFactory):
    customer_xid = factory.Faker("uuid4")

    class Meta:
        model = WalletUser


class WalletAccountFactory(factory.django.DjangoModelFactory):
    status = True
    enabled_at = timezone.localtime(timezone.now())

    class Meta:
        model = WalletAccount
