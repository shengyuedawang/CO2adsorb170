from __future__ import annotations

import html
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs"
HTML_PATH = OUTPUT_DIR / "co2adsorb_code_theory_running_guide.html"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def code_block(path: Path) -> str:
    text = html.escape(read_text(path))
    name = html.escape(path.name)
    return f"""
<details class="source-block">
  <summary>展开查看完整源码：{name}</summary>
  <pre><code>{text}</code></pre>
</details>
"""


def table_from_csv(path: Path, max_rows: int | None = None) -> str:
    df = pd.read_csv(path)
    if max_rows is not None:
        df = df.head(max_rows)
    return df.to_html(index=False, classes="data-table", border=0)


def write_html() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics_table = table_from_csv(OUTPUT_DIR / "model_metrics.csv")
    data_table = table_from_csv(ROOT / "data" / "co2_adsorbents.csv", max_rows=8)

    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>co2adsorb 学习版完整代码、配置、理论与运行流程说明</title>
  <style>
    :root {{
      --ink: #1f2933;
      --muted: #5f6b7a;
      --line: #d7dde6;
      --paper: #ffffff;
      --bg: #f4f6f8;
      --brand: #17415f;
      --brand-2: #2f6f73;
      --accent: #bd6b1f;
      --code: #101820;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
      color: var(--ink);
      background: var(--bg);
      line-height: 1.72;
    }}
    header {{
      padding: 36px 7vw 30px;
      background: linear-gradient(120deg, var(--brand), var(--brand-2));
      color: #fff;
    }}
    header h1 {{ margin: 0 0 10px; font-size: 30px; letter-spacing: 0; }}
    header p {{ margin: 0; max-width: 980px; color: #e8f2f2; }}
    nav {{
      position: sticky;
      top: 0;
      z-index: 2;
      background: #ffffff;
      border-bottom: 1px solid var(--line);
      padding: 10px 7vw;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    nav a {{
      color: var(--brand);
      text-decoration: none;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 5px 9px;
      font-size: 14px;
      background: #fff;
    }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 24px 20px 64px; }}
    section {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 22px 24px;
      margin: 18px 0;
    }}
    h2 {{ margin: 0 0 12px; color: var(--brand); font-size: 24px; }}
    h3 {{ margin: 20px 0 8px; font-size: 18px; color: #243b53; }}
    h4 {{ margin: 16px 0 6px; font-size: 16px; color: #334e68; }}
    p {{ margin: 8px 0; }}
    ul, ol {{ padding-left: 24px; }}
    li {{ margin: 5px 0; }}
    code, pre {{ font-family: Consolas, "Courier New", monospace; }}
    code {{ background: #edf2f7; padding: 1px 5px; border-radius: 4px; }}
    pre {{
      background: var(--code);
      color: #e8edf3;
      padding: 14px;
      border-radius: 7px;
      overflow-x: auto;
      line-height: 1.5;
      font-size: 13px;
    }}
    .lead {{ font-size: 16px; color: #334e68; }}
    .note {{
      border-left: 4px solid var(--accent);
      background: #fff7ed;
      padding: 11px 13px;
      margin: 12px 0;
    }}
    .ok {{
      border-left: 4px solid #2f855a;
      background: #f0fff4;
      padding: 11px 13px;
      margin: 12px 0;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 12px;
    }}
    .card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 13px 14px;
      background: #fbfcfd;
    }}
    .data-table {{
      border-collapse: collapse;
      width: 100%;
      margin: 12px 0;
      font-size: 13px;
    }}
    .data-table th, .data-table td {{
      border: 1px solid var(--line);
      padding: 7px 8px;
      text-align: left;
      vertical-align: top;
    }}
    .data-table th {{ background: #edf2f7; color: #243b53; }}
    img {{
      max-width: 100%;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #fff;
      margin: 8px 0 12px;
    }}
    details.source-block {{ margin-top: 12px; }}
    details.source-block summary {{
      cursor: pointer;
      color: var(--brand);
      font-weight: 700;
      padding: 8px 0;
    }}
    .flow {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 10px;
      counter-reset: step;
    }}
    .flow div {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #fbfcfd;
      min-height: 94px;
    }}
    .flow div:before {{
      counter-increment: step;
      content: counter(step);
      display: inline-flex;
      width: 24px;
      height: 24px;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      background: var(--brand);
      color: #fff;
      font-weight: 700;
      margin-right: 7px;
    }}
    footer {{ color: var(--muted); text-align: center; padding: 20px; }}
  </style>
</head>
<body>
<header>
  <h1>co2adsorb 学习版：完整代码、配置、理论与运行流程说明</h1>
  <p>这份 HTML 面向“打开文件夹即可学习和运行”的场景，系统解释 CO2 固体胺吸附量预测项目的环境配置、数据结构、机器学习流程、LLM 上下文建模、SHAP 解释，以及每个代码文件的作用。</p>
</header>
<nav>
  <a href="#overview">总览</a>
  <a href="#config">环境配置</a>
  <a href="#data">数据说明</a>
  <a href="#theory">理论基础</a>
  <a href="#workflow">运行流程</a>
  <a href="#run-experiment">run_experiment.py</a>
  <a href="#train-baseline">train_baseline.py</a>
  <a href="#prompt-generation">prompt_generation.py</a>
  <a href="#shap-analysis">SHAP_analysis.py</a>
  <a href="#outputs">输出结果</a>
  <a href="#faq">常见问题</a>
</nav>
<main>

<section id="overview">
  <h2>1. 项目总览</h2>
  <p class="lead">本项目的研究问题是：根据固体胺吸附剂的材料性质和实验条件，预测 CO2 吸附量 <code>co2_adsorbed_amount</code>，单位为 mmol/g。</p>
  <div class="grid">
    <div class="card">
      <h3>输入 X</h3>
      <p>比表面积、孔体积、胺类型、胺分子量、氮含量、伯/仲/叔胺比例、胺负载量、温度、CO2 分压、湿度等。</p>
    </div>
    <div class="card">
      <h3>输出 y</h3>
      <p><code>co2_adsorbed_amount</code>，即 CO2 吸附量。它是一个连续数值，所以任务类型是监督学习中的回归。</p>
    </div>
    <div class="card">
      <h3>模型对比</h3>
      <p>仿照论文 Fig. 3 的思路，对比 LR、RF、XGBoost、MLP 和 LLM 五类方法的评估指标。</p>
    </div>
    <div class="card">
      <h3>解释分析</h3>
      <p>使用 XGBoost + SHAP 画特征重要性图，帮助理解模型主要依赖哪些材料特征。</p>
    </div>
  </div>
  <p class="note">重要限制：当前数据来自原仓库示例，共 19 条。代码适合课程展示、方法学习和流程复现；数值结果不能等同于论文完整数据集上的结论。</p>
</section>

<section id="config">
  <h2>2. 所需配置与库</h2>
  <h3>2.1 推荐目录</h3>
  <pre><code>E:\\LLM2025\\co2adsorb_learning</code></pre>
  <p>用 VSCode 打开这个文件夹即可。`.vscode/settings.json` 已经指定 Python 解释器为：</p>
  <pre><code>E:\\LLM2025\\.venv\\Scripts\\python.exe</code></pre>

  <h3>2.2 安装依赖</h3>
  <p>如果环境已经存在，通常不需要重新安装。如果换电脑或环境损坏，可以在项目目录运行：</p>
  <pre><code>python -m venv E:\\LLM2025\\.venv
E:\\LLM2025\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt</code></pre>

  <h3>2.3 requirements.txt 逐项解释</h3>
  <table class="data-table">
    <thead><tr><th>库</th><th>作用</th><th>本项目中用在哪里</th></tr></thead>
    <tbody>
      <tr><td>pandas</td><td>表格数据读取、清洗、保存 CSV。</td><td>读取 <code>data/co2_adsorbents.csv</code>，保存指标和预测结果。</td></tr>
      <tr><td>numpy</td><td>数值计算。</td><td>计算数组、标准差、相关系数、LLM fallback 的距离权重。</td></tr>
      <tr><td>scikit-learn</td><td>传统机器学习主库。</td><td>LR、RF、MLP、预处理流水线、留一交叉验证、评估指标。</td></tr>
      <tr><td>matplotlib</td><td>画图。</td><td>生成 Fig. 3 风格柱状图和预测散点图。</td></tr>
      <tr><td>xgboost</td><td>梯度提升树模型。</td><td>训练 XGBoost 回归器，并作为 SHAP 解释对象。</td></tr>
      <tr><td>shap</td><td>模型解释。</td><td>生成 <code>shap_summary.png</code>。</td></tr>
      <tr><td>joblib / scipy</td><td>scikit-learn 依赖。</td><td>模型训练、并行、数值算法底层支持。</td></tr>
    </tbody>
  </table>
  <h3>2.4 requirements.txt 内容</h3>
  {code_block(ROOT / "requirements.txt")}
</section>

<section id="data">
  <h2>3. 数据文件说明</h2>
  <p>数据文件为 <code>data/co2_adsorbents.csv</code>。每一行是一种材料或实验条件组合，每一列是一个特征或目标值。</p>
  <h3>3.1 前 8 行数据预览</h3>
  {data_table}
  <h3>3.2 关键字段解释</h3>
  <table class="data-table">
    <thead><tr><th>字段</th><th>含义</th><th>为什么影响 CO2 吸附</th></tr></thead>
    <tbody>
      <tr><td>surface_area_before / after</td><td>胺分散前后的比表面积。</td><td>胺负载会覆盖孔道和表面；剩余可接触面积会影响 CO2 与胺位点接触。</td></tr>
      <tr><td>pore_volume_before / after</td><td>胺分散前后的孔体积。</td><td>孔体积过低可能表示孔道被胺堵塞，扩散变差；合适孔结构有利于吸附。</td></tr>
      <tr><td>amine_type</td><td>胺类型，如 PEI、TEPA、PGA。</td><td>不同胺的分子结构、氮含量和反应机制不同。</td></tr>
      <tr><td>nitrogen_atom_content</td><td>胺中的氮原子质量分数。</td><td>氮通常是 CO2 化学吸附的重要活性位点。</td></tr>
      <tr><td>primary/secondary/tertiary_amine_proportion</td><td>伯胺、仲胺、叔胺比例。</td><td>不同胺基与 CO2 的反应机理不同，湿度也会影响其作用。</td></tr>
      <tr><td>amine_loading</td><td>胺负载量。</td><td>负载量增加通常提供更多活性位点，但过量可能堵塞孔道。</td></tr>
      <tr><td>temperature</td><td>吸附温度。</td><td>温度影响吸附热力学和动力学。</td></tr>
      <tr><td>co2_partial_pressure</td><td>CO2 分压或浓度。</td><td>分压越高，吸附驱动力通常越强。</td></tr>
      <tr><td>relative_humidity</td><td>相对湿度。</td><td>水可能促进叔胺形成碳酸氢盐，也可能竞争吸附位点。</td></tr>
      <tr><td>co2_adsorbed_amount</td><td>目标值，CO2 吸附量。</td><td>模型要预测的 y。</td></tr>
    </tbody>
  </table>
</section>

<section id="theory">
  <h2>4. 理论基础</h2>
  <h3>4.1 监督学习回归</h3>
  <p>本项目把每个样本表示为一组输入特征 <code>X</code>，把 CO2 吸附量表示为目标值 <code>y</code>。模型学习一个函数 <code>y = f(X)</code>，用于预测未见过样本的吸附量。</p>

  <h3>4.2 为什么用 Leave-One-Out Cross-Validation</h3>
  <p>数据只有 19 条。如果随机划分训练集和测试集，比如 70%/30%，测试集只有约 6 条，结果波动很大。Leave-One-Out Cross-Validation，简称 LOOCV，每次只留 1 条测试，其余 18 条训练，循环 19 次。这样每条数据都被测试一次，更适合小样本教学实验。</p>

  <h3>4.3 五类模型的含义</h3>
  <table class="data-table">
    <thead><tr><th>模型</th><th>基本思想</th><th>优点</th><th>局限</th></tr></thead>
    <tbody>
      <tr><td>LR</td><td>线性回归，假设特征线性加权得到吸附量。</td><td>简单、可解释、训练快。</td><td>难以表达孔堵塞、胺类型、分压等非线性关系。</td></tr>
      <tr><td>RF</td><td>随机森林，用很多决策树平均预测。</td><td>能表达非线性，对表格数据稳健。</td><td>小数据下仍可能受样本分布影响。</td></tr>
      <tr><td>XGBoost</td><td>梯度提升树，逐轮学习前一轮残差。</td><td>表格数据强基线，常用于论文对比。</td><td>参数较多，小数据要控制树深和学习率。</td></tr>
      <tr><td>MLP</td><td>多层感知机神经网络。</td><td>表达能力强。</td><td>样本太少时容易不稳定或过拟合。</td></tr>
      <tr><td>LLM</td><td>把训练样本和材料知识写入 prompt，做 in-context prediction。</td><td>能利用文本背景、字段含义和少样本示例。</td><td>输出格式可能不稳定，真实调用依赖 CLI 和模型环境。</td></tr>
    </tbody>
  </table>

  <h3>4.4 评估指标</h3>
  <ul>
    <li><strong>MAE</strong>：平均绝对误差，越小越好，单位仍是 mmol/g。</li>
    <li><strong>MSE</strong>：均方误差，越小越好，对大误差惩罚更重。</li>
    <li><strong>RMSE</strong>：MSE 开平方，越小越好，单位回到 mmol/g。</li>
    <li><strong>R2</strong>：决定系数，衡量比“总预测平均值”好多少，越接近 1 越好；小样本中可能为负。</li>
    <li><strong>Pearson_r</strong>：预测值和真实值的线性相关系数，越接近 1 越好；但只看相关性不够，因为整体偏高或偏低也可能相关性高。</li>
  </ul>

  <h3>4.5 SHAP 解释</h3>
  <p>SHAP 用博弈论思想把一个预测值拆成各个特征的贡献。summary plot 中，每个点代表一个样本；横轴表示该特征把预测值往高或往低推了多少；颜色表示特征取值大小。它解释的是“模型怎么用特征”，不是严格证明材料因果机制。</p>
</section>

<section id="workflow">
  <h2>5. 运行流程总图</h2>
  <div class="flow">
    <div><strong>读取数据</strong><br>从 CSV 读取 19 条样本。</div>
    <div><strong>特征工程</strong><br>计算孔损失、比表面积损失、有效氮等衍生特征。</div>
    <div><strong>拆分 X/y</strong><br>去掉 sample_id 和目标列，得到输入特征。</div>
    <div><strong>预处理</strong><br>数值列填补+标准化，类别列 One-Hot 编码。</div>
    <div><strong>ML 训练评估</strong><br>LR/RF/XGBoost/MLP 做 LOOCV。</div>
    <div><strong>LLM 评估</strong><br>逐样本构造 prompt，调用 Codex 或 fallback。</div>
    <div><strong>指标计算</strong><br>计算 MAE、MSE、RMSE、R2、Pearson_r。</div>
    <div><strong>保存结果</strong><br>输出 CSV、图、prompt、HTML。</div>
  </div>

  <h3>5.1 推荐运行命令</h3>
  <pre><code>cd E:\\LLM2025\\co2adsorb_learning
E:\\LLM2025\\.venv\\Scripts\\python.exe .\\run_experiment.py --llm-mode fallback</code></pre>
  <p><code>fallback</code> 模式保证可跑通；<code>codex</code> 模式会尝试真实调用本地 Codex CLI。</p>

  <h3>5.2 VSCode 中怎么点运行</h3>
  <ol>
    <li>打开 VSCode。</li>
    <li>选择文件夹 <code>E:\\LLM2025\\co2adsorb_learning</code>。</li>
    <li>打开 <code>run_experiment.py</code>。</li>
    <li>确认右下角 Python 环境是 <code>E:\\LLM2025\\.venv\\Scripts\\python.exe</code>。</li>
    <li>点击右上角运行按钮，默认会用 fallback 模式生成完整结果。</li>
  </ol>
</section>

<section id="run-experiment">
  <h2>6. run_experiment.py 详解</h2>
  <p class="lead"><code>run_experiment.py</code> 是整个项目的主入口。它负责读数据、特征工程、训练四个 ML 模型、评估 LLM、画图、做 SHAP、写结果文件。</p>

  <h3>6.1 文件顶部导入</h3>
  <p>主要分为五类：标准库、画图、数值表格、scikit-learn、可选的 shap/xgboost。</p>
  <ul>
    <li><code>argparse</code>：解析命令行参数，例如 <code>--llm-mode fallback</code>。</li>
    <li><code>json/re/shlex/subprocess</code>：用于调用 Codex CLI、解析 LLM 输出 JSON 或数字。</li>
    <li><code>Path</code>：跨平台处理文件路径。</li>
    <li><code>matplotlib.use("Agg")</code>：无界面环境下也能保存图片。</li>
    <li><code>pandas/numpy</code>：表格和数值计算。</li>
    <li><code>ColumnTransformer/Pipeline</code>：把数据预处理和模型训练串成统一流程，避免数据泄漏。</li>
  </ul>

  <h3>6.2 全局常量</h3>
  <ul>
    <li><code>ROOT</code>：当前代码目录。</li>
    <li><code>DATA_PATH</code>：默认数据路径。</li>
    <li><code>TARGET</code>：目标列名 <code>co2_adsorbed_amount</code>。</li>
    <li><code>ID_COLUMNS</code>：样本编号列，不参与训练。</li>
    <li><code>CATEGORICAL_FEATURES</code>：类别列，这里只有 <code>amine_type</code>。</li>
    <li><code>RANDOM_STATE</code>：固定随机种子，让 RF、MLP、XGBoost 尽量复现同样结果。</li>
  </ul>

  <h3>6.3 数据读取：load_data</h3>
  <p>读取 CSV，并检查最关键的列是否存在。如果缺少目标值、胺类型、胺负载量或比表面积列，会直接报错。这比默默运行出错更适合教学。</p>

  <h3>6.4 特征工程：add_engineered_features</h3>
  <p>这个函数把原始材料字段转成更贴近机理的特征：</p>
  <ul>
    <li><code>surface_area_loss</code>：胺分散前后比表面积差，表示表面被胺覆盖或孔道被占据的程度。</li>
    <li><code>pore_volume_loss</code>：孔体积损失，反映胺进入孔道、堵塞孔道或形成薄膜。</li>
    <li><code>surface_area_retention</code> 和 <code>pore_volume_retention</code>：保留比例，用比例消除不同载体绝对值差异。</li>
    <li><code>film_thickness_proxy</code>：用孔体积损失除以比表面积损失，粗略模拟胺膜厚度。</li>
    <li><code>loaded_nitrogen</code>：胺负载量乘氮含量，近似材料表面的有效氮供给。</li>
    <li><code>primary/secondary/tertiary_loaded_nitrogen</code>：把有效氮进一步分到伯胺、仲胺、叔胺。</li>
    <li><code>pressure_temperature_ratio</code>：CO2 分压与绝对温度的比值，作为吸附驱动力的简化表征。</li>
  </ul>

  <h3>6.5 预处理：make_preprocessor</h3>
  <p>这个函数返回一个 <code>ColumnTransformer</code>。它把数值列和类别列分开处理：</p>
  <ul>
    <li>数值列：<code>SimpleImputer(strategy="median")</code> 用中位数补缺失，再用 <code>StandardScaler</code> 标准化。</li>
    <li>类别列：<code>SimpleImputer(strategy="most_frequent")</code> 用众数补缺失，再用 <code>OneHotEncoder</code> 编码。</li>
  </ul>
  <p>为什么要放进 Pipeline？因为交叉验证时，每一轮只能用训练集拟合预处理器，测试样本不能提前泄漏到标准化均值、方差或缺失值统计里。</p>

  <h3>6.6 模型构建：build_models</h3>
  <p>这里返回四个模型 Pipeline：</p>
  <ul>
    <li><code>LR</code>：<code>LinearRegression()</code>。</li>
    <li><code>RF</code>：600 棵树，最大深度 4，小数据下限制深度可以减少过拟合。</li>
    <li><code>XGBoost</code>：120 棵弱树，深度 2，学习率 0.05，适合小数据演示。</li>
    <li><code>MLP</code>：两层隐藏层 16 和 8 个神经元，最大迭代 5000，固定随机种子。</li>
  </ul>
  <p>如果没有安装 xgboost，代码会用一个浅层随机森林占位，保证程序不至于完全跑不起来。但正式对比建议安装 requirements 中的 xgboost。</p>

  <h3>6.7 评估：evaluate_ml_models</h3>
  <p>使用 <code>cross_val_predict(model, X, y, cv=LeaveOneOut())</code> 得到每条样本的留一预测。也就是说，预测 S01 时模型没有见过 S01，预测 S02 时模型没有见过 S02，以此类推。</p>

  <h3>6.8 LLM 部分：build_llm_prompt / evaluate_llm</h3>
  <p>LLM 不是像传统 ML 那样训练参数，而是把 18 条训练样本写进 prompt，再让模型预测留下的 1 条测试样本。这对应论文中的 context-based modeling / in-context learning 思路。</p>
  <ul>
    <li><code>build_llm_prompt</code>：写任务说明、领域背景、JSON 输出格式、训练例子和待预测样本。</li>
    <li><code>run_codex_cli</code>：用 <code>subprocess.run</code> 调用命令行 Codex，把 prompt 从 stdin 传给 Codex。</li>
    <li><code>parse_llm_predictions</code>：优先解析 JSON；如果 JSON 解析失败，尝试提取数字。</li>
    <li><code>context_fallback_prediction</code>：当 Codex 不可用时，用上下文近邻加权平均给出可复现预测。</li>
    <li><code>evaluate_llm</code>：对 19 条样本逐一构造 prompt、保存 prompt、保存响应、计算 LLM 指标。</li>
  </ul>
  <p class="note">fallback 不是论文中的真实 LLM，只是为了课堂演示可以稳定跑通。正式报告中应说明真实 Codex CLI 是否成功调用，以及 <code>predictions.csv</code> 里的 <code>llm_source</code> 字段来源。</p>

  <h3>6.9 图和 HTML 输出</h3>
  <ul>
    <li><code>plot_metric_bars</code>：生成 Fig. 3 风格指标柱状图。</li>
    <li><code>plot_predictions</code>：真实值 vs 预测值散点图，越靠近对角线越好。</li>
    <li><code>save_shap_summary</code>：拟合 XGBoost 并保存 SHAP summary plot。</li>
    <li><code>write_learning_html</code>：生成简版教学 HTML。当前这份文档是更详细的扩展版。</li>
  </ul>

  <h3>6.10 main 执行逻辑</h3>
  <p>文件底部的 <code>if __name__ == "__main__": run(parse_args())</code> 表示：直接运行这个文件时，先解析命令行参数，再执行完整实验。</p>

  {code_block(ROOT / "run_experiment.py")}
</section>

<section id="train-baseline">
  <h2>7. train_baseline.py 详解</h2>
  <p><code>train_baseline.py</code> 是兼容旧仓库命名的轻量入口。原仓库常把传统模型训练写在这个文件里，所以保留它可以让老师或同学按旧习惯运行。</p>
  <p>它只有三行核心逻辑：从 <code>run_experiment.py</code> 导入 <code>parse_args</code> 和 <code>run</code>，然后直接执行完整流程。因此：</p>
  <ul>
    <li>运行 <code>python train_baseline.py --llm-mode fallback</code> 等价于运行 <code>python run_experiment.py --llm-mode fallback</code>。</li>
    <li>好处是避免维护两套训练代码，降低不一致风险。</li>
    <li>如果以后要扩展模型，应该改 <code>run_experiment.py</code>，不用改这个包装文件。</li>
  </ul>
  {code_block(ROOT / "train_baseline.py")}
</section>

<section id="prompt-generation">
  <h2>8. prompt_generation.py 详解</h2>
  <p><code>prompt_generation.py</code> 专门用来生成一个示例 LLM prompt，便于查看“给 LLM 的输入到底长什么样”。</p>
  <h3>8.1 执行流程</h3>
  <ol>
    <li>调用 <code>load_data()</code> 读取 CSV。</li>
    <li>调用 <code>add_engineered_features()</code> 加上材料学衍生特征。</li>
    <li>取前 14 条作为训练例子，后 5 条作为待预测样本。</li>
    <li>调用 <code>build_llm_prompt(train_df, test_df)</code> 生成 prompt。</li>
    <li>保存到 <code>outputs/llm/example_llm_prompt.txt</code>。</li>
  </ol>
  <h3>8.2 为什么单独保留这个文件</h3>
  <p>LLM 实验最容易被质疑的是 prompt 是否泄漏答案、格式是否清晰、上下文是否公平。单独生成 prompt 文件，可以直接打开给老师检查。</p>
  <pre><code>E:\\LLM2025\\.venv\\Scripts\\python.exe .\\prompt_generation.py</code></pre>
  {code_block(ROOT / "prompt_generation.py")}
</section>

<section id="shap-analysis">
  <h2>9. SHAP_analysis.py 详解</h2>
  <p><code>SHAP_analysis.py</code> 是 SHAP 图的单独入口。如果只想重画解释图，不想完整跑 LR/RF/XGBoost/MLP/LLM 对比，可以运行它。</p>
  <h3>9.1 执行流程</h3>
  <ol>
    <li>读取数据。</li>
    <li>添加工程特征。</li>
    <li>调用 <code>save_shap_summary(df, output_path)</code>。</li>
    <li>输出 <code>outputs/shap_summary.png</code>。</li>
  </ol>
  <h3>9.2 注意点</h3>
  <p>SHAP 图基于 XGBoost 在全数据上的拟合结果，用于解释模型行为。因为只有 19 条样本，所以它更适合教学说明，不适合做强材料学因果结论。</p>
  <pre><code>E:\\LLM2025\\.venv\\Scripts\\python.exe .\\SHAP_analysis.py</code></pre>
  {code_block(ROOT / "SHAP_analysis.py")}
</section>

<section id="outputs">
  <h2>10. 输出结果与如何阅读</h2>
  <h3>10.1 当前模型指标</h3>
  {metrics_table}
  <p>一般阅读顺序：先看 MAE/RMSE，因为它们直接表示预测误差大小；再看 R2 是否明显高于 0；最后看 Pearson_r 判断趋势是否一致。</p>

  <h3>10.2 Fig. 3 风格柱状图</h3>
  <img src="fig3_model_metrics.png" alt="Fig. 3 风格指标柱状图">
  <p>这张图仿照论文 Fig. 3 的核心表达方式：把不同模型放在横轴，把多个评估指标分面展示，便于横向比较。</p>

  <h3>10.3 预测散点图</h3>
  <img src="prediction_comparison.png" alt="预测值与真实值散点图">
  <p>对角虚线表示完美预测。点越接近对角线，说明该模型对该样本预测越准。</p>

  <h3>10.4 SHAP summary plot</h3>
  <img src="shap_summary.png" alt="SHAP summary plot">
  <p>横轴表示特征贡献方向和强度。红色通常表示该特征取值较高，蓝色表示取值较低。若某个特征的点分布横向跨度大，说明它对模型输出影响较大。</p>

  <h3>10.5 LLM 文件</h3>
  <ul>
    <li><code>outputs/llm/llm_prompt_S01.txt</code> 到 <code>llm_prompt_S19.txt</code>：每次留一测试时给 LLM 的 prompt。</li>
    <li><code>outputs/llm/llm_response_S01.txt</code> 到 <code>llm_response_S19.txt</code>：Codex CLI 原始响应或 fallback 说明。</li>
    <li><code>predictions.csv</code> 中的 <code>llm_source</code>：记录该行 LLM 预测来自真实 CLI、解析失败回退，还是 fallback。</li>
  </ul>
</section>

<section id="faq">
  <h2>11. 常见问题</h2>
  <h3>11.1 为什么不用 __pycache__？</h3>
  <p><code>__pycache__</code> 是 Python 自动生成的字节码缓存，不是源码，也不是结果。删掉不影响代码运行；下次运行 Python 可能又自动生成。本项目已经在 <code>.gitignore</code> 中排除它。</p>

  <h3>11.2 为什么要标准化？</h3>
  <p>比表面积可能几百到上千，胺比例是 0 到 1，量纲差异很大。LR 和 MLP 对尺度敏感，标准化可以让模型更稳定。RF 和 XGBoost 对标准化不敏感，但统一放进 Pipeline 便于比较。</p>

  <h3>11.3 为什么类别变量要 One-Hot？</h3>
  <p><code>amine_type</code> 是文本类别，模型不能直接理解字符串。One-Hot 会把 PEI、TEPA、PGA 等转为 0/1 列，不强行给它们排序。</p>

  <h3>11.4 为什么 LLM 要求 JSON 输出？</h3>
  <p>如果 LLM 输出一大段自然语言，程序很难稳定提取预测值。要求 JSON 可以降低解析难度，也便于保存和复现实验。</p>

  <h3>11.5 如果 Codex CLI 不能调用怎么办？</h3>
  <p>用 <code>--llm-mode fallback</code>。这会使用可复现的上下文近邻模型模拟“根据相似训练样本推断”的过程，保证课堂演示跑通。正式汇报时要说明 fallback 与真实 LLM 的区别。</p>

  <h3>11.6 如果想加入更多数据怎么办？</h3>
  <p>直接在 <code>data/co2_adsorbents.csv</code> 追加行，保持列名不变。数据量变大后，可以考虑把 LOOCV 换成 KFold 或按文献来源/材料体系做 GroupKFold。</p>
</section>

</main>
<footer>
  <p>生成位置：E:\\LLM2025\\co2adsorb_learning\\outputs\\co2adsorb_code_theory_running_guide.html</p>
</footer>
</body>
</html>
"""
    HTML_PATH.write_text(html_text, encoding="utf-8")
    return HTML_PATH


if __name__ == "__main__":
    path = write_html()
    print(path.resolve())
