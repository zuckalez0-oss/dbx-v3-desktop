# DBX-V3 Desktop - Documentação Técnica Módulo por Módulo

## 1) Contexto do projeto

O DBX-V3 Desktop é uma aplicação PyQt5 voltada para operação industrial (plasma, laser e guilhotina), com foco em:

- cadastro e importação de peças;
- cálculo de aproveitamento de chapa (nesting);
- geração de saídas operacionais (PDF e DXF);
- exportação de orçamento em planilha Excel (layout novo e legado);
- histórico local de projetos;
- autenticação com Supabase para controle de acesso.

Arquiteturalmente, o projeto está dividido em:

- Camada Desktop/UI: pasta desktop_app;
- Camada de domínio compartilhado: módulos na raiz (cálculo, DXF, PDF, histórico, paths, código de peça);
- Camada de autenticação: desktop_app/auth;
- Build/distribuição: arquivos de script e spec de empacotamento.


## 2) Fluxo de execução (alto nível)

1. Entrada da aplicação por main.py (wrapper) ou desktop_app/__main__.py.
2. A classe DesktopAppController gerencia autenticação e ciclo de janela.
3. AuthService tenta restaurar sessão local (DPAPI) ou abre LoginDialog.
4. MainWindow centraliza operações de cadastro/importação/processamento/exportação.
5. ProcessThread gera PDF/DXF em background.
6. NestingDialog + CalculationThread executam cálculo de corte por espessura.
7. HistoryManager salva/carrega projetos concluídos em JSON local.


## 3) Mapa de módulos (arquivo por arquivo)

## 3.1 Módulos da raiz (domínio e infraestrutura compartilhada)

### main.py

Responsabilidade:
- Wrapper de compatibilidade para execução da aplicação desktop.

Pontos-chave:
- Reexporta MainWindow e main a partir de desktop_app.main_window.
- Mantém entrypoint antigo sem quebrar atalhos/scripts existentes.


### app_paths.py

Responsabilidade:
- Resolver caminhos de recursos e dados de usuário entre ambiente dev e executável empacotado.

Funções principais:
- _resource_roots: detecta raízes de recurso (incluindo PyInstaller via _MEIPASS).
- find_resource_path / get_resource_path: localiza assets/arquivos embarcados.
- get_app_data_dir: define diretório gravável de dados em AppData.
- get_log_file_path: cria caminho de log em pasta local da aplicação.
- ensure_user_file: garante arquivo de usuário local, copiando de recurso padrão quando necessário.

Importância para manutenção:
- É o módulo base para persistência local e compatibilidade entre ambiente local e build.
- Mudanças de localização de arquivos devem começar aqui.


### code_manager.py

Responsabilidade:
- Gerar código único de peça e persistir em base Excel local (codigo_database.xlsx).

Classe principal:
- CodeGenerator

Comportamento:
- Lê prefixo customizado da planilha (célula D2).
- Calcula próximo código sequencial não utilizado.
- Persiste código com timestamp e projeto.

Riscos/manutenção:
- Dependência de arquivo Excel aberto por outro processo pode gerar PermissionError.
- Alterações de layout da planilha exigem ajuste de nomes de coluna e célula de prefixo.


### calculo_cortes.py

Responsabilidade:
- Núcleo de nesting e análise de sobras/perdas.

Funções principais:
- orquestrar_planos_de_corte: organiza estratégia e tentativa de alocação.
- calcular_plano_de_corte_em_bins: executa packing com múltiplos algoritmos (rectpack) e escolhe melhor solução.
- encontrar_sobras: detecta sobras por varredura e classifica reaproveitamento.
- _merge_scraps: consolida retângulos adjacentes de sobra.

Comportamento técnico:
- Ordena peças por área.
- Faz tentativa progressiva de quantidade de chapas.
- Suporta formas especiais (pares de triângulo/trapézio) e cálculo de peso/sucata.

Riscos/manutenção:
- É módulo crítico de performance e resultado financeiro.
- Qualquer ajuste de regra de offset/margem/sobra deve ser validado com casos reais.


### dxf_engine.py

Responsabilidade:
- Gerar DXF de peças e ler bounding box de DXF importado.

Funções principais:
- prepare_and_validate_dxf_data: normaliza e valida payload de entrada.
- create_dxf_drawing: desenha contorno e furos em layers DXF.
- get_dxf_bounding_box: calcula largura/altura do conteúdo de DXF externo.

Riscos/manutenção:
- Mudança de convenções de campo (nome, forma, dimensões, furos) impacta importação/exportação.
- Tratamento de formas deve ficar alinhado com UI e exportadores.


### history_manager.py

Responsabilidade:
- Persistir e consultar histórico de projetos (project_history.json).

