from django.urls import path

from . import views

app_name = 'relatorios'

urlpatterns = [
    path('', views.RelatoriosHomeView.as_view(), name='home'),
    path('grade-professor/', views.RelatorioGradeProfessorView.as_view(), name='grade_professor'),
    path('carga-horaria/', views.RelatorioCargaHorariaView.as_view(), name='carga_horaria'),
    path('ocupacao-ambientes/', views.RelatorioOcupacaoAmbientesView.as_view(), name='ocupacao_ambientes'),
    path('pendencias/', views.RelatorioPendenciasView.as_view(), name='pendencias'),
]
