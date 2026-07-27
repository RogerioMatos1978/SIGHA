from django import forms

from .models import Ambiente


class AmbienteForm(forms.ModelForm):
    class Meta:
        model = Ambiente
        fields = ['nome', 'tipo', 'capacidade', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'capacidade': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
