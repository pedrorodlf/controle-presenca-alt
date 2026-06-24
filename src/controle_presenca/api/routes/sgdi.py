from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
from ...utils.excel_exporter import ExcelExporter

from ...database.connection import SessionLocal
from ...services.sgdi_service import SGDiService

router = APIRouter(prefix="/sgdi", tags=["SGDi"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CandidatoResponse(BaseModel):
    id: int
    nome: str
    cpf: str
    email: str
    status: str
    pontuacao_socioeconomica: float

    class Config:
        from_attributes = True

class CandidatoRespostaResponse(BaseModel):
    id: int
    nome: str
    cpf: str
    email: str
    status: str
    pontuacao_socioeconomica: float
    resposta: str

    class Config:
        from_attributes = True

class HistoricoStatusResponse(BaseModel):
    id: int
    candidato_id: Optional[int] = None
    candidato_nome: Optional[str] = None
    candidato_cpf: Optional[str] = None
    status_anterior: Optional[str] = None
    status_novo: str
    data_alteracao: datetime
    observacao: Optional[str] = None

    class Config:
        from_attributes = True

class RespostaQuestionarioResponse(BaseModel):
    id: int
    candidato_id: int
    questao: str
    resposta: Optional[str] = None
    pergunta_numero: Optional[int] = None
    pontos: float

    class Config:
        from_attributes = True

class QuestaoDisponivelResponse(BaseModel):
    pergunta_numero: Optional[int] = None
    questao: str

    class Config:
        from_attributes = True

class EstatisticaRespostaResponse(BaseModel):
    resposta: str
    quantidade: int
    percentual: float

class MatrículaRequest(BaseModel):
    cpf: str

class AprovarCorteRequest(BaseModel):
    quantidade: int

@router.get("/ranking", response_model=List[CandidatoResponse])
def get_ranking(limite: Optional[int] = 60, db: Session = Depends(get_db)):
    """Ver ranking socioeconômico de candidatos pendentes"""
    service = SGDiService(db)
    return service.gerar_ranking(limite)

@router.post("/aprovar-corte")
def aprovar_candidatos(req: AprovarCorteRequest, db: Session = Depends(get_db)):
    """Aprova os N primeiros candidatos do ranking socioeconômico"""
    service = SGDiService(db)
    try:
        n_aprovados = service.aprovar_corte(req.quantidade)
        return {"mensagem": f"✅ {n_aprovados} candidatos aprovados com sucesso."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/matricular")
def matricular(req: MatrículaRequest, db: Session = Depends(get_db)):
    """Efetiva a matrícula de um candidato aprovado por CPF"""
    service = SGDiService(db)
    sucesso, mensagem = service.matricular_candidato(req.cpf)
    if not sucesso:
        raise HTTPException(status_code=400, detail=mensagem)
    return {"mensagem": mensagem}

@router.get("/candidatos", response_model=List[CandidatoResponse])
def buscar_candidatos(termo: Optional[str] = "", db: Session = Depends(get_db)):
    """Pesquisa candidatos por nome ou CPF"""
    service = SGDiService(db)
    return service.pesquisar_candidatos(termo)

@router.delete("/candidatos/{candidato_id}")
def excluir_candidato(candidato_id: int, db: Session = Depends(get_db)):
    """Exclui permanentemente um candidato do banco de dados"""
    service = SGDiService(db)
    sucesso = service.excluir_candidato(candidato_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="❌ Candidato não encontrado.")
    return {"mensagem": "✅ Candidato excluído com sucesso."}

@router.delete("/alunos/{aluno_id}")
def desativar_aluno(aluno_id: int, db: Session = Depends(get_db)):
    """Desativa (exclusão lógica) um aluno do controle de presenças"""
    service = SGDiService(db)
    sucesso, mensagem = service.desativar_aluno(aluno_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail=mensagem)
    return {"mensagem": mensagem}

@router.post("/importar")
async def importar_planilha(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Importa candidatos a partir de uma planilha enviada"""
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())
        
    service = SGDiService(db)
    try:
        inseridos, erros = service.importar_candidatos_planilha(temp_path)
        return {
            "mensagem": "✅ Importação concluída.",
            "inseridos": inseridos,
            "erros": erros
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/sincronizar-drive")
def sincronizar_drive(db: Session = Depends(get_db)):
    """Sincroniza automaticamente a base de candidatos a partir do Google Drive"""
    service = SGDiService(db)
    try:
        sucesso, mensagem = service.sincronizar_importacao_drive()
        if not sucesso:
            raise HTTPException(status_code=400, detail=mensagem)
        return {"mensagem": mensagem}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor: {e}")

@router.get("/candidatos/{candidato_id}/historico", response_model=List[HistoricoStatusResponse])
def get_historico_candidato(candidato_id: int, db: Session = Depends(get_db)):
    """Retorna o histórico de status de um candidato específico"""
    service = SGDiService(db)
    return service.obter_historico_candidato(candidato_id)

@router.get("/historico-geral", response_model=List[HistoricoStatusResponse])
def get_historico_geral(db: Session = Depends(get_db)):
    """Retorna todo o histórico de status de candidatos (incluindo deletados)"""
    service = SGDiService(db)
    return service.obter_historico_geral()

@router.get("/questoes", response_model=List[QuestaoDisponivelResponse])
def get_questoes(db: Session = Depends(get_db)):
    """Retorna os enunciados de perguntas únicas já cadastradas na base"""
    service = SGDiService(db)
    return service.obter_questoes_disponiveis()

@router.get("/candidatos/{candidato_id}/respostas", response_model=List[RespostaQuestionarioResponse])
def get_respostas_candidato(candidato_id: int, db: Session = Depends(get_db)):
    """Retorna todas as respostas daquele candidato ordenadas pelo número da pergunta"""
    service = SGDiService(db)
    return service.obter_respostas_candidato(candidato_id)

@router.get("/questoes/estatisticas", response_model=List[EstatisticaRespostaResponse])
def get_estatisticas_questao(questao: str, db: Session = Depends(get_db)):
    """Retorna a distribuição estatística de respostas para uma determinada questão"""
    service = SGDiService(db)
    return service.obter_estatisticas_questao(questao)

@router.get("/questoes/respostas", response_model=List[CandidatoRespostaResponse])
def get_candidatos_por_resposta(questao: str, resposta: Optional[str] = None, db: Session = Depends(get_db)):
    """Retorna a lista de candidatos que responderam especificamente aquela opção para aquela questão"""
    service = SGDiService(db)
    return service.filtrar_candidatos_por_resposta(questao, resposta)

class ExportarRequest(BaseModel):
    questoes: List[int]

@router.post("/questoes/exportar")
def exportar_dados(req: ExportarRequest, db: Session = Depends(get_db)):
    """Gera e retorna a planilha ListaDeDados.xlsx com as questões selecionadas"""
    service = SGDiService(db)
    colunas, linhas = service.obter_dados_exportacao(req.questoes)
    
    os.makedirs("Cartola mágica", exist_ok=True)
    caminho_salvar = os.path.join("Cartola mágica", "ListaDeDados.xlsx")
    ExcelExporter.gerar_planilha(colunas, linhas, caminho_salvar)
    
    return FileResponse(
        caminho_salvar, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        filename="ListaDeDados.xlsx"
    )

@router.post("/atualizar-presencas")
def atualizar_presencas(db: Session = Depends(get_db)):
    """Sincroniza as presenças com a planilha do leitor (local ou Drive)"""
    service = SGDiService(db)
    try:
        logs = service.atualizar_presencas_leitor_service()
        return {"mensagem": "Sincronização concluída com sucesso.", "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na sincronização: {e}")

class ModificarPresencaRequest(BaseModel):
    cartoes: List[int]
    horas: float
    tipo: str # 'e' ou 'a'

@router.post("/modificar-presenca")
def modificar_presenca(req: ModificarPresencaRequest, db: Session = Depends(get_db)):
    """Modifica as horas de presença dos alunos associados aos cartões informados"""
    service = SGDiService(db)
    acertos, erros = service.modificar_dados_presenca_service(req.cartoes, req.horas, req.tipo)
    return {"acertos": acertos, "erros": erros}

