# Lições Aprendidas - Coastdown MDA



## Template



### Data: YYYY-MM-DD

### Contexto:

[O que estava fazendo]



### Erro:

[O que deu errado]



### Solução:

[Como foi corrigido]



### Lição:

[Regra para não repetir]



---



## 2026-04-24 - Correção Climática Muda Unidades, Não Só Valores

### Contexto:
Separação visual entre pares com e sem correção climática na tabela comparativo final.

### Decisão:
Os cabeçalhos das duas seções usam notações diferentes:
- Seção corrigida: F0 (N) e F2 (N/km/h²) — letras maiúsculas, unidade km/h
- Seção referência: f'0 (N) e f'2 (N/m/s²) — letras minúsculas com apóstrofe, unidade m/s

### Lição:
A correção climática não é apenas um ajuste de magnitude — ela também converte as
unidades de F2 de N/m/s² para N/km/h². Cabeçalhos de tabela devem refletir isso
explicitamente para que o usuário não compare valores entre as duas seções achando
que estão na mesma escala.

---



## 2026-04-24 - Seção de Referência para Dados Incompletos

### Contexto:
Pares calculados sem correção climática causavam crash (ValueError) e confusão
ao serem adicionados ao comparativo final, onde o código esperava valores numéricos.

### Solução adotada:
Separar a tabela em duas seções (corrigidos / referência) em vez de bloquear
a adição ou mostrar mensagens de erro inline. A seção de referência:
- Exibe os valores brutos (f0_mean, f2_mean) em vez de N/A
- Usa fundo laranja para sinalizar status sem precisar de texto extra
- Remove o checkbox — impossível selecionar acidentalmente para cálculo
- _is_corrected() centraliza a lógica de separação; batch actions respeitam isso

### Por que não bloquear a adição ao comparativo?
O usuário pode querer ver o par sem correção lado a lado com os corrigidos para
decidir se vale a pena retestar com condições climáticas registradas.

### Lição:
Quando um objeto pode existir em estado "incompleto mas útil para visualização",
prefira seção separada a mensagem de erro ou bloqueio. O usuário entende o contexto
pela posição visual do dado; erros inline interrompem o fluxo de análise.

---



## 2026-04-21 - Emojis em Software de Engenharia: Funcional vs Decorativo

### Contexto:

Polimento de UX da interface Coastdown MDA — remoção de emojis para aspecto
mais profissional em software de engenharia.

### Decisão:

Emojis decorativos (no título, botões de navegação, labels de status) foram
removidos. Emojis funcionais (📁 CSV, 📊 meteo, ⚙️ configurações) foram mantidos
porque ajudam o usuário a identificar rapidamente o tipo de conteúdo.

### Regra:

Antes de remover um emoji, perguntar: "ele identifica um tipo de conteúdo ou
é puramente decorativo?" Se funcional, manter. Se decorativo, remover.
Em software de engenharia, preferir clareza textual a enfeites visuais.

---

## 2026-04-21 - Navegação por st.tabs() em vez de Sidebar

### Contexto:

Sidebar tinha botões de navegação para as páginas 2-6. Migrado para `st.tabs()`
na área principal, deixando sidebar apenas com gerenciamento de testes e status.

### Limitação:

`st.tabs()` não permite seleção programática (sem `selected_tab` param).
Alternativa implementada: `st.caption()` como guia textual para o usuário.

### Lição:

Para navegação entre seções em Streamlit, `st.tabs()` é mais limpo visualmente
que botões na sidebar, mas exige aceitar a limitação de não poder redirecionar
automaticamente. Compensar com hints textuais próximos ao ponto de origem.

---

## 2026-04-21 - Gráficos em Sub-abas: Separar por Responsabilidade



### Contexto:

Refatoração das sub-abas Gráficos e Simulação da page_3 (Análise de Pares).
Gráficos 2 e 3 (F×V e Desaceleração×V) estavam na sub-aba de Gráficos mas
só apareciam com par calculado, sem aviso claro ao usuário.



### Decisão de design:

Sub-aba Gráficos = exclusivamente visualização das passadas brutas (V×T).
Sub-aba Simulação = tudo que depende de coeficientes (F×V, simulado×real).
Isso evita gráficos fantasmas que somem sem explicação.



### Lição:

Se um elemento de UI depende de um pré-requisito (par calculado, massa, etc.),
ele pertence à seção que controla esse pré-requisito, não à seção de visualização
geral. Agrupe por responsabilidade, não por tipo de widget.



---



## 2026-04-21 - Integração Numérica para Validação de Coeficientes



### Contexto:

Simulação de desaceleração para comparar curva V(t) real vs modelada com os
coeficientes F0 e F2 calculados pelo coastdown.



### Implementação:

Euler explícito com passo dt=0.05 s resolve `dV/dt = -(F0 + F2·V²) / m`.
V em m/s internamente (física correta), convertido para km/h na exibição.
Condição inicial = primeira amostra de velocidade da run real.
RMSE calculado por np.interp nos instantes reais (evita dependência de dt uniforme).



### Por que Euler e não RK4?

