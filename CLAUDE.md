# CLAUDE.md — Coastdown MDA Split

> Guia definitivo do projeto. Leia este arquivo inteiro antes de qualquer
> modificação não trivial.

---

## Visão Geral

**Coastdown MDA Split** é uma aplicação Streamlit para análise de coastdown
veicular pelo **método Split**, conforme ABNT NBR 10312.

Repositório: https://github.com/FelipeEckert/coastdown-mda-split
Branch de trabalho: confirme com `git branch --show-current`; não fixe orientação
do projeto a uma branch temporária.

O projeto foi criado a partir do codebase Standard (`cd-streamlit`), mas toda
lógica de método é Split pura. Standard e Split **nunca** se misturam.

---

## Princípio Central

Só reutilize código Standard que seja **neutro de método** (infraestrutura).
Toda lógica Split deve ser revisada, reimplementada e validada explicitamente.

**Reutilizável (neutro):**
- Layout Streamlit e sidebar multi-teste
- Session state e gerenciamento de testes
- Assets, logos, paleta de cores
- `translations.py` e sistema i18n
- Sincronização e carregamento de arquivo meteo
- Infraestrutura de exportação Excel
- Funções utilitárias genéricas

**Não reutilizável (método-específico):**
- Parser e modelo de dados
- Workflow e páginas
- Cálculo de coeficientes
- Regras de validação
- Conteúdo do relatório final

---

## Arquitetura da Aplicação

```
coastdown-mda-split/
├── app.py                          # Entrada Streamlit
├── CLAUDE.md                       # Este arquivo
├── AGENTS.md                       # Regras operacionais para agentes
├── translations.py                 # PT/EN (nunca traduzir termos técnicos)
├── requirements.txt
│
├── .streamlit/
│   └── config.toml
│
├── pages/                          # Páginas do fluxo Split ativo
│   ├── page_2_dados_veiculo.py     # Dados do veículo e massa efetiva
│   ├── page_split_workflow.py      # Entrada, intervalos e parser Split
│   ├── page_split_coefficient_calculation.py  # Cálculo, gráficos e seleção automática
│   ├── page_split_auto_selection.py           # Subaba de seleção automática
│   ├── page_split_final_comparison.py         # Comparativo final e seleção
│   └── page_split_results.py       # Resultados e acionamento da exportação
│
├── core/                           # ⚠️ Módulos puros — sem Streamlit
│   ├── split_calculations.py       # f'0, f'2, ΔV, fórmulas normativas
│   ├── split_corrections.py        # Correção climática f'→F (Split)
│   ├── split_candidate_generation.py  # Geração de candidatos (produto cartesiano)
│   ├── split_candidate_set_validation.py  # Validação normativa de conjuntos
│   ├── split_pair_candidate.py     # Builder de par candidato
│   ├── split_selection_algorithms.py   # Ranking e seleção top-K
│   ├── split_auto_selection.py     # Orquestrador de seleção automática
│   ├── split_time_validation.py    # CV e diferença entre sentidos
│   ├── split_comparison_merge.py   # Merge de candidatos no comparativo
│   ├── split_results.py            # Consolidação final Split
│   ├── split_state.py              # Estado e invalidação do fluxo Split
│   └── split_energy.py             # Cálculo de energia (Split)
│
├── data/
│   ├── loaders.py                  # Leitor VBOX herdado e neutro
│   ├── weather_loader.py           # Carregamento meteorológico
│   ├── split_parser.py             # Parser e rastreabilidade Split
│   └── split_exporters.py          # Workbook Excel Split
│
├── utils/
│   └── file_utils.py
│
└── tasks/
    ├── todo.md                     # Status operacional — sempre atualizar
    └── lessons.md                  # Decisões e lições duráveis
```

---

## Método Split — Conceito

### Diferença fundamental vs. Standard

| Aspecto | Standard | Split |
|---|---|---|
| Entrada | Curva contínua de desaceleração | Dois intervalos de velocidade configurados |
| Saída | F0, F2 por regressão | f'0, f'2 por sistema de 2 equações |
| "Par" | Uma passada + (ida) + uma passada − (volta) | high+, high−, low+, low− (4 componentes) |
| Validação principal | CV F0/F2 ≤ 10% | CV Δt ≤ 2,5% por grupo; \|Δmédias\| ≤ 10% entre sentidos |

### Intervalos padrão (norma — só defaults, não hardcode)

```
Alta velocidade:  90 → 70 km/h   Velocidade de referência V2 = 80 km/h
Baixa velocidade: 45 → 35 km/h   Velocidade de referência V1 = 40 km/h
```

### Convenção ΔV

```python
delta_v = abs(v_initial - v_final)   # sempre positivo
# NUNCA: delta_v = v_final - v_initial
```

---

## Equações Normativas (ABNT NBR 10312 — §5.2.1.6)

### Força resistiva por período

```
F = Me × (ΔV / Δt)
```

### Coeficientes f'0 e f'2

```
f'0 = Me / (V2² - V1²) × [(ΔV2/Δt2)×V1² − (ΔV1/Δt1)×V2²]

f'2 = Me / (V2² - V1²) × [(ΔV1/Δt1) − (ΔV2/Δt2)]
```

