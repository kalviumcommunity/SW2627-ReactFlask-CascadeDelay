import json
import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def compute_correlations(df):
    """
    Compute Pearson and Spearman correlation matrices.
    """

    pearson_corr = df.corr(
        method="pearson",
        numeric_only=True
    )

    spearman_corr = df.corr(
        method="spearman",
        numeric_only=True
    )

    return pearson_corr, spearman_corr


def compare_churn_correlations(
    pearson_corr,
    spearman_corr
):
    """
    Compare Pearson and Spearman correlations
    specifically against churn.
    """

    comparison = pd.DataFrame({
        "pearson": pearson_corr["churn"],
        "spearman": spearman_corr["churn"]
    })

    return comparison


def create_heatmap(
    correlation_matrix,
    output_path
):
    """
    Create and save Pearson correlation heatmap.
    """

    plt.figure(
        figsize=(12, 10)
    )

    sns.heatmap(
        correlation_matrix,
        annot=True,
        cmap="coolwarm",
        center=0,
        fmt=".2f"
    )

    plt.title(
        "Feature Correlation Matrix"
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=150
    )

    plt.close()


def find_strong_correlations(
    correlation_matrix,
    threshold=0.7
):
    """
    Find strong correlations above the
    specified absolute correlation threshold.

    Self-correlations of 1.0 are excluded.
    """

    corr_flat = (
        correlation_matrix
        .unstack()
    )

    strong = (
        corr_flat[
            corr_flat.abs() > threshold
        ]
        .sort_values(
            ascending=False
        )
    )

    strong = strong[
        strong != 1.0
    ]

    return strong.head(10)


def create_business_analysis(
    strong_correlations,
    pearson_corr
):
    """
    Create documented business interpretation.
    """

    analysis = {
        "correlation_is_not_causation": True,
        "principle": (
            "Correlation shows that variables move "
            "together. It does not prove that one "
            "variable causes another."
        ),
        "strong_relationships": []
    }

    for pair, correlation in (
        strong_correlations.items()
    ):

        variable_1, variable_2 = pair

        if correlation > 0:
            direction = "positive"
        else:
            direction = "negative"

        analysis[
            "strong_relationships"
        ].append({
            "variable_1": variable_1,
            "variable_2": variable_2,
            "correlation": round(
                float(correlation),
                4
            ),
            "direction": direction,
            "interpretation": (
                "Variables move together, but "
                "the correlation alone does not "
                "establish causation."
            )
        })

    # Specific business interpretation from the task
    if "support_tickets" in pearson_corr.columns:
        support_ticket_corr = pearson_corr.loc[
            "support_tickets",
            "churn"
        ]

        analysis[
            "support_tickets_churn"
        ] = {
            "correlation": round(
                float(support_ticket_corr),
                4
            ),
            "possible_directions": [
                "support_tickets -> churn",
                "churn -> support_tickets",
                "customer_pain -> both"
            ],
            "warning": (
                "Support tickets should not be "
                "interpreted as causing churn solely "
                "from correlation."
            )
        }

    return analysis


def perform_feature_selection(df):
    """
    Demonstrate correlation-based feature selection.

    engagement and transactions_per_month are
    conceptually redundant features, so engagement
    is removed while the more interpretable
    transactions_per_month feature is retained.
    """

    selected_columns = [
        "engagement",
        "transactions_per_month",
        "support_tickets",
        "churn"
    ]

    df_features = df[
        selected_columns
    ].copy()

    # The task specifies dropping engagement
    # because transactions_per_month is more
    # interpretable in business context.
    df_features = df_features.drop(
        "engagement",
        axis=1
    )

    return df_features


def save_json(
    data,
    output_path
):
    """
    Save dictionary as JSON.
    """

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2
        )


if __name__ == "__main__":

    input_path = (
        "data/raw/churn_data.csv"
    )

    heatmap_path = (
        "output/correlation_heatmap.png"
    )

    comparison_path = (
        "output/churn_correlation_comparison.csv"
    )

    strong_path = (
        "output/strong_correlations.csv"
    )

    analysis_path = (
        "output/business_correlation_analysis.json"
    )

    selected_features_path = (
        "data/processed/"
        "selected_churn_features.csv"
    )

    os.makedirs(
        "output",
        exist_ok=True
    )

    os.makedirs(
        "data/processed",
        exist_ok=True
    )

    print("\n" + "=" * 70)
    print("STARTING CORRELATION ANALYSIS")
    print("=" * 70)

    # Load dataset
    df = pd.read_csv(
        input_path
    )

    print(
        f"Initial records: {len(df)}"
    )

    # Task 1
    print(
        "\n[Task 1] "
        "Computing Pearson and Spearman correlations..."
    )

    pearson_corr, spearman_corr = (
        compute_correlations(df)
    )

    comparison = compare_churn_correlations(
        pearson_corr,
        spearman_corr
    )

    print("\nCorrelation with churn:")
    print(comparison)

    comparison.to_csv(
        comparison_path
    )

    # Task 2
    print(
        "\n[Task 2] "
        "Creating correlation heatmap..."
    )

    create_heatmap(
        pearson_corr,
        heatmap_path
    )

    print(
        f"Heatmap saved to: "
        f"{heatmap_path}"
    )

    # Task 3
    print(
        "\n[Task 3] "
        "Finding strong correlations..."
    )

    strong_correlations = (
        find_strong_correlations(
            pearson_corr,
            threshold=0.7
        )
    )

    print(
        "\nStrong correlations:"
    )

    print(
        strong_correlations
    )

    strong_correlations.to_csv(
        strong_path,
        header=["correlation"]
    )

    # Task 4
    print(
        "\n[Task 4] "
        "Creating business interpretation..."
    )

    business_analysis = (
        create_business_analysis(
            strong_correlations,
            pearson_corr
        )
    )

    print(
        json.dumps(
            business_analysis,
            indent=2
        )
    )

    save_json(
        business_analysis,
        analysis_path
    )

    # Task 5
    print(
        "\n[Task 5] "
        "Performing correlation-based feature selection..."
    )

    df_features = perform_feature_selection(
        df
    )

    print(
        "\nSelected features:"
    )

    print(
        df_features.head()
    )

    print(
        "\nSelected feature correlations:"
    )

    print(
        df_features.corr()
    )

    df_features.to_csv(
        selected_features_path,
        index=False
    )

    print("\n" + "=" * 70)
    print("CORRELATION ANALYSIS COMPLETE")
    print("=" * 70)

    print(
        f"Pearson matrix: "
        f"{pearson_corr.shape}"
    )

    print(
        f"Spearman matrix: "
        f"{spearman_corr.shape}"
    )

    print(
        f"Heatmap: "
        f"{heatmap_path}"
    )

    print(
        f"Comparison: "
        f"{comparison_path}"
    )

    print(
        f"Strong relationships: "
        f"{strong_path}"
    )

    print(
        f"Business analysis: "
        f"{analysis_path}"
    )

    print(
        f"Selected features: "
        f"{selected_features_path}"
    )
