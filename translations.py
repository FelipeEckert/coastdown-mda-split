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
        "pt": "Dados do Veículo",
        "en": "Vehicle Data"
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
    "report_plot_mode": {
        "pt": "Modo relatorio: graficos claros",
        "en": "Report mode: light charts"
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
        "pt": "Upload do arquivo CSV/XLSX de Dados Meteorológicos (opcional)",
        "en": "Upload Weather Data CSV/XLSX file (optional)"
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
    "mass_norm_note": {
        "pt": "Nota: a norma recomenda considerar 136 kg adicionais referentes a motorista + equipamento.",
        "en": "Note: the standard recommends considering an additional 136 kg for driver + equipment."
    },
    "frontal_area": {
        "pt": "Área Frontal (m²)",
        "en": "Frontal Area (m²)"
    },
    "calculate_coefficients": {
        "pt": "Calcular Coeficientes Individuais",
        "en": "Calculate Individual Coefficients"
    },
    "calculate_uncorrected_coefficients": {
        "pt": "Calcular coeficientes individuais não corrigidos",
        "en": "Calculate uncorrected individual coefficients"
    },
    "calculating_uncorrected_coefficients": {
        "pt": "Calculando coeficientes individuais não corrigidos...",
        "en": "Calculating uncorrected individual coefficients..."
    },
    "uncorrected_coefficients_success": {
        "pt": "Coeficientes individuais não corrigidos calculados para {count} runs!",
        "en": "Uncorrected individual coefficients calculated for {count} runs!"
    },
    "individual_uncorrected_coefficients": {
        "pt": "Coeficientes individuais não corrigidos calculados",
        "en": "Calculated uncorrected individual coefficients"
    },
    "uncorrected_coefficients_note": {
        "pt": "Estes coeficientes são não corrigidos, antes da correção climática.",
        "en": "These coefficients are uncorrected, before climate correction."
    },
    "individual_f0_coefficient": {
        "pt": "f'0 (N)",
        "en": "f'0 (N)"
    },
    "individual_f2_coefficient": {
        "pt": "f'2 (N/(m/s)²)",
        "en": "f'2 (N/(m/s)²)"
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
    
    "time_conformity_measured_value": {
        "pt": "Valor medido",
        "en": "Measured value"
    },
    "time_conformity_mean_detail": {
        "pt": "Média do intervalo",
        "en": "Interval mean"
    },
    "time_conformity_std_time": {
        "pt": "Desvio padrão",
        "en": "Standard deviation"
    },
    "time_conformity_difference_s": {
        "pt": "Diferença",
        "en": "Difference"
    },
    "time_conformity_status": {
        "pt": "Status",
        "en": "Status"
    },
    "time_conformity_status_conforming": {
        "pt": "Conforme",
        "en": "Conforming"
    },
    "time_conformity_status_non_conforming": {
        "pt": "Não conforme",
        "en": "Non-conforming"
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
    "select_all_pairs": {
        "pt": "Selecionar todos",
        "en": "Select all"
    },
    "deselect_all_pairs": {
        "pt": "Desmarcar todos",
        "en": "Deselect all"
    },
    "clear_all_pairs": {
        "pt": "Limpar tudo",
        "en": "Clear all"
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
    "split_current_combined_file": {
        "pt": "Arquivo coastdown combinado atual",
        "en": "Current combined coastdown file"
    },
    "split_vehicle_mass_title": {
        "pt": "Massas do método Split",
        "en": "Split method masses"
    },
    "split_running_order_mass": {
        "pt": "Massa em ordem de marcha [kg]",
        "en": "Running-order mass [kg]"
    },
    "split_rotational_mass_available": {
        "pt": "Massa equivalente de rotação me disponível?",
        "en": "Is rotational equivalent mass me available?"
    },
    "split_rotational_equivalent_mass": {
        "pt": "Massa equivalente de rotação me [kg]",
        "en": "Rotational equivalent mass me [kg]"
    },
    "split_rotational_mass_estimate_note": {
        "pt": "A massa equivalente de inércia será estimada como 3% da massa de ensaio M.",
        "en": "Equivalent inertial mass will be estimated as 3% of test mass M."
    },
    "split_vehicle_mass_summary": {
        "pt": "Resumo das massas",
        "en": "Mass summary"
    },
    "split_test_mass": {
        "pt": "Massa de ensaio M [kg]",
        "en": "Test mass M [kg]"
    },
    "split_effective_mass": {
        "pt": "Massa efetiva Me [kg]",
        "en": "Effective mass Me [kg]"
    },
    "split_current_high_file": {
        "pt": "Arquivo high-speed atual",
        "en": "Current high-speed file"
    },
    "split_current_low_file": {
        "pt": "Arquivo low-speed atual",
        "en": "Current low-speed file"
    },
    "split_current_weather_file": {
        "pt": "Arquivo meteorologico atual",
        "en": "Current weather file"
    },
    "no_meteo_file": {
        "pt": "Sem arquivo meteorológico",
        "en": "No meteorological file"
    },
    "split_no_low_file": {
        "pt": "Sem arquivo low-speed",
        "en": "No low-speed file"
    },
    "replace_csv": {
        "pt": "Substituir CSV",
        "en": "Replace CSV"
    },
    "split_replace_high_csv": {
        "pt": "Substituir arquivo high-speed",
        "en": "Replace high-speed file"
    },
    "split_replace_low_csv": {
        "pt": "Substituir arquivo low-speed",
        "en": "Replace low-speed file"
    },
    "split_add_low_csv": {
        "pt": "Adicionar arquivo low-speed",
        "en": "Add low-speed file"
    },
    "split_replace_combined_csv": {
        "pt": "Substituir arquivo coastdown combinado",
        "en": "Replace combined coastdown file"
    },
    "split_remove_low_file": {
        "pt": "Remover arquivo low-speed atual",
        "en": "Remove current low-speed file"
    },
    "split_high_file_required": {
        "pt": "Um arquivo high-speed valido e obrigatorio para manter o teste Split.",
        "en": "A valid high-speed file is required to keep the Split test."
    },
    "split_combined_low_edit_not_available": {
        "pt": "Testes com arquivo combinado nao possuem slot low-speed separado.",
        "en": "Combined-file tests do not have a separate low-speed slot."
    },
    "split_replace_combined_required": {
        "pt": "Informe um novo arquivo combinado para substituir esta entrada Split.",
        "en": "Provide a new combined file to replace this Split input."
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

    "sync_meteo_time_only_label": {
        "pt": "Sincronizar usando apenas os horários",
        "en": "Synchronize using times only"
    },
    "sync_meteo_time_only_help": {
        "pt": "As datas dos arquivos não coincidem. Deseja sincronizar usando apenas os horários, assumindo que os arquivos correspondem ao mesmo dia de teste?",
        "en": "The file dates do not match. Use this option if the dates are inconsistent but the times correspond to the same test."
    },
    "sync_meteo_time_only_active": {
        "pt": "Sincronização por horário ativada: a data será ignorada ao escolher o registro meteorológico mais próximo.",
        "en": "Time-only synchronization is active: the date will be ignored when choosing the nearest meteorological record."
    },
    "meteo_sync_no_valid_time": {
        "pt": "Não foi possível sincronizar o arquivo meteorológico porque as passadas não têm horário válido. Verifique o campo de horário no CSV ou use condições fixas.",
        "en": "The meteorological file could not be synchronized because the runs do not have valid times. Check the time field in the CSV or use fixed conditions."
    },
    "meteo_sync_mode_full_datetime": {
        "pt": "data + horário",
        "en": "date + time"
    },
    "meteo_sync_mode_time_only": {
        "pt": "somente horário",
        "en": "time only"
    },
    "meteo_sync_current_mode": {
        "pt": "Sincronização meteorológica atual: {mode}.",
        "en": "Current meteorological synchronization: {mode}."
    },
    "meteo_sync_details_expander": {
        "pt": "Ver detalhes da sincronização meteorológica",
        "en": "View meteorological synchronization details"
    },
    "meteo_sync_col_run": {
        "pt": "Run/passada",
        "en": "Run"
    },
    "meteo_sync_col_csv_time": {
        "pt": "Horário CSV",
        "en": "CSV time"
    },
    "meteo_sync_col_meteo_time": {
        "pt": "Horário Meteo sincronizado",
        "en": "Synchronized meteo time"
    },
    "meteo_sync_col_delta_s": {
        "pt": "Diferença (s)",
        "en": "Difference (s)"
    },
    "meteo_sync_col_mode": {
        "pt": "Modo usado",
        "en": "Mode used"
    },
    "meteo_sync_col_temp": {
        "pt": "Temperatura",
        "en": "Temperature"
    },
    "meteo_sync_col_press": {
        "pt": "Pressão",
        "en": "Pressure"
    },
    "meteo_sync_col_wind": {
        "pt": "Vento",
        "en": "Wind"
    },
    "meteo_wind_above_limit_warning": {
        "pt": "Atenção: vento acima de 3,0 m/s em {runs}. Vento acima desse limite é critério de atenção/exclusão pela norma.",
        "en": "Warning: wind above 3.0 m/s in {runs}. Wind above this limit is an attention/exclusion criterion under the standard."
    },

    # ===== SPLIT WORKFLOW =====
    "page_split_workflow": {
        "pt": "Seleção de Intervalos",
        "en": "Interval Selection"
    },
    "split_interval_configuration": {
        "pt": "Configuração dos intervalos Split",
        "en": "Split interval configuration"
    },
    "split_interval_defaults_note": {
        "pt": "Os valores normativos são apenas padrões. Ajuste-os conforme a configuração da aquisição.",
        "en": "Norm values are defaults only. Adjust them to match the acquisition setup."
    },
    "split_interval_step_kmh": {
        "pt": "Passo dos intervalos de desaceleração [km/h]",
        "en": "Coastdown interval step [km/h]"
    },
    "split_interval_high": {
        "pt": "Intervalo de alta",
        "en": "High interval"
    },
    "split_interval_low": {
        "pt": "Intervalo de baixa",
        "en": "Low interval"
    },
    "split_high_start_kmh": {
        "pt": "Início do intervalo high [km/h]",
        "en": "High interval start [km/h]"
    },
    "split_high_reference_kmh": {
        "pt": "Referência high V2 [km/h]",
        "en": "High reference V2 [km/h]"
    },
    "split_high_end_kmh": {
        "pt": "Fim do intervalo high [km/h]",
        "en": "High interval end [km/h]"
    },
    "split_low_start_kmh": {
        "pt": "Início do intervalo low [km/h]",
        "en": "Low interval start [km/h]"
    },
    "split_low_reference_kmh": {
        "pt": "Referência low V1 [km/h]",
        "en": "Low reference V1 [km/h]"
    },
    "split_low_end_kmh": {
        "pt": "Fim do intervalo low [km/h]",
        "en": "Low interval end [km/h]"
    },
    "split_parse_intervals": {
        "pt": "Processar intervalos Split",
        "en": "Process Split intervals"
    },
    "split_interval_edit_instruction": {
        "pt": "Ajuste os intervalos e clique em Processar intervalos Split.",
        "en": "Adjust the intervals and click Process Split intervals."
    },
    "split_interval_config_dirty": {
        "pt": "Configuração alterada. Clique em Processar intervalos Split para atualizar os dados.",
        "en": "Configuration changed. Click Process Split intervals to update the data."
    },
    "split_interval_preview_stale": {
        "pt": "Prévia desatualizada. Clique em Processar intervalos Split para atualizar.",
        "en": "Preview is outdated. Click Process Split intervals to update."
    },
    "split_processed_interval_summary": {
        "pt": "Configuração processada: high {high_start:g}-{high_end:g} km/h (ref. {high_reference:g}); low {low_start:g}-{low_end:g} km/h (ref. {low_reference:g}); passo {step:g} km/h.",
        "en": "Processed configuration: high {high_start:g}-{high_end:g} km/h (ref. {high_reference:g}); low {low_start:g}-{low_end:g} km/h (ref. {low_reference:g}); step {step:g} km/h."
    },
    "split_parse_dirty_calculation_blocked": {
        "pt": "A configuração dos intervalos foi alterada. Processe novamente os intervalos antes de calcular os coeficientes.",
        "en": "The interval configuration has changed. Process the intervals again before calculating coefficients."
    },
    "split_reset_intervals": {
        "pt": "Restaurar intervalos",
        "en": "Reset intervals"
    },
    "split_interval_step_invalid": {
        "pt": "O passo dos intervalos deve ser maior que zero.",
        "en": "Coastdown interval step must be greater than zero."
    },
    "split_interval_step_incompatible": {
        "pt": "A amplitude do {interval} ({span:g} km/h) deve ser múltipla exata do passo configurado ({step:g} km/h).",
        "en": "The {interval} span ({span:g} km/h) must be an exact multiple of the configured step ({step:g} km/h)."
    },
    "split_interval_order_invalid": {
        "pt": "O início do {interval} deve ser maior que o fim.",
        "en": "The {interval} start must be greater than its end."
    },
    "split_interval_reference_invalid": {
        "pt": "A velocidade de referência do {interval} deve ficar entre o início e o fim.",
        "en": "The {interval} reference speed must be between its start and end."
    },
    "split_interval_values_invalid": {
        "pt": "Os valores do {interval} devem ser numéricos e finitos.",
        "en": "The {interval} values must be numeric and finite."
    },
    "page_split_coefficient_calculation": {
        "pt": "Cálculo dos Coeficientes",
        "en": "Coefficient Calculation"
    },
    "page_split_pair_analysis": {
        "pt": "3. Análise de Pares",
        "en": "3. Pair Analysis"
    },
    "split_auto_tab": {
        "pt": "Sele\u00e7\u00e3o Autom\u00e1tica",
        "en": "Automatic Selection"
    },
    "split_auto_title": {
        "pt": "Sele\u00e7\u00e3o Autom\u00e1tica de Pares",
        "en": "Automatic Pair Selection"
    },
    "split_auto_description": {
        "pt": "Esta ferramenta gera e ranqueia candidatos completos Split. Revise ou substitua as sugest\u00f5es antes de adicion\u00e1-las ao Comparativo Final.",
        "en": "This tool generates and ranks complete Split candidates. Review or replace suggestions before adding them to Final Comparison."
    },
    "split_auto_process_intervals_first": {
        "pt": "Processe os intervalos Split antes de executar a sele\u00e7\u00e3o autom\u00e1tica.",
        "en": "Process the Split intervals before running automatic selection."
    },
    "split_auto_estimated_combinations": {
        "pt": "Combina\u00e7\u00f5es estimadas",
        "en": "Estimated combinations"
    },
    "split_auto_grouping_warnings": {
        "pt": "Avisos do agrupamento",
        "en": "Grouping warnings"
    },
    "split_auto_no_complete_combinations": {
        "pt": "N\u00e3o h\u00e1 combina\u00e7\u00f5es completas high+/low+/high-/low- dispon\u00edveis.",
        "en": "No complete high+/low+/high-/low- combinations are available."
    },
    "split_auto_settings": {
        "pt": "Configura\u00e7\u00f5es",
        "en": "Settings"
    },
    "split_auto_algorithm": {
        "pt": "Algoritmo",
        "en": "Algorithm"
    },
    "split_auto_algorithm_energy": {
        "pt": "Menor Energia",
        "en": "Lowest Energy"
    },
    "split_auto_algorithm_target": {
        "pt": "Proximidade ao Target F0/F2",
        "en": "F0/F2 Target Proximity"
    },
    "split_auto_k": {
        "pt": "Quantidade inicial de sugest\u00f5es",
        "en": "Initial number of suggestions"
    },
    "split_auto_max_combinations": {
        "pt": "Limite m\u00e1ximo de combina\u00e7\u00f5es no modo exato",
        "en": "Maximum combinations in exact mode"
    },
    "split_auto_avoid_repeated": {
        "pt": "Evitar passadas repetidas",
        "en": "Avoid repeated runs"
    },
    "split_auto_avoid_repeated_help": {
        "pt": "Quando ativado, a mesma passada high/low, dire\u00e7\u00e3o e fonte n\u00e3o ser\u00e1 usada em mais de um candidato sugerido.",
        "en": "When enabled, the same high/low run, direction, and source will not be used in more than one suggested candidate."
    },
    "split_auto_constraint_section": {
        "pt": "Critérios de validação do conjunto sugerido",
        "en": "Suggested-set validation criteria"
    },
    "split_auto_constraint_description": {
        "pt": "Esses critérios são avaliados sobre o conjunto de pares sugeridos, conforme a validação normativa dos tempos no método Split.",
        "en": "These criteria are evaluated over the suggested pair set according to the Split method's normative time validation."
    },
    "split_auto_require_time_cv": {
        "pt": "Exigir C.V. Δt por velocidade/sentido <= 2,5%",
        "en": "Require Δt C.V. per speed/direction <= 2.5%"
    },
    "split_auto_require_opposite_difference": {
        "pt": "Exigir diferença média entre sentidos <= 10%",
        "en": "Require mean difference between directions <= 10%"
    },
    "split_auto_search_advanced_settings": {
        "pt": "Configurações avançadas da busca",
        "en": "Advanced search settings"
    },
    "split_auto_search_pool_size": {
        "pt": "Tamanho máximo da pool de busca",
        "en": "Maximum search pool size"
    },
    "split_auto_search_max_set_evaluations": {
        "pt": "Máximo de conjuntos avaliados",
        "en": "Maximum evaluated sets"
    },
    "split_auto_search_max_seconds": {
        "pt": "Tempo máximo de busca [s]",
        "en": "Maximum search time [s]"
    },
    "split_auto_search_disabled_help": {
        "pt": "A busca constrained não é usada quando todos os critérios estão desligados.",
        "en": "Constrained search is not used when all criteria are disabled."
    },
    "split_auto_search_evaluated_sets": {
        "pt": "Conjuntos avaliados",
        "en": "Evaluated sets"
    },
    "split_auto_search_valid_sets": {
        "pt": "Conjuntos válidos encontrados",
        "en": "Valid sets found"
    },
    "split_auto_search_pool": {
        "pt": "Pool de busca",
        "en": "Search pool"
    },
    "split_auto_search_strategy": {
        "pt": "Estratégia",
        "en": "Strategy"
    },
    "split_auto_search_strategy_constraint_first": {
        "pt": "constraint-first",
        "en": "constraint-first"
    },
    "split_auto_search_elapsed_seconds": {
        "pt": "Tempo decorrido [s]",
        "en": "Elapsed time [s]"
    },
    "split_auto_search_time_limit": {
        "pt": "Limite de tempo [s]",
        "en": "Time limit [s]"
    },
    "split_auto_search_timeout_status": {
        "pt": "Timeout atingido",
        "en": "Timeout reached"
    },
    "split_auto_search_evaluation_limit_status": {
        "pt": "Limite de avaliações atingido",
        "en": "Evaluation limit reached"
    },
    "split_auto_yes": {"pt": "Sim", "en": "Yes"},
    "split_auto_no": {"pt": "Não", "en": "No"},
    "split_auto_search_limit_reached": {
        "pt": "A busca atingiu o limite configurado de avaliações; pode haver combinações válidas fora da busca avaliada.",
        "en": "The search reached the configured evaluation limit; valid combinations may exist outside the evaluated search."
    },
    "split_auto_search_limited_warning": {
        "pt": "A busca foi limitada por tempo/quantidade de combinações avaliadas. Pode haver combinações válidas fora do universo avaliado.",
        "en": "The search was limited by time/evaluated-combination count. Valid combinations may exist outside the evaluated universe."
    },
    "split_auto_diagnostics_title": {
        "pt": "Diagnóstico da seleção",
        "en": "Selection diagnostics"
    },
    "split_auto_diagnostics_generation": {
        "pt": "Geração de candidatos",
        "en": "Candidate generation"
    },
    "split_auto_diagnostics_failed_count": {
        "pt": "Falhas na geração",
        "en": "Generation failures"
    },
    "split_auto_diagnostics_prefilter": {
        "pt": "Pré-filtro MAD",
        "en": "MAD pre-filter"
    },
    "split_auto_diagnostics_prefilter_enabled": {
        "pt": "Aplicado",
        "en": "Applied"
    },
    "split_auto_diagnostics_prefilter_disabled": {
        "pt": "Desativado",
        "en": "Disabled"
    },
    "split_auto_diagnostics_search": {
        "pt": "Busca constrained",
        "en": "Constrained search"
    },
    "split_auto_diagnostics_search_not_applicable": {
        "pt": "Busca constrained não foi usada (nenhum critério normativo está ativo).",
        "en": "Constrained search was not used (no normative criterion is active)."
    },
    "split_auto_prefilter_group": {
        "pt": "Grupo",
        "en": "Group"
    },
    "split_auto_prefilter_input": {
        "pt": "Entrada",
        "en": "Input"
    },
    "split_auto_prefilter_output": {
        "pt": "Saída",
        "en": "Output"
    },
    "split_auto_prefilter_filtered": {
        "pt": "Filtradas",
        "en": "Filtered"
    },
    "split_auto_phase_generating": {
        "pt": "1. Gerando candidatos...",
        "en": "1. Generating candidates..."
    },
    "split_auto_phase_ranking": {
        "pt": "2. Rankeando candidatos...",
        "en": "2. Ranking candidates..."
    },
    "split_auto_phase_searching": {
        "pt": "3. Buscando combinação válida dentro dos limites configurados...",
        "en": "3. Searching for a valid combination within configured limits..."
    },
    "split_auto_phase_finalizing": {
        "pt": "4. Finalizando sugestões...",
        "en": "4. Finalizing suggestions..."
    },
    "split_auto_phase_stopped_by_limit": {
        "pt": "Busca encerrada por limite de tempo/avaliações.",
        "en": "Search stopped by the time/evaluation limit."
    },
    "split_auto_phase_completed": {
        "pt": "Seleção automática concluída.",
        "en": "Automatic selection completed."
    },
    "split_auto_target_f0": {
        "pt": "F0 alvo",
        "en": "Target F0"
    },
    "split_auto_target_f2": {
        "pt": "F2 alvo",
        "en": "Target F2"
    },
    "split_auto_target_score": {
        "pt": "Score target",
        "en": "Target score"
    },
    "split_auto_cv_f0_diagnostic": {
        "pt": "CV F0 [%] (diagnóstico)",
        "en": "F0 CV [%] (diagnostic)"
    },
    "split_auto_cv_f2_diagnostic": {
        "pt": "CV F2 [%] (diagnóstico)",
        "en": "F2 CV [%] (diagnostic)"
    },
    "split_auto_exact_limit_exceeded": {
        "pt": "O total estimado excede o limite configurado. A gera\u00e7\u00e3o exata ser\u00e1 bloqueada. Em rodada futura ser\u00e1 implementado o modo otimizado por pr\u00e9-sele\u00e7\u00e3o direcional.",
        "en": "The estimated total exceeds the configured limit. Exact generation is blocked. A future round will implement optimized directional preselection."
    },
    "split_auto_weather_sync_not_supported": {
        "pt": "A sele\u00e7\u00e3o autom\u00e1tica desta rodada usa apenas condi\u00e7\u00f5es ambientais fixas. A sincroniza\u00e7\u00e3o meteo por candidato ser\u00e1 integrada em uma rodada futura.",
        "en": "Automatic selection in this round supports fixed ambient conditions only. Per-candidate weather synchronization will be integrated in a future round."
    },
    "split_auto_environment_section": {"pt": "Condições ambientais", "en": "Environmental conditions"},
    "split_auto_environment": {"pt": "Ambiente", "en": "Environment"},
    "split_auto_fixed_temperature_c": {"pt": "Temperatura padrão (°C)", "en": "Default temperature (°C)"},
    "split_auto_fixed_pressure_kpa": {"pt": "Pressão padrão (kPa)", "en": "Default pressure (kPa)"},
    "split_auto_fixed_wind": {"pt": "Vento", "en": "Wind"},
    "split_auto_fixed_temperature_warning": {"pt": "A temperatura fixa está acima de 35 °C. Os candidatos serão mantidos com alerta.", "en": "Fixed temperature is above 35 °C. Candidates will remain available with a warning."},
    "split_auto_weather_required": {"pt": "Carregue um arquivo meteorológico válido antes de executar a sincronização.", "en": "Load a valid weather file before running synchronized weather mode."},
    "split_auto_weather_sync_limit": {"pt": "Limite de sincronização (s)", "en": "Synchronization limit (s)"},
    "split_auto_exclude_invalid_weather": {"pt": "Excluir candidatos com condições meteorológicas invalidantes", "en": "Exclude candidates with invalidating weather conditions"},
    "split_auto_weather_high_synced": {"pt": "Runs high sincronizadas", "en": "Synchronized high runs"},
    "split_auto_weather_low_synced": {"pt": "Runs low sincronizadas", "en": "Synchronized low runs"},
    "split_auto_weather_missing": {"pt": "Runs sem meteo", "en": "Runs without weather"},
    "split_auto_weather_wind_invalid": {"pt": "Vento > 3 m/s", "en": "Wind > 3 m/s"},
    "split_auto_weather_temp_invalid": {"pt": "Temp > 35 °C", "en": "Temp > 35 °C"},
    "split_auto_weather_max_delta": {"pt": "Maior diferença (s)", "en": "Largest delta (s)"},
    "split_auto_weather_temp_mean": {"pt": "Temp média (°C)", "en": "Mean temp (°C)"},
    "split_auto_weather_pressure_mean": {"pt": "Pressão média (kPa)", "en": "Mean pressure (kPa)"},
    "split_auto_weather_wind_max": {"pt": "Vento máx. (m/s)", "en": "Max wind (m/s)"},
    "split_auto_weather_status": {"pt": "Status meteo", "en": "Weather status"},
    "split_auto_weather_details": {"pt": "Detalhes meteorológicos", "en": "Weather details"},
    "split_auto_wind": {"pt": "Vento (m/s)", "en": "Wind (m/s)"},
    "split_auto_weather_alerts": {"pt": "Alertas", "en": "Warnings"},
    "split_auto_fixed_conditions_invalid": {
        "pt": "Defina temperatura e press\u00e3o fixas v\u00e1lidas antes de executar.",
        "en": "Set valid fixed temperature and pressure values before running."
    },
    "split_auto_run": {
        "pt": "Executar Sele\u00e7\u00e3o Autom\u00e1tica",
        "en": "Run Automatic Selection"
    },
    "split_auto_running": {
        "pt": "Gerando e ranqueando candidatos Split...",
        "en": "Generating and ranking Split candidates..."
    },
    "split_auto_no_candidates_returned": {
        "pt": "Nenhum candidato foi retornado. Consulte os avisos da execu\u00e7\u00e3o.",
        "en": "No candidates were returned. Review the execution warnings."
    },
    "split_auto_completed": {
        "pt": "Candidatos sugeridos",
        "en": "Candidates suggested"
    },
    "split_auto_generated_count": {
        "pt": "Candidatos gerados",
        "en": "Generated candidates"
    },
    "split_auto_ranked_count": {
        "pt": "Candidatos ranqueados",
        "en": "Ranked candidates"
    },
    "split_auto_suggested_count": {
        "pt": "Candidatos sugeridos",
        "en": "Suggested candidates"
    },
    "split_auto_added_count": {
        "pt": "Adicionados ao Comparativo",
        "en": "Added to Comparison"
    },
    "split_auto_duplicates_count": {
        "pt": "Duplicados encontrados",
        "en": "Duplicates found"
    },
    "split_auto_repeated_skipped": {
        "pt": "Repeti\u00e7\u00f5es ignoradas",
        "en": "Repeated runs skipped"
    },
    "split_auto_mode": {
        "pt": "Modo",
        "en": "Mode"
    },
    "split_auto_suggested_candidates": {
        "pt": "Candidatos sugeridos",
        "en": "Suggested candidates"
    },
    "split_auto_pending_review_help": {
        "pt": "Revise as sugest\u00f5es abaixo. Voc\u00ea pode substituir pares individuais ou adicionar o conjunto ao Comparativo Final.",
        "en": "Review the suggestions below. You can replace individual pairs or add the set to Final Comparison."
    },
    "split_auto_replace": {
        "pt": "\U0001F501 Substituir",
        "en": "\U0001F501 Replace"
    },
    "split_auto_replace_help": {
        "pt": "Substitui este par pelo pr\u00f3ximo candidato v\u00e1lido do mesmo ranking.",
        "en": "Replaces this pair with the next valid candidate from the same ranking."
    },
    "split_auto_replacement_succeeded": {
        "pt": "Sugest\u00e3o substitu\u00edda pelo pr\u00f3ximo candidato v\u00e1lido do ranking.",
        "en": "Suggestion replaced by the next valid candidate in the ranking."
    },
    "split_auto_replacement_unavailable": {
        "pt": "N\u00e3o h\u00e1 pr\u00f3xima sugest\u00e3o v\u00e1lida sem os conflitos configurados.",
        "en": "There is no next valid suggestion under the configured conflict rules."
    },
    "split_auto_replacement_unavailable_diagnostic": {
        "pt": "Nenhuma substitui\u00e7\u00e3o v\u00e1lida encontrada. Pool: {pool_size}; verificados: {checked}; pr\u00f3prio candidato: {old}; j\u00e1 vis\u00edveis: {existing}; conflito de passadas: {repeated}.",
        "en": "No valid replacement was found. Pool: {pool_size}; checked: {checked}; outgoing candidate: {old}; already visible: {existing}; run conflicts: {repeated}."
    },
    "split_auto_pending_pool_outdated": {
        "pt": "Estas sugest\u00f5es foram geradas com uma estrat\u00e9gia de reserva anterior. Execute novamente a Sele\u00e7\u00e3o Autom\u00e1tica para habilitar substitui\u00e7\u00f5es.",
        "en": "These suggestions were generated with an older reserve strategy. Run Automatic Selection again to enable replacements."
    },
    "split_auto_replace_confirmation": {
        "pt": "Voc\u00ea est\u00e1 prestes a substituir: {pair}. O sistema buscar\u00e1 a pr\u00f3xima sugest\u00e3o v\u00e1lida do ranking {ranking}, respeitando a configura\u00e7\u00e3o de passadas repetidas. Deseja continuar?",
        "en": "You are about to replace: {pair}. The system will find the next valid suggestion in the {ranking} ranking while respecting the repeated-run setting. Continue?"
    },
    "split_auto_replace_confirm": {
        "pt": "Confirmar substitui\u00e7\u00e3o",
        "en": "Confirm replacement"
    },
    "split_auto_replace_modal_description": {
        "pt": "Este par ser\u00e1 removido da lista de sugest\u00f5es e substitu\u00eddo pela pr\u00f3xima sugest\u00e3o v\u00e1lida do mesmo ranking.",
        "en": "This pair will be removed from the suggestion list and replaced by the next valid suggestion from the same ranking."
    },
    "split_auto_replace_current_constraint_status": {
        "pt": "Status atual do conjunto",
        "en": "Current set status"
    },
    "split_auto_replace_next_constraint_status": {
        "pt": "Status após substituição",
        "en": "Status after replacement"
    },
    "split_auto_replace_constraints_failed": {
        "pt": "A substituição deixa ou mantém o conjunto fora dos critérios ativos.",
        "en": "The replacement leaves or keeps the set outside the active criteria."
    },
    "split_auto_replace_constraints_inconclusive": {
        "pt": "Após a substituição, o conjunto permanece inconclusivo por dados insuficientes.",
        "en": "After replacement, the set remains inconclusive because of insufficient data."
    },
    "split_auto_replace_constraints_approved": {
        "pt": "Após a substituição, o conjunto atende aos critérios ativos.",
        "en": "After replacement, the set meets the active criteria."
    },
    "split_auto_replace_current_pair": {
        "pt": "Par atual",
        "en": "Current pair"
    },
    "split_auto_replace_next_pair": {
        "pt": "Pr\u00f3xima sugest\u00e3o",
        "en": "Next suggestion"
    },
    "split_auto_replace_request_invalid": {
        "pt": "O pedido de substitui\u00e7\u00e3o est\u00e1 incompleto. Feche o modal e tente novamente.",
        "en": "The replacement request is incomplete. Close the dialog and try again."
    },
    "split_auto_replace_preview_changed": {
        "pt": "As sugest\u00f5es mudaram desde a pr\u00e9-visualiza\u00e7\u00e3o. Abra novamente a substitui\u00e7\u00e3o para confirmar o candidato atualizado.",
        "en": "Suggestions changed after the preview. Open replacement again to confirm the updated candidate."
    },
    "split_auto_dialog_not_supported": {
        "pt": "A vers\u00e3o atual do Streamlit n\u00e3o suporta st.dialog. Atualize o Streamlit ou habilite um fallback explicitamente.",
        "en": "The current Streamlit version does not support st.dialog. Update Streamlit or explicitly enable a fallback."
    },
    "split_auto_replacement_pool_count": {
        "pt": "Reserva ranqueada",
        "en": "Ranked reserve"
    },
    "split_auto_add_pending_to_comparison": {
        "pt": "\u2705 Adicionar pares selecionados ao Comparativo Final",
        "en": "\u2705 Add selected pairs to Final Comparison"
    },
    "split_auto_clear_pending": {
        "pt": "\U0001F5D1\uFE0F Limpar sugest\u00f5es",
        "en": "\U0001F5D1\uFE0F Clear suggestions"
    },
    "split_auto_merge_completed": {
        "pt": "Comparativo atualizado: {added} adicionados, {duplicates} duplicados, {updated} atualizados e {preserved} selecionados preservados.",
        "en": "Comparison updated: {added} added, {duplicates} duplicates, {updated} updated, and {preserved} selected pairs preserved."
    },
    "split_auto_section": {
        "pt": "Trecho",
        "en": "Section"
    },
    "split_auto_outbound": {
        "pt": "Ida [+]",
        "en": "Outbound [+]"
    },
    "split_auto_return": {
        "pt": "Volta [-]",
        "en": "Return [-]"
    },
    "split_auto_average": {
        "pt": "M\u00e9dia",
        "en": "Average"
    },
    "split_auto_high_run": {
        "pt": "High Run",
        "en": "High Run"
    },
    "split_auto_low_run": {
        "pt": "Low Run",
        "en": "Low Run"
    },
    "split_auto_temperature": {
        "pt": "Temp (\u00b0C)",
        "en": "Temp (\u00b0C)"
    },
    "split_auto_pressure": {
        "pt": "Press (kPa)",
        "en": "Press (kPa)"
    },
    "split_auto_comparison_guidance": {
        "pt": "Pares adicionados ao Comparativo Final como sugest\u00f5es. A sele\u00e7\u00e3o final continua manual na aba Comparativo Final.",
        "en": "Pairs were added to Final Comparison as suggestions. Final selection remains manual in the Final Comparison tab."
    },
    "split_auto_time_diagnostic": {
        "pt": "Diagn\u00f3stico normativo dos tempos",
        "en": "Normative time diagnostic"
    },
    "split_auto_constraints_approved": {
        "pt": "✅ Conjunto sugerido atende aos critérios ativos.",
        "en": "✅ The suggested set meets the active criteria."
    },
    "split_auto_constraints_pending_failed": {
        "pt": "⚠️ Conjunto sugerido não atende a todos os critérios normativos de tempos.",
        "en": "⚠️ The suggested set does not meet all normative time criteria."
    },
    "split_auto_constraints_card_warning": {
        "pt": "⚠️ Conjunto sugerido não atende a todos os critérios normativos de tempos.",
        "en": "⚠️ The suggested set does not meet all normative time criteria."
    },
    "split_auto_constraints_inconclusive": {
        "pt": "O conjunto sugerido possui verificações inconclusivas por amostra insuficiente.",
        "en": "The suggested set has inconclusive checks because of insufficient samples."
    },
    "split_auto_constraints_no_valid_set": {
        "pt": "⚠️ Não foi encontrada combinação aprovada dentro dos limites de busca configurados para os critérios de tempos.",
        "en": "⚠️ No approved combination was found within the configured search limits for the time criteria."
    },
    "split_auto_use_fallback": {
        "pt": "Preencher sugestões mesmo assim",
        "en": "Fill suggestions anyway"
    },
    "split_auto_constraint_diagnostic": {
        "pt": "Diagnóstico do melhor conjunto encontrado",
        "en": "Best available set diagnostic"
    },
    "split_auto_constraint_warnings": {
        "pt": "Avisos da validação do conjunto",
        "en": "Set-validation warnings"
    },
    "split_auto_constraints_status_approved": {"pt": "Aprovado", "en": "Approved"},
    "split_auto_constraints_status_failed": {"pt": "Reprovado", "en": "Failed"},
    "split_auto_constraints_status_inconclusive": {"pt": "Inconclusivo", "en": "Inconclusive"},
    "split_auto_constraint_cv_high_plus": {"pt": "C.V. Δt — Vel. ref. alta [+]", "en": "Δt C.V. — High reference speed [+]"},
    "split_auto_constraint_cv_high_minus": {"pt": "C.V. Δt — Vel. ref. alta [-]", "en": "Δt C.V. — High reference speed [-]"},
    "split_auto_constraint_cv_low_plus": {"pt": "C.V. Δt — Vel. ref. baixa [+]", "en": "Δt C.V. — Low reference speed [+]"},
    "split_auto_constraint_cv_low_minus": {"pt": "C.V. Δt — Vel. ref. baixa [-]", "en": "Δt C.V. — Low reference speed [-]"},
    "split_auto_constraint_diff_high": {"pt": "Dif. médias Δt — Vel. ref. alta: [+] vs [-]", "en": "Δt mean difference — High reference speed: [+] vs [-]"},
    "split_auto_constraint_diff_low": {"pt": "Dif. médias Δt — Vel. ref. baixa: [+] vs [-]", "en": "Δt mean difference — Low reference speed: [+] vs [-]"},
    "split_auto_time_overall_status": {
        "pt": "Status geral",
        "en": "Overall status"
    },
    "split_auto_time_status_passed": {
        "pt": "Aprovado",
        "en": "Passed"
    },
    "split_auto_time_status_failed": {
        "pt": "Reprovado",
        "en": "Failed"
    },
    "split_auto_time_status_inconclusive": {
        "pt": "Inconclusivo",
        "en": "Inconclusive"
    },
    "split_auto_time_check": {
        "pt": "Verifica\u00e7\u00e3o",
        "en": "Check"
    },
    "split_auto_time_value": {
        "pt": "Valor [%]",
        "en": "Value [%]"
    },
    "split_auto_high_direction_difference": {
        "pt": "Diferen\u00e7a high ida/volta",
        "en": "High plus/minus difference"
    },
    "split_auto_low_direction_difference": {
        "pt": "Diferen\u00e7a low ida/volta",
        "en": "Low plus/minus difference"
    },
    "split_graphical_analysis": {
        "pt": "Análise Gráfica",
        "en": "Graphical Analysis"
    },
    "split_graph_available_runs": {
        "pt": "Passadas disponíveis",
        "en": "Available runs"
    },
    "split_graph_high_section_title": {
        "pt": "Alta velocidade",
        "en": "High speed"
    },
    "split_graph_low_section_title": {
        "pt": "Baixa velocidade",
        "en": "Low speed"
    },
    "split_graph_run_visualization": {
        "pt": "Visualização das passadas",
        "en": "Run visualization"
    },
    "split_graph_calculated_pairs": {
        "pt": "Pares calculados",
        "en": "Calculated pairs"
    },
    "split_graph_interval_type": {
        "pt": "Tipo de intervalo",
        "en": "Interval type"
    },
    "split_graph_direction_filter": {
        "pt": "Direção",
        "en": "Direction"
    },
    "split_graph_both": {
        "pt": "Ambos",
        "en": "Both"
    },
    "split_graph_both_directions": {
        "pt": "Ambas",
        "en": "Both"
    },
    "split_graph_high_speed": {
        "pt": "High-speed",
        "en": "High-speed"
    },
    "split_graph_low_speed": {
        "pt": "Low-speed",
        "en": "Low-speed"
    },
    "split_graph_runs_to_display": {
        "pt": "Runs/passadas a exibir",
        "en": "Runs to display"
    },
    "split_graph_selected_runs": {
        "pt": "Runs selecionadas",
        "en": "Selected runs"
    },
    "split_graph_add_all": {
        "pt": "Adicionar todas",
        "en": "Add all"
    },
    "split_graph_clear_selection": {
        "pt": "Limpar seleção",
        "en": "Clear selection"
    },
    "split_graph_no_runs_for_section": {
        "pt": "Nenhuma run disponível para a seção {section}.",
        "en": "No run is available for the {section} section."
    },
    "split_graph_no_runs_for_direction": {
        "pt": "Nenhuma run disponível para a direção selecionada.",
        "en": "No run is available for the selected direction."
    },
    "split_graph_no_runs_selected": {
        "pt": "Nenhuma run selecionada.",
        "en": "No run is selected."
    },
    "split_graph_no_runs_for_filters": {
        "pt": "Nenhuma passada disponível para a direção e o intervalo selecionados.",
        "en": "No run is available for the selected direction and interval."
    },
    "split_graph_process_intervals_first": {
        "pt": "Processe os intervalos Split antes de visualizar as passadas.",
        "en": "Process the Split intervals before viewing the runs."
    },
    "split_graph_select_at_least_one_run": {
        "pt": "Selecione pelo menos uma passada para visualizar o gráfico.",
        "en": "Select at least one run to view the chart."
    },
    "split_graph_insufficient_curve_data": {
        "pt": "Os dados disponíveis não permitem montar a visualização das passadas selecionadas.",
        "en": "The available data cannot build a visualization for the selected runs."
    },
    "split_graph_aggregate_data_notice": {
        "pt": "{count} passada(s) possui(em) apenas dados agregados; exibindo o segmento do intervalo.",
        "en": "{count} run(s) contain aggregate data only; displaying the interval segment."
    },
    "split_graph_deceleration_title": {
        "pt": "Curvas Split - Velocidade × Tempo",
        "en": "Split Curves - Speed × Time"
    },
    "split_graph_section_curve_title": {
        "pt": "{section} - Velocidade × tempo decorrido",
        "en": "{section} - Speed × elapsed time"
    },
    "split_graph_high_curve_title": {
        "pt": "Curvas de Desaceleração — Alta velocidade",
        "en": "Deceleration Curves — High speed"
    },
    "split_graph_low_curve_title": {
        "pt": "Curvas de Desaceleração — Baixa velocidade",
        "en": "Deceleration Curves — Low speed"
    },
    "split_graph_delta_t_title": {
        "pt": "Tempo de desaceleração por passada",
        "en": "Deceleration time by run"
    },
    "split_graph_section_delta_t_title": {
        "pt": "{section} - Delta t por passada",
        "en": "{section} - Delta t by run"
    },
    "split_graph_elapsed_time": {
        "pt": "Tempo decorrido",
        "en": "Elapsed time"
    },
    "split_graph_speed": {
        "pt": "Velocidade",
        "en": "Speed"
    },
    "split_graph_elapsed_time_axis": {
        "pt": "Tempo decorrido [s]",
        "en": "Elapsed time [s]"
    },
    "split_graph_speed_axis": {
        "pt": "Velocidade [km/h]",
        "en": "Speed [km/h]"
    },
    "split_graph_delta_t": {
        "pt": "Delta t",
        "en": "Delta t"
    },
    "split_graph_delta_t_axis": {
        "pt": "Delta t [s]",
        "en": "Delta t [s]"
    },
    "split_graph_select_pair": {
        "pt": "Par a visualizar",
        "en": "Pair to view"
    },
    "split_graph_no_calculated_pairs": {
        "pt": "Nenhum par foi adicionado ao Comparativo Final ainda.",
        "en": "No pair has been added to Final Comparison yet."
    },
    "split_graph_pair_data_unavailable": {
        "pt": "Os componentes deste par não possuem dados suficientes para visualização gráfica.",
        "en": "This pair's components do not contain enough data for graphical visualization."
    },
    "split_graph_pair_title": {
        "pt": "Componentes do par selecionado — Velocidade × Tempo",
        "en": "Selected pair components — Speed × Time"
    },
    "split_graph_active_pair": {
        "pt": "Par ativo",
        "en": "Active pair"
    },
    "page_split_final_comparison": {
        "pt": "Comparativo Final",
        "en": "Final Comparison"
    },
    "page_split_results": {
        "pt": "Resultados Split",
        "en": "Split Results"
    },
    "split_results_consolidated": {
        "pt": "Resultados consolidados",
        "en": "Consolidated results"
    },
    "split_results_final_f0": {
        "pt": "F0 final [N]",
        "en": "Final F0 [N]"
    },
    "split_results_final_f2": {
        "pt": "F2 final [N/(km/h)²]",
        "en": "Final F2 [N/(km/h)²]"
    },
    "split_results_mean_energy": {
        "pt": "Energia média [MJ/km]",
        "en": "Mean energy [MJ/km]"
    },
    "split_results_cv_f0": {
        "pt": "CV F0 [%]",
        "en": "F0 CV [%]"
    },
    "split_results_cv_f2": {
        "pt": "CV F2 [%]",
        "en": "F2 CV [%]"
    },
    "split_results_cv_energy": {
        "pt": "CV energia [%]",
        "en": "Energy CV [%]"
    },
    "split_results_not_applicable": {
        "pt": "N/A",
        "en": "N/A"
    },
    "split_results_conformity": {
        "pt": "Status de conformidade",
        "en": "Conformity status"
    },
    "split_results_status_conforming": {
        "pt": "Conforme",
        "en": "Conforming"
    },
    "split_results_status_nonconforming": {
        "pt": "Não conforme",
        "en": "Nonconforming"
    },
    "split_results_status_inconclusive": {
        "pt": "Inconclusivo",
        "en": "Inconclusive"
    },
    "split_results_status_not_evaluable": {
        "pt": "Não avaliável com menos de dois valores",
        "en": "Not evaluable with fewer than two values"
    },
    "split_results_status_incomplete": {
        "pt": "Incompleto: faltam coeficientes corrigidos",
        "en": "Incomplete: corrected coefficients are missing"
    },
    "split_results_status_warning": {
        "pt": "Consolidado com avisos",
        "en": "Consolidated with warnings"
    },
    "split_results_status_ready": {
        "pt": "Pronto",
        "en": "Ready"
    },
    "split_results_selected_source_note": {
        "pt": "{count} par(es) lido(s) diretamente da seleção do Comparativo Final.",
        "en": "{count} pair(s) read directly from the Final Comparison selection."
    },
    "split_results_validation": {
        "pt": "Validação dos resultados",
        "en": "Result validation"
    },
    "split_results_missing_corrected": {
        "pt": "Coeficientes corrigidos ausentes: F0 em {f0}/{total} par(es) e F2 em {f2}/{total} par(es). As demais informações continuam disponíveis.",
        "en": "Missing corrected coefficients: F0 in {f0}/{total} pair(s) and F2 in {f2}/{total} pair(s). Remaining information is still available."
    },
    "split_results_missing_energy": {
        "pt": "Energia ausente em {missing}/{total} par(es). A média usa somente valores disponíveis.",
        "en": "Energy is missing in {missing}/{total} pair(s). The mean uses available values only."
    },
    "split_results_warning_count": {
        "pt": "{count} aviso(s) único(s) preservado(s) nos detalhes dos pares.",
        "en": "{count} unique warning(s) preserved in pair details."
    },
    "split_results_no_pairs_available": {
        "pt": "Nenhum par está disponível no Comparativo Final. Volte à sub-aba Cálculo dos Coeficientes em Análise de Pares para adicionar pares.",
        "en": "No pair is available in Final Comparison. Return to the Coefficient Calculation sub-tab in Pair Analysis to add pairs."
    },
    "split_results_no_pairs_selected": {
        "pt": "Há pares no Comparativo Final, mas nenhum está selecionado. Volte ao Comparativo Final e marque os pares que devem compor o resultado.",
        "en": "Final Comparison has pairs, but none is selected. Return to Final Comparison and select the pairs that should compose the result."
    },
    "split_results_final_table": {
        "pt": "Tabela final dos pares selecionados",
        "en": "Final selected-pair table"
    },
    "split_results_pair_details": {
        "pt": "Detalhamento rastreável por par",
        "en": "Traceable details by pair"
    },
    "split_results_index": {
        "pt": "Índice",
        "en": "Index"
    },
    "split_results_uncorrected_f0": {
        "pt": "f'0 não corrigido [N]",
        "en": "Uncorrected f'0 [N]"
    },
    "split_results_uncorrected_f2": {
        "pt": "f'2 não corrigido [N/(m/s)²]",
        "en": "Uncorrected f'2 [N/(m/s)²]"
    },
    "split_results_deceleration_time": {
        "pt": "Tempo de desaceleração [s]",
        "en": "Deceleration time [s]"
    },
    "split_results_subintervals": {
        "pt": "Subintervalos",
        "en": "Subintervals"
    },
    "split_results_no_ambient_traceability": {
        "pt": "Este par não possui rastreabilidade ambiental por componente.",
        "en": "This pair has no component-level ambient traceability."
    },
    "split_results_card_conformity": {
        "pt": "Conformidade",
        "en": "Conformity"
    },
    "split_results_card_conformity_criteria": {
        "pt": "CV Δt ≤ 2,5% | Dif. médias ≤ 10%",
        "en": "Δt CV ≤ 2.5% | Mean diff ≤ 10%"
    },
    "split_results_diagnostic_label": {
        "pt": "(diagnóstico)",
        "en": "(diagnostic)"
    },
    "split_results_meteo_sync_expander": {
        "pt": "Detalhes de sincronização meteorológica ({count} avisos)",
        "en": "Weather synchronization details ({count} warnings)"
    },
    "split_results_deviation_title": {
        "pt": "Análise de desvios",
        "en": "Deviation analysis"
    },
    "split_results_deviation_time_overall": {
        "pt": "Tempos Δt",
        "en": "Δt times"
    },
    "split_results_deviation_weather": {
        "pt": "Meteorologia",
        "en": "Weather"
    },
    "split_results_deviation_time_criteria_title": {
        "pt": "Critérios normativos de tempo",
        "en": "Normative time criteria"
    },
    "split_results_deviation_metric": {
        "pt": "Métrica",
        "en": "Metric"
    },
    "split_results_deviation_value": {
        "pt": "Valor",
        "en": "Value"
    },
    "split_results_deviation_limit": {
        "pt": "Limite",
        "en": "Limit"
    },
    "split_results_deviation_status": {
        "pt": "Status",
        "en": "Status"
    },
    "split_results_deviation_coefficients_title": {
        "pt": "Diagnóstico de coeficientes (não normativo)",
        "en": "Coefficient diagnostics (non-normative)"
    },
    "split_results_deviation_details_note": {
        "pt": "Detalhes completos permanecem em Comparativo Final > Análise de desvios.",
        "en": "Full details remain available in Final Comparison > Deviation Analysis."
    },
    "split_results_export": {
        "pt": "Exportação",
        "en": "Export"
    },
    "split_results_export_button": {
        "pt": "Exportar resultados Split",
        "en": "Export Split results"
    },
    "split_results_generate_excel": {
        "pt": "Gerar Excel",
        "en": "Generate Excel"
    },
    "split_results_export_pending": {
        "pt": "Exportação Split pendente de adaptação ao novo consolidado. Nenhum exportador Standard está conectado a esta página.",
        "en": "Split export is pending adaptation to the new consolidation. No Standard exporter is connected to this page."
    },
    "split_coefficient_calculation_placeholder": {
        "pt": "A seleção de high/low e o cálculo do par serão implementados na próxima rodada.",
        "en": "High/low selection and pair coefficient calculation will be implemented in the next round."
    },
    "split_manual_pair_selection": {
        "pt": "Seleção manual do par",
        "en": "Manual pair selection"
    },
    "split_select_high_run": {
        "pt": "Run high-speed",
        "en": "High-speed run"
    },
    "split_select_low_run": {
        "pt": "Run low-speed",
        "en": "Low-speed run"
    },
    "split_ida_plus": {
        "pt": "Ida (+)",
        "en": "Ida (+)"
    },
    "split_volta_minus": {
        "pt": "Volta (-)",
        "en": "Volta (-)"
    },
    "split_high_speed_ida": {
        "pt": "High-speed ida (+)",
        "en": "High-speed ida (+)"
    },
    "split_low_speed_ida": {
        "pt": "Low-speed ida (+)",
        "en": "Low-speed ida (+)"
    },
    "split_high_speed_volta": {
        "pt": "High-speed volta (-)",
        "en": "High-speed volta (-)"
    },
    "split_low_speed_volta": {
        "pt": "Low-speed volta (-)",
        "en": "Low-speed volta (-)"
    },
    "split_select_high_plus_run": {
        "pt": "High-speed ida (+)",
        "en": "High-speed ida (+)"
    },
    "split_select_low_plus_run": {
        "pt": "Low-speed ida (+)",
        "en": "Low-speed ida (+)"
    },
    "split_select_high_minus_run": {
        "pt": "High-speed volta (-)",
        "en": "High-speed volta (-)"
    },
    "split_select_low_minus_run": {
        "pt": "Low-speed volta (-)",
        "en": "Low-speed volta (-)"
    },
    "split_pair_average": {
        "pt": "Media do par",
        "en": "Pair average"
    },
    "split_direction_plus_result": {
        "pt": "Resultado direcao +",
        "en": "Direction + result"
    },
    "split_direction_minus_result": {
        "pt": "Resultado direcao -",
        "en": "Direction - result"
    },
    "split_complete_ida_volta_pair_required": {
        "pt": "E necessario um par completo ida/volta: high+, low+, high- e low-.",
        "en": "A complete ida/volta pair is required: high+, low+, high-, and low-."
    },
    "split_complete_pair_missing_components": {
        "pt": "Componentes ausentes para calcular o par completo: {components}.",
        "en": "Missing components for the complete pair calculation: {components}."
    },
    "split_invalid_direction_records_warning": {
        "pt": "{count} intervalo(s) parseado(s) nao tem direcao explicita + ou -. O calculo do par completo esta bloqueado.",
        "en": "{count} parsed interval(s) do not have explicit + or - direction. Complete pair calculation is blocked."
    },
    "split_high_plus_records_available": {
        "pt": "High +",
        "en": "High +"
    },
    "split_low_plus_records_available": {
        "pt": "Low +",
        "en": "Low +"
    },
    "split_high_minus_records_available": {
        "pt": "High -",
        "en": "High -"
    },
    "split_low_minus_records_available": {
        "pt": "Low -",
        "en": "Low -"
    },
    "split_complete_pair_components": {
        "pt": "Componentes do par completo",
        "en": "Complete pair components"
    },
    "split_selected_pair_results": {
        "pt": "Resultados ida, volta e media",
        "en": "Ida, volta and average results"
    },
    "split_uncorrected_results": {
        "pt": "Coeficientes não corrigidos",
        "en": "Uncorrected coefficients"
    },
    "split_corrected_results": {
        "pt": "Coeficientes corrigidos",
        "en": "Corrected coefficients"
    },
    "split_pair_results_title": {
        "pt": "Resultados do Par",
        "en": "Pair Results"
    },
    "split_coefficient_details": {
        "pt": "Detalhes dos coeficientes calculados",
        "en": "Calculated coefficient details"
    },
    "split_components": {
        "pt": "Componentes",
        "en": "Components"
    },
    "split_corrected_results_unavailable": {
        "pt": "F0/F2 corrigidos não estão disponíveis porque as condições ambientais válidas estão incompletas.",
        "en": "Corrected F0/F2 are unavailable because valid ambient conditions are incomplete."
    },
    "split_ambient_conditions_title": {
        "pt": "Condições ambientais para correção",
        "en": "Ambient conditions for correction"
    },
    "split_ambient_mode_label": {
        "pt": "Modo ambiental",
        "en": "Ambient mode"
    },
    "split_ambient_mode_fixed": {
        "pt": "Usar temperatura e pressão fixas",
        "en": "Use fixed temperature and pressure"
    },
    "split_ambient_mode_weather_sync": {
        "pt": "Usar sincronização automática com arquivo meteorológico",
        "en": "Use automatic weather file synchronization"
    },
    "split_ambient_mode_fixed_short": {
        "pt": "Fixo",
        "en": "Fixed"
    },
    "split_ambient_mode_weather_sync_short": {
        "pt": "Sincronização meteo",
        "en": "Weather sync"
    },
    "split_ambient_change_invalidated": {
        "pt": "As condições ambientais mudaram. Resultados e cards anteriores foram limpos; recalcule os coeficientes.",
        "en": "Ambient conditions changed. Previous results and cards were cleared; recalculate the coefficients."
    },
    "split_fixed_temperature": {
        "pt": "Temperatura fixa (°C)",
        "en": "Fixed temperature (°C)"
    },
    "split_fixed_pressure": {
        "pt": "Pressão fixa (kPa)",
        "en": "Fixed pressure (kPa)"
    },
    "split_fixed_conditions_apply_all": {
        "pt": "A mesma temperatura e pressão serão aplicadas às quatro passadas do par.",
        "en": "The same temperature and pressure will be applied to all four runs in the pair."
    },
    "split_fixed_conditions_card": {
        "pt": "Correção calculada com temperatura e pressão fixas. Valores exibidos como ida / volta.",
        "en": "Correction calculated with fixed temperature and pressure. Values are shown as ida / volta."
    },
    "split_weather_correction_unavailable": {
        "pt": "A sincronização meteorológica está incompleta. O cálculo não corrigido continuará disponível, mas F0/F2 não serão preenchidos.",
        "en": "Weather synchronization is incomplete. Uncorrected calculation remains available, but F0/F2 will not be populated."
    },
    "split_ambient_source_summary": {
        "pt": "Fonte das condições ambientais: {source}.",
        "en": "Ambient condition source: {source}."
    },
    "split_ambient_source_manual_fixed": {
        "pt": "temperatura e pressão fixas",
        "en": "fixed temperature and pressure"
    },
    "split_ambient_source_weather_file_sync": {
        "pt": "sincronização com arquivo meteorológico",
        "en": "weather file synchronization"
    },
    "split_selected_pair_inputs": {
        "pt": "Resumo técnico do par selecionado",
        "en": "Selected pair technical summary"
    },
    "split_calculate_selected_pair": {
        "pt": "Calcular par selecionado",
        "en": "Calculate selected pair"
    },
    "split_calculate_coefficients": {
        "pt": "Calcular Coeficientes",
        "en": "Calculate Coefficients"
    },
    "split_selected_pair_calculated": {
        "pt": "Par Split calculado e salvo.",
        "en": "Split pair calculated and saved."
    },
    "split_saved_results_count": {
        "pt": "{count} resultado(s) Split salvo(s). Abra Resultados Split para agregar/exportar.",
        "en": "{count} Split result(s) saved. Open Split Results to aggregate/export."
    },
    "split_add_to_final_comparison": {
        "pt": "Adicionar à tabela comparativa final",
        "en": "Add to final comparison"
    },
    "split_add_pair_section": {
        "pt": "Adicionar par ao Comparativo Final",
        "en": "Add pair to Final Comparison"
    },
    "split_comparison_pairs_count": {
        "pt": "{count} par(es) na tabela comparativa final.",
        "en": "{count} pair(s) in the final comparison table."
    },
    "split_pair_added_to_comparison": {
        "pt": "Par adicionado à tabela comparativa final.",
        "en": "Pair added to final comparison."
    },
    "split_no_calculated_pair_to_add": {
        "pt": "Calcule um par selecionado antes de adicionar à tabela comparativa.",
        "en": "Calculate a selected pair before adding it to the comparison table."
    },
    "split_final_comparison_table": {
        "pt": "Tabela comparativa final",
        "en": "Final comparison table"
    },
    "split_selection_source_manual": {
        "pt": "Manual",
        "en": "Manual"
    },
    "split_selection_source_algorithm": {
        "pt": "Algoritmo",
        "en": "Algorithm"
    },
    "split_selection_source_unknown": {
        "pt": "Pendente",
        "en": "Pending"
    },
    "split_selection_source": {
        "pt": "Origem da seleção",
        "en": "Selection source"
    },
    "split_selected": {
        "pt": "Selecionado",
        "en": "Selected"
    },
    "split_selected_pairs": {
        "pt": "Pares selecionados",
        "en": "Selected pairs"
    },
    "split_selected_pairs_count": {
        "pt": "{selected} de {total} par(es) selecionado(s).",
        "en": "{selected} of {total} pair(s) selected."
    },
    "split_select_all_pairs": {
        "pt": "Selecionar todos",
        "en": "Select all"
    },
    "split_deselect_all_pairs": {
        "pt": "Desmarcar todos",
        "en": "Deselect all"
    },
    "split_corrected_pairs_section": {
        "pt": "Pares com Correção Climática",
        "en": "Pairs with Climatic Correction"
    },
    "split_uncorrected_pairs_reference_section": {
        "pt": "Pares sem Correção Climática - apenas referência",
        "en": "Pairs without Climatic Correction - reference only"
    },
    "split_uncorrected_pairs_reference_caption": {
        "pt": "Estes pares não possuem coeficientes corrigidos e não podem ser incluídos no cálculo de resultados finais.",
        "en": "These pairs do not have corrected coefficients and cannot be included in final-results calculation."
    },
    "split_selected_pair_statistics_title": {
        "pt": "Estatísticas dos Pares Selecionados ({count} pares)",
        "en": "Selected Pair Statistics ({count} pairs)"
    },
    "split_select_pairs_for_final_hint": {
        "pt": "Selecione pelo menos um par para ver as estatísticas e calcular os resultados finais.",
        "en": "Select at least one pair to view statistics and calculate final results."
    },
    "split_calculate_final_results": {
        "pt": "Calcular resultados finais",
        "en": "Calculate final results"
    },
    "split_go_to_results": {
        "pt": "Ir para Resultados Split",
        "en": "Go to Split Results"
    },
    "split_selected_pairs_traceability": {
        "pt": "Rastreabilidade dos pares selecionados",
        "en": "Selected pair traceability"
    },
    "split_selected_pairs_traceability_empty": {
        "pt": "Nenhuma rastreabilidade disponível para os pares selecionados.",
        "en": "No traceability is available for the selected pairs."
    },
    "split_cv_not_applicable_single_pair": {
        "pt": "N/A",
        "en": "N/A"
    },
    "split_no_corrected_pairs": {
        "pt": "Nenhum par com correção climática calculado ainda.",
        "en": "No pair with climatic correction has been calculated yet."
    },
    "split_temp_short": {
        "pt": "Temp (°C)",
        "en": "Temp (°C)"
    },
    "split_press_short": {
        "pt": "Press (kPa)",
        "en": "Press (kPa)"
    },
    "split_wind_short": {
        "pt": "Vento (m/s)",
        "en": "Wind (m/s)"
    },
    "split_comparison_legend": {
        "pt": "Legenda",
        "en": "Legend"
    },
    "split_legend_selected_pair": {
        "pt": "Par selecionado",
        "en": "Selected pair"
    },
    "split_legend_manual_pair": {
        "pt": "Manual",
        "en": "Manual"
    },
    "split_legend_energy_pair": {
        "pt": "Sugerido por menor energia",
        "en": "Suggested by lowest energy"
    },
    "split_legend_target_pair": {
        "pt": "Sugerido por target F0/F2",
        "en": "Suggested by F0/F2 target"
    },
    "split_legend_energy_target_pair": {
        "pt": "Sugerido por energia e target",
        "en": "Suggested by energy and target"
    },
    "split_legend_uncorrected_pair": {
        "pt": "Sem correção",
        "en": "No correction"
    },
    "split_legend_cv_warning": {
        "pt": "CV > 10%",
        "en": "CV > 10%"
    },
    "split_selected_short": {
        "pt": "Sel",
        "en": "Sel"
    },
    "split_pair_id": {
        "pt": "ID do par",
        "en": "Pair ID"
    },
    "split_high_plus_run_short": {
        "pt": "High+ run",
        "en": "High+ run"
    },
    "split_low_plus_run_short": {
        "pt": "Low+ run",
        "en": "Low+ run"
    },
    "split_high_minus_run_short": {
        "pt": "High- run",
        "en": "High- run"
    },
    "split_low_minus_run_short": {
        "pt": "Low- run",
        "en": "Low- run"
    },
    "split_corrected_coefficients": {
        "pt": "Coeficientes corrigidos",
        "en": "Corrected coefficients"
    },
    "split_corrected_f0_mean": {
        "pt": "F0 médio [N]",
        "en": "Mean F0 [N]"
    },
    "split_corrected_f2_mean": {
        "pt": "F2 médio [N/(km/h)²]",
        "en": "Mean F2 [N/(km/h)²]"
    },
    "split_energy_with_unit": {
        "pt": "Energia [MJ/km]",
        "en": "Energy [MJ/km]"
    },
    "split_temperature_plus_minus": {
        "pt": "Temp. ida/volta [°C]",
        "en": "Ida/volta temp. [°C]"
    },
    "split_pressure_plus_minus": {
        "pt": "Pressão ida/volta [kPa]",
        "en": "Ida/volta pressure [kPa]"
    },
    "split_comparison_status": {
        "pt": "Status/avisos",
        "en": "Status/warnings"
    },
    "split_comparison_status_ready": {
        "pt": "Pronto",
        "en": "Ready"
    },
    "split_comparison_status_warning": {
        "pt": "{count} aviso(s)",
        "en": "{count} warning(s)"
    },
    "split_comparison_status_incomplete": {
        "pt": "Incompleto",
        "en": "Incomplete"
    },
    "split_comparison_empty": {
        "pt": "Nenhum par calculado ainda.",
        "en": "No pair has been calculated yet."
    },
    "split_clear_final_comparison": {
        "pt": "Limpar todos",
        "en": "Clear all"
    },
    "split_comparison_pair_cards": {
        "pt": "Pares adicionados ao comparativo",
        "en": "Pairs added to the comparison"
    },
    "split_comparison_final_hint": {
        "pt": "Vá para Comparativo Final para selecionar e comparar os pares.",
        "en": "Go to Final Comparison to select and compare the pairs."
    },
    "split_remove_pair": {
        "pt": "Remover par",
        "en": "Remove pair"
    },
    "split_remove_pair_short": {
        "pt": "Remover",
        "en": "Remove"
    },
    "split_pair_to_remove": {
        "pt": "Par a remover",
        "en": "Pair to remove"
    },
    "split_card_high_source": {
        "pt": "Fonte high-speed",
        "en": "High-speed source"
    },
    "split_card_low_source": {
        "pt": "Fonte low-speed",
        "en": "Low-speed source"
    },
    "split_card_coefficients": {
        "pt": "Coeficientes e entradas",
        "en": "Coefficients and inputs"
    },
    "split_card_meteo": {
        "pt": "Meteorologia",
        "en": "Weather/meteo"
    },
    "split_card_energy": {
        "pt": "Energia",
        "en": "Energy"
    },
    "split_pair": {
        "pt": "Par",
        "en": "Pair"
    },
    "split_card_ambient_conditions": {
        "pt": "Condições Ambientais",
        "en": "Ambient Conditions"
    },
    "split_card_temp_ida_volta": {
        "pt": "Temp ida/volta",
        "en": "Ida/volta temp"
    },
    "split_card_pressure_ida_volta": {
        "pt": "Pressão ida/volta",
        "en": "Ida/volta pressure"
    },
    "split_temp_plus_used": {
        "pt": "Temp ida usada (média high+/low+)",
        "en": "Ida temperature used (high+/low+ mean)"
    },
    "split_temp_minus_used": {
        "pt": "Temp volta usada (média high-/low-)",
        "en": "Volta temperature used (high-/low- mean)"
    },
    "split_press_plus_used": {
        "pt": "Pressão ida usada (média high+/low+)",
        "en": "Ida pressure used (high+/low+ mean)"
    },
    "split_press_minus_used": {
        "pt": "Pressão volta usada (média high-/low-)",
        "en": "Volta pressure used (high-/low- mean)"
    },
    "split_ambient_traceability": {
        "pt": "Rastreabilidade ambiental das quatro passadas",
        "en": "Ambient traceability for the four runs"
    },
    "split_card_wind_ida_volta": {
        "pt": "Vento ida/volta",
        "en": "Ida/volta wind"
    },
    "split_card_variations": {
        "pt": "Variações",
        "en": "Variations"
    },
    "split_card_warnings": {
        "pt": "Avisos",
        "en": "Warnings"
    },
    "split_card_traceability": {
        "pt": "Rastreabilidade das passadas",
        "en": "Run traceability"
    },
    "split_f2_explicit_conversion_note": {
        "pt": "F2 corrigido usa conversão explícita de N/(m/s)² para N/(km/h)².",
        "en": "Corrected F2 uses an explicit conversion from N/(m/s)² to N/(km/h)²."
    },
    "split_energy_unavailable_contract": {
        "pt": "Energia indisponível porque F0/F2 corrigidos não estão disponíveis.",
        "en": "Energy is unavailable because corrected F0/F2 are not available."
    },
    "split_weather_sync_details": {
        "pt": "Detalhes da sincronização meteorológica",
        "en": "Weather synchronization details"
    },
    "split_weather_sync_summary_datetime": {
        "pt": "Sincronização meteo: data e hora",
        "en": "Weather sync: date and time"
    },
    "split_weather_sync_summary_time_only": {
        "pt": "Sincronização meteo: somente horário ⚠️",
        "en": "Weather sync: time only ⚠️"
    },
    "split_weather_sync_summary_not_found": {
        "pt": "Sincronização meteo: não encontrada ⚠️",
        "en": "Weather sync: not found ⚠️"
    },
    "split_weather_warning_equally_close": {
        "pt": "Foram encontrados registros meteorológicos igualmente próximos; o primeiro registro foi usado.",
        "en": "Multiple weather records were equally close; the first record was used."
    },
    "split_weather_warning_timezone_missing": {
        "pt": "O arquivo meteorológico não declara fuso horário; os horários foram comparados como horário local.",
        "en": "Weather timezone is not declared; timestamps were compared as local time."
    },
    "split_weather_warning_date_differs": {
        "pt": "A data meteorológica difere da passagem; a sincronização usou somente o horário.",
        "en": "Weather date differs from the run date; synchronization used time of day only."
    },
    "split_warning_count": {
        "pt": "{count} aviso(s); consulte os detalhes do par.",
        "en": "{count} warning(s); see pair details."
    },
    "split_file": {
        "pt": "Arquivo",
        "en": "File"
    },
    "split_run": {
        "pt": "Run",
        "en": "Run"
    },
    "split_direction": {
        "pt": "Direção",
        "en": "Direction"
    },
    "split_timestamp": {
        "pt": "Horário",
        "en": "Timestamp"
    },
    "split_meteo_not_synced_for_pair": {
        "pt": "Meteo não sincronizado para este par.",
        "en": "Meteo was not synchronized for this pair."
    },
    "split_meteo_display_only_warning": {
        "pt": "A sincronização é exibida com rastreabilidade completa; somente temperatura e pressão de matches válidos são usadas na correção.",
        "en": "Synchronization is shown with full traceability; only temperature and pressure from valid matches are used for correction."
    },
    "split_meteo_matched": {
        "pt": "Sincronizado",
        "en": "Matched"
    },
    "split_meteo_not_matched": {
        "pt": "Não sincronizado",
        "en": "Not matched"
    },
    "split_meteo_method_datetime": {
        "pt": "Data + hora",
        "en": "Date + time"
    },
    "split_meteo_method_time_only": {
        "pt": "Somente horário",
        "en": "Time only"
    },
    "split_meteo_method_manual_date_assumption": {
        "pt": "Data assumida pelo horário",
        "en": "Date assumed from time"
    },
    "split_meteo_method_not_found": {
        "pt": "Não encontrado",
        "en": "Not found"
    },
    "split_meteo_method_fixed": {
        "pt": "Condição fixa",
        "en": "Fixed condition"
    },
    "split_meteo_sync_limit": {
        "pt": "Limite automático de sincronização: {seconds} s.",
        "en": "Automatic synchronization limit: {seconds} s."
    },
    "split_meteo_pair_average": {
        "pt": "Resumo médio de {count} passagem(ns) sincronizada(s): {temperature} °C, {pressure} kPa, vento {wind} m/s.",
        "en": "Average summary from {count} matched run(s): {temperature} °C, {pressure} kPa, wind {wind} m/s."
    },
    "split_meteo_component": {
        "pt": "Componente",
        "en": "Component"
    },
    "split_meteo_status": {
        "pt": "Status",
        "en": "Status"
    },
    "split_meteo_method": {
        "pt": "Método",
        "en": "Method"
    },
    "split_meteo_run_datetime": {
        "pt": "Data/hora da passagem",
        "en": "Run datetime"
    },
    "split_meteo_weather_datetime": {
        "pt": "Data/hora meteo",
        "en": "Weather datetime"
    },
    "split_meteo_delta_seconds": {
        "pt": "Diferença (s)",
        "en": "Delta (s)"
    },
    "split_meteo_temperature": {
        "pt": "Temperatura (°C)",
        "en": "Temperature (°C)"
    },
    "split_meteo_pressure": {
        "pt": "Pressão (kPa)",
        "en": "Pressure (kPa)"
    },
    "split_meteo_wind_speed": {
        "pt": "Vento (m/s)",
        "en": "Wind (m/s)"
    },
    "split_meteo_wind_direction": {
        "pt": "Direção do vento",
        "en": "Wind direction"
    },
    "split_meteo_source_file": {
        "pt": "Arquivo meteo",
        "en": "Weather file"
    },
    "split_no_parsed_records_for_calculation": {
        "pt": "Nenhum intervalo high ou low foi parseado. Revise a aba Seleção de Intervalos.",
        "en": "No high or low interval was parsed. Review the Interval Selection tab."
    },
    "split_no_high_records_for_calculation": {
        "pt": "Nenhum intervalo high-speed foi parseado. O cálculo do par está bloqueado.",
        "en": "No high-speed interval was parsed. Pair calculation is blocked."
    },
    "split_no_low_records_for_calculation": {
        "pt": "Nenhum intervalo low-speed foi parseado. O cálculo do par está bloqueado.",
        "en": "No low-speed interval was parsed. Pair calculation is blocked."
    },
    "split_effective_mass_required_for_calculation": {
        "pt": "Informe e confirme a massa efetiva em Dados do Veículo antes de calcular.",
        "en": "Enter and confirm the effective mass in Vehicle Data before calculating."
    },
    "split_meteo_not_available_warning": {
        "pt": "Arquivo meteorológico não disponível. Os coeficientes não corrigidos podem ser calculados, mas F0/F2 por sincronização não serão preenchidos.",
        "en": "Weather/meteo file is not available. Uncorrected coefficients can be calculated, but synchronized F0/F2 will not be populated."
    },
    "split_meteo_loaded_not_applied_warning": {
        "pt": "Arquivo meteorológico carregado; sincronização atual: {mode}. A aplicação meteorológica no cálculo Split ainda não foi implementada.",
        "en": "Weather/meteo file loaded; current synchronization: {mode}. Meteo application in the Split calculation is not implemented yet."
    },
    "split_meteo_loaded_for_correction": {
        "pt": "Arquivo meteorológico carregado; sincronização para correção: {mode}.",
        "en": "Weather/meteo file loaded; synchronization for correction: {mode}."
    },
    "split_high_records_available": {
        "pt": "High parseado",
        "en": "Parsed high"
    },
    "split_low_records_available": {
        "pt": "Low parseado",
        "en": "Parsed low"
    },
    "split_effective_mass_available": {
        "pt": "Massa efetiva",
        "en": "Effective mass"
    },
    "split_input_sources_summary": {
        "pt": "Arquivos de entrada: {files}",
        "en": "Input files: {files}"
    },
    "yes": {
        "pt": "Sim",
        "en": "Yes"
    },
    "no": {
        "pt": "Não",
        "en": "No"
    },
    "split_upload_sources": {
        "pt": "Arquivos CSV do metodo Split",
        "en": "Split method CSV files"
    },
    "split_input_layout": {
        "pt": "Formato de entrada Split",
        "en": "Split input layout"
    },
    "split_input_mode": {
        "pt": "Modo de entrada",
        "en": "Input mode"
    },
    "split_input_mode_separate": {
        "pt": "Dois arquivos de desaceleracao separados",
        "en": "Two separate coastdown files"
    },
    "split_input_mode_combined": {
        "pt": "Um unico arquivo de desaceleracao combinado",
        "en": "Single combined coastdown file"
    },
    "split_input_layout_separate": {
        "pt": "Arquivos separados",
        "en": "Separate files"
    },
    "split_input_layout_combined": {
        "pt": "Arquivo unico/combinado",
        "en": "Single/combined file"
    },
    "split_upload_primary_csv": {
        "pt": "CSV principal: full coastdown, combinado ou alta velocidade",
        "en": "Primary CSV: full coastdown, combined, or high speed"
    },
    "split_upload_high_csv": {
        "pt": "CSV high-speed",
        "en": "High-speed CSV"
    },
    "split_upload_combined_csv": {
        "pt": "CSV unico/combinado",
        "en": "Single/combined CSV"
    },
    "split_upload_low_csv": {
        "pt": "CSV de baixa velocidade separado (opcional)",
        "en": "Separate low-speed CSV (optional)"
    },
    "warning_change_split_input_mode": {
        "pt": "Alterar o modo de entrada Split invalida parser, resultados, selecoes e export deste teste.",
        "en": "Changing the Split input mode invalidates parser output, results, selections, and export for this test."
    },
    "split_input_mode_change_requires_file": {
        "pt": "Para alterar o modo de entrada, carregue o arquivo principal correspondente ao novo modo.",
        "en": "To change the input mode, upload the primary file for the new mode."
    },
    "split_input_mode_separate_complete": {
        "pt": "Modo de entrada Split: dois arquivos de desaceleracao separados - intervalos de alta e baixa velocidade foram encontrados.",
        "en": "Split input mode: two separate coastdown files - high-speed and low-speed intervals were found."
    },
    "split_input_mode_separate_high_only": {
        "pt": "Modo de entrada Split: dois arquivos de desaceleracao separados - intervalo de alta velocidade encontrado, mas nenhum arquivo/intervalo de baixa velocidade valido foi fornecido.",
        "en": "Split input mode: two separate coastdown files - high-speed interval found, but no valid low-speed file/interval was provided."
    },
    "split_input_mode_separate_low_only": {
        "pt": "Modo de entrada Split: dois arquivos de desaceleracao separados - intervalo de baixa velocidade encontrado, mas nenhum arquivo/intervalo de alta velocidade valido foi fornecido.",
        "en": "Split input mode: two separate coastdown files - low-speed interval found, but no valid high-speed file/interval was provided."
    },
    "split_input_mode_separate_none": {
        "pt": "Modo de entrada Split: dois arquivos de desaceleracao separados - nenhum intervalo valido de alta ou baixa velocidade foi encontrado.",
        "en": "Split input mode: two separate coastdown files - no valid high-speed or low-speed interval was found."
    },
    "split_input_mode_combined_complete": {
        "pt": "Modo de entrada Split: um unico arquivo de desaceleracao combinado - intervalos de alta e baixa velocidade foram encontrados no mesmo arquivo.",
        "en": "Split input mode: single combined coastdown file - high-speed and low-speed intervals were found in the same file."
    },
    "split_input_mode_combined_high_only": {
        "pt": "Modo de entrada Split: um unico arquivo de desaceleracao combinado - intervalo de alta velocidade encontrado, mas nenhum intervalo de baixa velocidade valido foi detectado.",
        "en": "Split input mode: single combined coastdown file - high-speed interval found, but no valid low-speed interval was detected."
    },
    "split_input_mode_combined_low_only": {
        "pt": "Modo de entrada Split: um unico arquivo de desaceleracao combinado - intervalo de baixa velocidade encontrado, mas nenhum intervalo de alta velocidade valido foi detectado.",
        "en": "Split input mode: single combined coastdown file - low-speed interval found, but no valid high-speed interval was detected."
    },
    "split_input_mode_combined_none": {
        "pt": "Modo de entrada Split: um unico arquivo de desaceleracao combinado - nenhum intervalo valido de alta ou baixa velocidade foi encontrado.",
        "en": "Split input mode: single combined coastdown file - no valid high-speed or low-speed interval was found."
    },
    "split_input_mode_two_files_complete": {
        "pt": "Modo de entrada Split: 2 arquivos de coastdown detectados - intervalos de alta e baixa velocidade estao sendo processados separadamente.",
        "en": "Split input mode: 2 coastdown files detected - high-speed and low-speed intervals are being processed separately."
    },
    "split_input_mode_two_files_high_only": {
        "pt": "Modo de entrada Split: 2 arquivos de coastdown detectados - intervalo de alta velocidade encontrado, mas nenhum intervalo de baixa velocidade foi detectado.",
        "en": "Split input mode: 2 coastdown files detected - high-speed interval found, but no low-speed interval was detected."
    },
    "split_input_mode_two_files_low_only": {
        "pt": "Modo de entrada Split: 2 arquivos de coastdown detectados - intervalo de baixa velocidade encontrado, mas nenhum intervalo de alta velocidade foi detectado.",
        "en": "Split input mode: 2 coastdown files detected - low-speed interval found, but no high-speed interval was detected."
    },
    "split_input_mode_two_files_none": {
        "pt": "Modo de entrada Split: 2 arquivos de coastdown detectados - nenhum intervalo de alta ou baixa velocidade foi detectado.",
        "en": "Split input mode: 2 coastdown files detected - no high-speed or low-speed interval was detected."
    },
    "split_input_mode_one_file_complete": {
        "pt": "Modo de entrada Split: 1 arquivo de coastdown detectado - intervalos de alta e baixa velocidade foram extraidos do mesmo arquivo.",
        "en": "Split input mode: 1 coastdown file detected - high-speed and low-speed intervals were extracted from the same file."
    },
    "split_input_mode_one_file_high_only": {
        "pt": "Modo de entrada Split: 1 arquivo de coastdown detectado - intervalo de alta velocidade encontrado, mas nenhum intervalo de baixa velocidade foi detectado.",
        "en": "Split input mode: 1 coastdown file detected - high-speed interval found, but no low-speed interval was detected."
    },
    "split_input_mode_one_file_low_only": {
        "pt": "Modo de entrada Split: 1 arquivo de coastdown detectado - intervalo de baixa velocidade encontrado, mas nenhum intervalo de alta velocidade foi detectado.",
        "en": "Split input mode: 1 coastdown file detected - low-speed interval found, but no high-speed interval was detected."
    },
    "split_input_mode_one_file_none": {
        "pt": "Modo de entrada Split: 1 arquivo de coastdown detectado - nenhum intervalo de alta ou baixa velocidade foi detectado.",
        "en": "Split input mode: 1 coastdown file detected - no high-speed or low-speed interval was detected."
    },
    "split_confirm_vehicle_data": {
        "pt": "Confirmar dados do veiculo para Split",
        "en": "Confirm vehicle data for Split"
    },
    "split_vehicle_data_ready": {
        "pt": "Dados do veiculo prontos para o workflow Split.",
        "en": "Vehicle data is ready for the Split workflow."
    },
    "split_vehicle_data_required": {
        "pt": "Confirme os dados do veiculo e a massa efetiva antes do workflow Split.",
        "en": "Confirm vehicle data and effective mass before the Split workflow."
    },
    "split_saved_results": {
        "pt": "resultado(s) Split salvo(s)",
        "en": "saved Split result(s)"
    },
    "split_final_summary": {
        "pt": "resultado(s) no resumo Split",
        "en": "result(s) in Split summary"
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
    "split_final_comparison_tab_table": {"pt": "Tabela", "en": "Table"},
    "split_final_comparison_tab_deviation": {"pt": "Análise de desvios", "en": "Deviation analysis"},
    "split_final_comparison_section": {"pt": "Seção do Comparativo Final", "en": "Final Comparison section"},
    "split_deviation_select_pairs_hint": {"pt": "Selecione pares na aba Tabela para visualizar a análise de desvios.", "en": "Select pairs in the Table tab to view the deviation analysis."},
    "split_deviation_selected_count": {"pt": "Pares selecionados", "en": "Selected pairs"},
    "split_deviation_coefficients_status": {"pt": "Status coeficientes", "en": "Coefficient status"},
    "split_deviation_times_status": {"pt": "Status tempos", "en": "Time status"},
    "split_deviation_weather_status": {"pt": "Status meteorológico", "en": "Weather status"},
    "split_deviation_status_approved": {"pt": "aprovado", "en": "approved"},
    "split_deviation_status_warning": {"pt": "atenção", "en": "warning"},
    "split_deviation_status_failed": {"pt": "fora do limite", "en": "outside limit"},
    "split_deviation_status_insufficient_data": {"pt": "inconclusivo", "en": "inconclusive"},
    "split_deviation_coefficients_title": {"pt": "Coeficientes F0/F2", "en": "F0/F2 coefficients"},
    "split_deviation_coefficient": {"pt": "Coeficiente", "en": "Coefficient"},
    "split_deviation_mean": {"pt": "Média", "en": "Mean"},
    "split_deviation_sample_stdev": {"pt": "Desvio padrão amostral", "en": "Sample standard deviation"},
    "split_deviation_limit": {"pt": "Limite [%]", "en": "Limit [%]"},
    "split_deviation_status": {"pt": "Status", "en": "Status"},
    "split_deviation_times_title": {"pt": "Validação normativa dos tempos Δt", "en": "Normative validation of Δt times"},
    "split_deviation_group": {"pt": "Verificação", "en": "Check"},
    "split_deviation_mean_time": {"pt": "Média Δt [s]", "en": "Mean Δt [s]"},
    "split_deviation_speed": {"pt": "Velocidade de referência", "en": "Reference speed"},
    "split_deviation_mean_plus": {"pt": "Média Δt [+] [s]", "en": "Mean Δt [+] [s]"},
    "split_deviation_mean_minus": {"pt": "Média Δt [-] [s]", "en": "Mean Δt [-] [s]"},
    "split_deviation_difference_pct": {"pt": "Diferença entre médias [%]", "en": "Difference between means [%]"},
    "split_deviation_pairs_title": {"pt": "Desvios por par", "en": "Pair deviations"},
    "split_deviation_f0_abs": {"pt": "Desvio F0 absoluto", "en": "Absolute F0 deviation"},
    "split_deviation_f0_pct": {"pt": "Desvio F0 [%]", "en": "F0 deviation [%]"},
    "split_deviation_f2_abs": {"pt": "Desvio F2 absoluto", "en": "Absolute F2 deviation"},
    "split_deviation_f2_pct": {"pt": "Desvio F2 [%]", "en": "F2 deviation [%]"},
    "split_deviation_alert": {"pt": "Alertas", "en": "Alerts"},
    "split_deviation_weather_title": {"pt": "Condições meteorológicas", "en": "Weather conditions"},
    "split_deviation_weather_note": {"pt": "Os alertas meteorológicos são diagnósticos. Verifique os limites normativos aplicáveis e os dados originais do ensaio.", "en": "Weather alerts are diagnostic. Check the applicable normative limits and the original test data."},
    "split_deviation_leave_one_out_title": {"pt": "Impacto de remoção de pares", "en": "Pair-removal impact"},
    "split_deviation_leave_one_out_minimum": {"pt": "Análise leave-one-out requer pelo menos 3 pares selecionados.", "en": "Leave-one-out analysis requires at least 3 selected pairs."},
    "split_deviation_remove_pair": {"pt": "Remover par", "en": "Remove pair"},
    "split_deviation_interpretation": {"pt": "Interpretação", "en": "Interpretation"},
    "split_deviation_best_f0": {"pt": "Maior melhoria de CV F0", "en": "Largest F0 CV improvement"},
    "split_deviation_best_f2": {"pt": "Maior melhoria de CV F2", "en": "Largest F2 CV improvement"},
    "split_deviation_diagnostic_only": {"pt": "Variação diagnóstica", "en": "Diagnostic variation"},
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
