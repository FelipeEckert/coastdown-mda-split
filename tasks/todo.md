# Coastdown MDA - Tarefas

## FASE 2 - Sistema de Seleção Automática de Pares

### Análise (2026-04-21)
- [x] Mapear algoritmos: Menor Energia e Proximidade ao Target (page_4_selecao_algoritmo.py)
- [x] Mapear campos dos pares (page_3 vs page_4 têm schemas diferentes)
- [x] Mapear fluxo de dados: page_4 → calculated_pairs → page_5
- [x] Identificar problema: helpers _get_pair_*() retornavam 0.0 silenciosamente em falha

### Implementado
- [x] normalize_pair() em page_5_comparativo.py — unifica schemas de page_3 e page_4
  - Remove 5 funções _get_pair_*() com fallback silencioso (0.0)
  - Retorna None explicitamente para campos ausentes
  - Exibe "N/A" na tabela em vez de valor falso
  - Aviso st.warning visível ao usuário quando campo está ausente
  - Estatísticas e cálculo final excluem pares inválidos e avisam
  - calculate_and_store_final_results() aborta com st.error se F0/F2 ausentes
- [x] Bug: cor de destaque sumia ao usar segundo algoritmo (page_4_selecao_algoritmo.py)
  - Causa: limpeza de AMBAS as flags ao executar qualquer algoritmo
  - Fix: cada algoritmo limpa apenas sua própria flag, preservando a do outro

### Pendente (aguardando aprovação)
- [ ] Redirecionamento automático para page_5 após executar algoritmo
- [ ] Contador "X pares candidatos com CV ≤ Y%" antes do botão executar
- [ ] Badge na sidebar mostrando algoritmo usado por último

## FASE 3 - Sub-abas de Análise de Pares (page_3)

### Implementado
- [x] Botão "🤖 Seleção por Algoritmo →" no topo da page_3 (acesso rápido à page_4)
- [x] Sub-aba Gráficos — migração matplotlib → Plotly
  - Único gráfico V×T interativo (zoom, hover, download PNG)
  - Runs do par ativo em destaque: IDA azul #4a9eff / VOLTA laranja #ff9800, linha grossa
  - Demais runs em cores suaves, linha fina, opacidade 60%
  - Legenda do par ativo acima do gráfico em texto colorido
  - Default inteligente: runs do par calculado ou 4 primeiras
  - Gráficos F(V) e Desaceleração×Velocidade removidos daqui → movidos para Simulação
  - Import matplotlib removido (não mais necessário)
- [x] Sub-aba Simulação — implementação completa
  - Fonte de coeficientes: par atual / selecionar par calculado / inserir manualmente
  - Simulação 1: Força Resistiva F = F0 + F2·V² com Plotly
    - Faixa de velocidade configurável
    - Slider de inspeção pontual com destaque no gráfico
    - Métricas de F0, F2 e F na velocidade selecionada
    - Contribuição % atrito constante vs aerodinâmica
  - Simulação 2: Desaceleração Simulada × Real com Plotly
    - Integração numérica Euler (dV/dt = -F/m, passo 0.05 s)
    - Curva real (azul) sobreposta à simulada (laranja tracejado)
    - RMSE e erro máximo por interpolação nos instantes reais
    - Feedback qualitativo: ✅ < 1 km/h / ⚠️ < 3 km/h / ❌ acima
  - Simulação disponível mesmo sem par calculado (modo manual)
- [x] plotly>=5.0.0 adicionado ao requirements.txt e instalado no venv

---

## FASE 1 - Sidebar Moderna com Multi-Teste

### Estratégia
- Flat session state = estado do teste ATIVO
- save/restore ao trocar de teste (sem modificar páginas 2-6)
- Formulário de novo teste na área principal (não modal, Streamlit < 1.31)

### Tarefas
- [x] Analisar estrutura atual do app.py
- [x] Mapear chaves de session state usadas pelas páginas 2-6
- [x] Planejar estratégia de compatibilidade (save/restore)
- [x] Atualizar translations.py com novas chaves i18n (16 chaves adicionadas)
- [x] Refatorar app.py:
  - [x] Constantes TEST_STATE_KEYS e TEST_DEFAULTS
  - [x] init_session_state() com estrutura multi-teste
  - [x] save_active_test_state() / load_test_state()
  - [x] activate_test() / delete_test()
  - [x] render_sidebar() com cards de teste
  - [x] render_test_card() com estado visual (live para ativo, snapshot para outros)
  - [x] render_navigation() com botões de páginas 2-6
  - [x] render_new_test_form() com upload integrado
  - [x] _process_new_test() - processa arquivos e cria teste
  - [x] render_welcome() - tela inicial sem testes
  - [x] render_test_analysis() - despacha para páginas 2-6
- [ ] Testar com browser (streamlit run app.py)
- [ ] Testar compatibilidade com páginas 2-6
- [ ] Testar i18n (PT/EN)
- [x] Upgrade Streamlit 1.28→1.55 + converter formulário para @st.dialog
- [x] Melhorias visuais da sidebar (cards, navegação, status)

### Critérios de Sucesso
- [ ] Sidebar com cards estilo MDA (ativo/completo/erro)
- [ ] Criar/remover/alternar entre testes
- [ ] Formulário com upload de CSV + meteo
- [ ] Páginas 2-6 funcionando sem modificação
- [ ] Interface em PT e EN
- [ ] Zero regressão em funcionalidades existentes

### Notas
- Streamlit >= 1.28: st.container(border=True) disponível
- Streamlit < 1.31: @st.dialog NÃO disponível → form inline na área principal
- Manter pages 2-6 intactas (já validadas)
- Todos textos com t() para tradução
- Seguir paleta de cores do CLAUDE.md

## Review - Melhorias Visuais da Sidebar (2026-04-21)

### O que foi feito:
- Cards de teste com HTML+CSS customizados (3 estados: ativo/completo/incompleto)
- Badge "● ATIVO" com pill estilo azul translúcido no card ativo
- Status CSV/Meteo com ícones coloridos (verde/vermelho/laranja)
- Navegação migrada para `st.tabs()` na área principal (sidebar só mostra status)
- Sub-abas de análise de pares via `st.tabs()` aninhado (Cálculos / Gráficos / Simulação)
- Status resumido com HTML inline compacto na sidebar
- Adicionada chave i18n `page_algorithm_selection` que estava faltando

### Bug corrigido:
- Cards inativos exibiam HTML cru — causa: linha em branco no template multiline
  quebrava o bloco HTML no parser CommonMark do Streamlit (ver lessons.md)

## Review - Polimento de UX (2026-04-21)

### O que foi feito:
- Botão excluir (✕) movido para dentro da linha do card via `st.columns([5,1])`
- Fonte das abas aumentada: `font-size: 0.95rem` via CSS
- Espaço acima do título reduzido: `padding-top: 1rem` no block-container, `0.5rem` na sidebar
- Emojis removidos de: título sidebar, botão novo teste, título área principal, título welcome,
  label de status, contador de pares selecionados, sub-abas da page_3
- Emojis mantidos onde têm função visual: 📁 CSV upload, 📊 meteo upload, ⚙️ configurações

### Próximos passos:
- Testar visualmente no browser com múltiplos testes
- Testar compatibilidade com páginas 2-6
- Testar i18n (PT/EN)
