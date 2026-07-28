"""
Exportação da grade para imagem PNG/JPEG (Módulo 14), usando Pillow.

Desenha a mesma tabela (dias x horários) manualmente, célula por célula —
não existe um "Table" pronto no Pillow como no reportlab/python-docx.
"""
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

LARGURA_COLUNA_HORARIO = 130
LARGURA_COLUNA_DIA = 200
ALTURA_TITULO = 50
ALTURA_CABECALHO = 40
ALTURA_LINHA = 80
AZUL_CABECALHO = (13, 110, 253)
CAMINHOS_FONTE = {
    'negrito': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    'normal': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
}


def _carregar_fonte(estilo, tamanho):
    try:
        return ImageFont.truetype(CAMINHOS_FONTE[estilo], tamanho)
    except OSError:
        return ImageFont.load_default()


def gerar_imagem_grade(titulo, dias, grid, montar_linhas, formato='PNG'):
    horarios = list(grid.keys())
    largura = LARGURA_COLUNA_HORARIO + LARGURA_COLUNA_DIA * len(dias)
    altura = ALTURA_TITULO + ALTURA_CABECALHO + ALTURA_LINHA * max(len(horarios), 1)

    imagem = Image.new('RGB', (largura, altura), color='white')
    desenho = ImageDraw.Draw(imagem)

    fonte_titulo = _carregar_fonte('negrito', 20)
    fonte_cabecalho = _carregar_fonte('negrito', 14)
    fonte_celula = _carregar_fonte('normal', 12)

    desenho.text((10, 12), titulo, fill='black', font=fonte_titulo)

    y = ALTURA_TITULO
    desenho.rectangle([0, y, largura, y + ALTURA_CABECALHO], fill=AZUL_CABECALHO)
    desenho.text((10, y + 10), 'Horário', fill='white', font=fonte_cabecalho)
    x = LARGURA_COLUNA_HORARIO
    for _codigo, rotulo in dias:
        desenho.text((x + 10, y + 10), rotulo, fill='white', font=fonte_cabecalho)
        x += LARGURA_COLUNA_DIA

    y += ALTURA_CABECALHO
    for horario in horarios:
        desenho.rectangle([0, y, largura, y + ALTURA_LINHA], outline='black')
        rotulo_horario = f'{horario.inicio.strftime("%H:%M")}\n{horario.fim.strftime("%H:%M")}'
        desenho.multiline_text((10, y + 10), rotulo_horario, fill='black', font=fonte_celula)
        x = LARGURA_COLUNA_HORARIO
        por_dia = grid[horario]
        for codigo, _rotulo in dias:
            desenho.rectangle([x, y, x + LARGURA_COLUNA_DIA, y + ALTURA_LINHA], outline='black')
            aula = por_dia.get(codigo)
            if aula:
                texto = '\n'.join(montar_linhas(aula))
                desenho.multiline_text((x + 8, y + 8), texto, fill='black', font=fonte_celula)
            x += LARGURA_COLUNA_DIA
        y += ALTURA_LINHA

    buffer = BytesIO()
    if formato == 'JPEG':
        imagem.save(buffer, format='JPEG', quality=90)
    else:
        imagem.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer
