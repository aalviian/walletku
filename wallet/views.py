from django.core.exceptions import ValidationError
from django.db import transaction

from rest_framework import generics, permissions, viewsets
from rest_framework.views import APIView

from wallet.models import WalletAccount, WalletTransaction, WalletUser
from wallet.serializers import ObtainTokenSerializer, WalletAccountSerializer, WalletTransactionSerializer

from walletku.authentication import JWTAuthentication
from walletku.permissions import IsAuthenticated
from walletku.response import CustomResponse


class InitAuth(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ObtainTokenSerializer

    def get(self, request):
        return CustomResponse(data={"message": "Welcome to Wallet APIs"}, status="success")

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer_xid = request.data.get("customer_xid")
        user = WalletUser.objects.filter(customer_xid=customer_xid).first()
        if user is None:
            user = WalletUser.objects.create(customer_xid=customer_xid)

        jwt_token = JWTAuthentication.create_jwt(user)
        return CustomResponse(data={"token": jwt_token}, status="success")


class DetailWallet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = WalletAccountSerializer

    def get_object(self):
        instance = WalletAccount.objects.filter(owned_by=self.request.user).first()
        return instance

    def retrieve(self, request):
        instance = self.get_object()
        if not instance:
            return CustomResponse({"error": "Wallet not found"}, status="fail")

        serializer = self.serializer_class(instance)
        if serializer.data["status"]:
            status = "success"
            data = {"wallet": serializer.data}
        else:
            status = "fail"
            data = {"error": "Wallet disabled"}
        return CustomResponse(data, status=status)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": self.request})
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except ValidationError as e:
            return CustomResponse(data={"error": e.message}, status="fail")

        return CustomResponse(data={"wallet": serializer.data}, status="success")

    def partial_update(self, request, *args, **kwargs):
        wallet = WalletAccount.objects.filter(owned_by=self.request.user).first()
        if not wallet:
            return CustomResponse({"error": "Wallet not found"}, status="fail")

        serializer = self.serializer_class(
            wallet,
            data=request.data,
            context={"request": self.request},
            partial=True
        )

        if not serializer.is_valid(raise_exception=True):
            return CustomResponse(data={"error": serializer.errors}, status="fail")

        serializer.save()

        return CustomResponse(data={"wallet": serializer.data}, status="success")


class ListTransaction(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WalletTransactionSerializer

    def get_queryset(self):
        queryset = WalletTransaction.objects.filter(wallet__owned_by=self.request.user, wallet__status=1)
        return queryset

    def list(self, request, *args, **kwargs):
        wallet = request.user.wallet if hasattr(request.user, "wallet") else None
        if not wallet or not wallet.status:
            return CustomResponse(data={"error": "Wallet disabled"}, status="fail")

        transactions = WalletTransaction.objects.filter(wallet=wallet)
        serializer = self.get_serializer(transactions, many=True)
        return CustomResponse(data={"transactions": serializer.data}, status="success")


class CreateTransaction(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WalletTransactionSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        action_type = self.kwargs["action_type"]
        serializer = self.serializer_class(
            data=request.data, context={"request": request, "action_type": action_type}
        )
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except ValidationError as e:
            return CustomResponse(data={"error": e.message}, status="success")

        return CustomResponse(data={action_type: serializer.data}, status="success")
