# Coastdown MDA - Multi-Test Analysis Platform

## 🎯 Visão Geral do Projeto

**Coastdown MDA** é uma plataforma de análise multi-teste para dados de coastdown veicular segundo norma **ABNT 10312**. Inspirado no ETAS MDA (Measure Data Analyzer), permite carregar, analisar e comparar múltiplos testes simultaneamente.

### Escopo Atual
- **Método suportado:** Standard APENAS (método Split será software separado)
- **Fase de desenvolvimento:** v1.0 - Interface de gerenciamento de testes
- **Base de código:** Migração de PyQt5 → Streamlit (versão v16)

---

## 🏗️ Arquitetura da Aplicação

### Conceito Visual (Inspirado no ETAS MDA)

```
┌─────────────────────────────────────────────────────────┐
│  [Logo] Coastdown MDA                    [Config] [Help]│
├───────────────┬─────────────────────────────────────────┤
│               │                                         │
│  SIDEBAR      │         ÁREA PRINCIPAL                  │
│  Tests        │                                         │
│               │  ┌───────────────────────────────────┐  │
│ ┌───────────┐ │  │                                   │  │
│ │ + Novo    │ │  │     Análise do Teste Ativo        │  │
│ │   Teste   │ │  │                                   │  │
│ └───────────┘ │  │  [Pares] [Gráficos] [Algoritmos] │  │
│               │  │                                   │  │
│ ┌───────────┐ │  │                                   │  │
│ │ ✅ Teste A│◄──┼──┤  Dados, tabelas, visualizações  │  │
│ │ Veic. X   │ │  │                                   │  │
│ │ 📁📊      │ │  └───────────────────────────────────┘  │
│ └───────────┘ │                                         │
│               │                                         │
│ ┌───────────┐ │                                         │
│ │ ✅ Teste B│ │                                         │
│ │ Veic. Y   │ │                                         │
│ │ 📁📊      │ │                                         │
│ └───────────┘ │                                         │
│               │                                         │
│ ┌───────────┐ │                                         │
│ │ ⚠️ Teste C│ │                                         │
│ │ Veic. Z   │ │                                         │
│ │ 📁❌      │ │  (falta arquivo meteo)                 │
│ └───────────┘ │                                         │
└───────────────┴─────────────────────────────────────────┘
```

### Componentes Principais

#### 1. **Sidebar - Gerenciador de Testes**
- **Botão "+ Novo Teste"**: Abre modal para criar teste
- **Cards de Teste**: Mini-cards mostrando:
  - Nome do teste (editável)
  - Status dos arquivos (✅ CSV | ✅ Meteo)
  - Ícone de teste ativo (destaque visual)
  - Botões: Editar | Duplicar | Remover

#### 2. **Área Principal - Análise**
- Exibe análise do teste **selecionado** na sidebar
- Mantém toda a lógica das páginas 2-6 da v16:
  - Dados do veículo
  - Análise de pares
  - Seleção por algoritmo
  - Comparativo final
  - Resultados

#### 3. **Comparativo Multi-Teste** (Futuro - Fase 2)
- Opção especial na sidebar: "📊 Comparar Testes"
- Seleciona múltiplos testes
- Gráficos sobrepostos
- Tabela comparativa

---

## 📂 Estrutura de Arquivos (Atual v16)

```
coastdown_streamlit/
├── app.py                          # App principal Streamlit
├── CLAUDE.md                       # Este arquivo (contexto)
├── config.py                       # Configurações
├── translations.py                 # PT/EN
├── requirements.txt                # Dependências
│
├── .streamlit/
│   └── config.toml                # Config Streamlit
│
├── pages/                          # Páginas do fluxo (v16)
│   ├── page_1_abrir_teste.py      # [OBSOLETO] Será substituído
│   ├── page_2_dados_veiculo.py    # ✅ Reutilizar
│   ├── page_3_analise_pares.py    # ✅ Reutilizar
│   ├── page_4_selecao_algoritmo.py # ✅ Reutilizar
│   ├── page_5_comparativo.py      # ✅ Reutilizar
│   └── page_6_resultados.py       # ⚠️ Reutilizar (tem bug)
│
├── core/                           # ⚠️ NÃO MODIFICAR (código validado)
│   ├── __init__.py
│   ├── calculations.py            # Cálculos F0, F2, energia
│   └── corrections.py             # Correção climática
│
├── data/                          
│   ├── __init__.py
│   ├── loaders.py                 # Carrega CSV, meteo
│   └── exporters.py               # Exporta Excel
│
└── utils/
    ├── __init__.py
    └── file_utils.py              # Utilitários
```