Onde:
- `V1`, `V2` = velocidades de referência (baixa e alta), em m/s
- `ΔV1`, `ΔV2` = intervalos de velocidade centrados em V1 e V2, em m/s
- `Δt1`, `Δt2` = tempo médio de desaceleração em cada intervalo, em s
- `Me` = massa efetiva do veículo, em kg

### Cadeia de massa normativa

```
M  = massa em ordem de marcha + 136 kg
me = valor informado pelo usuário  OU  3% de M
Me = M + me
```

### Correção climática (f'→F)

Implementada em `core/split_corrections.py`. F2 inclui conversão de
`N/(m/s)²` para `N/(km/h)²` pelo fator 12,96.

---

## Validação Normativa (§5.2.1.6.3)

Duas restrições — aplicadas sobre o **conjunto** K de pares selecionados:

```
1. CV amostral de Δt ≤ 2,5%
   Calculado separadamente para: high+, high−, low+, low−

2. Diferença entre médias de sentidos opostos ≤ 10%
   Calculado separadamente para: alta velocidade e baixa velocidade
```

**Importante:** CV de F0/F2 é **diagnóstico apenas** — não reprova candidatos
na seleção automática (decisão normativa documentada em `tasks/lessons.md`
2026-06-24).

Uma amostra única mantém CV inconclusivo — não falha automaticamente.

---

## Algoritmo de Seleção Automática — Arquitetura Atual

### Pipeline (em ordem de execução)

```
split_parsed_runs
       │
       ▼
generate_full_split_candidates_exact()   ← GARGALO PRINCIPAL
  split_candidate_generation.py
  Produto cartesiano: high+ × high− × low+ × low−
  Cada combinação: cálculo f'0/f'2 + correção + energia
  Exemplo: 12⁴ = 20.736 candidatos gerados
       │
       ▼
rank_candidates_by_energy()  ou  rank_candidates_by_target()
  split_selection_algorithms.py
       │
       ▼
select_top_k_candidates_with_constraints_v2()   ← constraint-first
  Pool: max(80, k×20, k+40)
  Limite: 3.000 conjuntos avaliados + 30s timeout
  Valida CV Δt e diferença entre sentidos no conjunto completo
       │
       ▼
Resultado aprovado  ou  Fallback explícito (confirmação do usuário)
```

### Diagnóstico histórico de desempenho

Antes da implementação do pré-filtro MAD, o custo principal estava na
**geração**, não na busca constrained. Com 12 runs por grupo,
`build_algorithm_split_pair_candidate` é chamado 12⁴ = 20.736 vezes, cada
chamada fazendo cálculo completo (f'0/f'2 + correção climática + energia).
O pré-filtro atual reduz os grupos antes desse produto; o limite explícito de
combinações continua protegendo conjuntos grandes.

---

## Algoritmo de Seleção Automática — Pré-filtro Implementado

### Comportamento atual

Reduzir o pool de cada grupo (high+, high−, low+, low−) **antes** do produto
cartesiano, usando apenas os Δt brutos dos runs — sem cálculo de coeficientes.

### Heurística

Uma run cujo Δt é outlier no seu grupo muito provavelmente vai puxar o CV
acima de 2,5% em qualquer conjunto que ela entre. Filtrar esses outliers antes
da geração reduz o produto cartesiano drasticamente sem sacrificar a qualidade
do resultado.

Exemplo: 12 → 8 runs por grupo reduz de 12⁴ = 20.736 para 8⁴ = 4.096
candidatos — redução de **5×**.

### Método: MAD (Median Absolute Deviation)

MAD é mais robusto que média + desvio padrão para detectar outliers em amostras
pequenas (5–15 elementos):

```python
median = statistics.median(delta_t_values)
mad    = statistics.median([abs(x - median) for x in delta_t_values])
threshold = median + multiplier × mad   # multiplier padrão: 2.5
```

Uma run é marcada como outlier se seu Δt ultrapassar o threshold.

### Regras de segurança

1. **Pool mínimo garantido:** o pré-filtro nunca reduz um grupo abaixo de
   `min(len(group), min_pool_size)` runs. O orquestrador usa
   `min_pool_size = max(k + 2, 4)`.
   Se o filtro removeria demais, relaxa o threshold até preservar o mínimo.

2. **Grupo pequeno (< 3 runs):** pré-filtro é pulado — sem runs suficientes
   para calcular MAD com significância.

3. **MAD = 0:** todos os Δt são idênticos — sem outliers, pulado.

4. **Rastreabilidade:** metadata deve registrar quantas runs foram filtradas
   por grupo e qual threshold foi usado.

5. **Parâmetros configuráveis:** `mad_multiplier` (default 2.5) e
   `min_pool_size`, calculado pelo orquestrador.

### Ownership

**Arquivo:** `core/split_candidate_generation.py`

**Função pura:**
```python
def filter_group_by_mad(
    records: list[dict],
    *,
    mad_multiplier: float = 2.5,
    min_pool_size: int = 4,
) -> tuple[list[dict], dict]:
    """
    Remove outliers de Δt de um grupo por MAD.
    Retorna (lista_filtrada, metadata_do_filtro).
    Nunca reduz abaixo de min_pool_size.
    """
```

