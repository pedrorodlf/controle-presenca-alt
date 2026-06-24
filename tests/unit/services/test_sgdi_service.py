import pytest
from unittest.mock import MagicMock, patch

try:
    from controle_presenca.services.sgdi_service import SGDiService
    from controle_presenca.database.models import Aluno, Candidato
except ImportError:
    pytest.skip("SGDiService não disponível", allow_module_level=True)

def test_sgdi_service_initialization():
    """Testa inicialização do serviço SGDi"""
    mock_db = MagicMock()
    service = SGDiService(mock_db)
    
    assert service is not None
    assert service.db == mock_db

def test_sgdi_service_gerar_ranking():
    """Testa geração de ranking de candidatos"""
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_order = MagicMock()
    mock_filter.order_by.return_value = mock_order
    mock_limit = MagicMock()
    mock_order.limit.return_value = mock_limit
    mock_candidatos = [MagicMock(), MagicMock()]
    mock_limit.all.return_value = mock_candidatos
    
    service = SGDiService(mock_db)
    resultado = service.gerar_ranking(limite=10)
    
    assert resultado == mock_candidatos
    mock_db.query.assert_called_once()

def test_sgdi_service_aprovar_corte_sucesso():
    """Testa aprovação de candidatos por corte dentro do limite"""
    mock_db = MagicMock()
    mock_db.query().filter().count.return_value = 10  # 10 ativos
    
    service = SGDiService(mock_db)
    
    mock_candidato1 = MagicMock()
    mock_candidato2 = MagicMock()
    mock_candidato1.status = 'pendente'
    mock_candidato2.status = 'pendente'
    service.gerar_ranking = MagicMock(return_value=[mock_candidato1, mock_candidato2])
    
    resultado = service.aprovar_corte(quantidade=2)
    
    assert resultado == 2
    assert mock_candidato1.status == 'aprovado'
    assert mock_candidato2.status == 'aprovado'
    mock_db.commit.assert_called_once()

def test_sgdi_service_aprovar_corte_excedendo_limite():
    """Testa se aprovar_corte levanta erro se exceder 60"""
    mock_db = MagicMock()
    mock_db.query().filter().count.return_value = 59  # 59 ativos
    
    service = SGDiService(mock_db)
    
    with pytest.raises(ValueError) as exc:
        service.aprovar_corte(quantidade=2)
        
    assert "excede o limite máximo de 60" in str(exc.value)

def test_sgdi_service_matricular_candidato_sucesso():
    """Testa matrícula de candidato aprovado"""
    mock_db = MagicMock()
    mock_candidato = MagicMock()
    mock_candidato.status = 'aprovado'
    mock_candidato.nome = 'JOAO SILVA'
    mock_db.query().filter().first.return_value = mock_candidato
    
    service = SGDiService(mock_db)
    sucesso, mensagem = service.matricular_candidato(cpf='12345678900')
    
    assert sucesso is True
    assert 'confirmada' in mensagem
    assert 'JOAO SILVA' in mensagem
    assert mock_db.add.call_count == 2
    mock_db.commit.assert_called_once()

def test_sgdi_service_matricular_candidato_nao_encontrado():
    """Testa matrícula de candidato não encontrado"""
    mock_db = MagicMock()
    mock_db.query().filter().first.return_value = None
    
    service = SGDiService(mock_db)
    sucesso, mensagem = service.matricular_candidato(cpf='12345678900')
    
    assert sucesso is False
    assert 'não encontrado' in mensagem.lower()
    mock_db.add.assert_not_called()

def test_sgdi_service_matricular_candidato_nao_aprovado():
    """Testa matrícula de candidato não aprovado"""
    mock_db = MagicMock()
    mock_candidato = MagicMock()
    mock_candidato.status = 'pendente'
    mock_db.query().filter().first.return_value = mock_candidato
    
    service = SGDiService(mock_db)
    sucesso, mensagem = service.matricular_candidato(cpf='12345678900')
    
    assert sucesso is False
    assert 'não está aprovado' in mensagem.lower()
    mock_db.add.assert_not_called()

