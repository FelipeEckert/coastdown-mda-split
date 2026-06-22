git commit -m "Add Split graphical analysis sections"# Lições Aprendidas - Coastdown MDA



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


## Split-specific lessons

Registrar aqui decisoes e aprendizados especificos do metodo Split.

## 2026-06-12 - Split: Graficos Devem Projetar O Estado Parseado

### Contexto:
A nova Analise Grafica precisava se inspirar na pagina Standard sem importar
`calculated_pairs`, selecao Standard ou premissas de multiplos intervalos.
Os registros em `split_parsed_runs` guardam o resultado agregado e a
rastreabilidade, enquanto os tempos por bin permanecem em
`split_input_sources[*].all_run_data`.

### Decisao:
Usar o registro parseado como fonte da selecao e resolver sua serie original por
arquivo, role e run apenas para recuperar os bins ja aceitos pelo parser Split.
O grafico acumula os `time_s` medidos e usa somente as velocidades inicial/final
de cada bin. Quando a fonte detalhada nao esta disponivel, mostrar explicitamente
um segmento agregado entre inicio, `Delta t` e fim, sem interpolar amostras.
Pares calculados leem somente os quatro componentes persistidos em
`split_comparison_pairs`; o `pair_id` continua restrito a chave tecnica.

### Licao:
Uma visualizacao metodologicamente neutra deve ser uma projecao dos dados que o
metodo ativo ja validou. Nao duplicar series no estado nem reconstruir curvas
fisicas inexistentes. Fallback agregado precisa ser visualmente distinguivel e
explicado ao usuario.

---

## 2026-06-12 - Split: Selecao Grafica Deve Ser Isolada Por Intervalo

### Contexto:
Um unico multiselect para high e low misturava duas analises com escalas e
decisoes operacionais independentes. Botoes programaticos tambem precisam
sincronizar a widget key usada pelo `st.multiselect`.

### Decisao:
High e low usam keys separadas para direcao e runs selecionadas, sempre
escopadas por teste e versao dos inputs. Ao mudar o filtro, um helper puro
mantem somente IDs ainda disponiveis naquela secao. `Adicionar todas` e
`Limpar selecao` escrevem na key da propria secao antes de o multiselect ser
renderizado.

### Licao:
Quando duas visualizacoes representam conjuntos de dominio independentes, o
estado dos widgets tambem deve ser independente. Em Streamlit, reconciliar e
atualizar a widget key antes de criar o widget evita que um valor visual antigo
recontamine a selecao de dominio.

---

## 2026-06-09 - Split: Coeficientes Corrigidos Devem Ter Contrato Proprio

### Contexto:
A formula de correcao climatica existente era pura na pratica, mas estava no
modulo Standard junto de workflows, aliases legados e calculo de energia.

### Decisao:
Isolar a formula em `core/split_corrections.py`, recebendo explicitamente
`f'0`, `f'2`, temperatura e pressao. Manter `f'0/f'2` intactos e salvar `F0/F2`
em campos separados. A correcao de `F2` inclui a conversao de
`N/(m/s)^2` para `N/(km/h)^2` pelo fator 12,96.

### Licao:
Reaproveitar uma formula nao exige reaproveitar seu workflow. Unidades e
constantes fazem parte do contrato: a implementacao pode existir antes da
validacao normativa final, mas essa validacao deve continuar explicitamente
pendente e nao pode ser confundida com teste de software aprovado.

---

## 2026-06-09 - Split: Sincronizacao Meteo Nao E Correcao Climatica

### Contexto:
O fluxo Split precisava associar cada uma das quatro passadas do par aos dados
ambientais sem aplicar ainda a transformacao normativa de `f'0/f'2` para `F0/F2`.
O arquivo real de meteo possui datas de anos diferentes, registros duplicados
por minuto e nenhum timezone declarado.

### Decisao:
Sincronizar cada componente high+, low+, high- e low- separadamente. Preferir
data + hora completas, aplicar limite maximo de diferenca e usar somente horario
quando o fallback estiver explicitamente habilitado. Todo fallback, empate,
ausencia de timezone ou data ambigua deve permanecer visivel em warnings.

### Licao:
Sincronizacao meteo e uma etapa de rastreabilidade, nao uma correcao climatica.
Um match temporal nao autoriza alterar coeficientes. Fallback por horario deve
ser opt-in e auditavel, pois pode produzir um valor plausivel usando o dia errado.

---

## 2026-06-08 - Split: Par De Coeficientes Exige Ida E Volta

### Contexto:
A primeira versao da aba `Calculo dos Coeficientes` calculava um par a partir
de apenas uma run high-speed e uma run low-speed.

### Decisao:
O calculo Split operacional deve selecionar quatro componentes rastreaveis:
high+, low+, high- e low-. Cada sentido e calculado com a funcao Split revisada,
e o resultado do par usa a media aritmetica explicita entre os resultados dos
sentidos + e - enquanto nao houver outra regra normativa Split documentada.

### Licao:
Uma combinacao high+low simples e incompleta para representar um par Split.
A direcao `+`/`-` e parte do contrato de calculo; registros sem direcao explicita
devem bloquear o calculo em vez de serem pareados por inferencia.

---

## 2026-06-08 - Split: Revisar O Contrato Antes De Reusar Energia

### Contexto:
A tabela comparativa Split precisava exibir energia quando disponivel. A funcao
herdada `calcular_energia` existe, mas esta dentro do modulo Standard e usa
constantes/ciclo sem contrato Split documentado.

### Decisao:
Manter energia como N/A ate revisar o contrato da funcao. A revisao posterior
confirmou que `calcular_energia(f0, f2)` e uma funcao pura baseada somente nos
coeficientes corrigidos; a decisao atual de reutilizacao esta registrada na
secao de 2026-06-09.

### Licao:
Split pode reaproveitar funcoes puras, mas nao workflows Standard acoplados.
Uma pendencia de proveniencia normativa das constantes deve permanecer visivel,
mas nao transforma por si so uma funcao pura em workflow acoplado.

---

## 2026-06-09 - Split: Cards Corrigidos Dependem Da Assinatura Ambiental

### Contexto:
Os cards comparativos armazenam F0/F2 corrigidos e condicoes ambientais. Manter
esses cards apos alterar modo ambiental, temperatura ou pressao exibiria um
resultado tecnicamente obsoleto.

### Decisao:
Tratar modo ambiental e valores fixos como uma assinatura de calculo. Quando a
assinatura muda, limpar resultados, ultimo calculo, pares comparativos, resumo
final e buffer Excel antes de permitir novo uso.

### Licao:
Rastreabilidade visual nao substitui invalidacao de dependencia. Resultados
corrigidos devem ser recalculados sempre que qualquer entrada ambiental muda.
O CV ida/volta deve ser calculado a partir dos F0/F2 corrigidos de cada sentido.
Energia depende de um perfil nomeado e de unidades explicitas.

---

## 2026-06-09 - Split: Estado De Calculo Precisa De Chaves Canonicas

### Contexto:
Os coeficientes existiam em estruturas aninhadas como `result_plus` e
`corrected_pair_mean`, enquanto tabela e cards liam aliases como `F0`, `F2` e
`f0_prime`. O calculo estava correto, mas a copia entre resultado e comparativo
ficava dificil de auditar e podia produzir campos vazios por divergencia de nome.

### Decisao:
Cada resultado e par comparativo deve salvar explicitamente:
`f0_prime_plus/minus/mean`, `f2_prime_plus/minus/mean`,
`F0_plus/minus/mean` e `F2_plus/minus/mean`. Estruturas aninhadas e aliases
anteriores permanecem apenas para compatibilidade.

### Licao:
Calcular, persistir e exibir devem compartilhar o mesmo contrato de chaves.
Coeficientes nao corrigidos e corrigidos nunca devem usar nomes intercambiaveis.
Ausencia de energia tambem e estado valido e deve ser salva como `energy=None`
com justificativa, nao omitida silenciosamente.

---

## 2026-06-09 - Split: Energia Reutiliza A Funcao Herdada

### Contexto:
`calcular_energia(f0, f2)` usa fatores city/highway e ponderacao 55/45, mas a
origem normativa dessas constantes nao esta documentada no repositorio. A
aritmetica depende somente de F0/F2 corrigidos e retorna MJ/km.

### Decisao:
Usar `core/split_energy.py` como adaptador puro que valida os coeficientes e
chama explicitamente `core.calculations.calcular_energia(F0_mean, F2_mean)`.
O contrato exige F0 em N, F2 em N/(km/h)^2, retorna MJ/km e registra a origem
como `standard_formula_calcular_energia`. Massa e perfil nao sao entradas dessa
formula; as constantes continuam embutidas na funcao herdada.

