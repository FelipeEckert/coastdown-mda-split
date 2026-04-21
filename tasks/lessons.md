\# Lições Aprendidas - Coastdown MDA



\## Template



\### Data: YYYY-MM-DD

\### Contexto:

\[O que estava fazendo]



\### Erro:

\[O que deu errado]



\### Solução:

\[Como foi corrigido]



\### Lição:

\[Regra para não repetir]



---



\## 2026-04-21 - Emojis em Software de Engenharia: Funcional vs Decorativo

\### Contexto:

Polimento de UX da interface Coastdown MDA — remoção de emojis para aspecto
mais profissional em software de engenharia.

\### Decisão:

Emojis decorativos (no título, botões de navegação, labels de status) foram
removidos. Emojis funcionais (📁 CSV, 📊 meteo, ⚙️ configurações) foram mantidos
porque ajudam o usuário a identificar rapidamente o tipo de conteúdo.

\### Regra:

Antes de remover um emoji, perguntar: "ele identifica um tipo de conteúdo ou
é puramente decorativo?" Se funcional, manter. Se decorativo, remover.
Em software de engenharia, preferir clareza textual a enfeites visuais.

---

\## 2026-04-21 - Navegação por st.tabs() em vez de Sidebar

\### Contexto:

Sidebar tinha botões de navegação para as páginas 2-6. Migrado para `st.tabs()`
na área principal, deixando sidebar apenas com gerenciamento de testes e status.

\### Limitação:

`st.tabs()` não permite seleção programática (sem `selected_tab` param).
Alternativa implementada: `st.caption()` como guia textual para o usuário.

\### Lição:

Para navegação entre seções em Streamlit, `st.tabs()` é mais limpo visualmente
que botões na sidebar, mas exige aceitar a limitação de não poder redirecionar
automaticamente. Compensar com hints textuais próximos ao ponto de origem.

---

\## 2026-04-21 - Gráficos em Sub-abas: Separar por Responsabilidade



\### Contexto:

Refatoração das sub-abas Gráficos e Simulação da page_3 (Análise de Pares).
Gráficos 2 e 3 (F×V e Desaceleração×V) estavam na sub-aba de Gráficos mas
só apareciam com par calculado, sem aviso claro ao usuário.



\### Decisão de design:

Sub-aba Gráficos = exclusivamente visualização das passadas brutas (V×T).
Sub-aba Simulação = tudo que depende de coeficientes (F×V, simulado×real).
Isso evita gráficos fantasmas que somem sem explicação.



\### Lição:

Se um elemento de UI depende de um pré-requisito (par calculado, massa, etc.),
ele pertence à seção que controla esse pré-requisito, não à seção de visualização
geral. Agrupe por responsabilidade, não por tipo de widget.



---



\## 2026-04-21 - Integração Numérica para Validação de Coeficientes



\### Contexto:

Simulação de desaceleração para comparar curva V(t) real vs modelada com os
coeficientes F0 e F2 calculados pelo coastdown.



\### Implementação:

Euler explícito com passo dt=0.05 s resolve `dV/dt = -(F0 + F2·V²) / m`.
V em m/s internamente (física correta), convertido para km/h na exibição.
Condição inicial = primeira amostra de velocidade da run real.
RMSE calculado por np.interp nos instantes reais (evita dependência de dt uniforme).



\### Por que Euler e não RK4?

Passo de 0.05 s é pequeno o suficiente para a dinâmica lenta de coastdown
(constante de tempo >> 1 s). Euler é mais simples, sem dependência de scipy.
Se precisar de maior precisão no futuro, trocar por scipy.integrate.solve_ivp.



\### Critérios de qualidade adotados:

RMSE < 1 km/h = boa aderência; 1-3 km/h = moderada (possível vento/inclinação);
> 3 km/h = baixa (verificar coeficientes e condições do ensaio).
Esses limiares são heurísticos — podem ser ajustados com dados reais de validação.



---



\## 2026-04-21 - Limpeza de Flags Devia ser Cirúrgica, não Global



\### Contexto:

Bug reportado: ao executar o algoritmo de Energia e depois o de Target (ou vice-versa),
os pares selecionados pelo primeiro algoritmo perdiam a cor de destaque (verde/azul).



\### Causa:

`run_algorithm()` em page_4 limpava AMBAS as flags (`selected_by_energy_algo` e
`selected_by_target_algo`) em TODOS os pares antes de marcar os novos resultados,
independente de qual algoritmo estava sendo executado.

```python
# ❌ Errado — apaga resultado do outro algoritmo
for pair_id in st.session_state.calculated_pairs:
    pair["selected_by_energy_algo"] = False
    pair["selected_by_target_algo"] = False
```



\### Fix:

Cada algoritmo limpa apenas sua própria flag, preservando a do outro.

```python
# ✅ Correto — cada um cuida do próprio estado
if algorithm_mode == "Menor Energia":
    for pair_id in st.session_state.calculated_pairs:
        pair["selected_by_energy_algo"] = False
elif algorithm_mode == "Proximidade ao Target":
    for pair_id in st.session_state.calculated_pairs:
        pair["selected_by_target_algo"] = False
```



