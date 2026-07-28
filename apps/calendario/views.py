"""
Views do módulo Calendário (Módulo 12): visualização mensal, detalhe do
dia e CRUD de eventos.
"""
from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DeleteView

from . import services
from .forms import EventoForm
from .models import Evento
from .permissions import GerenciaAcademicoMixin

NOMES_MES = [
    '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
]


class CalendarioMesView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    """Visualização mensal do calendário, com navegação entre meses."""
    template_name = 'calendario/mes.html'

    def get(self, request):
        hoje = timezone.now().date()
        try:
            ano = int(request.GET.get('ano') or hoje.year)
            mes = int(request.GET.get('mes') or hoje.month)
        except (TypeError, ValueError):
            ano, mes = hoje.year, hoje.month

        if mes < 1:
            mes, ano = 12, ano - 1
        elif mes > 12:
            mes, ano = 1, ano + 1

        semanas = services.montar_mes(ano, mes)
        mes_anterior, ano_mes_anterior = (12, ano - 1) if mes == 1 else (mes - 1, ano)
        mes_seguinte, ano_mes_seguinte = (1, ano + 1) if mes == 12 else (mes + 1, ano)

        return render(request, self.template_name, {
            'semanas': semanas, 'ano': ano, 'mes': mes, 'nome_mes': NOMES_MES[mes], 'hoje': hoje,
            'ano_mes_anterior': ano_mes_anterior, 'mes_anterior': mes_anterior,
            'ano_mes_seguinte': ano_mes_seguinte, 'mes_seguinte': mes_seguinte,
        })


class DiaDetalheView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    """Detalhe de um dia: eventos cadastrados e aulas previstas (se for dia letivo)."""
    template_name = 'calendario/dia.html'

    def get(self, request, ano, mes, dia):
        try:
            data = date(ano, mes, dia)
        except ValueError:
            raise Http404('Data inválida.')
        contexto = services.resumo_do_dia(data)
        return render(request, self.template_name, contexto)


class EventoCreateView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    template_name = 'calendario/evento_form.html'

    def get(self, request):
        data_inicial = request.GET.get('data')
        form = EventoForm(initial={'data_inicio': data_inicial} if data_inicial else None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = EventoForm(request.POST)
        if form.is_valid():
            evento = form.save(commit=False)
            evento.criado_por = request.user
            try:
                evento.full_clean()
            except ValidationError as erro:
                form.add_error(None, erro)
                return render(request, self.template_name, {'form': form})
            evento.save()
            messages.success(request, 'Evento cadastrado com sucesso.')
            return redirect(
                f"{reverse('calendario:mes')}?ano={evento.data_inicio.year}&mes={evento.data_inicio.month}"
            )
        return render(request, self.template_name, {'form': form})


class EventoUpdateView(LoginRequiredMixin, GerenciaAcademicoMixin, View):
    template_name = 'calendario/evento_form.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.evento = get_object_or_404(Evento, pk=kwargs['pk'])

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': EventoForm(instance=self.evento), 'editando': True})

    def post(self, request, *args, **kwargs):
        form = EventoForm(request.POST, instance=self.evento)
        if form.is_valid():
            evento = form.save(commit=False)
            try:
                evento.full_clean()
            except ValidationError as erro:
                form.add_error(None, erro)
                return render(request, self.template_name, {'form': form, 'editando': True})
            evento.save()
            messages.success(request, 'Evento atualizado com sucesso.')
            return redirect(
                f"{reverse('calendario:mes')}?ano={evento.data_inicio.year}&mes={evento.data_inicio.month}"
            )
        return render(request, self.template_name, {'form': form, 'editando': True})


class EventoDeleteView(LoginRequiredMixin, GerenciaAcademicoMixin, DeleteView):
    model = Evento
    template_name = 'calendario/evento_confirmar_remocao.html'
    context_object_name = 'evento'

    def get_success_url(self):
        messages.success(self.request, 'Evento removido.')
        return f"{reverse('calendario:mes')}?ano={self.object.data_inicio.year}&mes={self.object.data_inicio.month}"