def test_cadastrar_candidato_cpf_invalido():
    """Testa cadastro com CPF com tamanho incorreto"""
    mock_db = MagicMock()
    service = SGDiService(mock_db)
    
    sucesso, msg = service.cadastrar_candidato("Joao", "123", "joao@email.com")
    assert sucesso is False
    assert "CPF inválido" in msg

def test_cadastrar_candidato_duplicado():
    """Testa cadastro de candidato com CPF já cadastrado"""
    mock_db = MagicMock()
    mock_db.query().filter().first.return_value = MagicMock() # Candidato existente
    
    service = SGDiService(mock_db)
    sucesso, msg = service.cadastrar_candidato("Joao", "123.456.789-00", "joao@email.com")
    assert sucesso is False
    assert "já cadastrado" in msg

def test_cadastrar_candidato_sucesso():
    """Testa cadastro de candidato com sucesso e pontuação calculada"""
    mock_db = MagicMock()
    mock_db.query().filter().first.return_value = None
    
    service = SGDiService(mock_db)
    
    with patch('controle_presenca.utils.score_calculator.ScoreCalculator.calcular_detalhes', return_value={10: {"resposta": "Sim", "pontos": 15.5}}) as mock_calc:
        sucesso, msg = service.cadastrar_candidato(
            nome="Joao Silva  ",
            cpf="123.456.789-00",
            email="joao@email.com",
            respostas={10: "Sim"}
        )
        assert sucesso is True
        assert "cadastrado com sucesso" in msg
        mock_calc.assert_called_once_with({10: "Sim"})
        assert mock_db.add.call_count == 2
        mock_db.commit.assert_called_once()

def test_pesquisar_candidatos_por_nome():
    """Testa busca de candidatos por nome"""
    mock_db = MagicMock()
    mock_cands = [MagicMock()]
    mock_db.query().filter().all.return_value = mock_cands
    
    service = SGDiService(mock_db)
    res = service.pesquisar_candidatos("Joao")
    assert res == mock_cands

def test_pesquisar_candidatos_por_cpf():
    """Testa busca de candidatos por CPF"""
    mock_db = MagicMock()
    mock_cands = [MagicMock()]
    mock_db.query().filter().all.return_value = mock_cands
    
    service = SGDiService(mock_db)
    res = service.pesquisar_candidatos("123.456.789-00")
    assert res == mock_cands

def test_excluir_candidato_inexistente():
    """Testa exclusão de candidato inexistente"""
    mock_db = MagicMock()
    mock_db.query().filter().first.return_value = None
    
    service = SGDiService(mock_db)
    sucesso, msg = service.excluir_candidato(99)
    assert sucesso is False
    assert "não encontrado" in msg

def test_excluir_candidato_sucesso():
    """Testa exclusão de candidato existente com sucesso"""
    mock_db = MagicMock()
    mock_cand = MagicMock()
    mock_db.query().filter().first.return_value = mock_cand
    
    service = SGDiService(mock_db)
    sucesso, msg = service.excluir_candidato(1)
    assert sucesso is True
    assert "excluído com sucesso" in msg
    mock_db.delete.assert_called_once_with(mock_cand)
    mock_db.commit.assert_called_once()

def test_pesquisar_alunos():
    """Testa busca de alunos por nome e cartao_id"""
    mock_db = MagicMock()
    mock_db.query().filter().all.return_value = [MagicMock()]
    
    service = SGDiService(mock_db)
    res1 = service.pesquisar_alunos("Joao")
    assert len(res1) == 1
    
    res2 = service.pesquisar_alunos("123456")
    assert len(res2) == 1

def test_desativar_aluno_inexistente():
    """Testa desativação de aluno inexistente"""
    mock_db = MagicMock()
    mock_db.query().filter().first.return_value = None
    
    service = SGDiService(mock_db)
    sucesso, msg = service.desativar_aluno(99)
    assert sucesso is False
    assert "não encontrado" in msg

