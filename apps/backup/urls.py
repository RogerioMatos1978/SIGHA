from django.urls import path

from . import views

app_name = 'backup'
urlpatterns = [
    path('', views.BackupListView.as_view(), name='lista'),
    path('gerar/', views.GerarBackupView.as_view(), name='gerar'),
    path('<int:pk>/baixar/', views.BaixarBackupView.as_view(), name='baixar'),
    path('<int:pk>/restaurar/', views.RestaurarBackupView.as_view(), name='restaurar'),
    path('<int:pk>/excluir/', views.ExcluirBackupView.as_view(), name='excluir'),
]
