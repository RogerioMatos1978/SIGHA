from django import forms

from .models import Turma


class TurmaForm(forms.ModelForm):
    class Meta:
        model = Turma
        fields = ['nome', 'serie', 'etapa_ensino', 'curso_tecnico', 'codigo_evento', 'turno', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'serie': forms.TextInput(attrs={'class': 'form-control'}),
            'etapa_ensino': forms.Select(attrs={'class': 'form-select'}),
            'curso_tecnico': forms.Select(attrs={'class': 'form-select'}),
            'codigo_evento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: 4321-2026'}),
            'turno': forms.Select(attrs={'class': 'form-select'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
