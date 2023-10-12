# apps/management/authentication.py

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model

import jwt

from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed, ParseError

from wallet.models import WalletUser

User = get_user_model()


class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        # Extract the JWT from the Authorization header
        jwt_token = request.META.get("HTTP_AUTHORIZATION")
        if jwt_token is None:
            return None

        # clean the token
        jwt_token = JWTAuthentication.get_the_token_from_header(jwt_token)

        # Decode the JWT and verify its signature
        try:
            payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.exceptions.InvalidSignatureError:
            raise AuthenticationFailed("Invalid signature")
        except Exception:
            raise ParseError()

        # Get the user from the database
        customer_xid = payload.get("user_identifier")
        if customer_xid is None:
            raise AuthenticationFailed("User identifier not found in JWT")

        user = WalletUser.objects.filter(customer_xid=customer_xid).first()
        if user is None:
            raise AuthenticationFailed("User not found")

        return user, payload

    def authenticate_header(self, request):
        return "Token"

    def get_user(self, user_id):
        try:
            return WalletUser.objects.get(customer_xid=user_id)
        except User.DoesNotExist:
            return None

    def _get_uuid_from_token(self, jwt_token):
        validated_token = self.get_validated_token(jwt_token)
        try:
            return validated_token["customer_xid"]
        except KeyError:
            raise AuthenticationFailed("Token contained no recognizable user identification")

    @classmethod
    def create_jwt(cls, user):
        payload = {
            "user_identifier": user.customer_xid,
            "exp": int((datetime.now() + timedelta(hours=24)).timestamp()),
            # set the expiration time for 5 hour from now
            "iat": datetime.now().timestamp(),
            "customer_xid": user.customer_xid
        }

        # Encode the JWT with the secret key
        jwt_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        return jwt_token

    @classmethod
    def get_the_token_from_header(cls, token):
        token = token.replace("Token", "").replace(" ", "")  # clean the token
        return token
