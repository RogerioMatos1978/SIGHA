"""
Camada de serviço do módulo Exportações (Módulo 14).

Reaproveita os grids já montados pelos Módulos 10 (Grade) e 13
(Relatórios) — {horario: {codigo_dia: aula_ou_None}} — e delega para o
gerador do formato pedido. Mantém num único lugar o mapeamento entre
"formato pedido na URL" e "content-type/extensão da resposta HTTP",
para não espalhar esse conhecimento pelas views.
"""
from django.core.exceptions import ValidationError

from .excel import gerar_excel_grade
from .imagem import gerar_imagem_grade
from .pdf import gerar_pdf_grade
from .word import gerar_docx_grade

FORMATOS = {
    'excel': {
        'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'extensao': 'xlsx',
    },
    'pdf': {'content_type': 'application/pdf', 'extensao': 'pdf'},
    'word': {
        'content_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'extensao': 'docx',
    },
    'png': {'content_type': 'image/png', 'extensao': 'png'},
    'jpeg': {'content_type': 'image/jpeg', 'extensao': 'jpg'},
}


def gerar_arquivo(formato, titulo, dias, grid, montar_linhas):
    """
    Retorna (buffer, content_type, extensao) para o formato pedido.
    Levanta ValidationError se o formato não for suportado.
    """
    if formato not in FORMATOS:
        raise ValidationError(f'Formato de exportação "{formato}" não suportado.')

    info = FORMATOS[formato]
    if formato == 'excel':
        buffer = gerar_excel_grade(titulo, dias, grid, montar_linhas)
    elif formato == 'pdf':
        buffer = gerar_pdf_grade(titulo, dias, grid, montar_linhas)
    elif formato == 'word':
        buffer = gerar_docx_grade(titulo, dias, grid, montar_linhas)
    elif formato in ('png', 'jpeg'):
        buffer = gerar_imagem_grade(titulo, dias, grid, montar_linhas, formato=formato.upper())
    return buffer, info['content_type'], info['extensao']


def linhas_celula_turma(aula):
    """Texto de cada célula na exportação da Grade por turma."""
    if not aula:
        return []
    return [aula.disciplina.sigla, aula.professor.nome, aula.ambiente.nome]


def linhas_celula_professor(aula):
    """Texto de cada célula na exportação da Grade por professor."""
    if not aula:
        return []
    return [aula.turma.nome, aula.disciplina.sigla, aula.ambiente.nome]
