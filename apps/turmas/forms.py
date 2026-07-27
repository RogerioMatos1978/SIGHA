from django import forms

from .models import Turma


class TurmaForm(forms.ModelForm):
    class Meta:
        model = Turma
        fields = ['nome', 'serie', 'turno', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'serie': forms.TextInput(attrs={'class': 'form-control'}),
            'turno': forms.Select(attrs={'class': 'form-select'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
