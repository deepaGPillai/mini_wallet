import uuid

from django.db import models
from django.utils import timezone

from customer.models import Customer


class Wallet(models.Model):
    id = models.BigAutoField(primary_key=True)
    wxid = models.UUIDField(unique=True, default=uuid.uuid4)
    customer = models.OneToOneField(Customer, blank=False, null=False, on_delete=models.CASCADE, db_column='cid')
    status = models.BooleanField(default=False)
    enabled_at = models.DateTimeField(default=timezone.now)
    balance = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'wallet'

    def get_dict(self):
        dict_obj = {'id': self.wxid if self.wxid else None,
                    'owned_by': str(self.customer.cxid) if self.customer.cxid else None,
                    'status': 'enabled' if self.status else 'disabled',
                    'enabled_at': str(self.enabled_at) if self.enabled_at else None,
                    'balance': str(self.balance)
                    }
        return dict_obj
