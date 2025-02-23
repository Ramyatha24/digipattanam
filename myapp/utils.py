import requests
from django.conf import settings

def get_payu_token():
    """
    Fetch access token from PayU Payouts API.
    """
    url = f"{settings.PAYU_PAYOUTS['BASE_URL']}/auth/oauth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": settings.PAYU_PAYOUTS["CLIENT_ID"],
        "client_secret": settings.PAYU_PAYOUTS["CLIENT_SECRET"],
        "grant_type": "client_credentials"
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        return None


def make_payout(seller_bank_details, amount):
    """
    Send payout to the seller after deducting 10% commission.
    """
    access_token = get_payu_token()
    if not access_token:
        return {"error": "Authentication failed"}

    payout_amount = amount * 0.9  # Deducting 10% commission
    url = f"{settings.PAYU_PAYOUTS['BASE_URL']}/payouts/initiate"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    data = {
        "bene_account_number": seller_bank_details["account_number"],
        "bene_ifsc": seller_bank_details["ifsc"],
        "bene_name": seller_bank_details["name"],
        "amount": payout_amount,
        "currency": "INR",
        "purpose": "Vendor Payout"
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()
