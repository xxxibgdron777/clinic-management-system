from django.urls import path
from . import views

app_name = 'revenue_share'
urlpatterns = [
    path('', views.partner_list, name='partner_list'),
    path('config/<int:pk>/', views.config_edit, name='config_edit'),
    path('calculations/', views.calculation_list, name='calculation_list'),
    path('calculate/<int:partner_pk>/<int:year>/<int:month>/', views.calculation_run, name='calculation_run'),
    path('statements/', views.statement_list, name='statement_list'),
    path('statements/generate/<int:calc_pk>/', views.statement_generate, name='statement_generate'),
]
