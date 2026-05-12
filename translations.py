# coding: utf-8
"""
Sistema de internacionalização (i18n) para a aplicação Coastdown.

Suporta Português (pt) e Inglês (en).
"""

TRANSLATIONS = {
    # ===== GERAL =====
    "app_title": {
        "pt": "Análise de Teste de Coastdown (ABNT 10312)",
        "en": "Coastdown Test Analysis (ABNT 10312)"
    },
    "language_selector": {
        "pt": "🌐 Idioma",
        "en": "🌐 Language"
    },
    "portuguese": {
        "pt": "Português",
        "en": "Portuguese"
    },
    "english": {
        "pt": "Inglês",
        "en": "English"
    },
    
    # ===== NAVEGAÇÃO / PÁGINAS =====
    "page_open_test": {
        "pt": "1. Abrir Teste",
        "en": "1. Open Test"
    },
    "page_vehicle_data": {
        "pt": "2. Dados do Veículo",
        "en": "2. Vehicle Data"
    },
    "page_pair_analysis": {
        "pt": "3. Análise de Pares",
        "en": "3. Pair Analysis"
    },
    "pair_calculations": {
        "pt": "Cálculos e Correções",
        "en": "Calculations & Corrections"
    },
    "pair_analysis_graphs": {
        "pt": "Gráficos",
        "en": "Graphs"
    },
    "pair_analysis_simulation": {
        "pt": "Simulação",
        "en": "Simulation"
    },
    "pair_time_conformity_tab": {
        "pt": "Conformidade de Tempos",
        "en": "Time Conformity"
    },
    "page_algorithm_selection": {
        "pt": "4. Seleção por Algoritmo",
        "en": "4. Algorithm Selection"
    },
    "page_final_comparison": {
        "pt": "5. Comparativo Final",
        "en": "5. Final Comparison"
    },
    "page_final_results": {
        "pt": "6. Resultados Finais",
        "en": "6. Final Results"
    },
    
    # ===== PÁGINA 1: ABRIR TESTE =====
    "select_test_method": {
        "pt": "Selecione o Método de Teste",
        "en": "Select Test Method"
    },
    "traditional_method": {
        "pt": "Método Tradicional",
        "en": "Traditional Method"
    },
    "split_method": {
        "pt": "Método Split",
        "en": "Split Method"
    },
    "upload_coastdown_csv": {
        "pt": "Upload do arquivo CSV de Coastdown",
        "en": "Upload Coastdown CSV file"
    },
    "upload_weather_csv": {
        "pt": "Upload do arquivo CSV de Dados Meteorológicos (opcional)",
        "en": "Upload Weather Data CSV file (optional)"
    },
    "upload_high_speed_csv": {
        "pt": "Upload do arquivo CSV de Alta Velocidade",
        "en": "Upload High Speed CSV file"
    },
    "upload_low_speed_csv": {
        "pt": "Upload do arquivo CSV de Baixa Velocidade",
        "en": "Upload Low Speed CSV file"
    },
    "file_loaded_success": {
        "pt": "✅ Arquivo carregado com sucesso!",
        "en": "✅ File loaded successfully!"
    },
    "file_load_error": {
        "pt": "❌ Erro ao carregar arquivo",
        "en": "❌ Error loading file"
    },
    "runs_detected": {
        "pt": "Runs detectados",
        "en": "Runs detected"
    },
    "proceed_to_vehicle_data": {
        "pt": "Prosseguir para Dados do Veículo",
        "en": "Proceed to Vehicle Data"
    },
    "load_data": {
        "pt": "Carregar Dados",
        "en": "Load Data"
    },
    
    # ===== PÁGINA 2: DADOS DO VEÍCULO =====
    "vehicle_information": {
        "pt": "Informações do Veículo",
        "en": "Vehicle Information"
    },
    "vehicle_model": {
        "pt": "Modelo do Veículo",
        "en": "Vehicle Model"
    },
    "test_date": {
        "pt": "Data do Teste",
        "en": "Test Date"
    },
    "mass_input_mode": {
        "pt": "Modo de Entrada de Massa",
        "en": "Mass Input Mode"
    },
    "total_mass_direct": {
        "pt": "Massa Total (entrada direta)",
        "en": "Total Mass (direct input)"
    },
    "component_masses": {
        "pt": "Massas por Componente",
        "en": "Component Masses"
    },
    "curb_mass": {
        "pt": "Massa em Ordem de Marcha (kg)",
        "en": "Curb Mass (kg)"
    },
    "driver_mass": {
        "pt": "Massa do Condutor (kg)",
        "en": "Driver Mass (kg)"
    },
    "equipment_mass": {
        "pt": "Massa de Equipamentos (kg)",
        "en": "Equipment Mass (kg)"
    },
    "total_mass": {
        "pt": "Massa Total (kg)",
        "en": "Total Mass (kg)"
    },
    "inertia_mass": {
        "pt": "Massa de Inércia (kg)",
        "en": "Inertia Mass (kg)"
    },
    "effective_mass": {
        "pt": "Massa Efetiva (kg)",
        "en": "Effective Mass (kg)"
    },
    "frontal_area": {
        "pt": "Área Frontal (m²)",
        "en": "Frontal Area (m²)"
    },
    "calculate_coefficients": {
        "pt": "Calcular Coeficientes Individuais",
        "en": "Calculate Individual Coefficients"
    },
    "proceed_to_pair_analysis": {
        "pt": "Prosseguir para Análise de Pares",
        "en": "Proceed to Pair Analysis"
    },
    
    # ===== PÁGINA 3: ANÁLISE DE PARES =====
    "pair_selection": {
        "pt": "Seleção de Pares",
        "en": "Pair Selection"
    },
    "select_outbound_run": {
        "pt": "Selecione o Run de Ida",
        "en": "Select Outbound Run"
    },
    "select_return_run": {
        "pt": "Selecione o Run de Volta",
        "en": "Select Return Run"
    },
    "environmental_conditions": {
        "pt": "Condições Ambientais",
        "en": "Environmental Conditions"
    },
    "temperature": {
        "pt": "Temperatura (°C)",
        "en": "Temperature (°C)"
    },
    "pressure": {
        "pt": "Pressão (kPa)",
        "en": "Pressure (kPa)"
    },
    "humidity": {
        "pt": "Umidade (%)",
        "en": "Humidity (%)"
    },
    "wind_speed": {
        "pt": "Velocidade do Vento (m/s)",
        "en": "Wind Speed (m/s)"
    },
    "apply_climate_correction": {
        "pt": "Aplicar Correção Climática",
        "en": "Apply Climate Correction"
    },
    "calculate_pair": {
        "pt": "Calcular Par",
        "en": "Calculate Pair"
    },
    "pair_results": {
        "pt": "Resultados do Par",
        "en": "Pair Results"
    },
    "use_pair": {
        "pt": "Usar Este Par",
        "en": "Use This Pair"
    },
    "f0_coefficient": {
        "pt": "Coeficiente F0 (N)",
        "en": "F0 Coefficient (N)"
    },
    "f2_coefficient": {
        "pt": "Coeficiente F2 (N/(km/h)²)",
        "en": "F2 Coefficient (N/(km/h)²)"
    },
    "energy": {
        "pt": "Energia (J)",
        "en": "Energy (J)"
    },
    "time_conformity_title": {
        "pt": "Conformidade dos Tempos de Desaceleração",
        "en": "Deceleration Time Conformity"
    },
    "time_conformity_description": {
        "pt": "Compare os tempos por intervalo de velocidade de cada passada e veja o desvio em relação à média daquele intervalo.",
        "en": "Compare each run's interval times and inspect the deviation relative to that interval's mean."
    },
    "time_conformity_source": {
        "pt": "Fonte das passadas",
        "en": "Run source"
    },
    "time_conformity_tolerance_pct": {
        "pt": "Tolerância (%)",
        "en": "Tolerance (%)"
    },
    "time_conformity_all_runs": {
        "pt": "Todas as passadas",
        "en": "All runs"
    },
    "time_conformity_selected_pair_runs": {
        "pt": "Passadas dos pares selecionados",
        "en": "Runs from selected pairs"
    },
    "time_conformity_all_runs_hint": {
        "pt": "Analisando {run_count} passadas válidas carregadas no teste ativo.",
        "en": "Analyzing {run_count} valid runs loaded in the active test."
    },
    "time_conformity_selected_runs_hint": {
        "pt": "Usando runs deduplicadas de {pair_count} par(es) marcado(s): {run_count} passada(s) encontrada(s).",
        "en": "Using deduplicated runs from {pair_count} checked pair(s): {run_count} run(s) found."
    },
    "time_conformity_no_selected_runs": {
        "pt": "Nenhuma passada disponível para a fonte selecionada.",
        "en": "No runs are available for the selected source."
    },
    "time_conformity_no_interval_data": {
        "pt": "Nenhuma passada possui dados válidos de tempo por intervalo para análise.",
        "en": "No runs contain valid interval-time data for analysis."
    },
    "time_conformity_split_not_supported": {
        "pt": "A análise de conformidade de tempos ainda não está disponível para o método Split.",
        "en": "Time conformity analysis is not available for the Split method yet."
    },
    "time_conformity_summary": {
        "pt": "Resumo por Intervalo",
        "en": "Interval Summary"
    },
    "time_conformity_matrix": {
        "pt": "Matriz de Tempos por Intervalo",
        "en": "Interval Time Matrix"
    },
    "time_conformity_details": {
        "pt": "Detalhamento por Passada",
        "en": "Run Details"
    },
    "time_conformity_run_label": {
        "pt": "Run {run_id}",
        "en": "Run {run_id}"
    },
    "time_conformity_interval": {
        "pt": "Intervalo",
        "en": "Interval"
    },
    "time_conformity_mean_time": {
        "pt": "Tempo Médio (s)",
        "en": "Mean Time (s)"
    },
    "time_conformity_min_time": {
        "pt": "Tempo Mínimo (s)",
        "en": "Min Time (s)"
    },
    "time_conformity_max_time": {
        "pt": "Tempo Máximo (s)",
        "en": "Max Time (s)"
    },
    "time_conformity_spread_s": {
        "pt": "Amplitude (s)",
        "en": "Spread (s)"
    },
    "time_conformity_cv_pct": {
        "pt": "CV (%)",
        "en": "CV (%)"
    },
    "time_conformity_max_deviation_pct": {
        "pt": "Maior Desvio (%)",
        "en": "Max Deviation (%)"
    },
    "time_conformity_deviation_s": {
        "pt": "Desvio (s)",
        "en": "Deviation (s)"
    },
    "time_conformity_deviation_pct": {
        "pt": "Desvio (%)",
        "en": "Deviation (%)"
    },
    "time_conformity_runs_count": {
        "pt": "Qtde. de Passadas",
        "en": "Run Count"
    },
    "time_conformity_intervals_count": {
        "pt": "Intervalos",
        "en": "Intervals"
    },
    "time_conformity_records_count": {
        "pt": "Registros",
        "en": "Records"
    },
    "time_conformity_non_conforming_count": {
        "pt": "Não Conformes",
        "en": "Non-conforming"
    },
    "time_conformity_non_conforming_runs": {
        "pt": "Células Não Conformes",
        "en": "Non-conforming Cells"
    },
    "time_conformity_non_conforming_intervals": {
        "pt": "Intervalos com Desvio",
        "en": "Intervals with Deviation"
    },
    "time_conformity_skipped_runs": {
        "pt": "Passadas ignoradas por falta de dados válidos de intervalo: {runs}",
        "en": "Runs skipped due to missing valid interval data: {runs}"
    },
    
    # ===== PÁGINA 4: COMPARATIVO FINAL =====
    "calculated_pairs": {
        "pt": "Pares Calculados",
        "en": "Calculated Pairs"
    },
    "select_pairs_for_final": {
        "pt": "Selecione os pares para o resultado final",
        "en": "Select pairs for final result"
    },
    "auto_select_best": {
        "pt": "Seleção Automática (Melhores Pares)",
        "en": "Auto Select (Best Pairs)"
    },
    "number_of_pairs": {
        "pt": "Número de Pares",
        "en": "Number of Pairs"
    },
    "max_cv_percent": {
        "pt": "CV Máximo (%)",
        "en": "Max CV (%)"
    },
    "target_f0": {
        "pt": "F0 Alvo (N)",
        "en": "Target F0 (N)"
    },
    "target_f2": {
        "pt": "F2 Alvo (N/(km/h)²)",
        "en": "Target F2 (N/(km/h)²)"
    },
    "run_auto_selection": {
        "pt": "Executar Seleção Automática",
        "en": "Run Auto Selection"
    },
    "calculate_final_results": {
        "pt": "Calcular Resultados Finais",
        "en": "Calculate Final Results"
    },
    "remove_pair": {
        "pt": "Remover Par",
        "en": "Remove Pair"
    },
    "cv_f0": {
        "pt": "CV F0 (%)",
        "en": "CV F0 (%)"
    },
    "cv_f2": {
        "pt": "CV F2 (%)",
        "en": "CV F2 (%)"
    },
    "mean_f0": {
        "pt": "F0 Médio (N)",
        "en": "Mean F0 (N)"
    },
    "mean_f2": {
        "pt": "F2 Médio (N/(km/h)²)",
        "en": "Mean F2 (N/(km/h)²)"
    },
    
    # ===== PÁGINA 5: RESULTADOS FINAIS =====
    "final_results": {
        "pt": "Resultados Finais",
        "en": "Final Results"
    },
    "summary": {
        "pt": "Resumo",
        "en": "Summary"
    },
    "selected_pairs": {
        "pt": "Pares Selecionados",
        "en": "Selected Pairs"
    },
    "export_to_excel": {
        "pt": "Exportar para Excel",
        "en": "Export to Excel"
    },
    "export_success": {
        "pt": "✅ Exportação realizada com sucesso!",
        "en": "✅ Export completed successfully!"
    },
    "download_excel": {
        "pt": "📥 Baixar Excel",
        "en": "📥 Download Excel"
    },
    "corrected_f0": {
        "pt": "F0 Corrigido (N)",
        "en": "Corrected F0 (N)"
    },
    "corrected_f2": {
        "pt": "F2 Corrigido (N/(km/h)²)",
        "en": "Corrected F2 (N/(km/h)²)"
    },
    "total_energy": {
        "pt": "Energia Total (J)",
        "en": "Total Energy (J)"
    },
    
    # ===== MENSAGENS DE ERRO =====
    "error_no_file": {
        "pt": "Por favor, carregue um arquivo CSV primeiro.",
        "en": "Please load a CSV file first."
    },
    "error_no_mass": {
        "pt": "Por favor, insira a massa do veículo.",
        "en": "Please enter the vehicle mass."
    },
    "error_no_pairs": {
        "pt": "Nenhum par foi calculado ainda.",
        "en": "No pairs have been calculated yet."
    },
    "error_select_pairs": {
        "pt": "Por favor, selecione pelo menos um par.",
        "en": "Please select at least one pair."
    },
    "error_calculation": {
        "pt": "Erro no cálculo",
        "en": "Calculation error"
    },
    
    # ===== TABELAS =====
    "run_id": {
        "pt": "ID do Run",
        "en": "Run ID"
    },
    "heading": {
        "pt": "Direção",
        "en": "Heading"
    },
    "outbound": {
        "pt": "Ida",
        "en": "Outbound"
    },
    "return": {
        "pt": "Volta",
        "en": "Return"
    },
    "pair_id": {
        "pt": "ID do Par",
        "en": "Pair ID"
    },
    "selected": {
        "pt": "Selecionado",
        "en": "Selected"
    },
    "actions": {
        "pt": "Ações",
        "en": "Actions"
    },
    
    # ===== GRÁFICOS =====
    "velocity_vs_time": {
        "pt": "Velocidade vs Tempo",
        "en": "Velocity vs Time"
    },
    "velocity_kmh": {
        "pt": "Velocidade (km/h)",
        "en": "Velocity (km/h)"
    },
    "time_s": {
        "pt": "Tempo (s)",
        "en": "Time (s)"
    },
    "deceleration_curve": {
        "pt": "Curva de Desaceleração",
        "en": "Deceleration Curve"
    },
    
    # ===== BOTÕES GERAIS =====
    "confirm": {
        "pt": "Confirmar",
        "en": "Confirm"
    },
    "cancel": {
        "pt": "Cancelar",
        "en": "Cancel"
    },
    "reset": {
        "pt": "Resetar",
        "en": "Reset"
    },
    "next": {
        "pt": "Próximo",
        "en": "Next"
    },
    "previous": {
        "pt": "Anterior",
        "en": "Previous"
    },
    "save": {
        "pt": "Salvar",
        "en": "Save"
    },

    # ===== MULTI-TESTE - SIDEBAR =====
    "new_test": {
        "pt": "Novo Teste",
        "en": "New Test"
    },
    "edit_test": {
        "pt": "Editar",
        "en": "Edit"
    },
    "edit_test_title": {
        "pt": "Editar teste",
        "en": "Edit test"
    },
    "test_name": {
        "pt": "Nome do Teste",
        "en": "Test Name"
    },
    "create_test": {
        "pt": "Criar Teste",
        "en": "Create Test"
    },
    "no_tests_title": {
        "pt": "Bem-vindo ao Coastdown MDA",
        "en": "Welcome to Coastdown MDA"
    },
    "no_tests_description": {
        "pt": "Nenhum teste criado ainda. Crie um novo teste para começar a análise.",
        "en": "No tests created yet. Create a new test to start the analysis."
    },
    "no_tests_message": {
        "pt": "Nenhum teste. Clique em + Novo Teste.",
        "en": "No tests. Click + New Test."
    },
    "active_test": {
        "pt": "Ativo",
        "en": "Active"
    },
    "remove_test": {
        "pt": "Remover teste",
        "en": "Remove test"
    },
    "switch_test": {
        "pt": "Selecionar",
        "en": "Select"
    },
    "navigation": {
        "pt": "Navegação",
        "en": "Navigation"
    },
    "status": {
        "pt": "Status",
        "en": "Status"
    },
    "confirm_delete_test": {
        "pt": "Remover este teste permanentemente?",
        "en": "Remove this test permanently?"
    },
    "confirm_remove_title": {
        "pt": "Confirmar remoção",
        "en": "Confirm removal"
    },
    "current_csv": {
        "pt": "CSV atual",
        "en": "Current CSV"
    },
    "current_meteo": {
        "pt": "Meteo atual",
        "en": "Current meteo"
    },
    "no_meteo_file": {
        "pt": "Sem arquivo meteorológico",
        "en": "No meteorological file"
    },
    "replace_csv": {
        "pt": "Substituir CSV",
        "en": "Replace CSV"
    },
    "replace_meteo": {
        "pt": "Substituir meteo",
        "en": "Replace meteo"
    },
    "add_meteo": {
        "pt": "Adicionar meteo",
        "en": "Add meteo"
    },
    "remove_meteo": {
        "pt": "Remover meteo atual",
        "en": "Remove current meteo"
    },
    "save_changes": {
        "pt": "Salvar alterações",
        "en": "Save changes"
    },
    "no_changes_detected": {
        "pt": "Nenhuma alteração detectada.",
        "en": "No changes detected."
    },
    "warning_replace_csv": {
        "pt": "⚠️ Substituir o CSV apagará cálculos, pares, seleções e resultados deste teste.",
        "en": "⚠️ Replacing the CSV will clear calculations, pairs, selections, and results for this test."
    },
    "warning_replace_meteo": {
        "pt": "⚠️ Alterar o arquivo meteorológico invalidará correções climáticas, pares calculados e resultados finais.",
        "en": "⚠️ Changing the meteorological file will invalidate climate corrections, calculated pairs, and final results."
    },
    "confirm_replace_csv_understand": {
        "pt": "Entendo que substituir o CSV apagará cálculos, pares, seleções e resultados.",
        "en": "I understand that replacing the CSV will clear calculations, pairs, selections, and results."
    },
    "confirm_replace_meteo_understand": {
        "pt": "Entendo que alterar o meteo exigirá recalcular correções e resultados.",
        "en": "I understand that changing the meteo will require recalculating corrections and results."
    },
    "invalid_csv_file": {
        "pt": "Nenhum dado válido foi encontrado no CSV informado.",
        "en": "No valid data was found in the provided CSV."
    },
    "invalid_meteo_file": {
        "pt": "Nenhum dado meteorológico válido foi encontrado no arquivo informado.",
        "en": "No valid meteorological data was found in the provided file."
    },
    "fixed_conditions": {
        "pt": "Condições Fixas (sem arquivo meteo)",
        "en": "Fixed Conditions (no meteo file)"
    },
    "fixed_conditions_hint": {
        "pt": "Valores usados para correção climática quando não há arquivo meteorológico.",
        "en": "Values used for climate correction when no meteorological file is provided."
    },
    "test_created": {
        "pt": "Teste criado com sucesso!",
        "en": "Test created successfully!"
    },
    "loading_files": {
        "pt": "Carregando arquivos...",
        "en": "Loading files..."
    },

    # ===== ALERTA DE DATA =====
    "date_mismatch_warning": {
        "pt": "⚠️ Atenção: Data do CSV ({data_csv}) difere do arquivo meteorológico ({data_meteo}). Isso pode afetar a correção climática.",
        "en": "⚠️ Warning: CSV date ({data_csv}) differs from meteorological file ({data_meteo}). This may affect climatic correction."
    },

    # ===== TAMANHO DE FONTE =====
    "font_size": {
        "pt": "Tamanho da fonte",
        "en": "Font size"
    },
    "font_small": {
        "pt": "Pequeno",
        "en": "Small"
    },
    "font_medium": {
        "pt": "Médio (padrão)",
        "en": "Medium (default)"
    },
    "font_large": {
        "pt": "Grande",
        "en": "Large"
    },
}


def get_translator(lang: str = "pt"):
    """
    Retorna uma função de tradução para o idioma especificado.

    Args:
        lang: Código do idioma ("pt" ou "en")

    Returns:
        Função t(key, **kwargs) que retorna o texto traduzido com interpolação opcional
    """
    def t(key: str, **kwargs) -> str:
        """Retorna o texto traduzido para a chave especificada."""
        if key in TRANSLATIONS:
            text = TRANSLATIONS[key].get(lang, TRANSLATIONS[key].get("pt", key))
        else:
            text = key
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass
        return text

    return t


def get_available_languages():
    """Retorna lista de idiomas disponíveis."""
    return [
        {"code": "pt", "name": "Português", "flag": "🇧🇷"},
        {"code": "en", "name": "English", "flag": "🇺🇸"}
    ]
