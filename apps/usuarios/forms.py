"""
Formulários do módulo Usuários.

Mantemos toda a validação de dados aqui (nunca no template e nunca só
no JavaScript do navegador) — isso é o que garante proteção real contra
dados inconsistentes e contra tentativas de burlar o formulário.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm

from .models import Usuario


class LoginForm(AuthenticationForm):
    """Formulário de login com campos estilizados para Bootstrap 5."""
    username = forms.CharField(
        label='Usuário',
        widget=forms.TextInput(attrs={'class': 'form-control', 'autofocus': True, 'placeholder': 'usuário ou matrícula'}),
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'senha'}),
    )


class UsuarioCreationForm(UserCreationForm):
    """Cadastro de novo usuário (usado pelo Administrador/Coordenador)."""

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'matricula', 'telefone', 'papel',
        )
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'matricula': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'papel': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class UsuarioUpdateForm(UserChangeForm):
    """Edição de usuário existente (sem expor o campo de senha em texto)."""
    password = None  # a troca de senha tem fluxo/tela própria

    class Meta:
        model = Usuario
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'matricula', 'telefone', 'papel', 'ativo',
        )
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'matricula': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'papel': forms.Select(attrs={'class': 'form-select'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
