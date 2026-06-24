const API_URL = 'http://localhost:8000';
let currentSection = 'frequencia';

// Exibir alertas
function showGlobalAlert(message, type) {
    const alert = document.getElementById('global-alert');
    alert.textContent = message;
    alert.className = `alert ${type}`;
    alert.classList.remove('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setTimeout(() => {
        alert.classList.add('hidden');
    }, 5000);
}

// Inicializar e verificar API
async function inicializar() {
    try {
        const response = await fetch(`${API_URL}/health`);
        const badge = document.getElementById('api-status');
        if (response.ok) {
            badge.innerHTML = '✅ API Online';
            badge.className = 'status-badge online';
            carregarDadosSecao();
        } else {
            throw new Error();
        }
    } catch (e) {
        const badge = document.getElementById('api-status');
        badge.innerHTML = '❌ API Offline';
        badge.className = 'status-badge offline';
    }
}

// Alterar Aba
function switchGestorTab(sectionName) {
    currentSection = sectionName;
    document.querySelectorAll('.gtab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.gestor-section').forEach(sec => sec.classList.add('hidden'));

    document.getElementById(`gtab-${sectionName}`).classList.add('active');
    document.getElementById(`sec-${sectionName}`).classList.remove('hidden');

    carregarDadosSecao();
}

// Carregar dados dependendo da aba ativa
function carregarDadosSecao() {
    if (currentSection === 'frequencia') {
        carregarAlunos();
    } else if (currentSection === 'sgdi') {
        carregarRanking();
    } else if (currentSection === 'auditoria') {
        carregarAuditoria();
    } else if (currentSection === 'busca') {
        popularSeletoresBusca();
    }
}

// ================= ABA 1: DISCENTES & FREQUÊNCIA =================

async function carregarAlunos() {
    const tbody = document.querySelector('#alunos-gestao-table tbody');
    try {
        const response = await fetch(`${API_URL}/alunos/`);
        if (response.ok) {
            const alunos = await response.json();
            if (alunos.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">Nenhum discente cadastrado no sistema.</td></tr>`;
                return;
            }

            // Precisamos buscar as métricas de presença na API detalhada ou carregar os valores reais
            // Como a rota de listar_alunos do backend já retorna percentual_presenca e carga_horaria_total,
            // podemos renderizar diretamente.
            // Para isso, vamos obter os dados reais retornados.
            tbody.innerHTML = alunos.map(a => `
                <tr>
                    <td>${a.id}</td>
                    <td><strong>${a.nome}</strong></td>
                    <td>${a.cartao_id}</td>
                    <td><span class="font-bold">${a.percentual_presenca !== undefined ? a.percentual_presenca : 0}%</span></td>
                    <td>${a.carga_horaria_total !== undefined ? a.carga_horaria_total : 0}h</td>
                    <td>
                        <span class="badge ${a.status === 'ATIVADO' ? 'badge-dentro' : 'badge-fora'}">
                            ${a.status}
                        </span>
                    </td>
                    <td>
                        ${a.status === 'ATIVADO' ? 
                            `<button onclick="desativarAluno(${a.id}, '${a.nome}')" class="btn-danger-sm">❌ Desativar</button>` : 
                            `<span class="text-muted">Desativado</span>`
                        }
                    </td>
                </tr>
            `).join('');
        }
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-red">Erro ao carregar lista de alunos.</td></tr>`;
    }
}

async function cadastrarAlunoManual() {
    const nome = document.getElementById('aluno-nome').value.trim();
    const cartao = document.getElementById('aluno-cartao').value.trim();
    const resultDiv = document.getElementById('cadastro-result');

    if (!nome || !cartao) {
        resultDiv.textContent = '⚠️ Preencha todos os campos!';
        resultDiv.className = 'alert error';
        resultDiv.classList.remove('hidden');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/alunos/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome: nome, cartao_id: parseInt(cartao) })
        });
        
        const data = await response.json();
        if (response.ok) {
            resultDiv.textContent = `✅ Aluno ${data.nome} cadastrado com sucesso!`;
            resultDiv.className = 'alert success';
            resultDiv.classList.remove('hidden');
            document.getElementById('aluno-nome').value = '';
            document.getElementById('aluno-cartao').value = '';
            carregarAlunos();
        } else {
            resultDiv.textContent = `❌ ${data.detail}`;
            resultDiv.className = 'alert error';
            resultDiv.classList.remove('hidden');
        }
    } catch (e) {
        resultDiv.textContent = '❌ Falha ao conectar com o servidor.';
        resultDiv.className = 'alert error';
        resultDiv.classList.remove('hidden');
    }
}

