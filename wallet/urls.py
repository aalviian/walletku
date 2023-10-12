from django.urls import path

from wallet import views as WalletViews

urlpatterns = [
    path("init/", WalletViews.InitAuth.as_view(), name="init-auth"),
    path("wallet/", WalletViews.DetailWallet.as_view({
        "get": "retrieve",
        "post": "create",
        "patch": "partial_update"
    }), name="wallet-detail"),
    path("wallet/transactions/", WalletViews.ListTransaction.as_view(), name="wallet-transactions"),
    path("wallet/<str:action_type>/", WalletViews.CreateTransaction.as_view(), name="create-transaction"),
]
