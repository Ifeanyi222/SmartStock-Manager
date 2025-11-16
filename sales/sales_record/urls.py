from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add-stock/', views.add_stock, name='add_stock'),
    path('record-sale/', views.record_sale, name='record_sale'),
    path('edit-stock/<int:pk>/', views.edit_stock, name='edit_stock'),
    path('delete-stock/<int:pk>/', views.delete_stock, name='delete_stock'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('search-dashboard/', views.search_dashboard, name='search_dashboard'),
    path('sale/<int:sale_id>/', views.view_sale, name='view_sale'),
   

]
