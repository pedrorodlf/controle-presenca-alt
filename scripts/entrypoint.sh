#!/bin/bash

echo "⏳ Aguardando o banco de dados..."
while ! nc -z db 5432; do
  sleep 0.5
done
echo "✅ Banco de dados pronto!"

echo "📊 Criando tabelas no banco de dados..."
# Cria e atualiza as tabelas via script Python
python /app/scripts/init_database.py

echo "🚀 Iniciando API..."
# Usa o 'python -m' para garantir que ele ache o uvicorn onde quer que esteja instalado
exec python -m uvicorn src.controle_presenca.api.main:app --host 0.0.0.0 --port 8000 --reload
