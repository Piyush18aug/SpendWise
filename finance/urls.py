from django.urls import path
from . import views, admin_views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('test/', views.test_view, name='test'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/add/', views.add_transaction, name='add_transaction'),
    path('transactions/edit/<int:pk>/', views.edit_transaction, name='edit_transaction'),
    path('transactions/delete/<int:pk>/', views.delete_transaction, name='delete_transaction'),
    path('goals/', views.goal_list, name='goal_list'),
    path('goals/add/', views.add_goal, name='add_goal'),
    path('goals/edit/<int:pk>/', views.edit_goal, name='edit_goal'),
    path('goals/delete/<int:pk>/', views.delete_goal, name='delete_goal'),
    path('awareness/', views.spending_awareness, name='spending_awareness'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
    path('profile/', views.profile_view, name='profile'),
    path('settings/', views.settings_view, name='settings'),
    path('email-summary/', views.send_summary_email, name='send_summary_email'),
    
    # Custom Admin URLs
    path('custom-admin/login/', admin_views.admin_login, name='admin_login'),
    path('custom-admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('custom-admin/logout/', admin_views.admin_logout, name='admin_logout'),
    path('custom-admin/users/', admin_views.admin_users, name='admin_users'),
    path('custom-admin/users/delete/<int:user_id>/', admin_views.delete_user, name='delete_user'),
    path('custom-admin/transactions/', admin_views.admin_transactions, name='admin_transactions'),
    path('custom-admin/export/csv/', admin_views.admin_export_csv, name='admin_export_csv'),
    path('custom-admin/export/pdf/', admin_views.admin_export_pdf, name='admin_export_pdf'),
]
