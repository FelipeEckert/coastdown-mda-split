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

### Implementado (2026-04-24 — sessão 2)
- [x] Bug: crash ValueError ao exibir par sem correção em page_3 (linha 771)
  - Causa: f0_corr/"N/A" (string) passava para :.4f sem isinstance check
  - Fix: mesmo padrão já usado para cv/energy nas linhas seguintes
- [x] Bug: par sem correção climática quebrava comparativo final (page_5)
  - Solução: tabela separada em duas seções com design e lógica distintos
  - Seção corrigida: checkboxes, F0 (N) / F2 (N/km/h²), cores de algoritmo
  - Seção referência: sem checkbox, fundo laranja, f'0 (N) / f'2 (N/m/s²), valores brutos
  - _is_corrected() bloqueia pares sem F0/F2 de entrar nas estatísticas e cálculo final
  - Batch actions (Selecionar Todos etc.) ignoram pares sem correção
  - Cabeçalhos refletem a mudança de unidade do processo de correção climática

### Pendente
- [ ] Redirecionamento automático para page_5 após executar algoritmo
- [ ] Contador "X pares candidatos com CV ≤ Y%" antes do botão executar
- [ ] Badge na sidebar mostrando algoritmo usado por último

---

## MELHORIAS DE UX — 2026-05-08

### Implementado
- [x] Alerta de data incompatível: CSV vs arquivo meteorológico
  - `carregar_dados_csv_robusto` já retornava `test_date`; `_process_new_test` agora captura como `csv_date`
  - Extrai `meteo_date` do primeiro registro de `weather_data`
  - Se diferença > 1 dia: armazena `date_mismatch_warning` no dict do teste
  - Exibido via `st.warning()` no topo da área de análise (persiste ao trocar de aba)
  - Tradução bilíngue com interpolação `{data_csv}` / `{data_meteo}`
  - `get_translator` atualizado para suportar `**kwargs` (`.format(**kwargs)`)
- [x] Seletor de tamanho de fonte na sidebar (Pequeno / Médio / Grande)
  - 13 px / 15 px / 17 px via CSS dinâmico injetado no `st.markdown`
  - Preferência salva em `st.session_state.font_size` (persiste na sessão)
  - Médio (15 px) já é leve aumento em relação ao padrão Streamlit (~14 px)
- [x] Botão ✕ de excluir teste corrigido (desalinhado / saindo do card)
  - Removido hack `<div style='padding-top:6px'>` que não fechava corretamente no DOM
  - Adicionada regra CSS `align-items: flex-start` no `stHorizontalBlock` da sidebar
- [x] Emoji 🤖 removido de `page_4_selecao_algoritmo.py` e `page_5_comparativo.py`

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
> **FASE 1 100% concluída e testada** (2026-04-21)
- [x] Sidebar com cards estilo MDA (ativo/completo/erro)
- [x] Criar/remover/alternar entre testes
- [x] Formulário com upload de CSV + meteo
- [x] Páginas 2-6 funcionando sem modificação
- [x] Interface em PT e EN
- [x] Zero regressão em funcionalidades existentes

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

---

## Retomada - Sincronizacao Flexivel CSV/Meteo (2026-05-13)

### Estado atual
- Implementacao parcial compila, mas ainda nao foi validada manualmente.
- Nao fazer commit/push antes dos testes com dados reais.

### Ja implementado
- Flag `sync_meteo_by_time_only` no estado do teste.
- Checkbox exibido quando ha divergencia de datas CSV/Meteo.
- Helper `find_closest_weather_record(..., time_only=False)`.
- Page 3 e page 4 usando o helper.
- Page 4 bloqueando execucao quando nao ha horario valido para sincronizar meteo.
- Traducoes PT/EN adicionadas/corrigidas.

### Testar antes de commit
- [ ] CSV e meteo com mesma data mantem sincronizacao por data + horario.
- [ ] CSV e meteo com datas diferentes e horarios compativeis funcionam no modo por horario.
- [ ] Checkbox aparece apenas quando necessario.
- [ ] Escolha fica salva no teste ativo.
- [ ] Page 3 e page 4 usam o mesmo comportamento.
- [ ] Correcao climatica nao sofreu regressao.
- [ ] Diff revisado antes do commit.

### Cuidados
- Nao modificar `core/`.
- Nao alterar logica F0/F2.
- Nao misturar com outras features.
- Se falhar, revisar primeiro `find_closest_weather_record()` e `sync_meteo_by_time_only`.

### Review final antes do merge (2026-05-14)
- [x] Modo normal preservado: sincronizacao por data + horario.
- [x] Modo flexivel preservado: sincronizacao somente por horario quando confirmado.
- [x] Tabela de auditoria exibida para arquivo meteo carregado, com horario CSV,
  horario meteo, diferenca, modo usado, temperatura, pressao e vento.
- [x] Alerta/destaque para vento > 3.0 m/s incluido na auditoria e nos coeficientes
  corrigidos.
- [x] Testes manuais realizados pelo usuario confirmaram a exibicao correta do vento
  e da sincronizacao meteorologica.
- [x] Antes do merge: revisar status, confirmar working tree limpo e confirmar que
  `core/` nao foi modificado.

---

## Review - Conformidade de Tempos com Tooltip (2026-05-14)

### Implementado
- [x] Tabela matriz de Conformidade de Tempos renderizada em HTML/CSS customizado.
- [x] Mantida a estrutura matriz: intervalo nas linhas, runs/passadas nas colunas e tempo em cada celula.
- [x] Tooltip por celula no hover, sem Plotly Table, sem JavaScript e sem selectbox.
- [x] Tooltip mostra valor medido, media do intervalo, desvio padrao, diferenca, desvio percentual e status.
- [x] Celulas nao conformes destacadas em vermelho escuro `#902626` com texto branco.
- [x] Scroll horizontal preservado para muitas runs; scroll vertical removido para mostrar todos os intervalos.
- [x] Tooltip abre para baixo nas primeiras linhas e para cima nas ultimas, evitando corte no topo/fim da tabela.
- [x] Primeira coluna destacada/fixa visualmente durante scroll horizontal.
- [x] Resumo por intervalo ajustado: removida coluna `Qtde. de Passadas`, incluido desvio padrao e numeros formatados com 2 casas decimais.
- [x] Label `Fonte das passadas` levemente aumentado para melhorar leitura.

### Validacao
- [x] `python -m py_compile pages/page_3_analise_pares.py`
- [x] `python -m py_compile translations.py`

### Escopo preservado
- [x] Sem alteracao em `core/`.
- [x] Sem alteracao em F0/F2.
- [x] Sem alteracao em sidebar/cards/modal.
- [x] Sem alteracao na sincronizacao meteorologica.
