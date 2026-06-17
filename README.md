# CO2 Adsorb: ML and LLM Comparison

This project is a runnable teaching version based on `zenonLEE/co2adsorb` and inspired by the 2025 Energy and AI paper:

> Methodology for predicting material performance by context-based modeling: A case study on solid amine CO2 adsorbents.

It compares five prediction methods for solid amine CO2 adsorption uptake:

- LR: Linear Regression
- RF: Random Forest
- XGBoost
- MLP: Multi-layer Perceptron
- LLM: prompt-based in-context prediction through Codex CLI, with a deterministic fallback

## Quick Start in VSCode

Open this folder in VSCode:

```powershell
E:\LLM2025\co2adsorb
```

Then open `run_experiment.py` and click Run.

The default run uses the deterministic LLM fallback so the whole project can run even when the Codex CLI is not available inside the Python process.

## Quick Start in Terminal

```powershell
cd E:\LLM2025\co2adsorb
E:\LLM2025\.venv\Scripts\python.exe .\run_experiment.py --llm-mode fallback
```

To try the local Codex CLI for the LLM part:

```powershell
E:\LLM2025\.venv\Scripts\python.exe .\run_experiment.py --llm-mode codex
```

If the Codex CLI call fails or its response cannot be parsed, the program records the error and automatically uses the fallback context model for that sample.

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

## Environment

The current workspace already has the required environment at:

```powershell
E:\LLM2025\.venv
```

To recreate the environment elsewhere:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Why `__pycache__` Is Not Included

`__pycache__` is generated automatically by Python. It stores bytecode cache files and is not source code or experiment output. This project excludes it through `.gitignore`.

## Important Limitation

The original repository contains only a small 19-row example dataset. The code is suitable for learning, method reproduction, and classroom demonstration, but the numeric results should not be treated as a full reproduction of the paper.
