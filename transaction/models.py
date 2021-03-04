import uuid
from django.db import models
from django.utils import timezone

from wallet.models import Wallet


class Transaction(models.Model):
    TX_STATUS = [('INIT', 'INITIATED'), ('ABT', 'ABORTED'), ('IP', 'IN-PROGRESS'), ('CMP', 'COMPLETED'), ('TO', 'TIMED-OUT')]
    TX_TYPE = [('DX', 'DEPOSIT'), ('WX', 'WITHDRAWAL'), ('US', 'UNSPECIFIED')]
    id = models.BigAutoField(primary_key=True)
    reference_id = models.UUIDField(unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(default=timezone.now)
    wallet = models.ForeignKey(Wallet, blank=False, null=False, on_delete=models.CASCADE, db_column='wid')
    amount = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=TX_STATUS, default='INIT')
    type = models.CharField(max_length=20, choices=TX_TYPE, default='US')

    class Meta:
        db_table = 'transaction'

    def get_dict(self):
        dict_obj = {'reference_id': self.reference_id if self.reference_id else None,
                    'created_at': str(self.created_at) if self.created_at else None,
                    'wallet_id': self.wallet.wxid if self.wallet.wxid else None,
                    'status': self.status if self.status else None
                    }
        return dict_obj
