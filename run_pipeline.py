"""Run the DataLens workflow from the command line."""

from pathlib import Path

from datalens.core import load_dataset, report_markdown, run_pipeline


def main() -> None:
    root = Path(__file__).resolve().parent
    source = root / "data" / "raw" / "transactions.csv"
    output = root / "output" / "datalens_report.md"
    result = run_pipeline(load_dataset(source))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report_markdown(result, "DataLens demo project"), encoding="utf-8")
    print(f"DataLens processed {len(result['data']):,} rows")
    print(f"Quality: {result['quality']['score']}/100 ({result['quality']['status']})")
    print(f"SQL validation: {result['sql']['status']}")
    print(f"Report: {output}")


if __name__ == "__main__":
    main()