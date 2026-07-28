"""
URLs raiz do projeto SIGHA.

Cada módulo (usuários, professores, turmas...) tem seu próprio urls.py,
incluído aqui com um prefixo. Isso mantém o roteamento organizado e
evita um único arquivo gigante conforme o sistema cresce.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios/', include('apps.usuarios.urls', namespace='usuarios')),
    path('professores/', include('apps.professores.urls', namespace='professores')),
    path('disciplinas/', include('apps.disciplinas.urls', namespace='disciplinas')),
    path('turmas/', include('apps.turmas.urls', namespace='turmas')),
    path('ambientes/', include('apps.ambientes.urls', namespace='ambientes')),
    path('horarios/', include('apps.horarios.urls', namespace='horarios')),
    path('disponibilidade/', include('apps.disponibilidade.urls', namespace='disponibilidade')),
    path('grade/', include('apps.grade.urls', namespace='grade')),
    path('algoritmo/', include('apps.algoritmo.urls', namespace='algoritmo')),
    path('calendario/', include('apps.calendario.urls', namespace='calendario')),
    path('relatorios/', include('apps.relatorios.urls', namespace='relatorios')),
    path('exportacoes/', include('apps.exportacoes.urls', namespace='exportacoes')),
    path('', include('apps.dashboard.urls')),
]
