FROM python:3.13-slim

# Evita arquivos .pyc e garante logs em tempo real no terminal do Docker.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# libpq-dev/gcc: exigidos pelo psycopg2 (driver PostgreSQL).
# fonts-dejavu-core: usada pelo Módulo 14 (Exportações) para desenhar texto
# legível nas imagens PNG/JPEG da grade — sem isso o Pillow cai numa fonte
# bitmap minúscula.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
