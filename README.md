# CO2 Adsorb: ML and LLM Comparison

This project is a runnable teaching version based on `zenonLEE/co2adsorb` and inspired by the 2025 Energy and AI paper:

> Methodology for predicting material performance by context-based modeling: A case study on solid amine CO2 adsorbents.

It compares five prediction methods for solid amine CO2 adsorption uptake:

- LR: Linear Regression
- RF: Random Forest
- XGBoost
- MLP: Multi-layer Perceptron
- LLM: prompt-based in-context prediction through Codex CLI, with a deterministic fallback

## Outputs

All results are saved under `outputs/`:

- `model_metrics.csv`: MAE, MSE, RMSE, R2, Pearson correlation for LR/RF/XGBoost/MLP/LLM
- `predictions.csv`: measured and predicted value for every sample
- `fig3_model_metrics.png`: Fig. 3-style bar chart of evaluation metrics
- `prediction_comparison.png`: measured vs predicted scatter plot
- `shap_summary.png`: XGBoost SHAP feature-importance summary
- `co2adsorb_running_logic_and_teaching.html`: Chinese teaching document with running logic and explanations
- `llm/llm_prompt_*.txt`: prompt sent to the LLM for each leave-one-out test
- `llm/llm_response_*.txt`: raw Codex CLI response or fallback note
