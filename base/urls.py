from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('frontend.urls', namespace='frontend')),
    path('account/', include('account.urls', namespace='account')),
    path('user/', include('customer.urls', namespace='customer')),
    path('staff/', include('staff.urls', namespace='staff')),
    path('strategy/', include('coin.urls', namespace='coin')),
    path('transaction/', include('transaction.urls', namespace='transaction')),
    path('kyc/', include('kyc.urls', namespace='kyc')),
]
