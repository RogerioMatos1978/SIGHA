from django.urls import path

from . import views

app_name = 'disponibilidade'

urlpatterns = [
    path('', views.ProfessorDisponibilidadeListView.as_view(), name='lista'),
    path('<int:professor_id>/', views.DisponibilidadeGradeView.as_view(), name='editar'),
]
