"""
Modelo de Professor (Módulo 4).

É uma entidade própria — separada do Usuário de login — porque nem todo
professor necessariamente acessa o sistema, e porque os módulos futuros
(Disponibilidade, Grade) precisam referenciar "o professor" independente
de ele ter ou não uma conta. Quando o professor também precisa fazer
login (para ver a própria grade, por exemplo), ele é vinculado a um
Usuário com papel=PROFESSOR através do campo `usuario`.

Vínculo com Turmas (Módulo 19): resolve o pedido "professor do Médio não
dá aula para o Fundamental, e os Fundamentais não se misturam". É um
modelo híbrido, não uma regra fixa no código:

- `etapas_autorizadas` diz em quais ETAPAS (Fund. I / Fund. II / Médio)
  o professor pode lecionar — vale para todas as turmas daquela etapa,
  sem precisar marcar turma por turma (menos manutenção a cada ano).
- `turmas_liberadas`/`turmas_bloqueadas` são exceções pontuais por turma
  específica, por cima da regra de etapa — ex.: um coordenador do Médio
  que cobre uma aula pontual no Fundamental II (liberada), ou um professor
  de uma etapa que não deve dar aula numa turma específica dela mesma
  (bloqueada).
- Se `etapas_autorizadas` estiver vazio, o professor não tem restrição
  nenhuma (pode lecionar em qualquer turma) — é o padrão para não quebrar
  professores já cadastrados antes deste campo existir.

Esta regra é apenas um AVISO na hora de montar a Grade/Atribuição
(Módulo 10) — nunca bloqueia o salvamento. Quem decide se um coordenador
pode ou não escalar alguém fora do vínculo é a própria pessoa, o sistema
só chama atenção.
"""
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

from apps.turmas.models import EtapaEnsino, Turma


class Professor(models.Model):
    nome = models.CharField('Nome completo', max_length=150)
    matricula = models.CharField('Matrícula', max_length=20, unique=True)
    email = models.EmailField('E-mail', blank=True)
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    carga_horaria = models.PositiveSmallIntegerField(
        'Carga horária semanal (aulas)', default=0,
        help_text='Quantidade máxima de aulas semanais deste professor.',
    )
    ativo = models.BooleanField('Ativo', default=True)
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name='Usuário de login (opcional)',
        on_delete=models.SET_NULL, null=True, blank=True, related_name='professor',
        help_text='Preencha somente se este professor também tiver acesso ao sistema.',
    )
    etapas_autorizadas = ArrayField(
        models.CharField(max_length=20, choices=EtapaEnsino.choices),
        verbose_name='Etapas de ensino em que pode lecionar', blank=True, default=list,
        help_text='Deixe em branco para não restringir por etapa (pode lecionar em turmas de qualquer etapa).',
    )
    turmas_liberadas = models.ManyToManyField(
        Turma, verbose_name='Turmas liberadas além da etapa', blank=True,
        related_name='professores_liberados',
        help_text='Turmas específicas em que pode lecionar mesmo fora das etapas marcadas acima.',
    )
    turmas_bloqueadas = models.ManyToManyField(
        Turma, verbose_name='Turmas bloqueadas mesmo dentro da etapa', blank=True,
        related_name='professores_bloqueados',
        help_text='Turmas específicas em que NÃO pode lecionar, mesmo pertencendo a uma etapa autorizada.',
    )
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Professor'
        verbose_name_plural = 'Professores'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.matricula})'

    @property
    def etapas_autorizadas_display(self):
        """Rótulos legíveis de `etapas_autorizadas` (que guarda só os códigos), para exibir em templates."""
        rotulos = dict(EtapaEnsino.choices)
        return [rotulos.get(codigo, codigo) for codigo in self.etapas_autorizadas]

    def pode_lecionar_em(self, turma):
        """
        Verifica o vínculo com a turma (etapa + exceções). Uso pensado só
        para AVISAR (Módulo 19) — quem chama decide se bloqueia ou não.
        """
        if turma.pk in {t.pk for t in self.turmas_bloqueadas.all()}:
            return False
        if turma.pk in {t.pk for t in self.turmas_liberadas.all()}:
            return True
        if not self.etapas_autorizadas:
            return True
        return turma.etapa_ensino in self.etapas_autorizadas