### Licao:
Uma funcao herdada pode ser reutilizada quando seu contrato e realmente puro e
explicito, sem importar o workflow Standard. Energia deve usar somente F0/F2
corrigidos; se a correcao nao existir, o estado correto continua sendo
`energy=None`. A origem normativa das constantes permanece uma validacao separada.

---

## 2026-06-09 - Split: Warnings Meteo Preservados Sem Poluir O Resultado

### Contexto:
Warnings tecnicos de sincronizacao eram exibidos em ingles e em linha aberta
junto aos coeficientes, dificultando a leitura do resultado principal.

### Decisao:
Mostrar no fluxo principal apenas o status curto da sincronizacao. Preservar
metodo, timestamps, delta temporal e warnings completos em expander colapsado,
traduzindo mensagens conhecidas na camada de apresentacao sem alterar o
sincronizador.

### Licao:
Rastreabilidade tecnica nao exige ruido permanente na tela. Warnings devem
continuar armazenados em sua forma original, enquanto a UI apresenta resumo
localizado e deixa os detalhes auditaveis sob demanda.

---

## 2026-06-09 - Split: Agregacao Por Direcao Preserva Quatro Passadas

### Contexto:
A correcao climatica usa uma condicao por sentido, mas cada sentido Split e
composto por uma passada high e uma low. Exibir somente as duas medias escondia
quais quatro registros meteorologicos produziram o resultado.

### Decisao:
Salvar `ambient_by_component` com high+, low+, high- e low-, mantendo timestamps,
metodo, delta, temperatura, pressao, vento, arquivo e warnings. A ida usa a media
de high+/low+ e a volta usa a media de high-/low-. Se uma direcao estiver
incompleta, somente ela fica sem F0/F2 corrigidos; a media final e a energia
exigem as duas direcoes validas.

### Licao:
Agregacao de calculo e rastreabilidade de relatorio sao contratos diferentes.
O calculo pode usar medias por direcao, mas resultado, comparativo e futuro
export devem preservar os quatro valores fonte. Valor de vento `0.0` e medicao
valida; ausencia deve permanecer `None`.

---

## 2026-06-09 - Split: Zero De Vento Nao E Ausencia

### Contexto:
Todos os ventos sincronizados apareciam como `0.0 m/s`, levantando a suspeita
de fallback incorreto. O arquivo real `AGRICULTR_SPLIT.csv` declara a coluna
`Wind Speed` em `m/s`; seus 9.476 registros contêm zero literal. `True Dir.`
preserva a direção em graus.

### Decisao:
O loader diferencia valor ausente, inválido e zero real. Zero permanece `0.0`;
ausente ou inválido vira `None` com warning. `km/h` é convertido explicitamente
para `m/s`; unidade desconhecida não é presumida. `Crosswind/Headwind` não
substituem automaticamente a coluna principal de vento.

### Licao:
Testes booleanos como `if not wind_speed` misturam zero válido com ausência.
Grandezas ambientais devem preservar o valor bruto, validar a unidade antes da
conversão e registrar qualquer transformação.

---

## 2026-06-08 - Split: Intervalo Validado Antes De Coeficiente

### Contexto:
A aba de selecao de intervalos acumulava configuracao, parser, revisao e calculo
do par, misturando validacao de entrada com decisao de engenharia.

### Decisao:
Separar o fluxo em duas etapas:
- Seleção de Intervalos: configurar, parsear, revisar cobertura e avisos;
- Cálculo dos Coeficientes: escolher manualmente high/low e calcular o par.

### Licao:
No metodo Split, calcular coeficientes deve depender de intervalos ja revisados.
Manter essas etapas separadas reduz ambiguidade e evita que a tela de parser
vire tambem uma tela de decisao de resultados.

---

## 2026-06-08 - Split: Input Mode Explicito Vem Antes Do Parser

### Contexto:
O fluxo Split precisava remover ambiguidade automatica na importacao, porque
inferir papel de arquivo ja havia permitido reinterpretar alta como baixa.

### Decisao:
A UI deve escolher explicitamente o modo de entrada:
- `separate`: high e low sao arquivos separados, com roles `high` e `low`;
- `combined`: um arquivo unico recebe role `full_or_combined`.

O parser pode continuar aceitando esses roles, mas nao deve decidir sozinho que
um arquivo high tambem e low, nem que um arquivo low tambem e high.

### Licao:
Em dados Split, o papel do arquivo e informacao de entrada, nao heuristica de
parser. Quando uma heuristica pode produzir um resultado numerico plausivel e
errado, a UI deve tornar a decisao explicita e invalidar derivados quando ela muda.

---

## 2026-06-08 - Split: Tracking Faz Parte Da Entrega

### Contexto:
As mudancas funcionais recentes do fluxo Split nao estavam sendo refletidas em
`tasks/todo.md`, deixando o tracker operacional atrasado em relacao ao codigo.

### Decisao:
Toda mudanca funcional deve revisar `tasks/todo.md`, e toda decisao tecnica ou
bug importante deve revisar `tasks/lessons.md`, antes de encerrar a tarefa.

### Licao:
Em uma migracao metodologica, documentacao de tracking nao e burocracia separada
do desenvolvimento. Ela evita que lacunas reais, como meteo, export e validacao
manual, desaparecam atras de um codigo que ja compila.

---

## 2026-06-08 - Split: Delta V Positivo E Coeficientes Road-Load-Positive

### Contexto:
O software exibe e armazena `Delta V` como amplitude positiva, mas a equacao
normativa descreve a desaceleracao como variacao assinada de velocidade.

### Decisao:
Manter `Delta V = abs(V_inicial - V_final)` na UI, rastreabilidade e testes.
Internamente, usar a forma equivalente que retorna `f'0` e `f'2` positivos para
road load, sem `return -f0_raw, -f2_raw` escondido.

### Licao:
Quando a convencao de exibicao difere da convencao algebrica da norma, documentar
a ponte explicitamente e testar com caso real conhecido. Inversao de sinal sem
justificativa e perigosa em calculos de engenharia.

---

## 2026-06-08 - Split: Troca De Arquivo Invalida Estado Derivado

### Contexto:
Substituir arquivos de coastdown ou meteo podia deixar resultados antigos vivos
em `session_state`, porque o editor original foi herdado de fluxo mais generico.

### Decisao:
Troca/remocao de high, low ou meteo deve limpar resultados derivados e export:
`split_parsed_runs`, `split_results`, `split_final_results`, `excel_buffer` e
sincronizacao meteo aplicavel. Seletores dependentes devem mudar de chave ou
versao quando o input muda.

### Licao:
Em Streamlit, o dado de dominio e as widget keys formam juntos o estado real.
Ao trocar arquivos, invalidar tambem selecoes visuais e buffers, nao apenas o
DataFrame carregado.

---

## 2026-06-08 - Split: Meteo Neutro Ainda Nao E Calculo Split

### Contexto:
O loader meteorologico herdado e util e aparentemente neutro, mas o metodo Split
ainda precisa decidir como aplicar meteo/correcao/auditoria no calculo e export.

### Decisao:
Reaproveitar o loader e a sincronizacao como infraestrutura neutra, mas manter
como pendente a integracao normativa no calculo Split e no relatorio Excel.

### Licao:
Infraestrutura neutra pode ser reutilizada; interpretacao metodologica nao pode
ser assumida. Meteo carregar corretamente nao significa que a correcao Split ja
esta implementada.

---

## Imported lessons from Coastdown MDA Standard

As lições abaixo foram herdadas do projeto Standard e devem ser usadas apenas quando forem metodologicamente neutras.
Não aplicar diretamente regras específicas do método Standard ao método Split.

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

---

## 2026-05-12 - Matriz de Engenharia: Shape Primeiro, Destaque Depois

### Contexto:
Aba `Conformidade de Tempos` na `page_3`, com ajuste posterior solicitado
para destacar apenas as células não conformes da matriz já pivotada.

### Erro:
Na primeira entrega da feature, foquei primeiro nos cálculos e tabelas
derivadas, mas não tratei o formato da visualização principal como requisito
funcional central. Isso gerou retrabalho em duas etapas:
- primeiro corrigir o shape para matriz;
- depois aplicar o destaque visual por célula.

### Solução:
Separar claramente as camadas:
- `DataFrame` longo para cálculo;
- `pivot_table` para matriz principal;
- máscara booleana alinhada para não conformidade;
- `pandas Styler` apenas para a pintura das células-alvo.