---

## 🔑 Estrutura de Dados

### Session State - Workspace Multi-Teste

```python
st.session_state.tests = {
    "test_1": {
        "id": "test_1",
        "name": "Teste A - Veículo X",
        "created_at": "2024-03-11 14:30:00",
        "status": "complete",  # 'incomplete' | 'complete'
        
        # Arquivos carregados
        "files": {
            "csv_loaded": True,
            "csv_path": "C:/data/teste_a.csv",
            "meteo_loaded": True,
            "meteo_path": "C:/data/meteo_a.csv"
        },
        
        # Dados do teste (da v16)
        "data_loaded": True,
        "all_run_data": {...},              # Dict de runs
        "vehicle_data_complete": True,
        "total_mass": 1500.0,
        "ref_vel_alta": 120.0,
        "ref_vel_baixa": 40.0,
        
        # Pares calculados (da v16)
        "calculated_pairs": {
            "1/2": {
                "pair_id": "1/2",
                "f0_corr": 110.1802,
                "f2_corr": 0.043108,
                "energy": 5.3974,
                "cv_f0": 14.64,
                "cv_f2": 4.30,
                "selected": False,
                "selected_by_energy_algo": False,
                "selected_by_target_algo": False
            },
            # ... mais pares
        },
        
        # Pares finais selecionados
        "pares_finais_selecionados": ["1/2", "3/4", "5/6"],
        
        # Resultados finais
        "final_results": {
            "mean_f0": 110.5,
            "mean_f2": 0.043,
            "cv_f0": 12.3,
            "cv_f2": 5.1,
            "energy": 5.4,
            "num_pairs": 5
        }
    },
    
    "test_2": {
        # Estrutura idêntica
        # ...
    }
}

# Teste ativo (exibido na área principal)
st.session_state.active_test_id = "test_1"

# Configurações globais
st.session_state.app_config = {
    "theme": "dark",
    "language": "pt",
    "auto_save": True
}
```

---

## 🎨 Design da Sidebar (Prioridade FASE 1)

### Card de Teste - Especificação

Cada card deve ter:

```
┌─────────────────────────────────┐
│ ✅ Teste A - Veículo X          │ ◄─ Nome (editável inline)
├─────────────────────────────────┤
│ 📁 CSV:   ✅ teste_a.csv        │ ◄─ Status arquivo CSV
│ 📊 Meteo: ✅ meteo_a.csv        │ ◄─ Status arquivo meteo
├─────────────────────────────────┤
│ [📝 Editar] [📋 Duplicar] [🗑️]  │ ◄─ Ações
└─────────────────────────────────┘
```

### Estados Visuais

| Status | Cor de Fundo | Borda | Descrição |
|--------|-------------|-------|-----------|
| **Ativo** | `#2d4a7c` | 2px solid `#4a9eff` | Teste selecionado |
| **Completo** | `#1e1e1e` | 1px solid `#3d3d3d` | Tudo OK |
| **Incompleto** | `#1e1e1e` | 1px solid `#ff9800` | Falta arquivo |
| **Erro** | `#1e1e1e` | 1px solid `#f44336` | Erro no carregamento |

### Modal "+ Novo Teste"

Ao clicar em "+ Novo Teste", abre modal:

