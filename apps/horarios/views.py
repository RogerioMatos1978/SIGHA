"""
Views do módulo Horários (Módulo 8). Mesmo padrão dos módulos anteriores,
exceto que a listagem não tem busca por texto — os horários são poucos
e a ordem (campo `ordem`) já organiza tudo visualmente.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, View

from .forms import HorarioForm
from .models import Horario
from .permissions import GerenciaAcademicoMixin


class HorarioListView(LoginRequiredMixin, GerenciaAcademicoMixin, ListView):
    model = Horario
    template_name = 'horarios/horario_list.html'
    context_object_name = 'horarios'


class HorarioCreateView(LoginRequiredMixin, GerenciaAcademicoMixin, SuccessMessageMixin, CreateView):
    model = Horario
    form_class = HorarioForm
    template_name = 'horarios/horario_form.html'
    success_url = reverse_lazy('horarios:lista')
    success_message = 'Horário cadastrado com sucesso.'


class HorarioUpdateView(LoginRequiredMixin, GerenciaAcademicoMixin, SuccessMessageMixin, UpdateView):
    model = Horario
    form_class = HorarioForm
    template_name = 'horarios/horario_form.html'
    success_url = reverse_lazy('horarios:lista')
    success_message = 'Horário atualizado com sucesso.'


class HorarioToggleAtivoView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    def post(self, request, pk):
        horario = get_object_or_404(Horario, pk=pk)
        horario.ativo = not horario.ativo
        horario.save(update_fields=['ativo'])
        estado = 'ativado' if horario.ativo else 'desativado'
        messages.success(request, f'Horário {estado} com sucesso.')
        return redirect('horarios:lista')
