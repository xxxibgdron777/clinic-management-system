from django.urls import path
from . import views

app_name = 'billing'
urlpatterns = [
    path('', views.import_list, name='import_list'),
    path('imports/', views.import_list, name='import_list'),
    path('imports/upload/', views.import_upload, name='import_upload'),
    path('templates/', views.template_list, name='template_list'),
    path('bills/', views.bill_list, name='bill_list'),
    path('bills/generate/<int:template_pk>/<int:year>/<int:month>/',
         views.bill_generate, name='bill_generate'),
]
