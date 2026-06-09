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
    "page_split_coefficient_calculation": {
        "pt": "Cálculo dos Coeficientes",
        "en": "Coefficient Calculation"
    },
    "page_split_results": {
        "pt": "Resultados Split",
        "en": "Split Results"
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
    "split_comparison_empty": {
        "pt": "Nenhum par foi adicionado à tabela comparativa final.",
        "en": "No pair has been added to the final comparison table."
    },
    "split_clear_final_comparison": {
        "pt": "Limpar tabela comparativa",
        "en": "Clear comparison table"
    },
    "split_comparison_pair_cards": {
        "pt": "Cards dos pares adicionados",
        "en": "Added pair cards"
    },
    "split_remove_pair": {
        "pt": "Remover par",
        "en": "Remove pair"
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
        "pt": "Não calculada: falta uma função Split neutra com F0/F2 corrigidos, massa e ciclo/perfil explícitos.",
        "en": "Not calculated: no neutral Split function has an explicit corrected F0/F2, mass and cycle/profile contract."
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
