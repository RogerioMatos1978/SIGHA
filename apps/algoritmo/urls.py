from django.urls import path

from . import views

app_name = 'algoritmo'

urlpatterns = [
    path('', views.AlgoritmoTurmaListView.as_view(), name='lista'),
    path('turma/<int:turma_id>/gerar/', views.GerarGradeView.as_view(), name='gerar'),
]