### LiÃ§Ã£o:
Em telas de análise técnica, o formato da grade é parte da regra de negócio.
Antes de pensar em cores, tooltips ou detalhes visuais, validar primeiro:
- o que é linha;
- o que é coluna;
- o que cada célula representa.

Se o requisito disser "matriz", a pivotagem correta vem antes de qualquer
polimento visual.

---

## 2026-05-12 - Persistência de Widget Também Faz Parte do Estado do Teste

### Contexto:
Correção do bug em que `vehicle_model` e `test_date` ficavam compartilhados
entre testes ao alternar o teste ativo na aplicação multi-teste.

### Erro:
Eu considerei suficiente persistir apenas `vehicle_info` por teste, mas a UI
da página 2 usava widgets com keys globais:
- `vehicle_model_input`
- `test_date_input`

Ao trocar de teste, `vehicle_info` era restaurado corretamente, porém o
Streamlit mantinha os valores antigos dessas widget keys. Na renderização
seguinte, o valor global do widget sobrescrevia o valor correto do teste ativo.

### Solução:
Tratar também as keys dos widgets como parte do estado isolado de cada teste:
- adicionar `vehicle_model_input` e `test_date_input` em `TEST_STATE_KEYS`;
- adicionar defaults correspondentes em `TEST_DEFAULTS`;
- restaurar fallback a partir de `vehicle_info` para compatibilidade com testes
  antigos;
- na `page_2_dados_veiculo.py`, deixar os widgets serem controlados pela
  própria key restaurada e depois sincronizar `vehicle_info` a partir dela,
  sem usar `value=` junto com `key=` nesse caso.

### Lição:
Em Streamlit multi-teste, não basta persistir apenas o dado de domínio. Sempre
verificar se o valor visível na tela está vindo de uma widget key separada. Se
o widget usa `key=` fixa e essa key não for isolada por teste, a interface pode
recontaminar o estado restaurado e parecer "global", mesmo quando o dicionário
de dados já está correto.

---

## 2026-05-12 - Editar Teste Existente: Validar Antes, Invalidar Depois

### Contexto:
Implementacao do fluxo para editar um teste ja criado a partir do card da
sidebar, permitindo alterar nome, substituir CSV, adicionar/substituir meteo
e remover meteo atual sem precisar excluir e recriar o teste.

### Problema:
Editar arquivos de um teste existente toca em estado sensivel:
- trocar CSV invalida coeficientes individuais, pares, selecoes e resultados;
- trocar/remover meteo invalida correcoes climaticas, pares e resultados;
- `current_pair_results` e `excel_buffer` eram estados auxiliares globais e
  poderiam sobreviver indevidamente apos uma edicao;
- se um novo arquivo fosse invalido, nao poderia apagar dados antigos;
- `st.dialog` podia reabrir em reruns globais se `edit_test_id` ficasse preso.

### Solucao:
- criar helpers de carregamento temporario para CSV e meteo, reutilizando
  `carregar_dados_csv_robusto()` e `read_weather_station_csv()`;
- carregar novos arquivos em variaveis temporarias e so substituir o teste
  depois que todos os arquivos fossem validados;
- preservar identidade e dados seguros do teste (`name`, `vehicle_info`, massa,
  modelo/data, metodo e velocidades de referencia);
- limpar somente os derivados afetados pela mudanca:
  - CSV: `individual_coeffs`, `calculated_pairs`, selecoes, resultados,
    algoritmo, par corrente, Excel e `vehicle_data_complete`;
  - meteo: `calculated_pairs`, selecoes, resultados, algoritmo, par corrente e Excel;
- adicionar `csv_test_date`, `current_pair_results` e `excel_buffer` ao estado
  por teste para manter isolamento multi-teste;
- usar `on_dismiss=_close_edit_test_dialog` no `st.dialog` e limpar o estado
  de edicao antes de reruns de idioma/tamanho de fonte.

### Licao:
Em fluxos de edicao de arquivos, nunca altere o teste atual antes de validar
os novos inputs. A ordem correta e:
1. salvar estado ativo;
2. copiar o dict do teste;
3. validar novos arquivos em temporarios;
4. aplicar alteracoes na copia;
5. invalidar apenas os derivados dependentes;
6. substituir o teste e recarregar o estado ativo.

Em Streamlit, todo dialog controlado por flag no `session_state` precisa ter
um caminho claro para limpar essa flag em salvar, cancelar, dismiss e reruns
globais. Caso contrario, mudar idioma/fonte ou qualquer widget global pode
reabrir um modal antigo inesperadamente.

---

## 2026-05-12 - Comparativo Final: Sincronizar Widget Key e Estado Real

### Contexto:
Correcao dos botoes da tabela de Comparativo Final:
- `Selecionar todos`;
- `Desmarcar todos`;
- substituicao de `Inverter selecao` por `Limpar tudo`.

### Problema:
A selecao real dos pares era salva em
`st.session_state.calculated_pairs[pair_id]["selected"]`, mas a tabela tambem
usava checkboxes com keys fixas `sel_{pair_id}`.

Os botoes atualizavam apenas o dict de dominio. No rerun, o Streamlit mantinha
o valor antigo da widget key do checkbox e a renderizacao da linha escrevia esse
valor antigo de volta em `calculated_pairs[pair_id]["selected"]`. O efeito na UI
era parecer que `Selecionar todos` e `Desselecionar todos` nao faziam nada.

### Solucao:
- centralizar a key do checkbox em helper (`sel_{pair_id}`);
- ao selecionar/desmarcar em lote, atualizar tanto
  `calculated_pairs[pair_id]["selected"]` quanto `st.session_state[sel_key]`;
- ao mudar selecao, invalidar resultados dependentes:
  `pares_finais_selecionados`, `final_results` e `excel_buffer`;
- ao remover/limpar pares, apagar tambem o estado dos checkboxes desses pares;
- trocar o antigo `Inverter selecao` por `Limpar tudo`, que remove todos os
  pares do Comparativo Final e reseta derivados como `algorithm_results` e
  `pairs_calculated`.

### Licao:
Em Streamlit, quando um widget tem `key=`, essa key tambem e fonte de verdade.
Se o estado de dominio e a widget key representam a mesma informacao, operacoes
programaticas precisam sincronizar os dois lados antes do `st.rerun()`. Caso
contrario, o valor antigo do widget pode recontaminar o estado correto na
renderizacao seguinte.

---

## 2026-05-13 - Sincronizacao Flexivel CSV/Meteo: Estado Parcial

### Contexto:
Implementacao parcial para permitir sincronizacao meteorologica flexivel quando
o CSV de coastdown e o arquivo meteo tem datas divergentes, mas horarios
compativeis. A funcionalidade compila, mas ainda nao foi validada manualmente.
Nao commitar/pushar antes de testar com dados reais.

### Implementacao parcial feita:
- adicionada flag `sync_meteo_by_time_only` ao estado do teste;
- adicionada UI/checkbox quando ha divergencia de datas entre CSV e meteo;
- criado helper `find_closest_weather_record(..., time_only=False)`;
- page 3 e page 4 passaram a usar o helper para escolher o registro meteo;
- page 4 passou a bloquear a execucao com aviso amigavel quando nao ha horario
  valido para sincronizar meteo;
- traducoes PT/EN foram adicionadas/corrigidas.

### Comportamento pretendido:
- modo normal: sincronizar meteo usando data + horario;
- modo flexivel: quando o usuario confirmar, sincronizar usando apenas horario
  do dia;
- usar modo flexivel apenas para arquivos CSV e meteo com datas divergentes,
  mas horarios compativeis.

### Pendente para retomar:
- testar manualmente com CSV e meteo de mesma data;
- testar manualmente com CSV e meteo de datas diferentes, mas horarios
  compativeis;
- confirmar que o checkbox aparece apenas quando necessario;
- confirmar que a escolha fica salva no teste ativo;
- confirmar que page 3 e page 4 usam o mesmo comportamento;
- confirmar que nao ha regressao na correcao climatica;
- revisar diff antes de commit;
- commitar somente depois do teste manual.

### Cuidados:
- nao modificar `core/`;
- nao alterar logica F0/F2;
- nao misturar esta alteracao com outras features;
- se o teste manual falhar, revisar primeiro `find_closest_weather_record()` e
  o uso de `sync_meteo_by_time_only`.

---

## 2026-05-14 - Sincronizacao CSV/Meteo: Auditoria e Vento