async function desativarAluno(id, nome) {
    if (!confirm(`Tem certeza que deseja desativar o aluno ${nome}? Ele será excluído logicamente das chamadas.`)) return;

    try {
        const response = await fetch(`${API_URL}/sgdi/alunos/${id}`, { method: 'DELETE' });
        const data = await response.json();
        if (response.ok) {
            showGlobalAlert(`✅ Aluno ${nome} desativado com sucesso.`, 'success');
            carregarAlunos();
        } else {
            showGlobalAlert(`❌ ${data.detail}`, 'error');
        }
    } catch (e) {
        showGlobalAlert("❌ Erro ao desativar aluno.", "error");
    }
}

function exportarRelatorioCSV() {
    window.open(`${API_URL}/alunos/relatorio/csv`, '_blank');
}

// ================= ABA 2: PROCESSO SELETIVO (SGDi) =================

async function carregarRanking() {
    const tbody = document.querySelector('#ranking-table tbody');
    try {
        const response = await fetch(`${API_URL}/sgdi/ranking`);
        if (response.ok) {
            const candidatos = await response.json();
            if (candidatos.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">Nenhum candidato pendente no ranking.</td></tr>`;
                return;
            }

            tbody.innerHTML = candidatos.map((c, i) => `
                <tr>
                    <td><strong>${i + 1}º</strong></td>
                    <td>${c.nome}</td>
                    <td>${c.cpf}</td>
                    <td>${c.email}</td>
                    <td><span class="font-bold">${c.pontuacao_socioeconomica}</span> pts</td>
                    <td>
                        <span class="badge badge-warning">${c.status}</span>
                    </td>
                    <td>
                        <button onclick="excluirCandidato(${c.id}, '${c.nome}')" class="btn-danger-sm">Excluir</button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-red">Erro ao carregar o ranking.</td></tr>`;
    }
}

async function sincronizarDrive() {
    const spinner = document.getElementById('sync-spinner');
    spinner.classList.remove('hidden');

    try {
        const response = await fetch(`${API_URL}/sgdi/sincronizar-drive`, { method: 'POST' });
        const data = await response.json();
        
        spinner.classList.add('hidden');
        if (response.ok) {
            showGlobalAlert(data.mensagem, 'success');
            carregarRanking();
        } else {
            showGlobalAlert(`❌ ${data.detail}`, 'error');
        }
    } catch (e) {
        spinner.classList.add('hidden');
        showGlobalAlert("❌ Erro ao sincronizar com o Google Drive.", "error");
    }
}

async function executarCorte() {
    const qtdInput = document.getElementById('corte-quantidade');
    const quantidade = parseInt(qtdInput.value.trim());

    if (!quantidade || quantidade < 1) {
        showGlobalAlert("⚠️ Insira uma quantidade válida maior que zero!", "error");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/sgdi/aprovar-corte`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quantidade: quantidade })
        });
        
        const data = await response.json();
        if (response.ok) {
            showGlobalAlert(data.mensagem, 'success');
            qtdInput.value = '';
            carregarRanking();
        } else {
            showGlobalAlert(`❌ ${data.detail}`, 'error');
        }
    } catch (e) {
        showGlobalAlert("❌ Erro ao executar linha de corte.", "error");
    }
}

async function efetivarMatricula() {
    const cpfInput = document.getElementById('matricula-cpf');
    const cpf = cpfInput.value.trim();

    if (!cpf) {
        showGlobalAlert("⚠️ Insira o CPF do candidato aprovado!", "error");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/sgdi/matricular`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cpf: cpf })
        });
        
        const data = await response.json();
        if (response.ok) {
            showGlobalAlert(data.mensagem, 'success');
            cpfInput.value = '';
            carregarRanking();
        } else {
            showGlobalAlert(`❌ ${data.detail}`, 'error');
        }
    } catch (e) {
        showGlobalAlert("❌ Erro ao matricular candidato.", "error");
    }
}

