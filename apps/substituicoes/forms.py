from django import forms

from apps.professores.models import Professor

from .models import Substituicao


class SubstituicaoForm(forms.ModelForm):
    class Meta:
        model = Substituicao
        fields = ['data', 'professor_substituto', 'aula_cancelada', 'motivo']
        widgets = {
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'professor_substituto': forms.Select(attrs={'class': 'form-select'}),
            'aula_cancelada': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'motivo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: atestado médico'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['professor_substituto'].queryset = Professor.objects.filter(ativo=True)
        self.fields['professor_substituto'].required = False
