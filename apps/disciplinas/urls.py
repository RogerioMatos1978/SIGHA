from django.urls import path

from . import views

app_name = 'disciplinas'

urlpatterns = [
    path('', views.DisciplinaListView.as_view(), name='lista'),
    path('novo/', views.DisciplinaCreateView.as_view(), name='criar'),
    path('<int:pk>/editar/', views.DisciplinaUpdateView.as_view(), name='editar'),
    path('<int:pk>/alternar-ativo/', views.DisciplinaToggleAtivoView.as_view(), name='alternar_ativo'),
]