async function excluirCandidato(id, nome) {
    if (!confirm(`Tem certeza que deseja excluir permanentemente o candidato ${nome}? Esta ação apagará seus dados de processo seletivo fisicamente.`)) return;

    try {
        const response = await fetch(`${API_URL}/sgdi/candidatos/${id}`, { method: 'DELETE' });
        const data = await response.json();
        if (response.ok) {
            showGlobalAlert(`✅ Candidato ${nome} excluído.`, 'success');
            carregarRanking();
        } else {
            showGlobalAlert(`❌ ${data.detail}`, 'error');
        }
    } catch (e) {
        showGlobalAlert("❌ Erro ao excluir candidato.", "error");
    }
}

// ================= ABA 3: HISTÓRICO & AUDITORIA =================

async function carregarAuditoria() {
    const tbody = document.querySelector('#auditoria-table tbody');
    try {
        const response = await fetch(`${API_URL}/sgdi/historico-geral`);
        if (response.ok) {
            const logs = await response.json();
            if (logs.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">Nenhum registro de transação gravado.</td></tr>`;
                return;
            }

            tbody.innerHTML = logs.map(log => {
                const date = new Date(log.data_alteracao).toLocaleString();
                const statusAnt = log.status_anterior ? `<span class="badge badge-neutral">${log.status_anterior}</span>` : '<i>(Início)</i>';
                const statusNovo = `<span class="badge ${
                    log.status_novo === 'confirmado' ? 'badge-dentro' : 
                    log.status_novo === 'aprovado' ? 'badge-aprovado' : 
                    log.status_novo === 'excluido' ? 'badge-fora' : 'badge-neutral'
                }">${log.status_novo}</span>`;
                
                // Trata exibição se discente foi excluído físico
                const nomeDisplay = log.candidato_nome || '<i>(Excluído físico)</i>';
                const cpfDisplay = log.candidato_cpf || '-';

                return `
                    <tr>
                        <td>#${log.id}</td>
                        <td><strong>${nomeDisplay}</strong></td>
                        <td>${cpfDisplay}</td>
                        <td>${statusAnt}</td>
                        <td>${statusNovo}</td>
                        <td>${date}</td>
                        <td><small>${log.observacao || ''}</small></td>
                    </tr>
                `;
            }).join('');
        }
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-red">Erro ao carregar log de auditoria.</td></tr>`;
    }
}

// Atualizar o nome do arquivo selecionado no label
function atualizarNomeArquivoImportado() {
    const fileInput = document.getElementById('local-xlsx-file');
    const label = document.getElementById('label-xlsx-file');
    if (fileInput.files && fileInput.files[0]) {
        label.textContent = `📂 ${fileInput.files[0].name}`;
    } else {
        label.textContent = '📂 Selecionar Planilha';
    }
}

