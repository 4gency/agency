FROM python:3.10-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código do bot
COPY . .

# Expor a porta da API
EXPOSE ${API_PORT}

# Comando para iniciar o bot
CMD ["python", "main.py"] 