Passo de 0.05 s é pequeno o suficiente para a dinâmica lenta de coastdown
(constante de tempo >> 1 s). Euler é mais simples, sem dependência de scipy.
Se precisar de maior precisão no futuro, trocar por scipy.integrate.solve_ivp.



### Critérios de qualidade adotados:

RMSE < 1 km/h = boa aderência; 1-3 km/h = moderada (possível vento/inclinação);
> 3 km/h = baixa (verificar coeficientes e condições do ensaio).
Esses limiares são heurísticos — podem ser ajustados com dados reais de validação.



---



## 2026-04-21 - Limpeza de Flags Devia ser Cirúrgica, não Global



### Contexto:

Bug reportado: ao executar o algoritmo de Energia e depois o de Target (ou vice-versa),
os pares selecionados pelo primeiro algoritmo perdiam a cor de destaque (verde/azul).



### Causa:

`run_algorithm()` em page_4 limpava AMBAS as flags (`selected_by_energy_algo` e
`selected_by_target_algo`) em TODOS os pares antes de marcar os novos resultados,
independente de qual algoritmo estava sendo executado.

```python
# ❌ Errado — apaga resultado do outro algoritmo
for pair_id in st.session_state.calculated_pairs:
    pair["selected_by_energy_algo"] = False
    pair["selected_by_target_algo"] = False
```



### Fix:

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



### Lição:

Ao limpar estado antes de uma operação, limpe apenas o escopo que a operação
vai reescrever. Limpeza global de flags interdependentes destrói contexto
que o usuário ainda precisa ver (no caso, a cor do algoritmo anterior).



---



## 2026-04-21 - Schema Duplo em calculated_pairs (page_3 vs page_4)



### Contexto:

Análise e robustez do sistema de seleção automática de pares.
page_3 (seleção manual) e page_4 (algoritmo automático) salvam pares no mesmo
dict `st.session_state.calculated_pairs`, mas com nomes de campos diferentes
para os mesmos valores.



### Problema:

As 5 funções `_get_pair_f0/f2/cv_f0/cv_f2/energy()` tentavam múltiplas chaves
e retornavam `0.0` como fallback quando nenhuma era encontrada. Um par com F0
ausente aparecia como `0.0000 N` na tabela — valor falso, sem aviso ao usuário.
O cálculo de resultados finais usava esse zero silenciosamente.



### Solução:

`normalize_pair(pair)` resolve as chaves de ambas as origens de uma vez,
adicionando `_f0`, `_f2`, `_cv_f0`, `_cv_f2`, `_energy` ao dict do par.
Retorna `None` (não `0.0`) quando o campo está ausente ou não-numérico.
O código de exibição trata `None` explicitamente: mostra "N/A" e emite
`st.warning` visível. Estatísticas e cálculo final excluem o par e avisam.



### Mapeamento de campos (referência futura):

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



### Lição:

Quando dois fluxos diferentes escrevem no mesmo dict de estado com schemas
divergentes, crie UMA função de normalização que centraliza toda a resolução
de chaves. Nunca use `0.0` como fallback silencioso em valores de engenharia —
prefira `None` e trate explicitamente na exibição.



---



## 2026-04-21 - HTML Customizado na Sidebar do Streamlit



### Contexto:

Aplicação de melhorias visuais nos cards de teste da sidebar.
Substituição de `st.container(border=True)` por divs HTML+CSS para obter
estados visuais distintos (ativo/completo/incompleto) conforme paleta do CLAUDE.md.



### Erro:

Cards inativos exibiam o HTML cru como texto na tela.
O template multiline do f-string produzia uma linha em branco onde `{badge_html}`
era string vazia. O parser CommonMark do Streamlit encerra um bloco HTML ao
encontrar linha em branco — tudo após ela virava texto puro.



### Solução:

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



### Lição:

**Ao usar HTML customizado via `st.markdown(unsafe_allow_html=True)` no Streamlit:**
- Nunca usar templates multiline com variáveis que podem ser string vazia
- Qualquer linha em branco dentro do bloco HTML encerra o parsing HTML (regra CommonMark)
- Preferir f-strings concatenadas em linha única para HTML com partes condicionais

**Quando usar HTML customizado vs componentes nativos:**
- Usar HTML quando precisar de estados visuais complexos (bordas coloridas, badges, layout flexbox)
- Usar `st.container(border=True)`, `st.success`, `st.info` para conteúdo simples sem estilo específico
- CSS via `st.markdown` no topo da página funciona globalmente — definir classes reutilizáveis



---



## 2026-05-08 - Alerta de Data: Dado Já Estava Disponível, Faltava Usá-lo

### Contexto:
Implementação de alerta quando CSV de coastdown e arquivo meteorológico têm datas diferentes.

### Observação:
`carregar_dados_csv_robusto` já retornava `test_date` como terceiro elemento da tupla.
Em `_process_new_test` ele era descartado com `_test_date`. O dado necessário já existia,
só precisava ser capturado e comparado.

