"""
URL configuration for clinic_management project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.dashboard, name='dashboard'),
    path('accounts/', include('apps.accounts_app.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('lab-bills/', include('apps.lab_bills.urls')),
    path('vip/', include('apps.vip.urls')),
    path('revenue-share/', include('apps.revenue_share.urls')),
    path('billing/', include('apps.billing.urls')),
    path('reports/', include('apps.reports.urls')),
    path('frontdesk/', include('apps.frontdesk.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