// Importar planilha localmente via API
async function importarPlanilhaLocal() {
    const fileInput = document.getElementById('local-xlsx-file');
    
    if (!fileInput.files || !fileInput.files[0]) {
        showGlobalAlert("⚠️ Por favor, selecione um arquivo de planilha (.xlsx) primeiro!", "error");
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch(`${API_URL}/sgdi/importar`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (response.ok) {
            showGlobalAlert(`✅ Planilha importada! Inseridos: ${data.inseridos}, Erros/Duplicados: ${data.erros}`, 'success');
            fileInput.value = '';
            atualizarNomeArquivoImportado();
            carregarRanking();
        } else {
            showGlobalAlert(`❌ ${data.detail || 'Erro ao processar planilha.'}`, 'error');
        }
    } catch (e) {
        showGlobalAlert("❌ Erro de conexão com o servidor ao importar planilha local.", "error");
    }
}

// ================= ABA 4: BUSCA AVANÇADA & RELATÓRIOS =================

// Cache local
let candidatosCache = [];
let questaoFiltroAtivo = null;
let candidatosQuestaoCache = [];

async function popularSeletoresBusca() {
    // Carregar candidatos
    const candSelect = document.getElementById('busca-candidato-select');
    try {
        const response = await fetch(`${API_URL}/sgdi/candidatos`);
        if (response.ok) {
            const candidatos = await response.json();
            candidatosCache = candidatos;
            candSelect.innerHTML = '<option value="">Selecione um candidato para ver o questionário...</option>' + 
                candidatos.map(c => `<option value="${c.id}">${c.nome} (CPF: ${c.cpf})</option>`).join('');
        }
    } catch (e) {
        console.error("Erro ao carregar candidatos para busca:", e);
    }

    // Carregar questões
    const questSelect = document.getElementById('busca-questao-select');
    const exportGrid = document.getElementById('exportar-questoes-grid');
    try {
        const response = await fetch(`${API_URL}/sgdi/questoes`);
        if (response.ok) {
            const questoes = await response.json();
            questSelect.innerHTML = '<option value="">Selecione uma questão do formulário...</option>' + 
                questoes.map(q => `<option value="${q.questao}">Q${q.pergunta_numero || '-'}: ${q.questao}</option>`).join('');
            
            if (exportGrid) {
                if (questoes.length === 0) {
                    exportGrid.innerHTML = '<div class="text-center text-muted" style="grid-column: 1 / -1;">Nenhuma questão disponível na base de dados.</div>';
                } else {
                    exportGrid.innerHTML = questoes.map(q => `
                        <label style="display: flex; align-items: flex-start; gap: 8px; cursor: pointer; padding: 6px; border-radius: 6px; background: white; border: 1px solid #f1f5f9; transition: all 0.2s; font-size: 0.85rem; line-height: 1.3;">
                            <input type="checkbox" name="export-questoes-checkbox" value="${q.pergunta_numero}" style="margin-top: 3px; cursor: pointer; width: auto; height: auto;">
                            <span style="color: #334155;"><strong>Q${q.pergunta_numero}:</strong> ${q.questao}</span>
                        </label>
                    `).join('');
                }
            }
        }
    } catch (e) {
        console.error("Erro ao carregar questões para busca:", e);
    }
}

function alternarTipoBusca() {
    const tipo = document.getElementById('busca-tipo-seletor').value;
    
    const grupoCandidato = document.getElementById('grupo-busca-candidato');
    const grupoQuestao = document.getElementById('grupo-busca-questao');
    const painelIndividual = document.getElementById('painel-resultados-individual');
    const painelQuestao = document.getElementById('painel-resultados-questao');

    if (tipo === 'individual') {
        grupoCandidato.classList.remove('hidden');
        grupoQuestao.classList.add('hidden');
        painelIndividual.classList.remove('hidden');
        painelQuestao.classList.add('hidden');
    } else {
        grupoCandidato.classList.add('hidden');
        grupoQuestao.classList.remove('hidden');
        painelIndividual.classList.add('hidden');
        painelQuestao.classList.remove('hidden');
    }
}

async function carregarRespostasCandidato() {
    const candId = document.getElementById('busca-candidato-select').value;
    const tbody = document.querySelector('#tabela-respostas-individual tbody');
    const scoreBadge = document.getElementById('detalhe-candidato-score');

    if (!candId) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">Selecione um candidato acima para carregar o questionário.</td></tr>`;
        scoreBadge.textContent = 'Score: -';
        return;
    }

    // Atualiza badge de score usando o cache
    const cand = candidatosCache.find(c => c.id == candId);
    if (cand) {
        scoreBadge.textContent = `Score: ${cand.pontuacao_socioeconomica.toFixed(1)} pts`;
    } else {
        scoreBadge.textContent = 'Score: -';
    }

    tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">Carregando questionário...</td></tr>`;

    try {
        const response = await fetch(`${API_URL}/sgdi/candidatos/${candId}/respostas`);
        if (response.ok) {
            const respostas = await response.json();
            if (respostas.length === 0) {
                tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">Nenhuma resposta encontrada para este candidato.</td></tr>`;
                return;
            }

            tbody.innerHTML = respostas.map(r => `
                <tr>
                    <td class="text-center font-bold">Q${r.pergunta_numero || '-'}</td>
                    <td>${r.questao}</td>
                    <td><span class="font-bold">${r.resposta || '<i>Sem resposta</i>'}</span></td>
                    <td><span class="badge badge-aprovado">${r.pontos.toFixed(1)} pts</span></td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center text-red">Erro ao carregar respostas do servidor.</td></tr>`;
        }
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center text-red">Erro de conexão ao carregar respostas.</td></tr>`;
    }
}

async function carregarEstatisticasQuestao() {
    const questao = document.getElementById('busca-questao-select').value;
    const cardsContainer = document.getElementById('estatisticas-questoes-cards');
    const tbody = document.querySelector('#tabela-respostas-questao tbody');
    
    // Reset filters
    questaoFiltroAtivo = null;
    document.getElementById('filtro-opcao-badge').classList.add('hidden');
    document.getElementById('btn-limpar-filtro-opcao').classList.add('hidden');

    if (!questao) {
        cardsContainer.innerHTML = '';
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Selecione uma questão acima para carregar a listagem.</td></tr>`;
        return;
    }

    cardsContainer.innerHTML = '<div class="text-center text-muted" style="width:100%;">Carregando estatísticas...</div>';
    tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Carregando discentes...</td></tr>`;

    try {
        // 1. Carregar estatísticas
        const responseStats = await fetch(`${API_URL}/sgdi/questoes/estatisticas?questao=${encodeURIComponent(questao)}`);
        if (responseStats.ok) {
            const stats = await responseStats.json();
            if (stats.length === 0) {
                cardsContainer.innerHTML = '<div class="text-center text-muted" style="width:100%;">Nenhuma estatística disponível para esta questão.</div>';
            } else {
                // Paleta harmoniosa de cores para os cards de estatísticas
                const colors = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#8b5cf6', '#ec4899'];
                
                cardsContainer.innerHTML = stats.map((s, idx) => {
                    const color = colors[idx % colors.length];
                    const safeQuestao = questao.replace(/'/g, "\\'").replace(/"/g, '&quot;');
                    const safeResposta = s.resposta.replace(/'/g, "\\'").replace(/"/g, '&quot;');
                    return `
                        <div class="card stat-card-interactive" onclick="filtrarPorOpcaoQuestao('${safeQuestao}', '${safeResposta}')" 
                             style="cursor: pointer; border-left: 5px solid ${color}; transition: all 0.2s ease; background: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 0;">
                            <div style="font-size: 14px; font-weight: 500; color: #4b5563; margin-bottom: 5px; word-break: break-word;">
                                ${s.resposta || '<i>Sem resposta</i>'}
                            </div>
                            <div style="display: flex; align-items: baseline; gap: 8px;">
                                <span style="font-size: 24px; font-weight: 700; color: #1f2937;">${s.percentual}%</span>
                                <span style="font-size: 14px; color: #6b7280;">(${s.quantidade} candidatos)</span>
                            </div>
                            <div style="width: 100%; background: #e5e7eb; height: 6px; border-radius: 3px; margin-top: 10px; overflow: hidden;">
                                <div style="width: ${s.percentual}%; background: ${color}; height: 100%; border-radius: 3px;"></div>
                            </div>
                        </div>
                    `;
                }).join('');
            }
        } else {
            cardsContainer.innerHTML = '<div class="text-center text-red" style="width:100%;">Erro ao carregar estatísticas.</div>';
        }

        // 2. Carregar todos discentes/respostas da questão
        const responseRespostas = await fetch(`${API_URL}/sgdi/questoes/respostas?questao=${encodeURIComponent(questao)}`);
        if (responseRespostas.ok) {
            const candidatos = await responseRespostas.json();
            candidatosQuestaoCache = candidatos;
            renderizarTabelaCandidatosQuestao(candidatos);
        } else {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center text-red">Erro ao carregar candidatos da questão.</td></tr>`;
        }
    } catch (e) {
        cardsContainer.innerHTML = '<div class="text-center text-red" style="width:100%;">Erro de conexão ao carregar dados.</div>';
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-red">Erro de conexão com o servidor.</td></tr>`;
    }
}

function renderizarTabelaCandidatosQuestao(candidatos) {
    const tbody = document.querySelector('#tabela-respostas-questao tbody');
    if (candidatos.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Nenhum candidato encontrado.</td></tr>`;
        return;
    }

    tbody.innerHTML = candidatos.map(c => `
        <tr>
            <td><strong>${c.nome}</strong></td>
            <td>${c.cpf}</td>
            <td>${c.email}</td>
            <td><span class="font-bold">${c.resposta || '<i>Sem resposta</i>'}</span></td>
            <td>
                <span class="badge ${
                    c.status === 'confirmado' ? 'badge-dentro' : 
                    c.status === 'aprovado' ? 'badge-aprovado' : 
                    c.status === 'pendente' ? 'badge-warning' : 'badge-fora'
                }">${c.status}</span>
            </td>
        </tr>
    `).join('');
}

function filtrarPorOpcaoQuestao(questao, resposta) {
    questaoFiltroAtivo = resposta;
    
    // Atualiza badge de filtro
    const badge = document.getElementById('filtro-opcao-badge');
    badge.textContent = `Filtrado por: ${resposta || 'Sem resposta'}`;
    badge.classList.remove('hidden');
    
    document.getElementById('btn-limpar-filtro-opcao').classList.remove('hidden');
    
    // Filtra no frontend
    const candidatosFiltrados = candidatosQuestaoCache.filter(c => c.resposta === resposta);
    renderizarTabelaCandidatosQuestao(candidatosFiltrados);
}

function limparFiltroOpcaoQuestao() {
    questaoFiltroAtivo = null;
    document.getElementById('filtro-opcao-badge').classList.add('hidden');
    document.getElementById('btn-limpar-filtro-opcao').classList.add('hidden');
    renderizarTabelaCandidatosQuestao(candidatosQuestaoCache);
}

// ================= OPÇÃO 4: EXPORTAR LISTA DE DADOS =================

function selecionarTodasQuestoesExport() {
    document.querySelectorAll('input[name="export-questoes-checkbox"]').forEach(cb => cb.checked = true);
}

function limparSelecaoQuestoesExport() {
    document.querySelectorAll('input[name="export-questoes-checkbox"]').forEach(cb => cb.checked = false);
}

async function exportarListaDadosWeb() {
    const checkboxes = document.querySelectorAll('input[name="export-questoes-checkbox"]:checked');
    if (checkboxes.length === 0) {
        showGlobalAlert("⚠️ Por favor, selecione pelo menos uma questão para exportação!", "error");
        return;
    }
    const questoesIds = Array.from(checkboxes).map(cb => parseInt(cb.value));
    
    try {
        const response = await fetch(`${API_URL}/sgdi/questoes/exportar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ questoes: questoesIds })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'ListaDeDados.xlsx';
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            showGlobalAlert("✅ Planilha ListaDeDados.xlsx gerada e salva na pasta 'Cartola mágica' com sucesso!", "success");
        } else {
            const err = await response.json();
            showGlobalAlert(`❌ Erro ao exportar dados: ${err.detail || 'Erro desconhecido'}`, 'error');
        }
    } catch (e) {
        showGlobalAlert("❌ Erro de conexão com o servidor ao exportar planilha.", "error");
    }
}

