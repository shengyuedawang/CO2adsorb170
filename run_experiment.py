from __future__ import annotations

import argparse #解析命令行参数
import json
import math
import re
import shlex
import subprocess
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    import shap
    import xgboost as xgb
except ImportError:
    shap = None
    xgb = None


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "supplementary_co2_adsorbents.csv"
TARGET = "co2_adsorbed_amount"
ID_COLUMNS = ["sample_id", "reference"]
CATEGORICAL_FEATURES = ["amine_type"]
RANDOM_STATE = 42
TEST_SIZE = 0.3

SHAP_ABBREVIATIONS = {
    "surface_area_before": "SSABD",
    "surface_area_after": "SSAAD",
    "pore_volume_before": "PVBD",
    "pore_volume_after": "PVAD",
    "amine_loading": "LA",
    "temperature": "Temp",
    "co2_partial_pressure": "PPCO2",
    "relative_humidity": "RH",
    "molecular_weight": "MW",
    "nitrogen_atom_content": "NAC",
    "primary_amine_proportion": "PA",
    "secondary_amine_proportion": "SA",
    "tertiary_amine_proportion": "TA",
    "surface_area_loss": "SAP",
    "pore_volume_loss": "PAP",
    "loaded_nitrogen": "TAP",
    "primary_loaded_nitrogen": "PAPN",
    "secondary_loaded_nitrogen": "SAPN",
    "tertiary_loaded_nitrogen": "TAPN",
    "surface_area_retention": "SSAR",
    "pore_volume_retention": "PVR",
    "film_thickness_proxy": "FTP",
    "pressure_temperature_ratio": "PTR",
}


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {TARGET, "amine_type", "amine_loading", "surface_area_before", "surface_area_after"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["surface_area_loss"] = data["surface_area_before"] - data["surface_area_after"]
    data["pore_volume_loss"] = data["pore_volume_before"] - data["pore_volume_after"]
    data["surface_area_retention"] = data["surface_area_after"] / data["surface_area_before"]
    data["pore_volume_retention"] = data["pore_volume_after"] / data["pore_volume_before"]
    data["film_thickness_proxy"] = data["pore_volume_loss"] / (data["surface_area_loss"].abs() + 1e-6)
    data["loaded_nitrogen"] = data["amine_loading"] * data["nitrogen_atom_content"]
    data["primary_loaded_nitrogen"] = data["loaded_nitrogen"] * data["primary_amine_proportion"]
    data["secondary_loaded_nitrogen"] = data["loaded_nitrogen"] * data["secondary_amine_proportion"]
    data["tertiary_loaded_nitrogen"] = data["loaded_nitrogen"] * data["tertiary_amine_proportion"]
    data["pressure_temperature_ratio"] = data["co2_partial_pressure"] / (data["temperature"] + 273.15)
    return data


def split_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    features = df.drop(columns=[TARGET, *ID_COLUMNS], errors="ignore")
    target = df[TARGET]
    return features, target


def split_train_test(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_df, test_df = train_test_split(
        df,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        shuffle=True,
    )
    return train_df.sort_index().copy(), test_df.sort_index().copy()


def make_one_hot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def abbreviate_shap_feature(name: str) -> str:
    clean = name.replace("numeric__", "").replace("categorical__", "")
    if clean.startswith("amine_type_"):
        return f"AT-{clean.removeprefix('amine_type_')}"
    return SHAP_ABBREVIATIONS.get(clean, clean)

#预处理
def make_preprocessor(x_frame: pd.DataFrame) -> ColumnTransformer:
    numeric_features = [column for column in x_frame.columns if column not in CATEGORICAL_FEATURES]
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", make_one_hot_encoder()),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric, numeric_features),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ]
    )


def build_models(x_frame: pd.DataFrame) -> dict[str, Pipeline]:
    def pipeline(model) -> Pipeline:
        return Pipeline(
            steps=[
                ("preprocess", make_preprocessor(x_frame)),
                ("model", model),
            ]
        )

    models = {
        "LR": pipeline(LinearRegression()),
        "RF": pipeline(
            RandomForestRegressor(
                n_estimators=600,
                max_depth=4,
                min_samples_leaf=1,
                random_state=RANDOM_STATE,
                n_jobs=-1,
            )
        ),
        "MLP": pipeline(
            MLPRegressor(
                hidden_layer_sizes=(16, 8),
                activation="relu",
                alpha=0.02,
                learning_rate_init=0.01,
                max_iter=5000,
                early_stopping=False,
                random_state=RANDOM_STATE,
            )
        ),
    }
    if xgb is not None:
        models["XGBoost"] = pipeline(
            xgb.XGBRegressor(
                objective="reg:squarederror",
                n_estimators=120,
                max_depth=2,
                learning_rate=0.05,
                subsample=0.9,
                colsample_bytree=0.9,
                reg_lambda=1.0,
                random_state=RANDOM_STATE,
                n_jobs=1,
            )
        )
    else:
        models["XGBoost"] = pipeline(
            RandomForestRegressor(
                n_estimators=300,
                max_depth=2,
                min_samples_leaf=2,
                random_state=RANDOM_STATE,
                n_jobs=-1,
            )
        )
    return {name: models[name] for name in ["LR", "RF", "XGBoost", "MLP"]}


def regression_metrics(y_true: Iterable[float], y_pred: Iterable[float]) -> dict[str, float]:
    actual = np.asarray(list(y_true), dtype=float)
    predicted = np.asarray(list(y_pred), dtype=float)
    if len(actual) < 2 or np.std(predicted) == 0 or np.std(actual) == 0:
        pearson = np.nan
    else:
        pearson = float(np.corrcoef(actual, predicted)[0, 1])
    return {
        "MAE": float(mean_absolute_error(actual, predicted)),
        "MSE": float(mean_squared_error(actual, predicted)),
        "RMSE": float(mean_squared_error(actual, predicted, squared=False)),
        "R2": float(r2_score(actual, predicted)),
        "Pearson_r": pearson,
    }


def evaluate_ml_models(train_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    x_train, y_train = split_xy(train_df)
    x_test, y_test = split_xy(test_df)
    predictions = pd.DataFrame({"sample_id": test_df["sample_id"], "Measured": y_test})
    rows = []
    for name, model in build_models(x_train).items():
        model.fit(x_train, y_train)
        predicted = model.predict(x_test)
        predictions[name] = predicted
        rows.append({"Model": name, **regression_metrics(y_test, predicted)})
    return pd.DataFrame(rows), predictions


def feature_text(row: pd.Series, include_target: bool = False) -> str:
    fields = [
        ("support surface area before amine dispersing", "surface_area_before", "m2/g"),
        ("support surface area after amine dispersing", "surface_area_after", "m2/g"),
        ("pore volume before amine dispersing", "pore_volume_before", "cm3/g"),
        ("pore volume after amine dispersing", "pore_volume_after", "cm3/g"),
        ("amine type", "amine_type", ""),
        ("amine molecular weight", "molecular_weight", "g/mol"),
        ("nitrogen atom content", "nitrogen_atom_content", "mass fraction"),
        ("primary amine proportion", "primary_amine_proportion", "fraction"),
        ("secondary amine proportion", "secondary_amine_proportion", "fraction"),
        ("tertiary amine proportion", "tertiary_amine_proportion", "fraction"),
        ("amine loading", "amine_loading", "g/g support"),
        ("temperature", "temperature", "deg C"),
        ("CO2 partial pressure", "co2_partial_pressure", "ppm"),
        ("relative humidity", "relative_humidity", "%"),
    ]
    chunks = []
    for label, column, unit in fields:
        value = row[column]
        chunks.append(f"{label}: {value} {unit}".strip())
    if include_target:
        chunks.append(f"CO2 adsorbed amount: {row[TARGET]} mmol/g")
    return "; ".join(chunks)


def build_llm_prompt(train_df: pd.DataFrame, test_df: pd.DataFrame) -> str:
    lines = [
        "You are predicting CO2 adsorption uptake for solid amine adsorbents.",
        "Use in-context learning from the numbered examples. Consider pore blocking, amine loading, accessible nitrogen, pressure, temperature, and amine chemistry.",
        "Return only valid JSON in this form: {\"predictions\":[{\"sample_id\":\"S01\",\"co2_adsorbed_amount\":1.23}]}",
        "",
        "Training examples:",
    ]
#训练集，输入包含目标值，输出让模型学习
    for _, row in train_df.iterrows():
        lines.append(f"- {row['sample_id']}: {feature_text(row, include_target=True)}")
    lines.append("")
    lines.append("Test samples:")
#测试集，输入不包含目标值，输出留空让模型预测
    for _, row in test_df.iterrows():
        lines.append(f"- {row['sample_id']}: {feature_text(row, include_target=False)}; CO2 adsorbed amount: ?")
    return "\n".join(lines)


def parse_llm_predictions(text: str, sample_ids: list[str]) -> dict[str, float]:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            parsed = {}
            for item in data.get("predictions", []):
                sample_id = str(item.get("sample_id", "")).strip()
                value = float(item.get("co2_adsorbed_amount"))
                if sample_id in sample_ids and math.isfinite(value):
                    parsed[sample_id] = value
            if parsed:
                return parsed
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    numbers = [float(value) for value in re.findall(r"[-+]?\d+(?:\.\d+)?", text)]
    return {sample_id: value for sample_id, value in zip(sample_ids, numbers)}


def run_codex_cli(prompt: str, command: str, timeout: int) -> str:
    args = shlex.split(command, posix=False)
    completed = subprocess.run(
        args,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "Codex CLI returned a non-zero exit code").strip())
    return completed.stdout.strip()


def context_fallback_prediction(train_df: pd.DataFrame, test_row: pd.Series) -> float:
    numeric_columns = [
        column
        for column in train_df.columns
        if column not in [TARGET, *ID_COLUMNS, "amine_type"] and pd.api.types.is_numeric_dtype(train_df[column])
    ]
    x_train = train_df[numeric_columns].to_numpy(dtype=float)
    x_test = test_row[numeric_columns].to_numpy(dtype=float).reshape(1, -1)
    scale = np.nanstd(x_train, axis=0)
    scale[scale == 0] = 1.0
    distances = np.sqrt(np.sum(((x_train - x_test) / scale) ** 2, axis=1))
    same_amine = (train_df["amine_type"].to_numpy() == test_row["amine_type"]).astype(float)
    distances = distances - 0.75 * same_amine
    nearest = np.argsort(distances)[: min(5, len(train_df))]
    weights = 1.0 / (np.maximum(distances[nearest], 0.01) + 0.25)
    value = np.average(train_df.iloc[nearest][TARGET].to_numpy(dtype=float), weights=weights)
    return float(max(0.0, value))

def evaluate_llm(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_dir: Path,
    mode: str,
    codex_command: str,
    timeout: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    predictions = []
    raw_rows = []
    for _, test_row in test_df.iterrows():
        test_one = test_row.to_frame().T
        sample_id = str(test_row["sample_id"])
        prompt = build_llm_prompt(train_df, test_one)
        prompt_path = output_dir / f"llm_prompt_{sample_id}.txt"
        prompt_path.write_text(prompt, encoding="utf-8")

        source = "fallback_context_model"
        response = ""
        value = context_fallback_prediction(train_df, test_row)
        if mode == "codex":
            try:
                response = run_codex_cli(prompt, codex_command, timeout)
                parsed = parse_llm_predictions(response, [sample_id])
                if sample_id in parsed:
                    value = parsed[sample_id]
                    source = "codex_cli"
                else:
                    source = "codex_cli_unparsed_fallback"
            except Exception as exc:
                response = f"Codex CLI failed; fallback used. Error: {exc}"
                source = "codex_cli_failed_fallback"
        response_path = output_dir / f"llm_response_{sample_id}.txt"
        response_path.write_text(response or "Fallback context model used without CLI call.", encoding="utf-8")
        predictions.append(value)
        raw_rows.append({"sample_id": sample_id, "LLM": value, "llm_source": source})

    pred_df = pd.DataFrame(raw_rows)
    metrics = pd.DataFrame([{"Model": "LLM", **regression_metrics(test_df[TARGET], predictions)}])
    return metrics, pred_df


def plot_metric_bars(metrics: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ordered = metrics.set_index("Model").loc[["LR", "RF", "XGBoost", "MLP", "LLM"]].reset_index()
    specs = [
        ("MAE", "Mean absolute error"),
        ("MSE", "Mean squared error"),
        ("R2", "R-squared"),
        ("Pearson_r", "Pearson correlation"),
    ]
    colors = ["#4C78A8", "#F58518", "#54A24B", "#B279A2", "#E45756"]
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    for ax, (metric, title) in zip(axes.flat, specs):
        values = ordered[metric].to_numpy(dtype=float)
        bars = ax.bar(ordered["Model"], values, color=colors, edgecolor="#333333", linewidth=0.5)
        ax.set_title(title)
        ax.set_ylabel(metric)
        ax.axhline(0, color="#333333", linewidth=0.8)
        for bar, value in zip(bars, values):
            label_y = value + 0.03 * (np.nanmax(np.abs(values)) + 1e-6)
            va = "bottom"
            if value < 0:
                label_y = value - 0.03 * (np.nanmax(np.abs(values)) + 1e-6)
                va = "top"
            ax.text(bar.get_x() + bar.get_width() / 2, label_y, f"{value:.2f}", ha="center", va=va, fontsize=9)
        ax.tick_params(axis="x", rotation=0)
    fig.suptitle("Fig. 3-style comparison of evaluation metrics for ML and LLM models", fontsize=14)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def plot_predictions(predictions: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    model_columns = ["LR", "RF", "XGBoost", "MLP", "LLM"]
    measured = predictions["Measured"].to_numpy(dtype=float)
    upper = max(predictions[model_columns + ["Measured"]].max().max(), 1.0) * 1.08
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    for column in model_columns:
        ax.scatter(measured, predictions[column], label=column, alpha=0.82, s=52)
    ax.plot([0, upper], [0, upper], linestyle="--", color="#333333", linewidth=1.2, label="perfect")
    ax.set_xlabel("Measured CO2 uptake (mmol/g)")
    ax.set_ylabel("70/30 test-set prediction (mmol/g)")
    ax.set_xlim(0, upper)
    ax.set_ylim(0, upper)
    ax.legend(ncol=2)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def save_shap_summary(df: pd.DataFrame, output_path: Path) -> str:
    if shap is None or xgb is None:
        return "Skipped because shap or xgboost is not installed."
    x_frame, y = split_xy(df)
    preprocessor = make_preprocessor(x_frame)
    transformed = preprocessor.fit_transform(x_frame)
    feature_names = [abbreviate_shap_feature(name) for name in preprocessor.get_feature_names_out()]
    model = xgb.XGBRegressor(
        objective="reg:squarederror",
        n_estimators=120,
        max_depth=2,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    model.fit(transformed, y)
    explanation = shap.TreeExplainer(model)(transformed)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shap.summary_plot(
        explanation.values,
        transformed,
        feature_names=feature_names,
        max_display=12,
        plot_size=(5.2, 4.4),
        show=False,
    )
    plt.xlabel("SHAP Value")
    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close()
    return "Saved."


def dataframe_to_html_table(df: pd.DataFrame, float_format: str = "{:.4f}") -> str:
    display = df.copy()
    for column in display.select_dtypes(include=[np.number]).columns:
        display[column] = display[column].map(lambda value: float_format.format(value))
    return display.to_html(index=False, classes="data-table", border=0)


def write_learning_html(metrics: pd.DataFrame, output_dir: Path, llm_sources: pd.DataFrame) -> Path:
    html_path = output_dir / "co2adsorb_running_logic_and_teaching.html"
    source_counts = llm_sources["llm_source"].value_counts().rename_axis("Source").reset_index(name="Count")
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CO2 Adsorb ML + LLM 运行逻辑与教学解释</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", Arial, sans-serif; margin: 0; color: #20242a; background: #f6f7f9; line-height: 1.65; }}
    header {{ background: #14324a; color: white; padding: 36px 7vw 28px; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 28px 20px 56px; }}
    section {{ background: white; border: 1px solid #d9dde3; border-radius: 8px; padding: 22px 24px; margin: 18px 0; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; }}
    h2 {{ margin-top: 0; color: #14324a; }}
    h3 {{ margin-bottom: 6px; }}
    code, pre {{ font-family: Consolas, "Courier New", monospace; }}
    pre {{ background: #101820; color: #e7edf4; padding: 14px; border-radius: 6px; overflow-x: auto; }}
    .data-table {{ border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 14px; }}
    .data-table th, .data-table td {{ border: 1px solid #d8dde6; padding: 8px 10px; text-align: left; }}
    .data-table th {{ background: #edf2f7; }}
    img {{ max-width: 100%; border: 1px solid #d8dde6; border-radius: 6px; background: white; }}
    .note {{ background: #fff8e6; border-left: 4px solid #d79b00; padding: 10px 12px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }}
  </style>
</head>
<body>
<header>
  <h1>CO2 固体胺吸附量预测：LR / RF / XGBoost / MLP / LLM 对比</h1>
  <p>基于 zenonLEE/co2adsorb 的示例数据，仿照 Energy and AI 2025 论文 Fig. 3 的评估思路，形成可运行的本地实验流程。</p>
</header>
<main>
  <section>
    <h2>1. 代码库怎么运行</h2>
    <p>在 VSCode 中打开 <code>E:\\LLM2025\\co2adsorb</code> 文件夹，打开 <code>run_experiment.py</code>，点击右上角运行即可。也可以在终端运行：</p>
    <pre>E:\\LLM2025\\.venv\\Scripts\\python.exe run_experiment.py --llm-mode fallback</pre>
    <p>如果要尝试真实调用本地 Codex CLI：</p>
    <pre>E:\\LLM2025\\.venv\\Scripts\\python.exe run_experiment.py --llm-mode codex</pre>
    <p class="note">如果 Codex CLI 无法在当前环境中执行，程序不会中断，会自动切换到可复现的上下文近邻回退模型，并在每个 <code>llm_response_*.txt</code> 中记录原因。</p>
  </section>

  <section>
    <h2>2. 运行逻辑流程</h2>
    <ol>
      <li>读取 <code>data/supplementary_co2_adsorbents.csv</code> 中从论文支撑材料 Table S1-1 抽取的 170 条固体胺 CO2 吸附样本。</li>
      <li>构造材料学特征：比表面积损失、孔体积损失、孔保留率、胺负载后的氮含量、伯/仲/叔胺有效氮等。</li>
      <li>把数值特征做缺失值填补和标准化，把 <code>amine_type</code> 做 One-Hot 编码。</li>
      <li>按照论文思路使用 70%/30% train-test split：119 条训练、51 条测试，不再使用留一法。</li>
      <li>训练并比较 LR、RF、XGBoost、MLP 四个传统机器学习回归模型。</li>
      <li>为 LLM 构造 in-context prompt：119 条带答案的训练例子 + 1 条待预测样本。真实 Codex CLI 可选调用；失败时使用上下文近邻回退。</li>
      <li>计算 MAE、MSE、RMSE、R2 和 Pearson 相关系数，并保存 Fig. 3 风格柱状图。</li>
      <li>用 XGBoost 在全数据上拟合一个解释模型，输出 SHAP summary plot 用于理解特征重要性。</li>
    </ol>
  </section>

  <section>
    <h2>3. 当前评估结果</h2>
    {dataframe_to_html_table(metrics)}
    <h3>LLM 来源统计</h3>
    {dataframe_to_html_table(source_counts, "{:.0f}")}
  </section>

  <section>
    <h2>4. 输出文件</h2>
    <div class="grid">
      <div><h3>模型指标</h3><p><code>outputs/model_metrics.csv</code></p></div>
      <div><h3>逐样本预测</h3><p><code>outputs/predictions.csv</code></p></div>
      <div><h3>Fig. 3 风格图</h3><p><code>outputs/fig3_model_metrics.png</code></p></div>
      <div><h3>预测散点图</h3><p><code>outputs/prediction_comparison.png</code></p></div>
      <div><h3>SHAP 图</h3><p><code>outputs/shap_summary.png</code></p></div>
      <div><h3>LLM Prompt</h3><p><code>outputs/llm/llm_prompt_*.txt</code> 等</p></div>
    </div>
  </section>

  <section>
    <h2>5. Fig. 3 风格结果图</h2>
    <img src="fig3_model_metrics.png" alt="Fig. 3 style model metrics">
  </section>

  <section>
    <h2>6. 预测值与真实值</h2>
    <img src="prediction_comparison.png" alt="Prediction comparison">
  </section>

  <section>
    <h2>7. SHAP 教学解释</h2>
    <p>SHAP 图解释的是 XGBoost 模型在当前 170 条支撑材料数据上如何使用特征。横轴越远离 0，说明该特征对预测的推动越强；颜色表示特征值大小。注意这仍然不是严格因果结论，而是当前数据和当前模型下的解释。</p>
    <img src="shap_summary.png" alt="SHAP summary">
  </section>

  <section>
    <h2>8. 五类模型怎么理解</h2>
    <p><strong>LR</strong> 是线性回归，假设吸附量可以由特征线性相加得到，优点是简单可解释，缺点是难表达非线性。</p>
    <p><strong>RF</strong> 是随机森林，用多棵决策树平均预测，能处理非线性和特征交互，小数据上相对稳健。</p>
    <p><strong>XGBoost</strong> 是梯度提升树，逐步修正前一轮模型误差，常用于表格数据，论文类实验中很常见。</p>
    <p><strong>MLP</strong> 是多层感知机神经网络，理论表达能力强，但在 170 条表格数据上仍然需要注意随机性和过拟合。</p>
    <p><strong>LLM</strong> 不是重新训练权重，而是把材料背景、训练例子和待预测样本写进 prompt，让模型做 in-context learning。这里保留了本地 Codex CLI 调用接口。</p>
  </section>

  <section>
    <h2>9. 为什么不需要 __pycache__</h2>
    <p><code>__pycache__</code> 是 Python 自动生成的字节码缓存，只是为了加快下次导入速度，不是源码，也不是实验结果。它不需要提交或交给老师，因此本项目的 <code>.gitignore</code> 已经排除了它。</p>
  </section>

  <section>
    <h2>10. 论文对应关系</h2>
    <p>参考论文：Shuangjun Li 等，<em>Methodology for predicting material performance by context-based modeling: A case study on solid amine CO2 adsorbents</em>，Energy and AI, Volume 20, May 2025, Article 100477, DOI: 10.1016/j.egyai.2025.100477。</p>
    <p>本代码使用论文支撑材料 Table S1-1 抽取出的 170 条样本，复现论文思想：用传统 ML 与 LLM 上下文建模比较 CO2 吸附量预测误差，并用 SHAP 分析特征贡献。由于模型参数、随机划分和 LLM 调用环境仍可能与论文不同，结果应视为接近论文流程的本地复现实验。</p>
  </section>
</main>
</body>
</html>
"""
    html_path.write_text(html, encoding="utf-8")
    return html_path


def run(args: argparse.Namespace) -> None:
    output_dir = args.output_dir.resolve()
    raw_df = load_data(args.data)
    raw_columns = list(raw_df.columns)
    df = add_engineered_features(raw_df)
    train_df, test_df = split_train_test(df)
    ml_metrics, predictions = evaluate_ml_models(train_df, test_df)
    llm_metrics, llm_predictions = evaluate_llm(
        train_df=train_df,
        test_df=test_df,
        output_dir=output_dir / "llm",
        mode=args.llm_mode,
        codex_command=args.codex_command,
        timeout=args.codex_timeout,
    )
    predictions = predictions.merge(llm_predictions, on="sample_id", how="left")
    metrics = pd.concat([ml_metrics, llm_metrics], ignore_index=True)
    metrics = metrics[["Model", "MAE", "MSE", "RMSE", "R2", "Pearson_r"]]

    output_dir.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(output_dir / "model_metrics.csv", index=False, encoding="utf-8-sig")
    predictions.to_csv(output_dir / "predictions.csv", index=False, encoding="utf-8-sig")
    train_df[raw_columns].to_csv(output_dir / "train_split.csv", index=False, encoding="utf-8-sig")
    test_df[raw_columns].to_csv(output_dir / "test_split.csv", index=False, encoding="utf-8-sig")
    plot_metric_bars(metrics, output_dir / "fig3_model_metrics.png")
    plot_predictions(predictions, output_dir / "prediction_comparison.png")
    shap_status = save_shap_summary(df, output_dir / "shap_summary.png")
    html_path = write_learning_html(metrics, output_dir, llm_predictions)

    print("\nModel metrics")
    print(metrics.to_string(index=False))
    print(f"\nSaved metrics: {output_dir / 'model_metrics.csv'}")
    print(f"Saved predictions: {output_dir / 'predictions.csv'}")
    print(f"Saved Fig. 3-style chart: {output_dir / 'fig3_model_metrics.png'}")
    print(f"Saved prediction chart: {output_dir / 'prediction_comparison.png'}")
    print(f"SHAP: {shap_status} {output_dir / 'shap_summary.png'}")
    print(f"Teaching HTML: {html_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare LR, RF, XGBoost, MLP, and LLM for CO2 adsorption prediction.")
    parser.add_argument("--data", type=Path, default=DATA_PATH, help="CSV data path.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs", help="Directory for results.")
    parser.add_argument(
        "--llm-mode",
        choices=["fallback", "codex"],
        default="fallback",
        help="fallback is deterministic and always runnable; codex tries the local Codex CLI and falls back if needed.",
    )
    parser.add_argument(
        "--codex-command",
        default="codex.cmd exec --skip-git-repo-check",
        help="Command used when --llm-mode codex. The prompt is sent through stdin.",
    )
    parser.add_argument("--codex-timeout", type=int, default=90, help="Timeout in seconds for each Codex CLI call.")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
