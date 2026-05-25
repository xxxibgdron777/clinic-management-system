from django.urls import path
from . import views

app_name = 'vip'
urlpatterns = [
    path('', views.member_list, name='member_list'),
    path('members/', views.member_list, name='member_list'),
    path('members/create/', views.member_create, name='member_create'),
    path('members/import/', views.member_import, name='member_import'),
    path('members/<int:pk>/', views.member_detail, name='member_detail'),
    path('members/<int:pk>/edit/', views.member_edit, name='member_edit'),
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.course_create, name='course_create'),
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/', views.payment_create, name='payment_create'),
    path('cost-items/', views.cost_item_list, name='cost_item_list'),
    path('cost-items/create/', views.cost_item_create, name='cost_item_create'),
    path('injection/import/', views.injection_import, name='injection_import'),
    path('injection/template/', views.injection_template, name='injection_template'),
]