### Contexto:
Finalizacao da sincronizacao meteorologica flexivel entre CSV e meteo.

### Implementacao:
- modo normal continua sincronizando por data + horario;
- modo flexivel, quando confirmado pelo usuario, sincroniza somente pelo horario
  do dia;
- tabela de auditoria mostra, por passada, horario CSV, horario meteo, diferenca,
  modo usado, temperatura, pressao e vento;
- vento meteorologico exibido vem do campo `wind_ms`, derivado de `Wind Speed`
  ou dos componentes `Crosswind`/`Headwind` quando necessario;
- vento acima de 3.0 m/s recebe destaque visual e aviso por ser criterio de
  atencao/exclusao pela norma.

### Validacao manual:
Testes manuais realizados pelo usuario confirmaram a exibicao correta da
sincronizacao e do vento na auditoria. Antes de novas alteracoes, preservar a
logica de escolha do registro meteo e mudar apenas apresentacao quando o pedido
for visual.

### Licao:
Auditoria de dados ambientais deve mostrar o dado realmente usado no calculo,
sem fallback silencioso para zero. Quando um valor e criterio normativo, ele
precisa aparecer na mesma tabela operacional e receber destaque visual.

---

## 2026-05-14 - Tabelas Matriz com Detalhe por Celula

### Contexto:
Melhoria da aba `Conformidade de Tempos` para explicar cada celula da matriz
intervalo x run sem mudar criterios de conformidade nem calculos.

### Tentativas descartadas:
- `plotly.graph_objects.Table` nao entregou tooltip por celula de forma
  confiavel no Streamlit.
- Selectbox de detalhes funcionava tecnicamente, mas piorava a experiencia
  porque tirava o usuario do contexto visual da celula.

### Solucao:
- renderizar a matriz como HTML/CSS escopado com `st.markdown(...,
  unsafe_allow_html=True)`;
- escapar textos dinamicos com `html.escape`;
- manter a mesma matriz de tempos e a mesma matriz de status ja calculadas;
- colocar o detalhe no hover da propria celula;
- usar classes por posicao: primeiras linhas abrem tooltip para baixo,
  ultimas linhas abrem para cima;
- manter apenas scroll horizontal e evitar scroll vertical que corta tooltip.

### Licao:
Quando a necessidade e detalhe por celula em uma matriz, preferir uma tabela
HTML escopada a widgets auxiliares ou Plotly Table. O detalhe deve aparecer no
ponto de atencao do usuario, sem clique extra e sem transformar a matriz em
formato longo. Para tooltips em tabelas com scroll, definir a direcao por linha
e alinhar bordas esquerda/direita explicitamente para evitar cortes.

---

## 2026-05-18 - Redirecionamento Entre Abas com `st.tabs`

### Contexto:
Melhoria de fluxo para enviar o usuario automaticamente da aba `Comparativo Final`
para `Resultados Finais` depois que o calculo final dos pares selecionados e salvo
com sucesso.

### Solucao:
- manter `current_page` como estado canonico da aba principal do teste ativo;
- criar uma flag curta (`navigate_to_results`) na pagina que conclui a acao;
- consumir a flag no `app.py` antes de criar as tabs;
- usar `st.tabs(..., default=..., key=..., on_change="rerun")` para abrir a aba
  correta sem refatorar a navegacao inteira;
- fazer a funcao de calculo retornar `True` somente quando grava `final_results`,
  evitando redirecionamento em caso de erro.

### Licao:
Quando a navegacao usa `st.tabs`, o redirecionamento deve ser feito pelo dono das
abas, nao pela pagina filha. A pagina filha sinaliza a intencao via `session_state`;
o `app.py` consome essa intencao, ajusta o estado do widget de tabs e rerenderiza.
Assim a mudanca fica pequena e nao mistura fluxo de UI com logica de calculo.
## 2026-06-03 - Split: Quarantine Standard Before Reusing Logic

### Contexto:
Implementacao inicial da migracao do Coastdown MDA Split a partir da base Standard.

### Decisao:
O fluxo visivel passou a usar paginas e modulos Split especificos. As paginas Standard
permanecem no repositorio como legado herdado, mas sairam da navegacao principal.
As antigas funcoes Split misturadas em `core/calculations.py`, `page_3` e `page_4`
nao sao usadas pelo novo workflow.

### Licao:
Antes de reaproveitar qualquer logica herdada, separar a superficie visivel e criar
contratos Split puros para parser, calculo, validacao e export. Reaproveitar somente
infraestrutura neutra ou trechos revisados, como conversao de unidades e estrutura
algebrica das equacoes.

---

## 2026-06-03 - Split: Slot Role Controls Interval Extraction

### Contexto:
Um arquivo apenas de alta velocidade estava sendo reinterpretado como baixa quando o
workflow tentava preencher automaticamente o intervalo faltante.

### Decisao:
O papel do arquivo passa a ser parte do contrato Split:
- slot high gera somente registros high;
- slot low gera somente registros low;
- arquivo unico/combinado tenta high e low apenas quando ambos os intervalos existem.

Substituicao de arquivos no editor tambem deve reconstruir `split_input_sources` e
limpar resultados derivados, usando hash de conteudo para rastreabilidade.

### Licao:
No metodo Split, fallback por posicao ou por "primeiras colunas disponiveis" cria
resultado plausivel e errado. O parser deve ser conservador e o fluxo deve avisar
quando falta high ou low, bloqueando calculo incompleto.

---

## 2026-06-10 - Split: O Passo Faz Parte Da Identidade Do Intervalo

### Contexto:
O parser aceitava qualquer sequencia continua que cobrisse o intervalo configurado,
mesmo que os bins do arquivo tivessem sido adquiridos com um passo diferente.

### Decisao:
`split_interval_config` passa a guardar `step_kmh`. O parser gera os bins esperados
a partir de inicio, fim e passo e exige correspondencia exata, sem juntar ou dividir
subintervalos implicitamente. A amplitude tambem precisa ser multipla do passo.

Alterar inicio, fim, referencia ou passo invalida parser, resultados, ultimo calculo,
comparativo e export antes do reprocessamento.

O loader Split nao deve fabricar velocidades iniciando em 90 ou 45 nem decrementar
sempre 5 km/h. Ele preserva tempos e rotulos das colunas. Rotulos explicitos sao
casados por velocidade; colunas sem rotulo so podem ser associadas quando o slot
separate define inequivocamente o papel high ou low. Combined sem rotulos deve
bloquear, pois nao ha informacao suficiente para separar os intervalos.

### Licao:
Cobertura continua nao e suficiente para provar que o arquivo representa a
configuracao de aquisicao escolhida. No Split, o passo deve ser rastreavel e validado
como parte do contrato do parser. Quando a cobertura falhar, registrar bins esperados,
encontrados e faltantes em vez de emitir apenas "intervalo nao encontrado".

---

## 2026-06-10 - Split: Reutilizar Funcoes Puras, Nao Workflows Standard

### Regra:
O Split pode reutilizar uma funcao herdada quando o contrato for explicito, puro e
independente de estado ou schema Standard. Exemplos aceitos sao conversao de unidade,
formatacao, leitura neutra de arquivo e `calcular_energia(f0, f2)`, desde que a origem
e as constantes permaneçam documentadas.

Nao reutilizar diretamente funcoes que dependam de `calculated_pairs`,
`pares_finais_selecionados`, `algorithm_results`, `f0_corr`, `f2_corr`, selecao por
algoritmo ou qualquer outro workflow Standard acoplado. Mesmo quando uma formula
interna parece aproveitavel, ela deve ser isolada atras de um contrato Split ou
neutro antes de entrar no fluxo ativo.

### Licao:
Separacao metodologica deve ser verificada pela cadeia de imports e pelo contrato de
estado, nao apenas pela navegacao visivel. `core/__init__.py` e `data/__init__.py`
ainda importam legado de forma antecipada; isso nao executa o workflow Standard hoje,
mas aumenta o risco de acoplamento e deve ser removido em uma etapa de compatibilidade
controlada.

---

## 2026-06-10 - Split: Editar Configuracao Nao Deve Processar Dados

### Decisao:
Os campos de inicio, fim, referencia e passo escrevem em
`split_interval_draft_config`. O parser so valida e grava
`split_interval_config`/`split_parsed_runs` apos a acao explicita de processamento.

Quando o draft difere da ultima configuracao processada, `split_parse_dirty=True`
identifica a previa como desatualizada e bloqueia o calculo de coeficientes. Erros
detalhados de bins e validacao pertencem a uma tentativa explicita, nao a cada rerun
causado pela edicao de widgets.