`generate_full_split_candidates_exact()` aplica o filtro antes de enumerar o
produto cartesiano e registra diagnósticos por grupo.

**Parâmetros da geração:**
```python
def generate_full_split_candidates_exact(
    split_parsed_runs: dict,
    *,
    vehicle_data: dict,
    correction_context: dict | None = None,
    candidate_builder=None,
    max_combinations: int | None = None,
    progress_callback=None,
    use_mad_prefilter: bool = True,
    mad_multiplier: float = 2.5,
    mad_min_pool_size: int = 4,
) -> tuple[list[dict], dict]:
```

### Integração com o orquestrador

`run_split_auto_selection_exact()` em `split_auto_selection.py` passa k para
o gerador e calcula `mad_min_pool_size = max(requested_k + 2, 4)`.

### Limites de ownership

- A busca constrained (`select_top_k_candidates_with_constraints_v2`) não muda.
- O validador de conjuntos (`validate_split_candidate_set`) não muda.
- O ranking (energia ou target) não muda.
- O fallback explícito não muda.
- O filtro pertence a `split_candidate_generation.py`; a configuração pertence
  ao orquestrador `split_auto_selection.py`.

---

## Session State — Estrutura Multi-Teste

```python
st.session_state.tests = {
    "test_1": {
        "id": "test_1",
        "name": "Teste A — Veículo X",
        "created_at": "2026-06-01 10:00:00",
        "status": "complete",           # 'incomplete' | 'complete'

        # Arquivos
        "split_input_mode": "separate", # 'separate' | 'combined'
        "split_input_version": 1,       # incrementa ao trocar arquivo

        # Dados do veículo
        "vehicle_info": {
            "model": "...",
            "test_date": "...",
            "running_order_mass_kg": 1300.0,
            "rotational_equivalent_mass_kg": 50.0,
            "effective_mass_kg": 1350.0,
        },
        "total_mass": 1300.0,

        # Resultados Split
        "split_parsed_runs": {...},     # saída do parser
        "split_comparison_pairs": [...],# pares calculados
        "split_auto_selection_pending": {...}, # ou None
        "split_final_results": {...},
        "excel_buffer": None,
    }
}
st.session_state.active_test_id = "test_1"
```

---

## Sistema i18n

```python
from translations import get_translator
t = get_translator(lang)   # lang = "pt" ou "en"

# Uso nas páginas:
def render(t):
    st.header(t("vehicle_data"))
    st.button(t("save"))
```

**Nunca traduzir:** Coastdown, F0, F2, f'0, f'2, Standard, Split, CV,
ABNT 10312, MDA, ΔV, Δt, Me, MAD.

---

## Regras de Desenvolvimento

### Antes de qualquer mudança não trivial

1. Ler este `CLAUDE.md`
2. Inspecionar o código atual dos arquivos envolvidos
3. Fazer um plano curto de implementação
4. Manter mudanças mínimas
5. Evitar refatorações não relacionadas

### Sempre

- `python -m py_compile <arquivo>` após cada modificação
- Adicionar arquivos ao stage individualmente
- Atualizar `tasks/todo.md` e `tasks/lessons.md` ao final de cada tarefa
- Funções puras em `core/` — sem imports de Streamlit

### Nunca

- `git add .`
- Misturar lógica Standard e Split
- Alterar fórmulas silenciosamente
- Hardcodar intervalos de velocidade
- Assumir formato de arquivo de entrada

---

## Paleta de Cores (Tema Escuro)

```python
BACKGROUND_PRIMARY   = "#0e1117"
BACKGROUND_SECONDARY = "#1e1e1e"
TEXT_PRIMARY         = "#ffffff"
TEXT_SECONDARY       = "#a0a0a0"
ACCENT_BLUE          = "#4a9eff"   # teste ativo
ACCENT_GREEN         = "#4caf50"   # sucesso / aprovado
ACCENT_ORANGE        = "#ff9800"   # aviso / fallback
ACCENT_RED           = "#f44336"   # erro / reprovado
ALGO_ENERGY          = "#D1FFBD"   # verde claro
ALGO_TARGET          = "#ADD8E6"   # azul claro
BORDER_DEFAULT       = "#3d3d3d"
BORDER_ACTIVE        = "#4a9eff"
```

---

## Stack Tecnológica

- Python 3.11+
- Streamlit 1.55+
- Pandas, NumPy, Plotly
- openpyxl (exportação Excel)

---

## Como Rodar

```bash
pip install -r requirements.txt
streamlit run app.py
# http://localhost:8501
```

---

## Rastreamento

- `tasks/todo.md` — status operacional: pendente, em andamento, feito,
  descoberto durante desenvolvimento
- `tasks/lessons.md` — decisões técnicas e lições duráveis

Toda mudança funcional deve atualizar os dois arquivos antes do commit final.

---

**Última atualização:** 2026-07-21
**Autor:** Felipe Eckert
**Status:** fluxo Split ativo, incluindo seleção automática com pré-filtro MAD
