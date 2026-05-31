# services/senepay.py
import requests
from django.conf import settings


class SenePayClient:
    def __init__(self):
        self.base_url = "https://api.sene-pay.com"
        self.api_key = settings.SENEPAY_API_KEY
        self.api_secret = settings.SENEPAY_API_SECRET

    def _headers(self):
        return {
            "Content-Type": "application/json",
            "X-Api-Key": self.api_key,
            "X-Api-Secret": self.api_secret,
        }

    def create_checkout(self, amount, order_ref, success_url, cancel_url, webhook_url, country=None):
        """Crée une session de paiement"""
        url = f"{self.base_url}/api/v1/checkout/sessions"
        payload = {
            "amount": int(amount),
            "currency": "XOF",
            "orderReference": order_ref,
            "successUrl": success_url,
            "cancelUrl": cancel_url,
            "webhookUrl": webhook_url,
        }
        # Ajouter le pays seulement s'il est spécifié
        if country:
            payload["country"] = country

        response = requests.post(url, json=payload, headers=self._headers())
        response.raise_for_status()
        return response.json()


senepay = SenePayClient()