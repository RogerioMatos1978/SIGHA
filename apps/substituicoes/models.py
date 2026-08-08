"""
Modelo de Substituição pontual de professor (Módulo 19).

Cobre o caso real de gestão escolar (o mesmo fluxo usado por sistemas como
o Sistema SIGA): um professor titular falta num dia específico, e alguém
precisa assumir aquela aula da grade (ou a aula é simplesmente cancelada,
sem atendimento pedagógico). Isso é diferente de trocar o professor da
Atribuição (Módulo 10) — aquilo é uma troca PERMANENTE, dali para frente;
uma Substituição vale só para UMA data, sem mexer na atribuição original.

Cada linha diz: "na data X, a aula Y (que normalmente é do professor
titular) foi dada pelo professor Z" (ou "foi cancelada, sem substituto").
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.disponibilidade.models import DiaSemana
from apps.grade.models import GradeAula
from apps.professores.models import Professor

# Índice de `date.weekday()` (Python: segunda=0 ... domingo=6) para o
# código de DiaSemana correspondente — usado para validar que a data
# escolhida realmente cai no dia da semana da aula original.
DIA_SEMANA_POR_WEEKDAY = {
    0: DiaSemana.SEGUNDA,
    1: DiaSemana.TERCA,
    2: DiaSemana.QUARTA,
    3: DiaSemana.QUINTA,
    4: DiaSemana.SEXTA,
}


class Substituicao(models.Model):
    aula = models.ForeignKey(
        GradeAula, verbose_name='Aula da grade', on_delete=models.CASCADE, related_name='substituicoes',
    )
    data = models.DateField('Data da substituição')
    professor_substituto = models.ForeignKey(
        Professor, verbose_name='Professor substituto', on_delete=models.PROTECT,
        null=True, blank=True, related_name='substituicoes_como_substituto',
        help_text='Deixe em branco se a aula foi cancelada (sem atendimento pedagógico nesse dia).',
    )
    aula_cancelada = models.BooleanField(
        'Aula cancelada (sem substituto)', default=False,
        help_text='Marque quando não houve professor eventual disponível para cobrir a falta.',
    )
    motivo = models.CharField('Motivo', max_length=255, blank=True, help_text='Ex.: atestado médico, licença.')
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Registrado por', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='substituicoes_registradas',
    )
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Substituição de professor'
        verbose_name_plural = 'Substituições de professores'
        ordering = ['-data']
        constraints = [
            models.UniqueConstraint(fields=['aula', 'data'], name='substituicao_unica_por_aula_e_data'),
        ]

    def __str__(self):
        quem = self.professor_substituto.nome if self.professor_substituto_id else 'aula cancelada'
        return f'{self.aula.turma.nome} — {self.data:%d/%m/%Y} — {quem}'

    def clean(self):
        erros = {}

        if not self.aula_cancelada and not self.professor_substituto_id:
            erros['professor_substituto'] = 'Informe o professor substituto ou marque a aula como cancelada.'
        if self.aula_cancelada and self.professor_substituto_id:
            erros['aula_cancelada'] = 'Não é possível ter um substituto e marcar a aula como cancelada ao mesmo tempo.'

        if self.aula_id and self.data:
            dia_da_data = DIA_SEMANA_POR_WEEKDAY.get(self.data.weekday())
            if dia_da_data is None:
                erros['data'] = 'A data cai num sábado ou domingo — a grade só tem aulas de segunda a sexta.'
            elif dia_da_data != self.aula.dia_semana:
                erros['data'] = (
                    f'A aula "{self.aula}" acontece {self.aula.get_dia_semana_display()}; '
                    f'{self.data:%d/%m/%Y} não cai nesse dia da semana.'
                )

        if self.professor_substituto_id and self.aula_id:
            if self.professor_substituto_id == self.aula.professor_id:
                erros['professor_substituto'] = 'O substituto não pode ser o mesmo professor titular da aula.'

            conflito_grade_regular = GradeAula.objects.filter(
                professor_id=self.professor_substituto_id, dia_semana=self.aula.dia_semana,
                horario_id=self.aula.horario_id, ano_letivo=self.aula.ano_letivo, semestre=self.aula.semestre,
            ).exclude(pk=self.aula_id).exists()
            if conflito_grade_regular:
                erros['professor_substituto'] = (
                    f'{self.professor_substituto.nome} já dá aula regularmente nesse mesmo horário '
                    'em outra turma — não pode substituir também aqui nessa data.'
                )

            conflito_outra_substituicao = Substituicao.objects.filter(
                professor_substituto_id=self.professor_substituto_id, data=self.data,
                aula__dia_semana=self.aula.dia_semana, aula__horario_id=self.aula.horario_id,
            ).exclude(pk=self.pk).exists()
            if conflito_outra_substituicao:
                erros['professor_substituto'] = (
                    f'{self.professor_substituto.nome} já está substituindo outra aula nesse mesmo '
                    f'horário em {self.data:%d/%m/%Y}.'
                )

        if erros:
            raise ValidationError(erros)
