import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

def test_get_questoes():
    from src.controle_presenca.api.main import app
    client = TestClient(app)
    
    with patch('src.controle_presenca.api.routes.sgdi.SessionLocal') as mock_db:
        mock_session = MagicMock()
        mock_db.return_value.__enter__.return_value = mock_session
        
        with patch('src.controle_presenca.api.routes.sgdi.SGDiService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.obter_questoes_disponiveis.return_value = [
                {"pergunta_numero": 1, "questao": "Questão 1"}
            ]
            
            response = client.get("/sgdi/questoes")
            assert response.status_code == 200
            assert response.json() == [
                {"pergunta_numero": 1, "questao": "Questão 1"}
            ]

def test_get_respostas_candidato():
    from src.controle_presenca.api.main import app
    client = TestClient(app)
    
    with patch('src.controle_presenca.api.routes.sgdi.SessionLocal') as mock_db:
        mock_session = MagicMock()
        mock_db.return_value.__enter__.return_value = mock_session
        
        with patch('src.controle_presenca.api.routes.sgdi.SGDiService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.obter_respostas_candidato.return_value = [
                MagicMock(id=1, candidato_id=42, questao="Q1", resposta="R1", pergunta_numero=1, pontos=2.5)
            ]
            
            response = client.get("/sgdi/candidatos/42/respostas")
            assert response.status_code == 200
            assert len(response.json()) == 1
            assert response.json()[0]["questao"] == "Q1"
            assert response.json()[0]["pontos"] == 2.5

def test_get_estatisticas_questao():
    from src.controle_presenca.api.main import app
    client = TestClient(app)
    
    with patch('src.controle_presenca.api.routes.sgdi.SessionLocal') as mock_db:
        mock_session = MagicMock()
        mock_db.return_value.__enter__.return_value = mock_session
        
        with patch('src.controle_presenca.api.routes.sgdi.SGDiService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.obter_estatisticas_questao.return_value = [
                {"resposta": "Sim", "quantidade": 8, "percentual": 80.0}
            ]
            
            response = client.get("/sgdi/questoes/estatisticas?questao=Q1")
            assert response.status_code == 200
            assert response.json() == [
                {"resposta": "Sim", "quantidade": 8, "percentual": 80.0}
            ]

def test_get_candidatos_por_resposta():
    from src.controle_presenca.api.main import app
    client = TestClient(app)
    
    with patch('src.controle_presenca.api.routes.sgdi.SessionLocal') as mock_db:
        mock_session = MagicMock()
        mock_db.return_value.__enter__.return_value = mock_session
        
        with patch('src.controle_presenca.api.routes.sgdi.SGDiService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.filtrar_candidatos_por_resposta.return_value = [
                {
                    "id": 1,
                    "nome": "CANDIDATO 1",
                    "cpf": "11122233344",
                    "email": "c1@email.com",
                    "status": "pendente",
                    "pontuacao_socioeconomica": 15.0,
                    "resposta": "Sim"
                }
            ]
            
            response = client.get("/sgdi/questoes/respostas?questao=Q1&resposta=Sim")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["nome"] == "CANDIDATO 1"
            assert data[0]["resposta"] == "Sim"

def test_exportar_dados():
    from src.controle_presenca.api.main import app
    client = TestClient(app)
    
    with patch('src.controle_presenca.api.routes.sgdi.SessionLocal') as mock_db:
        mock_session = MagicMock()
        mock_db.return_value.__enter__.return_value = mock_session
        
        with patch('src.controle_presenca.api.routes.sgdi.SGDiService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.obter_dados_exportacao.return_value = (["Nome", "Q1"], [["CARLOS", "Sim"]])
            
            with patch('src.controle_presenca.api.routes.sgdi.ExcelExporter.gerar_planilha') as mock_exporter, \
                 patch('os.makedirs') as mock_makedirs, \
                 patch('src.controle_presenca.api.routes.sgdi.FileResponse') as mock_fileresponse:
                
                mock_fileresponse.return_value = "file_response_object"
                
                response = client.post("/sgdi/questoes/exportar", json={"questoes": [1]})
                
                assert response.status_code == 200
                mock_service.obter_dados_exportacao.assert_called_once_with([1])
                mock_exporter.assert_called_once()
                mock_makedirs.assert_called_once_with("Cartola mágica", exist_ok=True)

def test_atualizar_presencas():
    from src.controle_presenca.api.main import app
    client = TestClient(app)
    
    with patch('src.controle_presenca.api.routes.sgdi.SessionLocal') as mock_db:
        mock_session = MagicMock()
        mock_db.return_value.__enter__.return_value = mock_session
        
        with patch('src.controle_presenca.api.routes.sgdi.SGDiService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.atualizar_presencas_leitor_service.return_value = ["log1", "log2"]
            
            response = client.post("/sgdi/atualizar-presencas")
            assert response.status_code == 200
            assert response.json()["mensagem"] == "Sincronização concluída com sucesso."
            assert response.json()["logs"] == ["log1", "log2"]

def test_modificar_presenca():
    from src.controle_presenca.api.main import app
    client = TestClient(app)
    
    with patch('src.controle_presenca.api.routes.sgdi.SessionLocal') as mock_db:
        mock_session = MagicMock()
        mock_db.return_value.__enter__.return_value = mock_session
        
        with patch('src.controle_presenca.api.routes.sgdi.SGDiService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.modificar_dados_presenca_service.return_value = (["acerto1"], [2, 3])
            
            response = client.post("/sgdi/modificar-presenca", json={"cartoes": [1, 2, 3], "horas": 1.5, "tipo": "e"})
            assert response.status_code == 200
            assert response.json()["acertos"] == ["acerto1"]
            assert response.json()["erros"] == [2, 3]
            mock_service.modificar_dados_presenca_service.assert_called_once_with([1, 2, 3], 1.5, "e")

