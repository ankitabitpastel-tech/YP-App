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
    
    path('company_followers_list/', views.company_followers_list, name='company_followers_list'),
    path('company_followers/data/', views.company_followers_data, name='company_followers_data'),
    path('company_followers/add/', views.add_company_follower, name='add_company_follower'),
    path('company_followers/unfollow/<str:encrypted_id>/', views.unfollow_company, name='unfollow_company'),
    path('company_followers/get_companies/', views.get_companies_not_followed, name='get_companies_not_followed'),

    path('job_posts/', views.job_posts_list, name='job_posts_list'),
    path('job_posts/data/', views.job_posts_data, name='job_posts_data'),
    path('job_posts/add/', views.add_job_post, name='add_job_post'),
    path('job_posts/details/<str:encrypted_id>/', views.job_post_details, name='job_post_details'),
    path('job_posts/edit/<str:encrypted_id>/', views.edit_job_post, name='edit_job_post'),
    path('job_posts/delete/<str:encrypted_id>/', views.delete_job_post, name='delete_job_post'),

    path('job-applications/', views.job_applications_list, name='job_applications_list'),
    path('job-applications/data/', views.job_applications_data, name='job_applications_data'),
    path('job-applications/add/', views.add_job_application, name='add_job_application'),
    path('job-applications/get-users/', views.get_users_not_applied, name='get_users_not_applied'),
    path('job_application/details/<str:encrypted_id>/', views.job_application_details, name='job_application_details'),
    path('job_application/edit/<str:encrypted_id>/', views.edit_job_application, name='edit_job_application'),
    path('job_application/delete/<str:encrypted_id>/', views.delete_job_application, name='delete_job_application'),

    path('articles/', views.articles_list, name='articles_list'),
    path('articles/data/', views.articles_data, name='articles_data'),
    path('articles/add/', views.add_article, name='add_article'),
    path('articles/edit/<str:encrypted_id>/', views.edit_article, name='edit_article'),
    path('articles/delete/<str:encrypted_id>/', views.delete_article, name='delete_article'),
    path('articles/details/<str:encrypted_id>/', views.article_details, name='article_details'),



    
]