As keys dos `number_input` devem ser estaveis por teste e ser a unica fonte dos
widgets durante a edicao. Repassar `value` a cada rerun ou variar `step` com outro
widget altera a identidade do controle no Streamlit e pode restaurar o valor,
produzindo cliques aparentemente perdidos.

O Parser review le um snapshot isolado de `split_interval_config`,
`split_parsed_runs` e `split_processed_at`. Ele nunca consulta o draft, mesmo quando
a previa antiga permanece visivel durante uma nova edicao.

### Licao:
Em Streamlit, separar estado de edicao de estado processado evita validacao ruidosa,
trabalho repetido e uso acidental de resultados calculados com configuracao antiga.
O estado derivado deve ser invalidado no processamento confirmado, enquanto o draft
apenas marca a necessidade de reprocessar.

---

## 2026-06-10 - Split: Reaproveitar Linguagem Visual, Nao Estado Standard

### Decisao:
A tabela comparativa Split pode adotar padroes visuais observados no comparativo
Standard, como cabecalho compacto, linhas coloridas por origem, status resumido e
acoes discretas. A implementacao permanece sobre `split_comparison_pairs` e helpers
puros de `core/split_comparison.py`.

Cada par guarda `selection_source` (`manual`, `algorithm` ou `unknown`) e `selected`.
Pares adicionados pela UI atual sao sempre `manual`. A futura selecao automatica
devera apenas produzir o mesmo contrato Split com origem `algorithm`, sem importar
`calculated_pairs`, `algorithm_results`, `pares_finais_selecionados`,
`f0_corr/f2_corr` ou regras de selecao Standard.

### Licao:
Referencia visual e contrato metodologico sao camadas diferentes. Cores, densidade,
formatacao e hierarquia podem inspirar uma nova tela; schemas de estado, algoritmos e
validacoes devem continuar pertencendo exclusivamente ao metodo Split.

---

## 2026-06-10 - Split: Comparativo Final Deve Ter Pagina Propria

### Decisao:
O comparativo completo foi retirado de Calculo dos Coeficientes e passou para
`pages/page_split_final_comparison.py`. A aba de calculo seleciona as quatro passadas,
calcula o par e apenas adiciona o ultimo resultado ao comparativo.

A nova pagina replica o template estrutural do comparativo Standard com acoes em
lote, legenda, cabecalho escuro, linhas construidas com `st.columns`, checkbox e
remocao por par. Os dados continuam vindo exclusivamente de
`split_comparison_pairs` e das chaves canonicas Split.

### Licao:
Separar criacao e comparacao reduz poluicao visual e deixa cada etapa do workflow
com uma responsabilidade clara. Mesmo quando uma pagina legado serve de template,
a nova pagina deve possuir seu proprio estado, helpers e contratos metodologicos.

---

## 2026-06-10 - Split: Resultados Reutilizam Hierarquia Visual, Nao O Resumo Standard

### Decisao:
A pagina `page_6_resultados.py` serve apenas como referencia para a hierarquia de
apresentacao: metricas principais, informacoes do veiculo, tabela final, validacao,
detalhes e area de exportacao.

O consolidado Split e calculado por helpers puros em `core/split_results.py` a
partir de `split_comparison_pairs` marcados com `selected=True`. As chaves canonicas
sao `F0_mean`, `F2_mean`, `energy`, `f0_prime_mean`, `f2_prime_mean`, warnings e
`ambient_by_component`. Estados e aliases metodologicos Standard nao participam.

O CV final usa desvio-padrao amostral e so e exibido com pelo menos dois valores
validos. Dados ausentes reduzem a amostra disponivel e geram aviso, sem substituir
valores por zero. O export permanece desabilitado ate consumir esse mesmo contrato.

### Licao:
Reaproveitar um template visual nao significa copiar o momento em que o resultado
e calculado nem sua fonte de estado. A pagina final deve ser uma projecao defensiva
do contrato do metodo ativo, com consolidacao pura testavel e UI tolerante a dados
parciais.

---

## 2026-06-10 - Split: Identidade Tecnica Nao E Rotulo Publico

### Decisao:
O campo `id` com formato `split_pair_*` permanece como chave tecnica para selecao,
remocao, widget keys e persistencia. A UI identifica o par pela composicao das runs:
`[+]: Run high / Run low | [-]: Run high / Run low`.

Os seletores de passadas mostram somente run, Delta t e arquivo. Direcao e horario
continuam nos dados e nas secoes de rastreabilidade, sem poluir o label operacional.
Os dois formatos sao centralizados em helpers puros de `core/split_display.py`.

Ao validar a mudanca na aplicacao, verificar tambem processos Streamlit duplicados.
Uma instancia iniciada antes da alteracao pode continuar servindo bytecode antigo,
mesmo quando testes e imports em um novo processo ja resolvem o arquivo correto.
Confirmar porta/PID e reiniciar a instancia usada pelo navegador faz parte da
validacao de mudancas visuais.

### Licao:
Chaves estaveis devem permanecer independentes do texto apresentado. Um identificador
publico derivado dos componentes de dominio melhora a leitura sem alterar referencias
internas, e um unico helper evita que tabelas, cards e seletores descrevam o mesmo par
de maneiras divergentes.

---

## 2026-06-17 - Split: Preview Compacto Nao Duplica Rastreabilidade

### Decisao:
A sub-aba Calculo dos Coeficientes deve priorizar a acao imediata: selecionar
passadas, calcular f'0/f'2, conferir F0/F2 corrigidos, energia e adicionar o par ao
comparativo. O resumo tecnico do par selecionado fica em expander fechado, e os
detalhes de sincronizacao meteorologica aparecem uma unica vez no expander da secao
ambiental.

Os cards de pares adicionados nessa sub-aba sao apenas uma previa compacta baseada
em `split_comparison_pairs`, com titulo publico via `format_split_pair_label()` e
chaves canonicas Split (`F0_mean`, `F2_mean`, `energy`,
`ambient_by_component` e medias ida/volta). A selecao e comparacao seguem
concentradas no Comparativo Final.

### Licao:
Limpeza visual nao deve apagar rastreabilidade nem criar um segundo fluxo de
comparacao. Dados tecnicos permanecem salvos no contrato Split e em expanders
fechados; a tela principal mostra so o necessario para a proxima decisao do usuario.

---

## 2026-06-17 - Split: Resultado Calculado Usa Tabela HTML Especifica

### Decisao:
O resumo tecnico do par selecionado saiu da sub-aba Calculo dos Coeficientes. Apos
calcular, a tela passa a mostrar `Resultados do Par` com duas tabelas HTML
escopadas por classes `split-*`: uma para f'0/f'2 nao corrigidos e outra para
F0/F2 corrigidos quando a correcao estiver disponivel.

A tabela nao corrigida usa `f0_prime_plus/minus/mean` e
`f2_prime_plus/minus/mean`, mantendo f'2 em `N/(m/s)^2`. A tabela corrigida usa
`F0_plus/minus/mean`, `F2_plus/minus/mean`, `temp_plus/minus_used`,
`press_plus/minus_used`, vento medio por direcao a partir de
`ambient_by_component` e `energy`. Labels publicos de direcao sao derivados das
runs high/low de cada sentido, nunca do `id` tecnico `split_pair_*`.

### Licao:
Copiar o estilo visual Standard requer um adaptador de apresentacao Split, nao
copiar variaveis Standard como `selected_ida` ou `f0_corr`. Tabelas ricas devem
usar classes CSS escopadas, formatadores tolerantes a `None`/`NaN` e thresholds
visuais que nao alteram os valores calculados nem a persistencia do par.

---

## 2026-06-17 - Split: Tabelas Altas Devem Ficar Em Detalhes

### Decisao:
As tabelas HTML de coeficientes calculados permanecem no fluxo de Resultados do
Par, mas ficam dentro de um expander fechado por padrao. O titulo da secao e a
acao de adicionar ao comparativo continuam visiveis fora do expander.

### Licao:
Quando uma tela de calculo precisa confirmar rapidamente o proximo passo, detalhes
tabulares altos devem ser consultaveis sob demanda. O botao operacional deve ficar
na superficie principal para nao esconder a acao esperada apos o calculo.

---

## 2026-06-17 - Split: Graficos Podem Reusar Tema, Nao Estado Standard

### Decisao:
Os graficos velocidade x tempo da Analise Grafica Split adotam o tema escuro
visual inspirado no Standard, mas continuam lendo somente split_parsed_runs,
split_input_sources e split_comparison_pairs. O par ativo e resolvido pelo
selectbox Split de pares calculados, usando labels publicos e componentes
high/low por direcao.