Classe principal:
- HistoryManager

Funções principais:
- get_projects, get_project_data, save_project, delete_project.

Riscos/manutenção:
- Estrutura JSON de peças deve permanecer compatível com MainWindow e HistoryDialog.


### pdf_generator.py

Responsabilidade:
- Renderização de desenhos técnicos em PDF com cotas e informações de peça.

Comportamento:
- Desenha formas geométricas (retângulo, círculo, triângulo, trapézio).
- Desenha cotas gerais e de furação.
- Pode desenhar entidades vindas de DXF em canvas ReportLab.

Riscos/manutenção:
- Alterações visuais/escala exigem teste em peças de geometrias variadas.
- A legibilidade das cotas depende de proporção e espaçamento.


## 3.2 Camada desktop_app (UI e orquestração)

### desktop_app/__main__.py

Responsabilidade:
- Entrypoint do pacote desktop_app.

Comportamento:
- Ajusta sys.path quando executado fora do contexto de pacote e chama main.


### desktop_app/__init__.py

Responsabilidade:
- Exportar API do pacote (MainWindow e main).


### desktop_app/app_controller.py

Responsabilidade:
- Orquestrar ciclo de autenticação e abertura da aplicação.

Classe principal:
- DesktopAppController

Fluxo:
- Carrega configuração de auth.
- Tenta restore de sessão.
- Abre LoginDialog quando necessário.
- Inicializa MainWindow e trata logout.

Riscos/manutenção:
- Qualquer mudança de fluxo de login/logout deve passar por este módulo.


### desktop_app/main_window.py

Responsabilidade:
- Janela principal e núcleo de funcionalidades de negócio da aplicação desktop.

Classe principal:
- MainWindow

Blocos funcionais relevantes:
- Inicialização de UI e estilo global;
- Gestão de sessão/projeto;
- Cadastro manual de peça e furos;
- Importação por planilha e por DXF;
- Importação automática por JSON;
- Exportação de orçamento para planilha (novo + legado), incluindo perdas auxiliares;
- Disparo de processamento em thread (PDF/DXF);
- Acesso a histórico, nesting, arquivos de suporte e ajuda.

Observação de manutenção:
- Arquivo grande e centralizador (alto acoplamento).
- Evoluções grandes devem, preferencialmente, extrair serviços específicos para reduzir risco de regressão.


### desktop_app/history_dialog.py

Responsabilidade:
- Diálogo de histórico para visualizar, carregar e excluir projetos salvos.

Classe principal:
- HistoryDialog

Integração:
- Consome HistoryManager para listar projetos e popular tabela de peças.


### desktop_app/nesting_dialog.py

Responsabilidade:
- Interface e processamento assíncrono para cálculo de aproveitamento.

Classes/funções principais:
- CalculationThread: prepara peças por espessura e chama orquestrar_planos_de_corte.
- CuttingPlanWidget: desenha visualização gráfica de chapas, peças e sobras.
- PlanVisualizationDialog: exibe planos calculados.
- NestingDialog: coleta parâmetros, dispara cálculo e organiza resultados.

Regras relevantes:
- Ajuste dinâmico de offset/margem por espessura;
- Tratamento específico para método guilhotina.


### desktop_app/processing.py

Responsabilidade:
- Processamento em background para geração de PDF e DXF.

Classe principal:
- ProcessThread

Comportamento:
- Agrupa por espessura para gerar PDFs por lote.
- Gera ZIP de DXFs por item.
- Emite sinais de progresso/status para a UI.


## 3.3 Camada de autenticação (desktop_app/auth)

### desktop_app/auth/__init__.py

Responsabilidade:
- Expor interface pública da camada de autenticação.


### desktop_app/auth/errors.py

Responsabilidade:
- Definir hierarquia de exceções de autenticação.

Exceções:
- AuthError;
- AuthConfigurationError;
- AuthSetupRequiredError;
- AuthSessionError;
- AuthAccessDeniedError.


### desktop_app/auth/config.py

Responsabilidade:
- Carregar e validar configuração de autenticação (arquivo + variáveis de ambiente).

Pontos-chave:
- Usa diretório local de app (AppData) para supabase_config.json.
- Gera arquivo de exemplo se não existir.
- Valida placeholders e formato de URL.
- Combina parâmetros de autorização de perfil/status.

Campos importantes:
- supabase_url, supabase_anon_key;
- profiles_table, profile_lookup_column;
- require_dbx_access_claim, require_profile;
- desktop_access_column, status_column, allowed_statuses.


### desktop_app/auth/client.py

Responsabilidade:
- Criar client do Supabase de forma isolada e validada.

