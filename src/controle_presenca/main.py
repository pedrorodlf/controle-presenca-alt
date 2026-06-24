import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.controle_presenca.database.connection import SessionLocal
from src.controle_presenca.services.presenca_service import PresencaService
from src.controle_presenca.services.sgdi_service import SGDiService
from src.controle_presenca.database.models import Aluno

# Constantes para evitar duplicação de Strings (Exigência do SonarCloud)
MSG_ESCOLHA = "\nEscolha: "
MSG_VOLTAR = "\nENTER para voltar..."

def limpar_tela():
    os.system('clear')

def _pausar():
    input(MSG_VOLTAR)

def iniciar_sessao_aula():
    with SessionLocal() as db:
        svc = PresencaService(db)
        _, msg = svc.iniciar_sessao()
        print(f"\n{msg}")
    _pausar()

def encerrar_sessao_aula():
    with SessionLocal() as db:
        svc = PresencaService(db)
        _, msg = svc.encerrar_sessao()
        print(f"\n{msg}")
    _pausar()

def iniciar_intervalo_aula():
    with SessionLocal() as db:
        svc = PresencaService(db)
        _, msg = svc.iniciar_intervalo()
        print(f"\n{msg}")
    _pausar()

def encerrar_intervalo_aula():
    with SessionLocal() as db:
        svc = PresencaService(db)
        _, msg = svc.encerrar_intervalo()
        print(f"\n{msg}")
    _pausar()

def bater_ponto():
    with SessionLocal() as db:
        svc = PresencaService(db)
        if not svc.repo.obter_sessao_ativa():
            print("\n⚠️ Inicie a sessão primeiro!")
            _pausar()
            return
            
        print("\n[MODO LEITURA - Digite 'sair' para parar]")
        while True:
            cartao = input("Cartão: ").strip()
            if cartao.lower() == 'sair':
                break
            sucesso, msg = svc.processar_leitura(cartao)
            print(f"✅ {msg}" if sucesso else f"❌ {msg}")

def exibir_ranking_sgdi():
    with SessionLocal() as db:
        svc = SGDiService(db)
        ranking = svc.gerar_ranking()
        print("\n--- RANKING PENDENTES ---")
        for i, c in enumerate(ranking):
            print(f"{i+1}º | {c.nome} | CPF: {c.cpf} | Pontos: {c.pontuacao_socioeconomica}")
        if not ranking:
            print("Nenhum candidato pendente.")
    _pausar()

def aprovar_candidatos_sgdi():
    qtd = input("\nAprovar quantos candidatos do topo do ranking? ")
    if qtd.isdigit():
        with SessionLocal() as db:
            svc = SGDiService(db)
            try:
                n_aprovados = svc.aprovar_corte(int(qtd))
                print(f"\n✅ {n_aprovados} candidatos aprovados com sucesso!")
            except ValueError as e:
                print(f"\n❌ Erro: {e}")
    _pausar()

def efetivar_matricula_sgdi():
    cpf = input("\nDigite o CPF do candidato aprovado: ").strip()
    with SessionLocal() as db:
        svc = SGDiService(db)
        _, msg = svc.matricular_candidato(cpf)
        print(f"\n{msg}")
    _pausar()

def importar_candidatos_planilha_cli():
    caminho = input("\nDigite o caminho da planilha de respostas (.xlsx): ").strip()
    if not os.path.exists(caminho):
        print("\n❌ Arquivo não encontrado.")
        _pausar()
        return
    with SessionLocal() as db:
        svc = SGDiService(db)
        inseridos, erros = svc.importar_candidatos_planilha(caminho)
        print(f"\n✅ Importação concluída! {inseridos} candidatos importados, {erros} erros/duplicados.")
    _pausar()

def pesquisar_candidato_aluno_cli():
    termo = input("\nDigite o Nome, CPF ou ID do cartão para busca: ").strip()
    with SessionLocal() as db:
        svc = SGDiService(db)
        cands = svc.pesquisar_candidatos(termo)
        alunos = svc.pesquisar_alunos(termo)
        
        print("\n--- CANDIDATOS ENCONTRADOS ---")
        for c in cands:
            print(f"ID: {c.id} | {c.nome} | CPF: {c.cpf} | Status: {c.status}")
        if not cands:
            print("Nenhum candidato encontrado.")
            
        print("\n--- ALUNOS ENCONTRADOS ---")
        for a in alunos:
            print(f"ID: {a.id} | {a.nome} | Cartão: {a.cartao_id} | Status: {a.status}")
        if not alunos:
            print("Nenhum aluno encontrado.")
    _pausar()