def test_desativar_aluno_sucesso():
    """Testa desativação (exclusão lógica) de aluno existente com sucesso"""
    mock_db = MagicMock()
    mock_aluno = MagicMock()
    mock_aluno.status = 'ATIVADO'
    mock_db.query().filter().first.return_value = mock_aluno
    
    service = SGDiService(mock_db)
    sucesso, msg = service.desativar_aluno(1)
    assert sucesso is True
    assert "desativado com sucesso" in msg
    assert mock_aluno.status == 'DESATIVADO'
    mock_db.commit.assert_called_once()

@patch('openpyxl.load_workbook')
def test_importar_candidatos_planilha(mock_load):
    """Testa importação de candidatos a partir de planilha"""
    mock_db = MagicMock()
    service = SGDiService(mock_db)
    
    # Mocks do openpyxl
    mock_wb = MagicMock()
    mock_sheet = MagicMock()
    mock_load.return_value = mock_wb
    mock_wb.active = mock_sheet
    
    mock_sheet.max_row = 2
    
    # Células da linha 2
    # E=5 (Nome), D=4 (Email), I=9 (CPF), K=11 (Q10)...
    cell_values = {
        (2, 5): "Candidato Importado",
        (2, 4): "importado@email.com",
        (2, 9): "98765432100",
        (2, 11): "Opção A"
    }
    
    def side_effect(row, column):
        cell = MagicMock()
        cell.value = cell_values.get((row, column), None)
        return cell
    mock_sheet.cell.side_effect = side_effect
    
    # Mock do cadastrar_candidato
    service.cadastrar_candidato = MagicMock(return_value=(True, ""))
    
    inseridos, erros = service.importar_candidatos_planilha("fake_path.xlsx")
    
    assert inseridos == 1
    assert erros == 0
    service.cadastrar_candidato.assert_called_once()
    mock_wb.close.assert_called_once()

def test_sgdi_service_obter_historico_candidato():
    """Testa obtenção do histórico de status de um candidato"""
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_order = MagicMock()
    mock_filter.order_by.return_value = mock_order
    
    mock_historico = [MagicMock(), MagicMock()]
    mock_order.all.return_value = mock_historico
    
    service = SGDiService(mock_db)
    res = service.obter_historico_candidato(candidato_id=1)
    
    assert res == mock_historico
    mock_db.query.assert_called_once()

@patch('controle_presenca.utils.google_drive.GoogleDriveDownloader.baixar_planilha_forms')
def test_sgdi_service_sincronizar_importacao_drive_sucesso(mock_baixar):
    """Testa sincronização e importação do Google Drive com sucesso"""
    mock_db = MagicMock()
    service = SGDiService(mock_db)
    service.importar_candidatos_planilha = MagicMock(return_value=(5, 0))
    
    sucesso, mensagem = service.sincronizar_importacao_drive()
    
    assert sucesso is True
    assert "Sincronização concluída" in mensagem
    assert "5 candidatos importados" in mensagem
    mock_baixar.assert_called_once_with("temp_drive_import.xlsx")
    service.importar_candidatos_planilha.assert_called_once_with("temp_drive_import.xlsx")

@patch('controle_presenca.utils.google_drive.GoogleDriveDownloader.baixar_planilha_forms')
def test_sgdi_service_sincronizar_importacao_drive_erro(mock_baixar):
    """Testa falha ao sincronizar com Google Drive"""
    mock_db = MagicMock()
    service = SGDiService(mock_db)
    mock_baixar.side_effect = Exception("Erro na API do Drive")
    
    sucesso, mensagem = service.sincronizar_importacao_drive()
    
    assert sucesso is False
    assert "Erro na sincronização" in mensagem
    assert "Erro na API do Drive" in mensagem

def test_sgdi_service_obter_respostas_candidato():
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value.filter.return_value.order_by.return_value
    mock_query.all.return_value = ["res1", "res2"]
    
    service = SGDiService(mock_db)
    res = service.obter_respostas_candidato(candidato_id=42)
    assert res == ["res1", "res2"]

