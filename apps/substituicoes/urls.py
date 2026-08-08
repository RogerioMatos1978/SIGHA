from django.urls import path

from . import views

app_name = 'substituicoes'

urlpatterns = [
    path('', views.SubstituicaoListView.as_view(), name='lista'),
    path('aula/<int:aula_id>/nova/', views.SubstituicaoCreateView.as_view(), name='criar'),
    path('<int:pk>/remover/', views.SubstituicaoDeleteView.as_view(), name='remover'),
]