### Solução:
Renomear `_test_date` → `csv_date`, extrair `meteo_date = weather_data[0]['timestamp'].date()`,
comparar com `abs((meteo_date - csv_date).days) > 1`. Armazenar mensagem no dict do teste
(chave `date_mismatch_warning`) para exibir via `st.warning` na área de análise.

### Por que armazenar no dict do teste (não mostrar inline no dialog)?
O `@st.dialog` fecha com `st.rerun()` ao criar o teste. Qualquer `st.warning` dentro do
spinner não sobrevive ao rerun. Armazenar no estado do teste garante que o alerta persista
e reapareça ao trocar de aba.

### Lição:
Antes de buscar o dado em outro lugar, verificar se ele já é retornado por alguma função
existente e apenas descartado. Em `_process_new_test` havia vários `_var` com underline
que sinalizavam exatamente isso.

---

## 2026-05-08 - get_translator Precisava de Suporte a Interpolação

### Contexto:
Adição de chaves de tradução com placeholders (`{data_csv}`, `{data_meteo}`).

### Problema:
`get_translator` retornava `t(key: str) -> str` sem suporte a kwargs.
O CLAUDE.md já documentava o padrão `t("key", percent=15.2)` mas nunca foi implementado.

### Solução:
```python
def t(key: str, **kwargs) -> str:
    text = TRANSLATIONS[key].get(lang, ...)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text
```
O `try/except` garante que chaves sem placeholders não quebrem se kwargs forem passados.

### Lição:
Quando o CLAUDE.md especifica um padrão de uso, implementar imediatamente — não deixar
para quando o primeiro caso de uso aparecer. Dívida de spec cria surpresa desnecessária.

---

## 2026-05-08 - Div Aberto/Fechado Não Funciona como Wrapper em Streamlit

### Contexto:
Tentativa de ajustar alinhamento do botão ✕ (excluir teste) na sidebar.

### Erro anterior:
```python
st.markdown("<div style='padding-top:6px'>", unsafe_allow_html=True)
st.button("✕", ...)
st.markdown("</div>", unsafe_allow_html=True)
```
Cada `st.markdown` é um elemento Streamlit independente. O `<div>` de abertura e o de
fechamento não envolvem o botão — ficam como elementos irmãos no DOM, não pai/filho.
O resultado visual é o botão fora do alinhamento esperado.

### Solução:
Remover o hack e usar CSS estrutural:
```css
section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
    align-items: flex-start !important;
}
```
Isso ancora todas as colunas ao topo dentro dos `st.columns()` da sidebar,
sem precisar de wrappers manuais.

### Lição:
Não tentar simular wrappers HTML abrindo/fechando divs em chamadas separadas de
`st.markdown`. Para ajustes de alinhamento, usar CSS no seletor do container pai.
O elemento correto a targetar é `[data-testid="stHorizontalBlock"]` para colunas.

---

## 2026-05-11 - Sidebar no Streamlit: Estrutura Nativa Primeiro, CSS Escopado Depois

### Contexto:
Rodada de correções na sidebar envolvendo:
- seletor de tamanho de fonte;
- layout dos cards de teste;
- botão `X` de remoção;
- confirmação de remoção em modal/pop-up;
- recuperação do destaque azul do card ativo.

### Erro:
Os cards da sidebar quebravam visualmente:
- `X` desalinhado;
- confirmação de remoção aparecendo dentro da sidebar;
- `CSV/Meteo` escapando ou sendo cortado;
- muito espaço vertical vazio;
- mistura de HTML/CSS customizado com widgets Streamlit (`st.button`, `st.caption`, etc.).

### Causa raiz:
Widgets Streamlit não ficam realmente dentro do HTML criado via
`st.markdown(..., unsafe_allow_html=True)`. Além disso:
- seletores CSS amplos demais afetavam subcontainers e botões não relacionados;
- prefixes/keys sobrepostos faziam o estilo vazar entre container principal e wrappers internos;
- colunas e containers estavam sendo usados para simular um card customizado instável.

### Solução:
- migrar o card para estrutura nativa estável com `st.container(border=True)`;
- manter os elementos em fluxo normal: nome, estado (`● ATIVO` ou `Selecionar`), status e `X`;
- usar `st.dialog` para a confirmação de remoção, nunca renderizando confirmação na sidebar;
- aplicar CSS apenas quando necessário e sempre escopado por `key` específica;
- separar card ativo e inativo por keys diferentes;
- usar wrapper dedicado para o botão `X` quando precisar refinamento visual local.

### Lição:
No Streamlit, não tentar envolver widgets com HTML customizado para montar cards.
Preferir sempre:
- containers nativos;
- CSS escopado por `key`;
- seletores estreitos;
- modal/diálogo fora da sidebar para fluxos de confirmação importantes.

Se o layout começar a exigir hacks de DOM, a estrutura está errada e precisa voltar
para componentes nativos antes de qualquer polimento visual.

---

## Início do Projeto - 2024-03-11



### Setup inicial concluído

- CLAUDE.md criado com especificação completa

- Workflow orchestration implementado

- Estrutura de tasks/ configurada

- Pronto para desenvolvimento com Claude Code