def test_sgdi_service_obter_questoes_disponiveis():
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value.distinct.return_value.order_by.return_value
    mock_query.all.return_value = [(1, "Questão 1"), (2, "Questão 2"), (3, None)]
    
    service = SGDiService(mock_db)
    res = service.obter_questoes_disponiveis()
    assert res == [
        {"pergunta_numero": 1, "questao": "Questão 1"},
        {"pergunta_numero": 2, "questao": "Questão 2"}
    ]

def test_sgdi_service_obter_estatisticas_questao():
    mock_db = MagicMock()
    # Mock total count query
    mock_query_total = MagicMock()
    mock_query_total.filter.return_value.count.return_value = 10
    
    # Mock group by query
    mock_query_group = MagicMock()
    mock_db.query.side_effect = [mock_query_total, mock_query_group]
    
    mock_query_group.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [
        ("Resposta A", 6),
        ("Resposta B", 4)
    ]
    
    service = SGDiService(mock_db)
    res = service.obter_estatisticas_questao("Questão 1")
    assert len(res) == 2
    assert res[0] == {"resposta": "Resposta A", "quantidade": 6, "percentual": 60.0}
    assert res[1] == {"resposta": "Resposta B", "quantidade": 4, "percentual": 40.0}

def test_sgdi_service_filtrar_candidatos_por_resposta():
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [
        (1, "JOAO", "12345678900", "joao@email.com", "pendente", 12.5, "Resposta A")
    ]
    
    service = SGDiService(mock_db)
    res = service.filtrar_candidatos_por_resposta("Questão 1", "Resposta A")
    assert len(res) == 1
    assert res[0]["nome"] == "JOAO"
    assert res[0]["resposta"] == "Resposta A"

def test_sgdi_service_filtrar_candidatos_por_resposta_sem_opcao():
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [
        (1, "JOAO", "12345678900", "joao@email.com", "pendente", 12.5, "Resposta A")
    ]
    
    service = SGDiService(mock_db)
    res = service.filtrar_candidatos_por_resposta("Questão 1")
    assert len(res) == 1
    assert res[0]["nome"] == "JOAO"
    assert res[0]["resposta"] == "Resposta A"

def test_sgdi_service_obter_dados_exportacao():
    mock_db = MagicMock()
    
    # Mock para obter enunciados
    mock_questoes_db = [(1, "Pergunta 1"), (2, "Pergunta 2")]
    mock_db.query.return_value.filter.return_value.distinct.return_value.all.return_value = mock_questoes_db
    
    # Mock para obter candidatos
    mock_cand1 = MagicMock()
    mock_cand1.id = 10
    mock_cand1.nome = "carlos silva"
    
    mock_cand2 = MagicMock()
    mock_cand2.id = 20
    mock_cand2.nome = "maria oliveira"
    
    # Configura side_effect para a primeira consulta de Candidatos e depois as consultas de respostas
    mock_query_cands = MagicMock()
    mock_query_cands.order_by.return_value.all.return_value = [mock_cand1, mock_cand2]
    
    # Respostas para Carlos (cand_id=10) e Maria (cand_id=20)
    mock_respostas_cand1 = [(1, "Sim"), (2, "Não")]
    mock_respostas_cand2 = [(1, "Não"), (2, "Sim")]
    
    mock_query_respostas = MagicMock()
    mock_query_respostas.filter.return_value.all.side_effect = [mock_respostas_cand1, mock_respostas_cand2]
    
    mock_db.query.side_effect = [
        mock_db.query.return_value, # Pela consulta de enunciados
        mock_query_cands,            # Pela consulta de todos os candidatos
        mock_query_respostas,        # Respostas do Carlos
        mock_query_respostas         # Respostas da Maria
    ]
    
    service = SGDiService(mock_db)
    colunas, linhas = service.obter_dados_exportacao([1, 2])
    
    assert colunas == ["Nome", "Pergunta 1", "Pergunta 2"]
    assert len(linhas) == 2
    assert linhas[0] == ["CARLOS SILVA", "Sim", "Não"]
    assert linhas[1] == ["MARIA OLIVEIRA", "Não", "Sim"]