// ================= OPÇÃO 5: SINCRONIZAR PRESENÇAS DO LEITOR =================

async function sincronizarPresencasLeitorWeb() {
    const spinner = document.getElementById('sinc-leitor-spinner');
    const logsContainer = document.getElementById('sinc-leitor-logs-container');
    const logsDiv = document.getElementById('sinc-leitor-logs');
    const btn = document.getElementById('btn-sinc-leitor');

    spinner.classList.remove('hidden');
    logsContainer.classList.add('hidden');
    btn.disabled = true;

    try {
        const response = await fetch(`${API_URL}/sgdi/atualizar-presencas`, {
            method: 'POST'
        });
        const data = await response.json();
        spinner.classList.add('hidden');
        btn.disabled = false;
        
        if (response.ok) {
            showGlobalAlert(`✅ ${data.mensagem}`, 'success');
            
            // Exibir logs de sincronização
            if (data.logs && data.logs.length > 0) {
                logsDiv.innerHTML = data.logs.map(log => {
                    let text = log;
                    if (log.startsWith('💙')) {
                        text = `<span style="color: #89b4fa;">${log}</span>`;
                    } else if (log.startsWith('💚')) {
                        text = `<span style="color: #a6e3a1;">${log}</span>`;
                    } else if (log.startsWith('❤️')) {
                        text = `<span style="color: #f38ba8;">${log}</span>`;
                    } else if (log.startsWith('⚠️')) {
                        text = `<span style="color: #f9e2af;">${log}</span>`;
                    }
                    return text;
                }).join('\n');
                logsContainer.classList.remove('hidden');
            }
            
            // Recarrega lista de alunos para atualizar frequências e cartões gerados
            carregarAlunos();
        } else {
            showGlobalAlert(`❌ ${data.detail || 'Erro ao sincronizar presenças.'}`, 'error');
        }
    } catch (e) {
        spinner.classList.add('hidden');
        btn.disabled = false;
        showGlobalAlert("❌ Erro de conexão com o servidor ao sincronizar presenças.", "error");
    }
}

