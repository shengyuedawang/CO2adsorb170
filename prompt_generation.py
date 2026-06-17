from pathlib import Path

from run_experiment import add_engineered_features, build_llm_prompt, load_data


def main() -> None:
    df = add_engineered_features(load_data())
    train_df = df.iloc[:14].copy()
    test_df = df.iloc[14:].copy()
    prompt = build_llm_prompt(train_df, test_df)
    output_dir = Path("outputs") / "llm"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "example_llm_prompt.txt"
    output_path.write_text(prompt, encoding="utf-8")
    print(output_path.resolve())


if __name__ == "__main__":
    main()
