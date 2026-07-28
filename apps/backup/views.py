"""
Views do módulo Backup (Módulo 17): gerar, listar, baixar, restaurar e
remover backups do banco de dados. Tudo restrito a Administrador — é a
tela mais sensível do sistema (restaurar substitui os dados atuais).
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView

from apps.auditoria.middleware import obter_ip_atual

from . import services
from .models import RegistroBackup
from .permissions import SomenteAdministradorMixin


class BackupListView(LoginRequiredMixin, SomenteAdministradorMixin, ListView):
    model = RegistroBackup
    template_name = 'backup/lista.html'
    context_object_name = 'backups'

    def get_queryset(self):
        return services.listar_backups()


class GerarBackupView(LoginRequiredMixin, SomenteAdministradorMixin, View):
    def post(self, request):
        try:
            registro = services.gerar_backup(usuario=request.user)
            messages.success(request, f'Backup "{registro.nome_arquivo}" gerado com sucesso.')
        except services.ErroDeBackup as erro:
            messages.error(request, f'Não foi possível gerar o backup: {erro}')
        return redirect('backup:lista')


class BaixarBackupView(LoginRequiredMixin, SomenteAdministradorMixin, View):
    def get(self, request, pk):
        registro = get_object_or_404(RegistroBackup, pk=pk)
        if not registro.existe_no_disco():
            raise Http404('Arquivo de backup não encontrado no disco.')
        return FileResponse(
            open(registro.caminho_arquivo(), 'rb'),
            as_attachment=True,
            filename=registro.nome_arquivo,
        )


class RestaurarBackupView(LoginRequiredMixin, SomenteAdministradorMixin, View):
    def post(self, request, pk):
        registro = get_object_or_404(RegistroBackup, pk=pk)
        confirmacao = request.POST.get('confirmacao', '')
        if confirmacao != registro.nome_arquivo:
            messages.error(request, 'Confirmação incorreta. Digite o nome exato do arquivo para restaurar.')
            return redirect('backup:lista')
        try:
            services.restaurar_backup(registro, usuario=request.user, ip=obter_ip_atual())
            messages.success(request, f'Banco de dados restaurado a partir de "{registro.nome_arquivo}".')
        except services.ErroDeBackup as erro:
            messages.error(request, f'Falha ao restaurar: {erro}')
        return redirect('backup:lista')


class ExcluirBackupView(LoginRequiredMixin, SomenteAdministradorMixin, View):
    def post(self, request, pk):
        registro = get_object_or_404(RegistroBackup, pk=pk)
        nome = registro.nome_arquivo
        services.excluir_backup(registro)
        messages.success(request, f'Backup "{nome}" removido.')
        return redirect('backup:lista')