### Licao:
Tema Plotly, cores, espessuras e hover sao apresentacao reutilizavel. Fonte de
dados, selecao ativa e nomes de traces devem permanecer no contrato Split para
evitar acoplamento com all_run_data, current_pair_results ou run_ida/run_volta
do metodo Standard.

---

## 2026-06-17 - Split: Labels De Grafico Devem Ser Mais Curtos Que Labels De Calculo

### Decisao:
A Analise Grafica usa um label proprio com Run e Delta t, sem arquivo ou horario.
Os hovers dos graficos velocidade x tempo e Delta t tambem omitem arquivo e
timestamp. A secao visual de pares calculados foi removida da sub-aba grafica; o
estado split_comparison_pairs permanece intacto para Comparativo Final e demais
paginas.

### Licao:
Labels bons para selecao tecnica podem ser longos, mas graficos precisam de menos
ruido visual. Quando a mesma run aparece em contextos diferentes, use helpers de
display especificos por contexto em vez de enfraquecer um label ja util em outra
tela.

---

## 2026-06-17 - Split: Comparativo Final Seleciona Apenas Pares Corrigidos

### Decisao:
A primeira etapa da refatoracao do Comparativo Final usa exclusivamente
`split_comparison_pairs`. A tabela foi separada em pares com correcao climatica
e pares de referencia sem correcao. Somente itens com `F0_mean/F2_mean` finitos
sao selecionaveis; pares sem correcao sao automaticamente gravados como
`selected=False` e ficam sem checkbox.

A normalizacao da UI vive em helpers Split de `core/split_comparison.py`,
retornando valores canonicos para F0/F2 corrigidos, f'0/f'2 nao corrigidos,
CV, energia e condicoes ambientais sem substituir ausencias por zero. Acoes em
lote e remocao invalidam apenas `split_final_results` e `excel_buffer`; runs
parseadas, arquivos carregados e parser permanecem intactos.

### Licao:
Separar visualmente dados corrigidos de dados apenas referenciais evita que um
par numericamente util para inspecao entre no resultado final sem contrato
climatico completo. Em Streamlit, selecao programatica deve atualizar tanto o
objeto de dominio quanto a widget key; quando o item nao e selecionavel, a
renderizacao tambem deve reparar estados antigos.

---

## 2026-06-17 - Split: Comparativo E Resultados Compartilham Consolidacao

### Decisao:
A parte inferior do Comparativo Final coleta apenas pares em
`split_comparison_pairs` com `selected=True` e F0/F2 corrigidos finitos. As
estatisticas exibidas ali usam `consolidate_split_final_results`, o mesmo helper
da aba Resultados Split, para medias de F0, F2, energia, CVs e status de
conformidade.

O botao de resultado final grava `split_final_results` com esse consolidado e
sinaliza `navigate_to_results=True`; a navegacao continua sendo resolvida pelo
`app.py`. A rastreabilidade complementar mostra somente campos ja persistidos no
contrato Split, sem importar a analise de tempos Standard.

### Licao:
Telas diferentes podem projetar o mesmo resumo, mas nao devem recalcular regras
paralelas. Quando uma pagina intermedia mostra estatisticas finais, ela deve usar
o mesmo helper da pagina final ou vira uma segunda fonte de verdade. Analises
tecnicas herdadas so entram depois de revisao metodologica Split.

---

## 2026-06-17 - Split: Checkbox Nao Pode Ser Ressincronizado Depois De Criado

### Contexto:
O Comparativo Final Split gerou `StreamlitAPIException` ao marcar/desmarcar um
par, porque a renderizacao criava `st.checkbox(key=...)` e depois um helper
reescrevia diretamente a mesma key em `st.session_state`.

### Decisao:
A linha da tabela inicializa a widget key somente antes do checkbox existir.
Depois da criacao do widget, o retorno de `st.checkbox` e copiado apenas para
`split_comparison_pairs[*]["selected"]`, sem escrever em
`st.session_state[widget_key]`. Acoes em lote continuam antes da tabela e fazem
`st.rerun()` imediato quando sincronizam keys para a proxima execucao.

A tabela tambem voltou ao estilo compacto do Standard como referencia visual:
`st.columns`, cabecalho HTML simples, celulas HTML escuras, CV acima de 10 em
vermelho e pares sem correcao em laranja. A fonte real segue sendo
`split_comparison_pairs`.

### Licao:
Widget key em Streamlit nao e um campo de estado de dominio livre durante a
execucao. Depois que o widget e instanciado, altere o objeto de dominio, nao a
key do widget. Sincronizacao programatica de widget deve acontecer antes da
instanciacao ou em uma execucao nova apos `st.rerun()`.

---

## 2026-06-17 - Split: Legenda Visual Nao Pode Inventar Origem

### Decisao:
A rodada visual do Comparativo Final adicionou uma legenda para estados reais do
Split: par selecionado, par sem correcao e CV acima de 10%. A tabela passou a
destacar linhas selecionadas em verde claro, manter corrigidos nao selecionados
em fundo escuro e mostrar pares sem correcao em laranja. As celulas usam o
padrao visual compacto do Standard como referencia, com borda suave,
arredondamento, `display:flex` e conteudo centralizado.

### Licao:
Referencia visual nao autoriza criar significado operacional inexistente. Se o
Split ainda nao possui selecao automatica por energia/target, a legenda deve
explicar apenas os estados persistidos em `split_comparison_pairs` e os limites
visuais aplicados na propria tela.

---

## 2026-06-17 - Split: Tabela HTML Precisa De Altura De Linha Estavel

### Decisao:
As celulas do Comparativo Final usam `height:50px`, `width:100%`,
`box-sizing:border-box`, `display:flex`, alinhamento central e `line-height:1.45`.
O mesmo helper alimenta celulas normais, selecionadas, sem correcao, par e CV em
warning, para que linhas com uma ou duas quebras tenham a mesma altura visual.

### Licao:
Em tabelas montadas com `st.columns` e HTML, `min-height` nao basta quando uma
coluna tem duas linhas e outra tem uma. A altura precisa fazer parte do contrato
do estilo base, inclusive nos estados especiais, ou a tabela volta a parecer
desalinhada.

---

## 2026-06-17 - Split: Valores Ida/Volta Devem Empilhar Na Tabela Compacta

### Decisao:
No Comparativo Final, os valores ambientais ida/volta de temperatura, pressao e
vento sao exibidos em linhas separadas dentro da mesma celula. Os coeficientes
da tabela foram padronizados para leitura compacta: F0/f'0 com duas casas e
F2/f'2 com quatro casas. A mudanca e apenas de apresentacao; os valores
persistidos em `split_comparison_pairs` continuam intactos.

### Licao:
Em tabelas compactas, usar separador horizontal para valores ida/volta compete
com colunas estreitas e deixa o alinhamento dependente da quebra automatica do
navegador. Quebra controlada na camada de display preserva a leitura sem alterar
o contrato numerico.

---

## 2026-06-19 - Split: Algoritmo Automatico Deve Reusar O Motor Manual

### Decisao:
A auditoria para a futura selecao automatica confirmou que o fluxo manual ativo ja
possui a cadeia de calculo que deve ser reutilizada: `calculate_complete_split_pair`,
`apply_split_pair_correction` e `build_split_comparison_pair`. A proxima etapa deve
extrair um helper puro de candidato automatico sobre essa cadeia, sem duplicar
formulas e sem importar o workflow legado de `page_4_selecao_algoritmo.py`.

Pares sugeridos por algoritmo devem entrar em `split_comparison_pairs` com
`selection_source="algorithm"` e `selected=False`. A selecao final continua sendo
uma decisao manual do usuario no Comparativo Final.

### Licao:
No Split, "sugerir candidato" e "selecionar para o resultado final" sao estados
diferentes. O algoritmo pode preencher o comparativo, mas nao deve marcar o par
como selecionado. Flags visuais de energia/target devem ser adicionadas ao contrato
Split de forma explicita, porque hoje a tela ativa reconhece origem generica
`algorithm`, par selecionado, par sem correcao e CV alto.

---

## 2026-06-19 - Split: Candidato Automatico Tem Identidade Por Componentes

### Decisao:
O helper puro `core/split_pair_candidate.py` cria um candidato automatico usando o
mesmo trio do calculo manual: `calculate_complete_split_pair`,
`apply_split_pair_correction` e `build_split_comparison_pair`. O helper nao acessa
estado de UI e forca `selection_source="algorithm"` com `selected=False`.