Ponto-chave:
- Falha explicitamente com AuthConfigurationError se biblioteca supabase não estiver disponível.


### desktop_app/auth/models.py

Responsabilidade:
- Definir modelos de dados de sessão e contexto autenticado.

Modelos:
- SessionTokens;
- AuthenticatedUserContext.


### desktop_app/auth/session_store.py

Responsabilidade:
- Persistência local segura da sessão usando DPAPI (Windows).

Classe principal:
- SessionStore

Comportamento:
- Salva e lê sessão criptografada em session.bin;
- Limpa sessão no logout/erro;
- Requer pywin32 para CryptProtectData/CryptUnprotectData.


### desktop_app/auth/service.py

Responsabilidade:
- Regras de autenticação/autorização e ciclo de sessão com Supabase.

Classe principal:
- AuthService

Funções de negócio:
- sign_in, restore_session, sign_out, request_password_reset.

Regras de autorização:
- Pode exigir claim dbx_access no app_metadata;
- Pode validar perfil em tabela profiles;
- Pode validar status permitido e bloqueio desktop_access.


### desktop_app/auth/login_dialog.py

Responsabilidade:
- Tela de login e recuperação de senha.

Classe principal:
- LoginDialog

Comportamento:
- Recebe credenciais e chama AuthService;
- Exibe mensagens amigáveis para erro de sessão e acesso negado.


## 3.4 Arquivos operacionais e de build

### main.spec

Responsabilidade:
- Configuração de build PyInstaller (empacotamento executável).


### build_desktop.ps1

Responsabilidade:
- Script principal de build/distribuição para Windows.


### start_desktop.bat

Responsabilidade:
- Atalho/script de execução local para facilitar operação.


### requirements.txt e desktop_app/requirements.txt

Responsabilidade:
- Dependências Python de execução e build.

Observação:
- Manter sincronia entre bibliotecas necessárias para execução local e ambiente de empacotamento.


### supabase_config.example.json e SUPABASE_AUTH_SETUP.md

Responsabilidade:
- Guia e modelo de configuração de autenticação Supabase.


### PROD_RELEASE_CHECKLIST.md

Responsabilidade:
- Checklist de release operacional do produto desktop.


## 4) Dependências críticas

- PyQt5: interface principal e diálogos;
- pandas/openpyxl: leitura e escrita de planilhas;
- rectpack: algoritmo de nesting;
- ezdxf: importação e geração de DXF;
- reportlab: geração de PDF;
- supabase: autenticação e acesso a dados de perfil;
- pywin32: criptografia local de sessão no Windows.


## 5) Guia de manutenção por tipo de demanda

### Nova regra de negócio de peça (campos, validação, forma)

Módulos-alvo:
- desktop_app/main_window.py;
- dxf_engine.py;
- pdf_generator.py;
- calculo_cortes.py.

Checklist:
- atualizar coleta/normalização de campos;
- atualizar exportadores (PDF/DXF/Excel);
- validar impacto no nesting e no histórico.


### Ajustes de layout de orçamento Excel

Módulos-alvo:
- desktop_app/main_window.py (rotinas de exportação e mapeamento de colunas);
- templates de planilha usados na operação.

Checklist:
- validar nomes de cabeçalho e aliases;
- testar layout novo e legado;
- validar fórmulas e perdas auxiliares.


### Mudança de autenticação/autorização

Módulos-alvo:
- desktop_app/auth/config.py;
- desktop_app/auth/service.py;
- desktop_app/app_controller.py;
- desktop_app/auth/login_dialog.py.

Checklist:
- validar configuração carregada de arquivo e env;
- validar restore de sessão e logout;
- validar cenários de acesso negado (claim/perfil/status).


### Ajuste de performance de cálculo de corte

Módulos-alvo:
- calculo_cortes.py;
- desktop_app/nesting_dialog.py.

Checklist:
- medir tempo por espessura;
- comparar resultado de aproveitamento antes/depois;
- validar classificação de sobras reaproveitáveis.


## 6) Pontos de atenção (dívida técnica e risco)

- MainWindow concentra muitas responsabilidades e impacta testabilidade.
- Forte dependência de planilhas e nomes de coluna, suscetível a quebra por alteração de template.
- Execução em Windows com DPAPI exige pywin32 instalado no ambiente final.
- Cálculo de nesting é sensível a ajustes pequenos (offset/margem e heurísticas).


## 7) Sugestão de evolução da documentação

Para manter esta documentação viva:

- atualizar este arquivo a cada mudança estrutural de módulo;
- registrar decisões arquiteturais em docs com data e motivo;
- incluir exemplos de payload de importação JSON/DXF/Excel;
- criar seção de testes manuais mínimos por fluxo (login, importação, exportação, nesting).
