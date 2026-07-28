from django.urls import path

from . import views

app_name = 'horarios'

urlpatterns = [
    path('', views.HorarioListView.as_view(), name='lista'),
    path('novo/', views.HorarioCreateView.as_view(), name='criar'),
    path('<int:pk>/editar/', views.HorarioUpdateView.as_view(), name='editar'),
    path('<int:pk>/alternar-ativo/', views.HorarioToggleAtivoView.as_view(), name='alternar_ativo'),
]