def test_sgdi_service_modificar_dados_presenca_service():
    mock_db = MagicMock()
    
    # Aluno Mock
    aluno = MagicMock()
    aluno.cartao_id = 42
    aluno.nome = "Carlos"
    aluno.percentual_presenca = 80.0
    aluno.carga_horaria_total = 10.0
    aluno.status = 'ATIVADO'
    
    mock_db.query.return_value.filter.return_value.all.return_value = [aluno]
    
    service = SGDiService(mock_db)
    
    # Testando modificação do tipo 'efetiva' (tipo 'e')
    # Horas atuais: (80/100)*10 = 8h. Vamos adicionar 1h -> deve virar 9h (90%).
    acertos, erros = service.modificar_dados_presenca_service([42], 1.0, 'e')
    
    assert len(acertos) == 1
    assert len(erros) == 0
    assert acertos[0]["nome"] == "Carlos"
    assert aluno.percentual_presenca == 90.0
    assert aluno.carga_horaria_total == 10.0
    mock_db.commit.assert_called_once()
    
    # Reset mock_db commit and change aluno values to test absolute type ('a')
    mock_db.commit.reset_mock()
    aluno.percentual_presenca = 80.0
    aluno.carga_horaria_total = 10.0
    
    # Testando modificação do tipo 'absoluta' (tipo 'a')
    # Horas atuais: (80/100)*10 = 8h. Vamos adicionar 2h -> presença vira 10h e total vira 12h.
    # Percentual: 10 / 12 = 83.33%
    acertos, erros = service.modificar_dados_presenca_service([42], 2.0, 'a')
    
    assert len(acertos) == 1
    assert aluno.percentual_presenca == 83.33
    assert aluno.carga_horaria_total == 12.0
    mock_db.commit.assert_called_once()


@patch('os.makedirs')
@patch('os.path.exists', return_value=True)
@patch('openpyxl.load_workbook')
@patch('openpyxl.Workbook')
@patch('controle_presenca.utils.google_drive.GoogleDriveDownloader.obter_servico', side_effect=Exception("Sem internet"))
def test_sgdi_service_atualizar_presencas_leitor_service(mock_drive, mock_wb_class, mock_load_wb, mock_exists, mock_makedirs):
    mock_db = MagicMock()
    
    # Aluno ativo com cartão ID = 5
    aluno = MagicMock()
    aluno.cartao_id = 5
    aluno.nome = "Carlos"
    aluno.status = "ATIVADO"
    aluno.percentual_presenca = 50.0
    aluno.carga_horaria_total = 10.0 # 5 horas presente
    
    mock_db.query.return_value.filter.return_value.all.return_value = [aluno]
    
    # Mock da planilha openpyxl
    mock_wb = MagicMock()
    mock_ws = MagicMock()
    mock_load_wb.return_value = mock_wb
    mock_wb.active = mock_ws
    
    # Max row = 2 (linha 1: cabeçalho, linha 2: cartão 5)
    mock_ws.max_row = 2
    
    cell_values = {
        (2, 1): 5,   # Cartao ID
        (2, 2): "ATIVADO",
        (2, 3): 100,   # Presenças novas (porcentagem, e.g. 100%)
        (2, 4): 2,   # Aulas novas
        (2, 5): "Carlos"
    }
    
    def side_effect(row, column, value=None):
        cell = MagicMock()
        cell.value = cell_values.get((row, column), None)
        return cell
        
    mock_ws.cell.side_effect = side_effect
    
    service = SGDiService(mock_db)
    logs = service.atualizar_presencas_leitor_service()
    
    # Nova carga total: 10 + 2 = 12h
    # Nova presença total: 5 + 2 = 7h
    # Novo percentual: 7 / 12 = 58.33%
    assert aluno.percentual_presenca == 58.33
    assert aluno.carga_horaria_total == 12.0
    assert len(logs) > 0
    assert any("Carlos" in l for l in logs)
    mock_db.commit.assert_called_once()
    mock_wb.save.assert_called()
    mock_wb.close.assert_called()
