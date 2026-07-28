"""
Exportação da grade para PDF (Módulo 14), usando reportlab.
"""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

AZUL_CABECALHO = colors.HexColor('#0D6EFD')


def gerar_pdf_grade(titulo, dias, grid, montar_linhas):
    buffer = BytesIO()
    documento = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        leftMargin=1 * cm, rightMargin=1 * cm, topMargin=1 * cm, bottomMargin=1 * cm,
    )
    estilos = getSampleStyleSheet()

    linhas_tabela = [['Horário'] + [rotulo for _codigo, rotulo in dias]]
    for horario, por_dia in grid.items():
        linha = [f'{horario.inicio.strftime("%H:%M")}–{horario.fim.strftime("%H:%M")}']
        for codigo, _rotulo in dias:
            aula = por_dia.get(codigo)
            linha.append('\n'.join(montar_linhas(aula)) if aula else '')
        linhas_tabela.append(linha)

    tabela = Table(linhas_tabela, repeatRows=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_CABECALHO),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ]))

    documento.build([Paragraph(titulo, estilos['Title']), Spacer(1, 12), tabela])
    buffer.seek(0)
    return buffer
