from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('frontend.urls', namespace='frontend')),
    path('user/', include('customer.urls', namespace='customer')),
    path('staff/', include('staff.urls', namespace='staff')),
]