```
┌────────────────────────────────────┐
│  Criar Novo Teste                  │
├────────────────────────────────────┤
│                                    │
│  Nome do Teste:                    │
│  [Teste A - Veículo X________]     │
│                                    │
│  Arquivo CSV (dados do teste):     │
│  [Selecionar arquivo...]  [📁]     │
│                                    │
│  Arquivo Meteorológico (opcional): │
│  [Selecionar arquivo...]  [📁]     │
│                                    │
│  ┌──────────────────────────────┐  │
│  │  ⚠️ Dados Fixos              │  │
│  │  (se não tiver meteo)        │  │
│  │                              │  │
│  │  Temperatura: [25.0] °C      │  │
│  │  Pressão:     [101.3] kPa    │  │
│  └──────────────────────────────┘  │
│                                    │
│      [Cancelar]  [Criar Teste]     │
└────────────────────────────────────┘
```

---

## 🔄 Fluxo de Usuário (UX)

### Workflow Típico

1. **Iniciar aplicação**
   - Sidebar vazia (sem testes)
   - Área principal: mensagem "Crie ou carregue um teste para começar"

2. **Criar primeiro teste**
   - Clica "+ Novo Teste"
   - Preenche nome
   - Carrega CSV
   - Carrega meteo (ou insere T/P fixas)
   - Clica "Criar Teste"

3. **Análise automática**
   - Card aparece na sidebar
   - Teste é ativado automaticamente
   - Área principal carrega dados do veículo (página 2 da v16)

4. **Análise de pares**
   - Usuário navega pelas sub-abas:
     - Dados do Veículo
     - Análise de Pares
     - Seleção por Algoritmo
     - Comparativo Final
     - Resultados

5. **Adicionar mais testes**
   - Clica "+ Novo Teste" novamente
   - Repete processo
   - Agora tem 2+ testes na sidebar

6. **Alternar entre testes**
   - Clica em qualquer card da sidebar
   - Área principal atualiza para mostrar dados daquele teste

7. **Comparar testes** (Futuro - Fase 2)
   - Clica em "📊 Comparar Testes"
   - Seleciona quais testes comparar
   - Vê gráficos/tabelas lado a lado

---

## 🛠️ Tarefas de Desenvolvimento - FASE 1

### Prioridade ALTA (Fazer AGORA com Claude Code)

- [ ] **1. Refatorar app.py**
  - Criar sidebar moderna
  - Implementar gerenciador de testes
  - Modal "+ Novo Teste"

- [ ] **2. Criar componente TestCard**
  - Visual moderno (cards estilo MDA)
  - Estados visuais (ativo/completo/erro)
  - Ações inline (editar/duplicar/remover)

- [ ] **3. Adaptar Session State**
  - Migrar de `st.session_state.calculated_pairs` único
  - Para `st.session_state.tests[test_id].calculated_pairs`
  - Manter compatibilidade com páginas 2-6

- [ ] **4. Integrar páginas existentes**
  - Páginas 2-6 devem ler dados do `active_test_id`
  - Função helper: `get_active_test()` → retorna dict do teste ativo
  - **NÃO reescrever lógica de cálculos!**

### Prioridade MÉDIA (Depois da Fase 1)

- [ ] **5. Testar Página 6**
  - Verificar se resultados aparecem corretamente
  - Testar com múltiplos testes
  - Validar exportação

- [ ] **6. Sistema de salvamento**
  - Salvar workspace em JSON/pickle
  - Botão "Salvar Projeto"
  - Botão "Abrir Projeto"

- [ ] **7. Melhorias UX**
  - Drag & drop de arquivos
  - Atalhos de teclado
  - Tooltips informativos

### Prioridade BAIXA (Fase 2 - Futuro)

- [ ] **7. Comparativo multi-teste**
  - Seleção de múltiplos testes
  - Gráficos sobrepostos
  - Tabela comparativa

- [ ] **8. Exportação avançada**
  - Relatório PDF multi-teste
  - Excel com múltiplas abas (um teste por aba)

---

## 🤖 Claude Code - Workflow Orchestration

### Diretrizes de Trabalho

Estas são instruções **específicas para o Claude Code** ao trabalhar neste projeto.

