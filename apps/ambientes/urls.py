from django.urls import path

from . import views

app_name = 'ambientes'

urlpatterns = [
    path('', views.AmbienteListView.as_view(), name='lista'),
    path('novo/', views.AmbienteCreateView.as_view(), name='criar'),
    path('<int:pk>/editar/', views.AmbienteUpdateView.as_view(), name='editar'),
    path('<int:pk>/alternar-ativo/', views.AmbienteToggleAtivoView.as_view(), name='alternar_ativo'),
]
