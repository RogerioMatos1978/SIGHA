"""
Views do módulo Usuários (Módulos 1 e 2 da especificação: Cadastro + Login).

Cada view faz uma única coisa (funções/classes pequenas, sem duplicação),
seguindo o padrão Class-Based View do Django para reaproveitar as
implementações prontas de lista/criação/edição e reduzir código repetido.
"""
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import ListView, CreateView, UpdateView, View
from django.shortcuts import redirect, get_object_or_404
from django_ratelimit.decorators import ratelimit

from .forms import LoginForm, UsuarioCreationForm, UsuarioUpdateForm
from .models import Usuario
from .permissions import GerenciaUsuariosMixin


@method_decorator(never_cache, name='dispatch')
@method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True), name='post')
class LoginView(auth_views.LoginView):
    """
    Login customizado com:
    - template Bootstrap 5 próprio;
    - rate limit de 10 tentativas por minuto por IP (proteção contra força bruta);
    - never_cache para a tela de login nunca ficar em cache do navegador.
    """
    template_name = 'usuarios/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        usuario = form.get_user()
        if not usuario.esta_liberado_para_login:
            messages.error(self.request, 'Este usuário está inativo. Procure a Secretaria.')
            return self.form_invalid(form)
        return super().form_valid(form)


class LogoutView(auth_views.LogoutView):
    """Efetua logout e sempre redireciona para a tela de login."""
    next_page = 'usuarios:login'


class UsuarioListView(LoginRequiredMixin, GerenciaUsuariosMixin, ListView):
    """Lista todos os usuários cadastrados, com busca simples por nome/matrícula."""
    model = Usuario
    template_name = 'usuarios/usuario_list.html'
    context_object_name = 'usuarios'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        termo = self.request.GET.get('q', '').strip()
        if termo:
            from django.db.models import Q
            qs = qs.filter(
                Q(first_name__icontains=termo)
                | Q(last_name__icontains=termo)
                | Q(username__icontains=termo)
                | Q(matricula__icontains=termo)
            )
        return qs


class UsuarioCreateView(LoginRequiredMixin, GerenciaUsuariosMixin, SuccessMessageMixin, CreateView):
    """Cadastra um novo usuário do sistema."""
    model = Usuario
    form_class = UsuarioCreationForm
    template_name = 'usuarios/usuario_form.html'
    success_url = reverse_lazy('usuarios:lista')
    success_message = 'Usuário "%(username)s" cadastrado com sucesso.'


class UsuarioUpdateView(LoginRequiredMixin, GerenciaUsuariosMixin, SuccessMessageMixin, UpdateView):
    """Edita dados de um usuário existente."""
    model = Usuario
    form_class = UsuarioUpdateForm
    template_name = 'usuarios/usuario_form.html'
    success_url = reverse_lazy('usuarios:lista')
    success_message = 'Usuário "%(username)s" atualizado com sucesso.'


class UsuarioToggleAtivoView(LoginRequiredMixin, GerenciaUsuariosMixin, View):
    """
    Ativa/desativa um usuário. Nunca excluímos o registro do banco:
    isso preserva o histórico e o vínculo com outros módulos (grade,
    disponibilidade etc.) que vão referenciar este usuário no futuro.
    """
    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        if usuario == request.user:
            messages.error(request, 'Você não pode desativar o próprio usuário.')
        else:
            usuario.ativo = not usuario.ativo
            usuario.save(update_fields=['ativo'])
            estado = 'ativado' if usuario.ativo else 'desativado'
            messages.success(request, f'Usuário "{usuario.username}" {estado} com sucesso.')
        return redirect('usuarios:lista')