#### 1. Plan Mode Default ⚡
- **SEMPRE** entrar em modo planejamento para tarefas não-triviais (3+ passos ou decisões arquiteturais)
- Se algo der errado, **PARAR** e replanejar imediatamente - não continuar empurrando
- Usar modo planejamento para etapas de verificação, não apenas construção
- Escrever specs detalhadas antecipadamente para reduzir ambiguidade

**Exemplo:**
```
Antes de refatorar app.py:
1. Analisar estrutura atual
2. Planejar migração Session State
3. Listar arquivos a modificar
4. Verificar compatibilidade com páginas 2-6
5. Só então executar
```

#### 2. Subagent Strategy 🔀
- Usar subagentes liberalmente para manter janela de contexto limpa
- Delegar pesquisa, exploração e análise paralela para subagentes
- Para problemas complexos, jogar mais compute via subagentes
- **Uma tarefa por subagent** para execução focada

**Quando usar subagents:**
- Analisar múltiplos arquivos simultaneamente
- Pesquisar padrões em codebase grande
- Validar compatibilidade entre componentes
- Explorar soluções alternativas

#### 3. Self-Improvement Loop 📚
- Após **QUALQUER** correção do usuário: atualizar `tasks/lessons.md` com o padrão
- Escrever regras para si mesmo que previnem o mesmo erro
- Iterar implacavelmente nestas lições até taxa de erro cair
- Revisar lições no início da sessão para projetos relevantes

**Exemplo de lesson.md:**
```markdown
## Lição: Session State Multi-Teste

### Erro:
Tentei modificar `st.session_state.calculated_pairs` diretamente, 
quebrando compatibilidade com páginas 2-6.

### Correção:
Criar helper `get_active_test()` que retorna os dados do teste ativo.
Páginas continuam acessando `calculated_pairs` mas via helper.

### Regra:
Sempre manter retrocompatibilidade ao refatorar Session State.
Usar abstração (helpers) ao invés de quebrar interfaces.
```

#### 4. Verification Before Done ✓
- **NUNCA** marcar tarefa como completa sem provar que funciona
- Fazer diff entre main e suas mudanças quando relevante
- Perguntar a si mesmo: "Um engenheiro sênior aprovaria isso?"
- Rodar testes, checar logs, demonstrar correção

**Checklist antes de "Done":**
- [ ] Código roda sem erros
- [ ] Testes passam (ou criar se não existir)
- [ ] Compatibilidade verificada
- [ ] i18n implementado (PT/EN)
- [ ] Comentários em português
- [ ] Commit message descritivo

#### 5. Demand Elegance (Balanceado) 🎨
- Para mudanças não-triviais: pausar e perguntar "há uma forma mais elegante?"
- Se um fix parece hacky: "Sabendo tudo que sei agora, implementar a solução elegante"
- **Pular para fixes simples e óbvios** - não over-engineer
- Desafiar seu próprio trabalho antes de apresentar

