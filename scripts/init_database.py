import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.controle_presenca.database.connection import engine
from src.controle_presenca.database.models import Base
from sqlalchemy import text

def inicializar_banco():
    """Cria todas as tabelas definidas nos modelos e atualiza colunas ausentes no PostgreSQL"""
    print("🔨 Criando estrutura do banco de dados...")
    try:
        Base.metadata.create_all(bind=engine)
        
        # Garante que novas colunas adicionadas no modelo em tabelas existentes sejam criadas (PostgreSQL)
        if engine.dialect.name == 'postgresql':
            with engine.connect() as conn:
                print("🔧 Atualizando colunas na tabela 'pontuacoes_questionario'...")
                conn.execute(text("ALTER TABLE pontuacoes_questionario ADD COLUMN IF NOT EXISTS resposta VARCHAR(500)"))
                conn.execute(text("ALTER TABLE pontuacoes_questionario ADD COLUMN IF NOT EXISTS pergunta_numero INTEGER"))
                conn.commit()
                
        print("✅ Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        sys.exit(1)

if __name__ == "__main__":
    inicializar_banco()
