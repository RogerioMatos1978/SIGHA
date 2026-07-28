from django import forms

from .models import Horario


class HorarioForm(forms.ModelForm):
    class Meta:
        model = Horario
        fields = ['ordem', 'inicio', 'fim', 'intervalo', 'ativo']
        widgets = {
            'ordem': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'fim': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'intervalo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