def remover_candidato_aluno_cli():
    print("\n1. Excluir Candidato")
    print("2. Desativar Aluno (Exclusão Lógica)")
    op = input(MSG_ESCOLHA).strip()
    
    with SessionLocal() as db:
        svc = SGDiService(db)
        if op == '1':
            cid = input("ID do Candidato: ").strip()
            if cid.isdigit():
                _, msg = svc.excluir_candidato(int(cid))
                print(f"\n{msg}")
            else:
                print("\n❌ ID inválido.")
        elif op == '2':
            aid = input("ID do Aluno: ").strip()
            if aid.isdigit():
                _, msg = svc.desativar_aluno(int(aid))
                print(f"\n{msg}")
            else:
                print("\n❌ ID inválido.")
    _pausar()

def menu_leitor():
    while True:
        limpar_tela()
        print("--- LEITOR DE PRESENÇA ---")
        print("1. Iniciar Sessão de Aula")
        print("2. Encerrar Sessão de Aula")
        print("3. Iniciar Intervalo")
        print("4. Encerrar Intervalo")
        print("5. Bater Ponto")
        print("6. Voltar")
        
        opcao = input(MSG_ESCOLHA).strip()
        
        match opcao:
            case '1': iniciar_sessao_aula()
            case '2': encerrar_sessao_aula()
            case '3': iniciar_intervalo_aula()
            case '4': encerrar_intervalo_aula()
            case '5': bater_ponto()
            case '6': break

def gerar_lista_dados_cli():
    with SessionLocal() as db:
        svc = SGDiService(db)
        questoes = svc.obter_questoes_disponiveis()
        if not questoes:
            print("\n⚠️ Nenhuma questão socioeconômica encontrada no banco de dados!")
            _pausar()
            return
        print("\n--- QUESTÕES DISPONÍVEIS ---")
        for i, q in enumerate(questoes, 1):
            print(f"{i}- {q['questao']}")
        
        jk = input("\nA sua lista de dados deve conter as informações de cada aluno para quantas questões?: ").strip()
        if not jk.isdigit():
            print("❌ Quantidade inválida.")
            _pausar()
            return
        jk = int(jk)
        
        questoes_selecionadas = []
        for i in range(jk):
            num = input(f"Insira o número da questão {i+1} da sua lista de dados: ").strip()
            if num.isdigit() and 1 <= int(num) <= len(questoes):
                q_num = questoes[int(num)-1]["pergunta_numero"]
                questoes_selecionadas.append(q_num)
            else:
                print("⚠️ Número inválido. Pulando...")
                
        if not questoes_selecionadas:
            print("❌ Nenhuma questão válida selecionada.")
            _pausar()
            return
            
        colunas, linhas = svc.obter_dados_exportacao(questoes_selecionadas)
        
        from src.controle_presenca.utils.excel_exporter import ExcelExporter
        os.makedirs("Cartola mágica", exist_ok=True)
        caminho_salvar = os.path.join("Cartola mágica", "ListaDeDados.xlsx")
        ExcelExporter.gerar_planilha(colunas, linhas, caminho_salvar)
        
        print(f"\n✅ A lista de dados já foi gerada e você pode acessá-la na pasta \"Cartola mágica\"")
    _pausar()

def atualizar_presencas_leitor_cli():
    from src.controle_presenca.cli.colors import Colors, print_c
    print("\n⏳ Iniciando atualização de presenças do leitor...")
    with SessionLocal() as db:
        svc = SGDiService(db)
        logs = svc.atualizar_presencas_leitor_service()
        print("\n--- RELATÓRIO DE ATUALIZAÇÃO ---")
        for log in logs:
            if log.startswith("💙"):
                print_c(log, Colors.BLUE)
            elif log.startswith("💚"):
                print_c(log, Colors.GREEN)
            elif log.startswith("❤️"):
                print_c(log, Colors.RED)
            elif log.startswith("⚠️"):
                print_c(log, Colors.YELLOW)
            else:
                print_c(log, Colors.MAGENTA)
    _pausar()