A identidade `run_usage` e a assinatura estavel sao baseadas nas quatro passadas,
na ordem high+, low+, high-, low-, incluindo tipo high/low, direcao, `run_id`,
arquivo, `source_role` e hash de fonte quando disponivel. Valores ausentes viram
`"<missing>"` para manter uma assinatura controlada sem mascarar a falta de
rastreabilidade.

### Licao:
O `id` tecnico do par e adequado para widget/remocao, mas nao para deduplicar
candidatos automaticos. Duplicidade de algoritmo deve ser decidida pelos quatro
componentes de dominio usados no calculo, pois o mesmo candidato pode receber ids
diferentes quando reconstruido.

---

## 2026-06-19 - Split: Top-k Automatico Nao Completa Repeticoes

### Decisao:
Os helpers puros de ranking ficam separados da geracao de candidatos e da UI. O
ranking por energia usa `energy`; o ranking por target usa `F0_mean` e `F2_mean`
corrigidos, adicionando apenas metadados de score em copias dos candidatos.

O top-k com `avoid_repeated_runs=True` compara itens exatos de `run_usage`.
Passadas com mesmo `run_id` nao conflitam se diferem por high/low, direcao,
arquivo, papel ou hash. Se nao houver candidatos suficientes sem repeticao, a
funcao retorna menos que `k` e registra warning; ela nao completa automaticamente
com repetidos.

### Licao:
A camada de algoritmo deve ser previsivel e auditavel: ranquear, filtrar
repeticoes e reportar perdas sao responsabilidades puras. A decisao de aceitar
repeticao por falta de candidatos, se existir, deve ser uma etapa explicita de UI
ou politica normativa, nao um fallback silencioso dentro do seletor.

---

## 2026-06-19 - Split: Validacao De Tempos Pode Ser Inconclusiva

### Decisao:
A validacao normativa pura dos tempos trabalha sobre o conjunto de candidatos
selecionados e monta quatro grupos: high+, high-, low+ e low-. O CV usa desvio
padrao amostral e so e avaliavel com pelo menos dois tempos validos no grupo.
A diferenca entre sentidos compara as medias high+/high- e low+/low-.

O resultado geral usa tres estados: `True` quando tudo e avaliavel e passa,
`False` quando qualquer verificacao avaliavel falha, e `None` quando falta amostra
para avaliar tudo mas nenhuma verificacao avaliavel falhou.

### Licao:
Amostra insuficiente nao deve ser mascarada como aprovado nem reprovado. Para o
Split automatico, diagnostico inconclusivo precisa chegar como warning e estado
neutro para a camada de UI/politica decidir se bloqueia, avisa ou solicita mais
candidatos.

---

## 2026-06-19 - Split: Geracao Exata Deve Ter Limite Explícito

### Decisao:
A geracao pura de candidatos completos usa o produto cartesiano high+ x low+ x
high- x low- e chama `build_algorithm_split_pair_candidate` para cada combinacao.
O modulo calcula o total estimado antes de gerar e respeita `max_combinations`;
quando o limite e excedido, ele nao tenta gerar parcialmente.

Erros de uma combinacao individual sao capturados em metadata e nao abortam a
geracao das demais combinacoes.

### Licao:
O modo exato e simples, auditavel e util para conjuntos pequenos, mas pode crescer
rapidamente. A decisao entre modo exato e modo otimizado deve acontecer antes da
geracao, com um limite explicito, para evitar custo computacional surpresa e para
manter a futura UI honesta sobre quantos candidatos existem.

---

## 2026-06-19 - Split: Orquestrador Automatico Nao Persiste Candidatos

### Decisao:
O orquestrador puro `run_split_auto_selection_exact` combina geracao exata,
ranking, top-k, marcacao de origem e diagnostico normativo de tempos, mas retorna
apenas candidatos e metadata. Ele nao adiciona nada em `split_comparison_pairs` e
nao toca estado de UI.

Mesmo apos top-k, os candidatos passam por `mark_algorithm_source`, preservando
`selected=False`, `selection_source="algorithm"` e `algorithm_source` especifico
do algoritmo.

### Licao:
A selecao automatica deve permanecer em duas fases: sugerir candidatos e depois,
em outra camada explicita, adiciona-los ao comparativo. Separar orquestracao pura
de persistencia evita que algoritmo vire selecao final por efeito colateral.

---

## 2026-06-19 - Split: Merge Automatico Preserva A Selecao Manual

### Decisao:
O helper puro de merge entre candidatos automaticos e `split_comparison_pairs`
deduplica por identidade das quatro passadas, preferindo `run_usage` e usando
campos reais do par apenas como fallback. Quando a sugestao do algoritmo ja existe
no comparativo, o par existente continua sendo a fonte principal: `selected`,
F0/F2, energia, warnings, labels e demais dados calculados nao sao sobrescritos.

A origem algoritimica fica acumulada em `algorithm_sources`, com flags
`selected_by_energy_algo` e `selected_by_target_algo` para compatibilidade visual
futura. Em duplicatas manuais, `selection_source` nao e reclassificado para nao
apagar como o par entrou originalmente no comparativo.

### Licao:
Mesclar sugestao automatica nao e recalcular nem selecionar resultado final.
Deduplicacao deve proteger a decisao manual do usuario e enriquecer apenas
metadados rastreaveis de algoritmo. Quando um par pode ter mais de uma origem
algoritmica, lista acumulativa e mais auditavel do que substituir uma string.

---

## 2026-06-19 - Split: UI Automatica Nao Pode Reusar Meteo De Um Par Manual

### Decisao:
A primeira integracao de UI da selecao automatica usa o modo exato e as condicoes
ambientais fixas ja persistidas pelo fluxo Split. O contexto inclui temperatura,
pressao e configuracao processada dos intervalos, e continua delegando correcao
ao motor puro existente.

O modo de sincronizacao meteorologica nao e aplicado nesta rodada. No fluxo manual,
o meteo e resolvido depois que quatro passadas especificas foram escolhidas; no
automatico, cada combinacao possui quatro passadas potencialmente diferentes.
Reutilizar um unico `weather_sync` para todas as combinacoes produziria candidatos
numericamente plausiveis com rastreabilidade ambiental errada. A UI bloqueia essa
execucao e informa a limitacao.

### Licao:
Integracao de UI nao autoriza simplificar dependencia por candidato. Quando uma
entrada varia com a combinacao avaliada, ela deve ser resolvida dentro do contexto
daquela combinacao ou o modo precisa permanecer indisponivel. Um bloqueio explicito
e tecnicamente melhor do que aplicar meteo incorreto silenciosamente.

---

## 2026-06-19 - Split: Origem Algoritmica Nao E Selecao Final

### Decisao:
O Comparativo Final deriva a cor da linha de `algorithm_sources`,
`algorithm_source` e `selection_source`, usando os flags de energia/target apenas
como compatibilidade. Energia, target e origem combinada possuem cores proprias;
o checkbox `selected` continua sendo somente a decisao do usuario para o resultado
final. CV acima de 10% sobrescreve apenas o estilo da celula correspondente.

`split_comparison_pairs` passa por inicializacao idempotente somente quando a chave
nao existe. Renderizar ou navegar entre abas nunca substitui uma lista existente;
limpezas permanecem restritas a acoes explicitas e invalidacoes reais de entrada,
parser ou ambiente.

A tabela de sugestoes e uma projecao dos campos direcionais ja calculados. Cada
candidato gera linhas Ida, Volta e Media, com ausencias exibidas como `N/A`, sem
alterar o motor puro nem inferir valores.

### Licao:
Origem, selecao final e disponibilidade de correcao sao dimensoes independentes de
estado. A UI deve representa-las sem fazer uma substituir a outra, e inicializacao
de session state deve distinguir chave ausente de colecao legitimamente preenchida.

---

## 2026-06-19 - Split: Sugestoes Automaticas Precisam De Hierarquia Por Par

### Decisao:
A secao de candidatos sugeridos renderiza cada candidato em um bloco proprio. O
label publico identifica o bloco uma unica vez e a tabela interna mostra somente
Ida, Volta e Media. A linha Media permanece destacada e Energia continua como a
ultima coluna.

Ausencias sao convertidas para `-` apenas na projecao visual. O helper aceita
`None`, `NaN` e strings sentinela como `N/A`, sem alterar o dicionario do candidato
nem os metadados persistidos.

