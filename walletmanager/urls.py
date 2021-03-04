from django.urls import path

from customer.views import register_view, MyTokenObtainPairView
from wallet.views import wallet_view, deposit_view, withdrawal_view, reference_view

urlpatterns = [
    path('api/v1/auth/register', register_view, name='register'),
    path('api/v1/init', MyTokenObtainPairView.as_view(), name='token'),
    path('api/v1/wallet', wallet_view, name='wallet'),
    path('api/v1/wallet/reference', reference_view, name='reference-id'),
    path('api/v1/wallet/deposit', deposit_view, name='deposit'),
    path('api/v1/wallet/withdrawal', withdrawal_view, name='withdrawal'),
]
