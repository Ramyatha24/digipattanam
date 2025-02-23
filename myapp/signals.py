from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import OrderDetail, BankDetails
from .utils import make_payout

@receiver(post_save, sender=OrderDetail)
def auto_payout(sender, instance, **kwargs):
    """
    Automatically trigger payout when an order is marked as paid.
    """
    if instance.has_paid:  # Ensure order is marked as paid (Boolean check)
        seller = instance.product.user  # Get the seller of the product

        # Fetch seller's bank details
        try:
            seller_bank = BankDetails.objects.get(user=seller)
            seller_bank_details = {
                "account_number": seller_bank.account_number,
                "ifsc": seller_bank.ifsc_code,
                "name": seller_bank.account_holder_name
            }
            make_payout(seller_bank_details, instance.amount)  # Initiate payout
        except BankDetails.DoesNotExist:
            print(f"Bank details not found for seller: {seller.username}")
