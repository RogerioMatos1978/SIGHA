from django import forms

from apps.turmas.models import EtapaEnsino, Turma

from .models import Professor


class ProfessorForm(forms.ModelForm):
    # Declarado explicitamente (em vez de deixar o ModelForm inferir a
    # partir do ArrayField) para virar uma lista de checkboxes em vez de
    # um campo de texto separado por vírgula — MultipleChoiceField.clean()
    # devolve uma lista de strings, que já é o formato salvo no ArrayField.
    etapas_autorizadas = forms.MultipleChoiceField(
        label='Etapas de ensino em que pode lecionar', choices=EtapaEnsino.choices, required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Deixe tudo desmarcado para não restringir por etapa.',
    )

    class Meta:
        model = Professor
        fields = [
            'nome', 'matricula', 'email', 'telefone', 'carga_horaria', 'ativo',
            'etapas_autorizadas', 'turmas_liberadas', 'turmas_bloqueadas',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'matricula': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'carga_horaria': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 60}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'turmas_liberadas': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 6}),
            'turmas_bloqueadas': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        turmas_ativas = Turma.objects.filter(ativo=True).order_by('etapa_ensino', 'serie', 'nome')
        self.fields['turmas_liberadas'].queryset = turmas_ativas
        self.fields['turmas_bloqueadas'].queryset = turmas_ativas
