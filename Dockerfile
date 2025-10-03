# Usa uma imagem base oficial do Python
FROM python:3.9-slim

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de requerimentos para o contêiner
COPY requirements.txt ./requirements.txt

# Instala as bibliotecas necessárias
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos os outros arquivos (seu script e seus excels) para o contêiner
COPY . .

# Expõe a porta que o Streamlit usa
EXPOSE 8080

# O comando para iniciar a aplicação quando o contêiner rodar
CMD ["streamlit", "run", "dashboard.py", "--server.port=8080", "--server.address=0.0.0.0"]