// ================= OPÇÃO 6: MODIFICAR PRESENÇAS / AJUSTE DE HORAS =================

async function modificarPresencaWeb() {
    const cartoesInput = document.getElementById('ajuste-cartoes').value.trim();
    const tipo = document.getElementById('ajuste-tipo').value;
    const horasInput = document.getElementById('ajuste-horas').value.trim();
    const resultContainer = document.getElementById('ajuste-resultado-container');
    const resultLogs = document.getElementById('ajuste-resultado-logs');

    if (!cartoesInput || !horasInput) {
        showGlobalAlert("⚠️ Por favor, preencha todos os campos do ajuste de horas!", "error");
        return;
    }

    const horas = parseFloat(horasInput);
    if (isNaN(horas)) {
        showGlobalAlert("⚠️ O valor de horas deve ser um número decimal!", "error");
        return;
    }

    // Processa a lista de cartões (se for 't', envia todos os cartões ativos, senão faz o split)
    let cartoes = [];
    if (cartoesInput.toLowerCase() === 't') {
        try {
            const res = await fetch(`${API_URL}/alunos/`);
            if (res.ok) {
                const alunos = await res.json();
                cartoes = alunos
                    .filter(a => a.status === 'ATIVADO' && a.cartao_id !== null && a.cartao_id !== 0)
                    .map(a => a.cartao_id);
            }
        } catch (e) {
            showGlobalAlert("❌ Erro ao buscar cartões dos alunos cadastrados.", "error");
            return;
        }
    } else {
        cartoes = cartoesInput.split(',')
            .map(c => parseInt(c.trim()))
            .filter(c => !isNaN(c));
    }

    if (cartoes.length === 0) {
        showGlobalAlert("⚠️ Nenhum número de cartão válido informado ou nenhum aluno ativo encontrado!", "error");
        return;
    }

    resultContainer.classList.add('hidden');

    try {
        const response = await fetch(`${API_URL}/sgdi/modificar-presenca`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cartoes: cartoes, horas: horas, tipo: tipo })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            let resText = `Ajuste concluído! Acertos: ${data.acertos.length}, Erros: ${data.erros.length}\n\n`;
            
            if (data.acertos.length > 0) {
                resText += `✅ MODIFICAÇÕES APLICADAS:\n`;
                data.acertos.forEach(a => {
                    const sinal = a.variacao >= 0 ? '+' : '';
                    resText += `• Aluno: ${a.nome} (Cartão: ${a.cartao})\n  Horas: ${a.hant.toFixed(1)}h / ${a.htotal0.toFixed(1)}h (${a.pant}%)  --->  ${a.hmod.toFixed(1)}h / ${a.htotal.toFixed(1)}h (${a.pmod}%)\n  Variação: ${sinal}${a.variacao.toFixed(1)}h\n\n`;
                });
            }
            
            if (data.erros.length > 0) {
                resText += `❌ ERROS (Cartões não encontrados ou desativados):\n`;
                resText += `• Cartões: ${data.erros.join(', ')}\n`;
            }
            
            resultLogs.innerHTML = resText;
            resultContainer.classList.remove('hidden');
            
            showGlobalAlert(`✅ Ajuste de horas executado com sucesso!`, 'success');
            
            // Limpa campos
            document.getElementById('ajuste-cartoes').value = '';
            document.getElementById('ajuste-horas').value = '';
            
            // Recarrega lista de alunos
            carregarAlunos();
        } else {
            showGlobalAlert(`❌ ${data.detail || 'Erro ao modificar presenças.'}`, 'error');
        }
    } catch (e) {
        showGlobalAlert("❌ Erro de conexão com o servidor ao modificar presenças.", "error");
    }
}

// Inicializar
inicializar();
