from django.urls import path

from . import views

app_name = 'exportacoes'

urlpatterns = [
    path(
        'grade/turma/<int:turma_id>/<str:formato>/',
        views.ExportarGradeTurmaView.as_view(), name='grade_turma',
    ),
    path(
        'grade/professor/<int:professor_id>/<str:formato>/',
        views.ExportarGradeProfessorView.as_view(), name='grade_professor',
    ),
]
