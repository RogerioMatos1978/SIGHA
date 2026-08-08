from rest_framework.routers import DefaultRouter

from . import views

app_name = 'api'

router = DefaultRouter()
router.register('usuarios', views.UsuarioViewSet, basename='usuario')
router.register('professores', views.ProfessorViewSet, basename='professor')
router.register('disciplinas', views.DisciplinaViewSet, basename='disciplina')
router.register('turmas', views.TurmaViewSet, basename='turma')
router.register('ambientes', views.AmbienteViewSet, basename='ambiente')
router.register('horarios', views.HorarioViewSet, basename='horario')
router.register('disponibilidade', views.DisponibilidadeProfessorViewSet, basename='disponibilidade')
router.register('atribuicoes', views.AtribuicaoViewSet, basename='atribuicao')
router.register('grade', views.GradeAulaViewSet, basename='gradeaula')
router.register('substituicoes', views.SubstituicaoViewSet, basename='substituicao')
router.register('calendario/eventos', views.EventoViewSet, basename='evento')

urlpatterns = router.urls
