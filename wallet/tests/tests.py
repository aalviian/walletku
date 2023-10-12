from unittest.mock import patch

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase


class InitAuthTest(APITestCase):
    def setUp(self):
        self.data = {
            "customer_xid": "ea0212d3-abd6-406f-8c67-868e814a2436"
        }

    def test_get_init_auth(self):
        expected_response = {
            "status": "success",
            "data": {
                "message": "Welcome to Wallet APIs"
            }
        }
        response = self.client.get(reverse("init-auth"))
        self.assertEqual(response.data, expected_response)

    @patch("walletku.authentication.JWTAuthentication.create_jwt")
    def test_create_init_auth(self, mock_jwt_token):
        mock_jwt_token.return_value = "abced12345"
        expected_response = {
            "status": "success",
            "data": {
                "token": "abced12345"
            }
        }
        response = self.client.post(
            reverse("init-auth"),
            data=self.data,
        )
        self.assertEqual(response.data, expected_response)
