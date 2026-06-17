from pathlib import Path

from run_experiment import add_engineered_features, load_data, save_shap_summary


def main() -> None:
    df = add_engineered_features(load_data())
    output_path = Path("outputs") / "shap_summary.png"
    status = save_shap_summary(df, output_path)
    print(f"{status} {output_path.resolve()}")


if __name__ == "__main__":
    main()