**Critérios de elegância:**
- Código legível e autodocumentado
- Princípio DRY (Don't Repeat Yourself)
- Separation of concerns
- Mínimo de dependências
- Fácil de testar

#### 6. Autonomous Bug Fixing 🔧
- Quando receber report de bug: apenas conserte. Não pedir hand-holding
- Apontar para logs, errors, failing tests → então resolver
- Zero context switching necessário do usuário
- Ir consertar testes CI que falharem sem ser avisado

**Workflow de bug:**
```
1. Reproduzir o bug
2. Identificar root cause
3. Implementar fix
4. Adicionar teste para prevenir regressão
5. Documentar em lessons.md se for padrão
```

---

### Task Management 📋

#### Estrutura de Arquivos

```
tasks/
├── todo.md          # Checklist de tarefas
└── lessons.md       # Lições aprendidas
```

#### 1. **Plan First** ⭐⭐
Escrever plano em `tasks/todo.md` com itens checkáveis:

```markdown
# FASE 1 - Sidebar Moderna

## Tarefas
- [ ] Analisar app.py atual
- [ ] Criar componente TestCard
- [ ] Implementar modal "+ Novo Teste"
- [ ] Adaptar Session State para multi-teste
- [ ] Testar compatibilidade com páginas 2-6

## Notas
- Manter páginas 2-6 intactas
- Todos textos com t() para i18n
- Seguir paleta de cores do CLAUDE.md
```

#### 2. **Verify Plan** ✓
Checar antes de começar implementação:
- [ ] Todos os passos estão claros?
- [ ] Há dependências entre tarefas?
- [ ] Algum passo precisa de research primeiro?

#### 3. **Track Progress** 📊
Marcar itens completos conforme avança:
```markdown
- [x] Analisar app.py atual
- [x] Criar componente TestCard
- [ ] Implementar modal "+ Novo Teste"  ← trabalhando aqui
```

#### 4. **Explain Changes** 💬
Ao final de cada passo, resumo de alto nível:
```
✅ Componente TestCard criado
- Visual moderno com estados (ativo/completo/erro)
- Ações inline (editar/duplicar/remover)
- Totalmente i18n (PT/EN)
```

#### 5. **Document Results** 📝
Adicionar seção de review em `tasks/todo.md`:
```markdown
## Review - FASE 1 Concluída

### O que funcionou:
- Sidebar moderna implementada
- Cards visuais estilo MDA
- Multi-teste funcionando

### Desafios:
- Session State precisou de mais refatoração que esperado
- Compatibilidade com página 3 exigiu helper adicional

### Próximos passos:
- Testar com dados reais
- Implementar salvamento de workspace
```

#### 6. **Capture Lessons** 📚
Atualizar `tasks/lessons.md` após correções do usuário:
```markdown
## 2024-03-11 - Session State Refactoring

### Contexto:
Refatoração para suportar múltiplos testes simultâneos.

### Erro Original:
Quebrei páginas 2-6 ao mudar estrutura do Session State.

### Solução:
Criar função `get_active_test()` que abstrai acesso ao teste ativo.
Páginas continuam usando mesma interface.

### Lição:
Sempre manter retrocompatibilidade. Usar abstração via helpers.
Testar integração ANTES de considerar tarefa completa.
```

---

### Core Principles 🎯

#### ⭐⭐ Simplicity First
- Fazer cada mudança o mais simples possível
- Impacto mínimo no código existente
- Se precisa mudar 10 arquivos, replanejar

**Perguntas guia:**
- Posso fazer isso com menos código?
- Há uma solução mais direta?
- Estou over-engineering?

#### ⭐⭐ No Laziness
- Encontrar root causes, não sintomas
- Sem temporary fixes ou TODOs
- Padrões de engenheiro sênior
- Se não sabe como fazer direito, pesquisar primeiro

**Red flags:**
- "Vou fazer um quick fix agora e arrumar depois" ❌
- "Funciona mas não sei por quê" ❌
- "TODO: refatorar isso" ❌

#### ⭐⭐ Minimal Impact
- Mudanças devem tocar apenas o necessário
- Evitar introduzir bugs em código funcionando
- Refatoração incremental, não Big Bang

**Checklist:**
- [ ] Apenas arquivos estritamente necessários modificados?
- [ ] Código que funciona permanece intacto?
- [ ] Mudanças são reversíveis facilmente?

---

### Comunicação com Usuário 💬

#### Formato de Updates

**Ao iniciar tarefa:**
```
🎯 Iniciando: Refatoração do app.py para sidebar moderna

Plano:
1. Analisar estrutura atual
2. Criar componente TestCard
3. Implementar gerenciador de testes
4. Testar compatibilidade

Vou começar pela análise...
```

**Durante execução:**
```
✅ Step 1/4 completo: Estrutura atual analisada
- app.py tem 256 linhas
- Session State usa estrutura simples
- Páginas 2-6 acessam calculated_pairs diretamente

Próximo: Criar componente TestCard...
```

**Ao concluir:**
```
✅ Tarefa concluída: Sidebar moderna implementada

Mudanças:
- app.py refatorado (sidebar + gerenciador)
- Novo: components/test_card.py
- Session State adaptado (retrocompatível)
- Todas páginas testadas e funcionando
- i18n completo (PT/EN)

Pronto para testar!
```

#### Quando Pedir Ajuda

**Perguntar ao usuário APENAS se:**
- Decisão de UX/design (cor, layout, texto)
- Regra de negócio ambígua
- Trade-off que afeta experiência do usuário
- Dados de teste necessários

**NÃO perguntar:**
- Como implementar algo técnico (pesquisar!)
- Se deve seguir as regras (sempre seguir!)
- Permissão para consertar bugs (apenas conserte!)

---

### Exemplo de Sessão Ideal 🌟

```
👤 Usuário:
Vamos começar a FASE 1. Preciso da sidebar moderna com 
gerenciamento de testes.

🤖 Claude Code:
🎯 Entendido! Vou implementar a sidebar moderna conforme 
especificado no CLAUDE.md.

📋 Plano (criando tasks/todo.md):
- [ ] Analisar app.py atual
- [ ] Criar componente TestCard  
- [ ] Implementar modal "+ Novo Teste"
- [ ] Adaptar Session State
- [ ] Verificar compatibilidade páginas 2-6

Começando pela análise do app.py...

[Trabalha autonomamente]

✅ Análise completa! 
- Estrutura atual identificada
- Pontos de integração mapeados
- Plano de refatoração validado

Próximo: Implementando componente TestCard...

[Continua trabalhando]

✅ FASE 1 Concluída!

Implementado:
✓ Sidebar moderna com cards estilo MDA
✓ Gerenciador de testes funcional
✓ Modal "+ Novo Teste" com validação
✓ Session State multi-teste (retrocompatível)
✓ Todas páginas 2-6 testadas e funcionando
✓ i18n completo (PT/EN)
✓ Commits descritivos feitos

Pronto para uso! Quer testar ou seguir para próxima fase?

👤 Usuário:
Perfeito! Vamos testar...
```

---

## 📝 Convenções de Código

### Nomenclatura
- **Variáveis:** `snake_case`
- **Funções:** `snake_case`
- **Constantes:** `UPPER_CASE`
- **Classes:** `PascalCase` (se usar)

### Session State
- **SEMPRE** usar `st.session_state` para estado global
- **NUNCA** usar variáveis globais Python
- Inicializar no `app.py` antes de renderizar páginas

### Arquivos Core
- **NÃO MODIFICAR** `core/calculations.py` sem necessidade
- **NÃO MODIFICAR** `core/corrections.py` sem necessidade
- Estes arquivos são validados e funcionam corretamente no PyQt5

### Tradução
- Usar função `t()` para textos visíveis
- Inglês como fallback
- Adicionar novas chaves em `translations.py`
- Ver seção completa de i18n abaixo para detalhes

### Cores de Algoritmos
- Verde `#D1FFBD` = Selecionado por Energia
- Azul `#ADD8E6` = Selecionado por Target
- Manter consistência em todas as páginas

---

## 🌍 Internacionalização (i18n)

### Sistema de Tradução

O app utiliza um sistema baseado em dicionário Python (`translations.py`) com função helper `t()`.

**Idiomas suportados:**
- 🇧🇷 Português (pt) - Padrão
- 🇺🇸 Inglês (en)

### Como Funciona

```python
# translations.py
TRANSLATIONS = {
    "pt": {
        "app_title": "Coastdown MDA - Análise Multi-Teste",
        "save": "Salvar",
        "cancel": "Cancelar",
        # ... mais traduções
    },
    "en": {
        "app_title": "Coastdown MDA - Multi-Test Analysis",
        "save": "Save",
        "cancel": "Cancel",
        # ... more translations
    }
}

def get_translator(language="pt"):
    """Retorna função de tradução para o idioma."""
    def translate(key, **kwargs):
        translation = TRANSLATIONS.get(language, TRANSLATIONS["pt"]).get(key, key)
        if kwargs:
            return translation.format(**kwargs)
        return translation
    return translate
```

### Uso no Código

**No app.py (raiz):**
```python
from translations import get_translator

# Seletor de idioma
lang_options = {"🇧🇷 Português": "pt", "🇺🇸 English": "en"}
selected_lang = st.sidebar.selectbox(
    "Language / Idioma",
    options=list(lang_options.keys())
)

# Obter tradutor
t = get_translator(lang_options[selected_lang])
st.title(t("app_title"))
```

**Nas páginas:**
```python
def render(t):
    """t = função de tradução passada do app.py"""
    st.header(t("vehicle_data"))
    st.button(t("save"))
```

### Regras Importantes

✅ **SEMPRE traduzir:**
- Botões, menus, labels
- Mensagens de erro/sucesso
- Tooltips e ajudas
- Títulos de páginas

❌ **NUNCA traduzir (termos técnicos):**
- "Coastdown", "F0", "F2"
- "Standard", "Split"
- "CV" (Coefficient of Variation)
- "ABNT 10312", "MDA"

### Interpolação de Valores

```python
# No translations.py:
"error_cv_exceeded": "CV de {percent}% excede {limit}%"

# No código:
t("error_cv_exceeded", percent=15.2, limit=10)
# PT: "CV de 15.2% excede 10%"
# EN: "CV of 15.2% exceeds 10%"
```

### Adicionando Nova Tradução

1. Adicione a chave em PT e EN no `translations.py`
2. Use `t("nova_chave")` no código
3. Teste em ambos os idiomas
4. Commit: `git commit -m "i18n: adiciona tradução X"`

### Checklist i18n

Ao criar nova feature:
- [ ] Todos textos usam `t()`
- [ ] Chaves em PT e EN
- [ ] Termos técnicos sem tradução
- [ ] Testado em ambos idiomas

---

## 🧮 Conceitos de Coastdown (Referência)

### Método Standard
- **Um arquivo CSV** com múltiplas runs
- **Pares formados:** passada ida (+) com passada volta (-)
- **Correção climática:** Aplicada individualmente por passada ANTES de calcular médias
- **Coeficientes:** F0 (N), F2 (N/(km/h)²)
- **Validação:** CV ≤ 10% para Standard

### Equações Principais

#### Força de Resistência
```
F_total = F0 + F2 × v²

Onde:
F0 = Resistência constante (atrito rolamento, etc)
F2 = Resistência aerodinâmica
v  = Velocidade (km/h)
```

#### Energia por km
```
E = (F0 / 3.6) + (F2 × v_ref² / 3.6)

Onde v_ref é a velocidade de referência (120 km/h normalmente)
```

#### Correção Climática
```
F0_corr = F0 × (ρ_ref / ρ_test)
F2_corr = F2 × (ρ_ref / ρ_test)

Onde:
ρ_test = (P_test / (R × T_test))
ρ_ref  = (P_ref / (R × T_ref))
P_ref  = 101.3 kPa
T_ref  = 293.15 K (20°C)
R      = 287.058 J/(kg·K)
```

---

## 🎯 Objetivos da Fase 1

### Critérios de Sucesso

✅ **Interface moderna e profissional**
- Sidebar com gerenciamento de testes
- Cards visuais estilo MDA
- Estados claros (ativo/completo/erro)

✅ **Funcionalidade multi-teste**
- Criar múltiplos testes
- Alternar entre testes
- Cada teste mantém seus dados isolados

✅ **Compatibilidade com código existente**
- Páginas 2-6 funcionando sem reescrever
- Algoritmos de seleção funcionando
- Correção climática funcionando
- **Páginas 2-6 já validadas e funcionando (v16)**

### Fora do Escopo (Fase 2)
❌ Comparativo multi-teste (gráficos sobrepostos)
❌ Banco de dados SQLite
❌ Método Split (será outro software)
❌ Exportação PDF

---

## 📚 Referências Técnicas

### Normas
- **ABNT NBR 10312:2024** - Veículos rodoviários automotores leves - Determinação das forças de resistência ao movimento de rodagem
- Método de desaceleração (coastdown)

### Software Inspiração
- **ETAS MDA** - Measure Data Analyzer
  - Conceito de múltiplos arquivos
  - Instrumentos de visualização
  - Comparação de medições

### Stack Tecnológica
- **Python 3.11+**
- **Streamlit** (framework web)
- **Pandas** (manipulação de dados)
- **NumPy** (cálculos numéricos)
- **Plotly** (gráficos - futuro)

---

## 🚀 Como Rodar

```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar aplicação
streamlit run app.py

# Abrir navegador em:
# http://localhost:8501
```

---

## 💡 Dicas para Claude Code

### Ao modificar código:
1. **SEMPRE** ler este CLAUDE.md primeiro
2. **NUNCA** mexer em `core/` sem motivo forte
3. **SEMPRE** manter compatibilidade com Session State existente
4. **TESTAR** cada mudança isoladamente
5. **COMMITAR** com mensagens descritivas

### Ao adicionar features:
1. Verificar se já existe código similar nas páginas 2-6
2. Reutilizar ao invés de reescrever
3. Manter estilo visual consistente
4. Adicionar comentários em português

### Ao debugar:
1. Usar `st.write("DEBUG:", variable)` liberalmente
2. Verificar Session State: `st.write(st.session_state)`
3. Testar com dados reais
4. Verificar tipos de dados (int vs float vs str)

---

## 📞 Pontos de Atenção

### Decisões Arquiteturais Importantes

1. **Por que Session State ao invés de banco de dados?**
   - Mais simples para v1.0
   - Streamlit já gerencia
   - Facilita desenvolvimento rápido
   - Pode migrar para DB depois se necessário

2. **Por que separar Standard e Split?**
   - Métodos muito diferentes (cálculos, UI, validação)
   - Reduz complexidade de cada software
   - Usuário pode rodar ambos simultaneamente
   - Manutenção mais fácil

3. **Por que manter código PyQt5 em `core/`?**
   - Código validado e testado
   - Cálculos complexos funcionando
   - Evita introduzir bugs
   - Facilita migração incremental

---

## 🎨 Paleta de Cores (Tema Escuro)

```python
# Fundo
BACKGROUND_PRIMARY   = "#0e1117"  # Fundo principal
BACKGROUND_SECONDARY = "#1e1e1e"  # Cards, sidebar

# Texto
TEXT_PRIMARY   = "#ffffff"  # Texto principal
TEXT_SECONDARY = "#a0a0a0"  # Texto secundário

# Destaque
ACCENT_BLUE   = "#4a9eff"  # Teste ativo
ACCENT_GREEN  = "#4caf50"  # Sucesso
ACCENT_ORANGE = "#ff9800"  # Aviso
ACCENT_RED    = "#f44336"  # Erro

# Algoritmos
ALGO_ENERGY = "#D1FFBD"  # Verde claro
ALGO_TARGET = "#ADD8E6"  # Azul claro

# Bordas
BORDER_DEFAULT = "#3d3d3d"
BORDER_ACTIVE  = "#4a9eff"
```

---

## 📌 Próximos Passos Imediatos

**AÇÃO IMEDIATA** (primeira tarefa para Claude Code):

```
1. Refatorar app.py para incluir sidebar de gerenciamento de testes
2. Criar componente de card de teste (visual moderno)
3. Implementar modal "+ Novo Teste"
4. Adaptar Session State para estrutura multi-teste
5. Manter páginas 2-6 funcionando (compatibilidade)
```

**DEPOIS:**
- Corrigir bug Página 6
- Melhorar UX da sidebar
- Implementar salvamento de workspace

---

## 📝 Notas Finais

Este documento é o **guia definitivo** do projeto. Sempre que houver dúvida sobre:
- Estrutura de dados
- Fluxo de usuário
- Decisões arquiteturais
- Convenções de código

**Consulte este arquivo primeiro!**

Qualquer mudança significativa na arquitetura deve ser **discutida** e **documentada aqui**.

---

**Última atualização:** 2024-03-11  
**Versão:** 1.0 - Especificação Fase 1  
**Autor:** Felipe Eckert  
**Status:** 🚧 Em desenvolvimento
