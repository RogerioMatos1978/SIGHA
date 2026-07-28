from django import forms

from .models import Evento


class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['titulo', 'tipo', 'data_inicio', 'data_fim', 'descricao', 'afeta_aulas', 'ano_letivo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'afeta_aulas': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ano_letivo': forms.NumberInput(attrs={'class': 'form-control'}),
        }
