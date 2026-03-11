# Coastdown Analysis Application - Streamlit Version

Aplicação web para análise de testes de coastdown conforme norma ABNT 10312.

## Características

- 🌐 **Internacionalização**: Suporte a Português e Inglês
- 📊 **Análise Completa**: Método Tradicional e Split
- 🔢 **Cálculos Validados**: Fórmulas conforme ABNT 10312
- 📈 **Seleção Automática**: Algoritmos de otimização de pares
- 📥 **Exportação**: Relatórios em Excel e TXT
- 🎨 **Tema Escuro**: Interface moderna e profissional

## Estrutura do Projeto

```
coastdown_streamlit/
├── app.py                    # Aplicação principal
├── translations.py           # Sistema de internacionalização
├── requirements.txt          # Dependências
├── README.md                 # Este arquivo
│
├── .streamlit/
│   └── config.toml           # Configurações do Streamlit (tema escuro)
│
├── core/                     # Módulo de cálculos (ABNT 10312)
│   ├── calculations.py       # calcular_energia, calcular_coeficientes_individuais, etc.
│   └── corrections.py        # apply_climate_correction
│
├── data/                     # Módulo de dados
│   ├── loaders.py            # carregar_dados_csv_robusto
│   └── exporters.py          # gerar_excel
│
├── pages/                    # Páginas da aplicação
│   ├── page_1_abrir_teste.py     # Upload de arquivos
│   ├── page_2_dados_veiculo.py   # Dados do veículo
│   ├── page_3_analise_pares.py   # Análise de pares
│   ├── page_4_comparativo.py     # Comparativo final
│   └── page_5_resultados.py      # Resultados finais
│
└── utils/                    # Utilitários
    └── file_utils.py         # Funções auxiliares
```

## Instalação

### 1. Criar ambiente virtual (recomendado)

```bash
cd coastdown_streamlit
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

## Execução

```bash
streamlit run app.py
```

A aplicação abrirá automaticamente no navegador em `http://localhost:8501`

## Funcionalidades por Página

### 1. Abrir Teste
- Seleção do método de teste (Tradicional ou Split)
- Upload de arquivos CSV de coastdown
- Upload de dados meteorológicos (opcional)
- Visualização dos runs detectados

### 2. Dados do Veículo
- Informações do veículo (modelo, data)
- Entrada de massa (total ou por componentes)
- Cálculo de coeficientes individuais

### 3. Análise de Pares
- Seleção de pares ida/volta
- Condições ambientais
- Correção climática
- Cálculo de F0/F2 por par

### 4. Comparativo Final
- Tabela de pares calculados
- Seleção manual ou automática
- Algoritmos de otimização:
  - Menor Energia
  - Por Alvo F0/F2
  - Menor CV

### 5. Resultados Finais
- Resumo dos resultados
- Tabela de pares selecionados
- Exportação para Excel
- Relatório em texto

## Internacionalização

A aplicação suporta dois idiomas:
- 🇧🇷 Português (padrão)
- 🇺🇸 English

Para trocar o idioma, use o seletor na barra lateral.

## Fórmulas e Cálculos

Todos os cálculos seguem a norma ABNT 10312:

- **F0**: Coeficiente de resistência ao rolamento (N)
- **F2**: Coeficiente de resistência aerodinâmica (N/(km/h)²)
- **Energia**: Calculada pela integral da força de resistência
- **Correção Climática**: Ajuste por temperatura e pressão

## Deploy

### Streamlit Cloud (Gratuito)

1. Faça push do código para um repositório GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte seu repositório
4. Deploy automático!

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

## Licença

Uso interno - Todos os direitos reservados.
