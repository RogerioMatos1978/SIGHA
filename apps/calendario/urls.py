from django.urls import path

from . import views

app_name = 'calendario'

urlpatterns = [
    path('', views.CalendarioMesView.as_view(), name='mes'),
    path('dia/<int:ano>/<int:mes>/<int:dia>/', views.DiaDetalheView.as_view(), name='dia'),
    path('evento/novo/', views.EventoCreateView.as_view(), name='evento_criar'),
    path('evento/<int:pk>/editar/', views.EventoUpdateView.as_view(), name='evento_editar'),
    path('evento/<int:pk>/remover/', views.EventoDeleteView.as_view(), name='evento_remover'),
]
