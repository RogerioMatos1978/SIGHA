"""
Formulário de cadastro de aula na Grade (Módulo 10).

Turma, dia da semana, horário, ano letivo e semestre não aparecem aqui:
eles vêm da célula da grade que o usuário clicou (definidos na view, a
partir da URL), então o formulário só pergunta o que falta decidir:
disciplina, professor e ambiente. As demais regras de conflito são
validadas pelo `GradeAula.clean()` chamado explicitamente na view.
"""
from django import forms

from .models import GradeAula


class GradeAulaForm(forms.ModelForm):
    class Meta:
        model = GradeAula
        fields = ['disciplina', 'professor', 'ambiente']
        widgets = {
            'disciplina': forms.Select(attrs={'class': 'form-select'}),
            'professor': forms.Select(attrs={'class': 'form-select'}),
            'ambiente': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['disciplina'].queryset = self.fields['disciplina'].queryset.filter(ativo=True)
        self.fields['professor'].queryset = self.fields['professor'].queryset.filter(ativo=True)
        self.fields['ambiente'].queryset = self.fields['ambiente'].queryset.filter(ativo=True)