\### Lição:

Ao limpar estado antes de uma operação, limpe apenas o escopo que a operação
vai reescrever. Limpeza global de flags interdependentes destrói contexto
que o usuário ainda precisa ver (no caso, a cor do algoritmo anterior).



---



\## 2026-04-21 - Schema Duplo em calculated_pairs (page_3 vs page_4)



\### Contexto:

Análise e robustez do sistema de seleção automática de pares.
page_3 (seleção manual) e page_4 (algoritmo automático) salvam pares no mesmo
dict `st.session_state.calculated_pairs`, mas com nomes de campos diferentes
para os mesmos valores.



\### Problema:

As 5 funções `_get_pair_f0/f2/cv_f0/cv_f2/energy()` tentavam múltiplas chaves
e retornavam `0.0` como fallback quando nenhuma era encontrada. Um par com F0
ausente aparecia como `0.0000 N` na tabela — valor falso, sem aviso ao usuário.
O cálculo de resultados finais usava esse zero silenciosamente.



\### Solução:

`normalize_pair(pair)` resolve as chaves de ambas as origens de uma vez,
adicionando `_f0`, `_f2`, `_cv_f0`, `_cv_f2`, `_energy` ao dict do par.
Retorna `None` (não `0.0`) quando o campo está ausente ou não-numérico.
O código de exibição trata `None` explicitamente: mostra "N/A" e emite
`st.warning` visível. Estatísticas e cálculo final excluem o par e avisam.



\### Mapeamento de campos (referência futura):

| Valor         | page_3 (manual)       | page_4 (algoritmo)      | canônico  |
|---------------|-----------------------|-------------------------|-----------|
| F0 corrigido  | f0_corr / f0corr_mean | mean_f0_corrected       | _f0       |
| F2 corrigido  | f2_corr / f2corr_mean | mean_f2_corrected       | _f2       |
| CV F0         | cv_f0_corr            | cv_f0_corrected / cv_f0 | _cv_f0    |
| CV F2         | cv_f2_corr            | cv_f2_corrected / cv_f2 | _cv_f2    |
| Energia       | energy                | mean_energy_corrected   | _energy   |

Atenção: cv_f0_corr e energy de page_3 podem ser a string "N/A" quando
correção climática não foi aplicada — normalize_pair trata isso corretamente
com o isinstance(v, (int, float)) antes de aceitar o valor.



\### Lição:

Quando dois fluxos diferentes escrevem no mesmo dict de estado com schemas
divergentes, crie UMA função de normalização que centraliza toda a resolução
de chaves. Nunca use `0.0` como fallback silencioso em valores de engenharia —
prefira `None` e trate explicitamente na exibição.



---



\## 2026-04-21 - HTML Customizado na Sidebar do Streamlit



\### Contexto:

Aplicação de melhorias visuais nos cards de teste da sidebar.
Substituição de `st.container(border=True)` por divs HTML+CSS para obter
estados visuais distintos (ativo/completo/incompleto) conforme paleta do CLAUDE.md.



\### Erro:

Cards inativos exibiam o HTML cru como texto na tela.
O template multiline do f-string produzia uma linha em branco onde `{badge_html}`
era string vazia. O parser CommonMark do Streamlit encerra um bloco HTML ao
encontrar linha em branco — tudo após ela virava texto puro.



\### Solução:

Substituir o template multiline por f-strings concatenadas em linha única,
sem nenhuma quebra de linha entre as tags. O HTML chega ao Streamlit como
uma string contínua, imune ao comportamento do parser.

```python
# ❌ Quebra quando badge_html = ""
st.markdown(f"""
<div class="card">
    <span>{name}</span>
    {badge_html}        ← linha em branco aqui encerra o bloco HTML
</div>
""", unsafe_allow_html=True)

# ✅ Correto
st.markdown(
    f'<div class="card"><span>{name}</span>{badge_html}</div>',
    unsafe_allow_html=True
)
```



\### Lição:

**Ao usar HTML customizado via `st.markdown(unsafe_allow_html=True)` no Streamlit:**
- Nunca usar templates multiline com variáveis que podem ser string vazia
- Qualquer linha em branco dentro do bloco HTML encerra o parsing HTML (regra CommonMark)
- Preferir f-strings concatenadas em linha única para HTML com partes condicionais

**Quando usar HTML customizado vs componentes nativos:**
- Usar HTML quando precisar de estados visuais complexos (bordas coloridas, badges, layout flexbox)
- Usar `st.container(border=True)`, `st.success`, `st.info` para conteúdo simples sem estilo específico
- CSS via `st.markdown` no topo da página funciona globalmente — definir classes reutilizáveis



---



\## Início do Projeto - 2024-03-11



\### Setup inicial concluído

\- CLAUDE.md criado com especificação completa

\- Workflow orchestration implementado

\- Estrutura de tasks/ configurada

\- Pronto para desenvolvimento com Claude Code