### Licao:
Quando uma tabela repete uma entidade composta em varias linhas, o identificador
funciona melhor como titulo do grupo. A formatacao de ausencias deve acontecer
depois que o pandas normaliza tipos, pois `None` em coluna numerica pode virar
`NaN` durante a construcao do DataFrame.

---

## 2026-06-19 - Split: Sugestao Pendente Precede O Comparativo

### Decisao:
Executar a selecao automatica passa a preencher somente
`split_auto_selection_pending`. O merge com `split_comparison_pairs` acontece
exclusivamente na acao explicita de adicionar o conjunto revisado. Limpar
sugestoes remove apenas o estado temporario e nunca altera o comparativo.

O orquestrador pode expor uma reserva opcional e limitada na mesma ordem do
ranking energy ou target. A UI usa no minimo 100 itens e cresce ate `k * 5` para
pedidos maiores, evitando que uma pequena alteracao de K seja necessaria apenas
para revelar a proxima substituicao valida, sem persistir o
universo completo de combinacoes. O helper puro de substituicao percorre essa
reserva, ignora identidades ja visiveis e compara os itens completos de
`run_usage` com os demais candidatos quando repeticao esta bloqueada.

### Licao:
Gerar, revisar, adicionar ao comparativo e selecionar para o resultado final sao
quatro transicoes distintas. Representa-las em estados separados evita efeitos
colaterais e permite trocar uma sugestao sem reexecutar formulas ou mudar o
criterio original do ranking.

---

## 2026-06-19 - Split: Candidato De Saida Nao E Conflito Remanescente

### Decisao:
Na substituicao, a assinatura do candidato antigo e tratada separadamente apenas
para impedir uma troca por ele mesmo. Duplicidade e conflito de `run_usage` sao
calculados exclusivamente contra os candidatos que permanecem. O metadata separa
`skipped_old_candidate_count`, `skipped_existing_count` e
`skipped_repeated_count`.

A tabela de sugestoes mostra run e Delta t usando a mesma ordem de fallback do
diagnostico de tempos: `time_components`, campo achatado e registro embutido. Essa
projecao visual nao altera os candidatos.

### Licao:
Remover um item antes de validar seu substituto exige separar identidade do item
de saida de conflitos com o conjunto restante. Reservas curtas dependentes de K
tambem podem imitar um erro de conflito; o limite deve ser explicito e suficiente
para a interacao esperada.

---

## 2026-06-19 - Split: Primeiros N Do Ranking Nao Garantem Reserva Util

### Decisao:
A reserva de substituicao nao e mais um recorte cego dos primeiros candidatos.
O orquestrador percorre o ranking completo e coleta, na ordem, opcoes validas
distribuidas entre as posicoes visiveis, sob o limite
`max(100, k * 10, k + 50)`. O estado recebe `pool_strategy="balanced_v2"`; uma
pendencia antiga fica bloqueada para troca ate nova execucao.

Antes da troca, um `st.dialog` mostra o candidato atual e o proximo candidato em
tabelas completas. Cancelar limpa apenas o pedido; confirmar valida a assinatura
pre-visualizada, executa o helper, registra metadata, limpa o pedido e faz rerun. Falhas
mostram tamanho da pool, quantidade verificada e descartes por candidato antigo,
duplicidade visivel e conflito de passadas.

### Licao:
Uma lista globalmente bem ranqueada pode ser uma reserva ruim para uma restricao
local. Quando cada posicao tem um conjunto diferente de substitutos validos, a
reserva limitada deve ser construida considerando essa utilidade, sem reordenar o
ranking original.

---

## 2026-06-19 - Split: Preview E Aplicacao Compartilham A Mesma Busca

### Decisao:
`find_replacement_candidate()` localiza o primeiro substituto valido e retorna
metadata sem mutar entradas. `replace_pending_candidate()` reutiliza esse helper.
A UI guarda candidatos atual/novo e suas assinaturas no pedido do modal; ao
confirmar, restringe a aplicacao ao candidato mostrado e compara a assinatura
inserida antes de persistir.

Nao existe filtro de CV na substituicao. Os motivos reais de descarte sao:
candidato antigo, identidade ja visivel, conflito exato de `run_usage`, uso
invalido e esgotamento da reserva balanceada.

### Licao:
Confirmacao confiavel exige que preview e escrita nao implementem buscas paralelas.
Guardar e validar uma identidade estavel evita que uma mudanca de estado transforme
o candidato confirmado em outro candidato silenciosamente.

---

## 2026-06-19 - Split: Request Persistido Nao Significa Dialog Aberto

### Decisao:
O modal de substituicao usa dois estados: `split_auto_replace_request` guarda o
preview e `split_auto_replace_dialog_open` autoriza a abertura. `st.dialog` usa
`on_dismiss` para limpar ambos ao fechar pelo X. Cancelar, confirmar, mesclar,
limpar sugestoes e invalidar entradas tambem limpam os dois estados.

Antes de renderizar, a UI saneia requests orfaos, pendencias ja mescladas, pools
obsoletas e ausencia de sugestoes pendentes. O dialog so e chamado quando request
e flag formam um estado acionavel.

### Licao:
Em Streamlit, dados necessarios ao modal e intencao de abri-lo sao estados
diferentes. Vincular abertura apenas a existencia dos dados faz qualquer rerun
reproduzir uma acao antiga; um flag de ciclo de vida e callback de dismiss tornam
a transicao explicita.

---

## 2026-06-22 - Split: Resultado Final E Uma Projecao Da Selecao Explicita

### Decisao:
A pagina Resultados Split e o exportador Excel consomem apenas pares de
`split_comparison_pairs` cujo campo `selected` seja explicitamente `True`. A
consolidacao e o diagnostico permanecem nos helpers puros existentes; a pagina
somente apresenta seus resultados e nao grava selecao nem recalcula formulas.

O relatorio Excel foi isolado em `data/split_exporters.py`, sem importar
Streamlit. Ele reconsolida defensivamente os pares recebidos, preserva as quatro
passadas e a rastreabilidade ambiental, representa ausencias com `-` e trata
pressao apenas como dado de rastreabilidade. Alertas ambientais continuam
limitados a vento acima de 3 m/s e temperatura acima de 35 graus Celsius.

### Licao:
Um estado ausente de selecao nao equivale a selecao positiva. Em relatorios
finais, o filtro deve exigir `selected is True` em todas as fronteiras, inclusive
no core e no exportador. Separar a geracao do workbook da pagina permite testar
conteudo, imutabilidade e dependencia arquitetural sem iniciar o Streamlit.

---

## 2026-06-19 - Split: Analise De Desvios E Diagnostica

### Decisao:
A Analise de desvios do Comparativo Final consome exclusivamente pares com
`selected=True` e nao altera selecao, ordem ou conteudo persistido. O modulo puro
reutiliza a consolidacao de resultados para CV amostral de F0/F2 e a validacao
Split existente para CV dos quatro grupos deltaT e diferenca entre sentidos.

Os limites ambientais iniciais sao parametros diagnosticos: vento acima de 3 m/s
e temperatura acima de 35 graus Celsius geram alerta potencialmente invalidante.
Pressao e exibida para rastreabilidade, mas nao produz reprovacao sem uma regra
explicita. Leave-one-out apenas simula novos CVs e nunca remove o par.

### Licao:
Uma tela de diagnostico deve projetar as mesmas fontes numericas das telas finais,
nao recriar formulas paralelas. Dados insuficientes precisam permanecer
inconclusivos; ausencia de amostra nao equivale a aprovacao nem reprovacao.

---

## 2026-06-22 - Split: Meteo Automatica Deve Ser Resolvida Por Run

### Decisao:
A selecao automatica sincroniza cada run high/low uma unica vez e trabalha sobre
uma copia enriquecida de `split_parsed_runs`. Cada combinacao monta seu
`weather_sync` com as quatro passadas e delega a correcao ao motor Split
existente, que calcula temperatura e pressao medias separadamente para os
sentidos positivo e negativo.

Vento acima de 3 m/s, temperatura acima de 35 graus Celsius e meteorologia
obrigatoria ausente produzem status invalidante parametrizavel. Pressao continua
sem limite de reprovacao. O filtro ocorre depois da geracao/correcao de todos os
candidatos e antes do ranking; desligar o filtro preserva candidatos e warnings.

### Licao:
Sincronizar dentro do produto cartesiano repetiria trabalho e permitiria que a
mesma run recebesse contextos divergentes. Enriquecer as runs primeiro torna a
rastreabilidade deterministica e impede que um pre-ranking sem correcao elimine
candidatos cuja posicao muda com o clima.

---
