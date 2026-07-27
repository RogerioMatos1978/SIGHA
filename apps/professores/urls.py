from django.urls import path

from . import views

app_name = 'professores'

urlpatterns = [
    path('', views.ProfessorListView.as_view(), name='lista'),
    path('novo/', views.ProfessorCreateView.as_view(), name='criar'),
    path('<int:pk>/editar/', views.ProfessorUpdateView.as_view(), name='editar'),
    path('<int:pk>/alternar-ativo/', views.ProfessorToggleAtivoView.as_view(), name='alternar_ativo'),
]
