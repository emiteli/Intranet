# Use a imagem oficial do Python como base
FROM python:3.12-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Copiar o arquivo de requisitos e instalá-los
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todos os arquivos do projeto para o container
COPY . .

# Expor a porta que o Flask vai rodar (geralmente a 5000)
EXPOSE 5000

# Definir a variável de ambiente para rodar o Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

# Comando para rodar o servidor Flask
CMD ["flask", "run", "--host=0.0.0.0"]