def modificar_dados_presenca_cli():
    from src.controle_presenca.cli.colors import Colors, print_c
    with SessionLocal() as db:
        svc = SGDiService(db)
        alunos = db.query(Aluno).filter(Aluno.status == 'ATIVADO').order_by(Aluno.id.asc()).all()
        
        if not alunos:
            print("\n⚠️ Nenhum discente cadastrado ou ativo no sistema.")
            _pausar()
            return
            
        print("\n--- ALUNOS ATIVOS ---")
        print(f"{'ID':<4} | {'Nome':<30} | {'Cartão':<8} | {'Horas Ef.':<10} | {'Horas Tot.':<10} | {'Presença':<8}")
        print("-" * 80)
        for a in alunos:
            h_tot = float(a.carga_horaria_total or 0.0)
            perc = float(a.percentual_presenca or 0.0)
            h_ef = (perc * h_tot) / 100.0
            cartao_str = str(a.cartao_id) if a.cartao_id else "-"
            print(f"{a.id:<4} | {a.nome[:30]:<30} | {cartao_str:<8} | {h_ef:<10.1f} | {h_tot:<10.1f} | {perc:<6.1f}%")
            
        print("\nOs dados de presença que você deseja modificar são pertencentes a quais cartões?")
        print("Insira os números dos cartões (separados por vírgula. Ex: 1,5,15...).")
        print("Caso queira modificar todos, digite 't'. Para sair, digite 's'.")
        
        cartoes_input = input("Sua resposta: ").strip().lower()
        if cartoes_input == 's':
            return
            
        cartoes_selecionados = []
        if cartoes_input == 't':
            cartoes_selecionados = [a.cartao_id for a in alunos if a.cartao_id is not None]
        else:
            for token in cartoes_input.split(','):
                t = token.strip()
                if t.isdigit():
                    cartoes_selecionados.append(int(t))
                    
        if not cartoes_selecionados:
            print("❌ Nenhum cartão selecionado.")
            _pausar()
            return
            
        print("\nVocê deseja conceder/retirar dos alunos horas de presença efetivas ou absolutas?")
        print("Digite 'e' para efetivas ou qualquer outra tecla para absolutas.")
        tipo = input("Resposta: ").strip().lower()
        
        horas_str = input("\nInsira o número de horas (número negativo para retirar): ").strip()
        try:
            horas = float(horas_str)
        except ValueError:
            print("❌ Valor de horas inválido.")
            _pausar()
            return
            
        acertos, erros = svc.modificar_dados_presenca_service(cartoes_selecionados, horas, tipo)
        
        print("\n--- ALTERAÇÕES REALIZADAS ---")
        for item in acertos:
            tipo_str = "efetivas" if tipo == 'e' else "absolutas"
            var = item["variacao"]
            color = Colors.GREEN if var >= 0 else Colors.RED
            
            print_c(
                f"Modificação de {var} horas {tipo_str} na presença de {item['nome'].upper()} (Cartão: {item['cartao']}) realizada com sucesso.", 
                color
            )
            print_c(
                f"Antigo percentual: {item['pant']}% | Novo percentual: {item['pmod']}%", 
                Colors.CYAN
            )
            
        if erros:
            print(f"\n⚠️ Lista de entradas não reconhecidas: {erros}")
            
    _pausar()

def menu_sgdi():
    while True:
        limpar_tela()
        print("--- SGDi (Gestor de Discentes) ---")
        print("1. Ver Ranking Socioeconômico")
        print("2. Registrar Corte de Candidatos (Linha de Corte)")
        print("3. Efetivar Matrícula (Gerar Aluno)")
        print("4. Gerar Lista de Dados (Legado/Customizado)")
        print("5. Atualizar Presenças do Leitor (Google Drive/Planilha)")
        print("6. Modificar Dados de Freqüência (Ajuste de Horas)")
        print("7. Importar Candidatos de Planilha")
        print("8. Pesquisar Candidato ou Aluno")
        print("9. Excluir Candidato / Desativar Aluno")
        print("10. Voltar")
        
        opcao = input(MSG_ESCOLHA).strip()
        
        match opcao:
            case '1': exibir_ranking_sgdi()
            case '2': aprovar_candidatos_sgdi()
            case '3': efetivar_matricula_sgdi()
            case '4': gerar_lista_dados_cli()
            case '5': atualizar_presencas_leitor_cli()
            case '6': modificar_dados_presenca_cli()
            case '7': importar_candidatos_planilha_cli()
            case '8': pesquisar_candidato_aluno_cli()
            case '9': remover_candidato_aluno_cli()
            case '10': break

def executar_menu():
    while True:
        limpar_tela()
        print("="*55)
        print(" SISTEMA INTEGRADO EXPLICAASO")
        print("="*55)
        print("\n1. 📍 LEITOR DE PRESENÇA")
        print("2. 📊 SGDi (Gestor de Discentes)")
        print("3. 🚪 SAIR")
        
        opcao = input(MSG_ESCOLHA).strip()
        
        match opcao:
            case '1': menu_leitor()
            case '2': menu_sgdi()
            case '3':
                print("\n👋 Encerrando o sistema...")
                break
            case _:
                print("\n❌ Opção inválida!")
                input("Pressione ENTER para tentar novamente...")

if __name__ == "__main__":
    executar_menu()
