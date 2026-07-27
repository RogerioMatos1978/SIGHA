from django import forms

from .models import Disciplina


class DisciplinaForm(forms.ModelForm):
    class Meta:
        model = Disciplina
        fields = ['nome', 'sigla', 'quantidade_aulas_semana', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'sigla': forms.TextInput(attrs={'class': 'form-control text-uppercase'}),
            'quantidade_aulas_semana': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 20}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_sigla(self):
        return self.cleaned_data['sigla'].strip().upper()
