from django.urls import path
from . import views

urlpatterns = [
    path ('', views.welcome, name='welcome'),
    path('login/', views.welcome, name='login'),
    path ('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.user_logout, name='logout'),
    path('users/', views.users, name='users'),
    path('users/data/', views.users_data, name='users_data'),  
    path('users/add/', views.add_user, name='add_user'),  
    path('users/edit/<str:encrypted_id>/', views.edit_user, name='edit_user'),  
    path('users/delete/<str:encrypted_id>/', views.delete_user, name='delete_user'),  
    path('users/details/<str:encrypted_id>/', views.user_details, name='user_details'),

    path('companies/', views.companies, name='companies'),
    path('companies/add/', views.add_company, name='add_company'),
    path('companies/data/', views.companies_data, name='companies_data'),
    path('companies/edit/<str:encrypted_id>/', views.edit_company, name='edit_company'),
    path('companies/delete/<str:encrypted_id>/', views.delete_company, name='delete_company'),
    path('companies/details/<str:encrypted_id>/', views.company_details, name='company_details'),




    
]