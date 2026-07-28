from django.urls import path

from . import views

app_name = 'grade'

urlpatterns = [
    path('', views.GradeTurmaListView.as_view(), name='lista'),
    path('turma/<int:turma_id>/', views.GradeVisualView.as_view(), name='visual'),
    path(
        'turma/<int:turma_id>/dia/<str:dia_semana>/horario/<int:horario_id>/nova/',
        views.GradeAulaCreateView.as_view(), name='criar',
    ),
    path('aula/<int:pk>/editar/', views.GradeAulaUpdateView.as_view(), name='editar'),
    path('aula/<int:pk>/remover/', views.GradeAulaDeleteView.as_view(), name='remover'),
]
