"""Tables and charts about the freelance market, built from the extractions."""

import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw to files, no window
import matplotlib.pyplot as plt
import pandas as pd


def load(postings_file: Path, extractions_file: Path) -> pd.DataFrame:
    postings = pd.DataFrame(json.loads(line) for line in postings_file.open(encoding="utf-8"))
    rows = []
    for line in extractions_file.open(encoding="utf-8"):
        record = json.loads(line)
        rows.append({"id": record["id"], "problems": record["problems"], **record["data"]})
    return postings.merge(pd.DataFrame(rows), on="id")


def table(df: pd.DataFrame) -> str:
    return df.to_markdown() if hasattr(df, "to_markdown") else df.to_string()


def bar_chart(counts: pd.Series, title: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    counts.sort_values().plot.barh(ax=ax, color="#2b6cb0")
    ax.set_title(title)
    ax.set_xlabel("Postings")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run(postings_file: Path, extractions_file: Path, out_dir: Path) -> None:
    out_dir.mkdir(exist_ok=True)
    df = load(postings_file, extractions_file)
    n = len(df)

    passed = (df["problems"].str.len() == 0).mean()
    problem_counts = Counter(p for problems in df["problems"] for p in problems)
    budget_rate = df["stated_budget"].notna().mean()

    types = df["project_type"].value_counts()
    tools = Counter(t.lower().strip() for items in df["tools"] for t in set(items))
    top_tools = pd.Series(dict(tools.most_common(15)))

    experience = pd.crosstab(df["project_type"], df["experience_level"], normalize="index").round(2)
    flags = Counter(f for items in df["red_flags"] for f in items)
    by_type = (
        df.groupby("project_type")
        .agg(
            postings=("id", "count"),
            urgent=("is_urgent", "mean"),
            ongoing=("is_ongoing", "mean"),
            median_days=("timeline_days", "median"),
        )
        .round(2)
    )

    top_countries = df["country"].value_counts().head(8).index
    country_mix = pd.crosstab(
        df[df["country"].isin(top_countries)]["country"],
        df[df["country"].isin(top_countries)]["project_type"],
        normalize="index",
    ).round(2)

    bar_chart(types, "What freelance clients ask for", out_dir / "project_types.png")
    bar_chart(top_tools, "Most requested tools", out_dir / "top_tools.png")

    lines = [
        "# Freelance job postings, extracted",
        "",
        f"{n} postings processed.",
        "",
        "## How reliable is the extraction?",
        "",
        f"- {passed:.1%} of postings passed every check (quotes found in the text, numbers present).",
        f"- Problems found: {dict(problem_counts) or 'none'}.",
        f"- A budget was written in the text for {budget_rate:.1%} of postings. A model that invents values would report far more.",
        "",
        "## Project types",
        "",
        table(types.rename("postings").to_frame()),
        "",
        "## Most requested tools",
        "",
        table(top_tools.rename("postings").to_frame()),
        "",
        "## Experience level asked for, by project type (share of postings)",
        "",
        table(experience),
        "",
        "## Urgency, ongoing work and timeline, by project type",
        "",
        table(by_type),
        "",
        "## Red flags (count)",
        "",
        table(pd.Series(flags, name="postings").to_frame()),
        "",
        "## Project mix in the 8 biggest client countries (share of postings)",
        "",
        table(country_mix),
        "",
        "![Project types](project_types.png)",
        "",
        "![Top tools](top_tools.png)",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_dir / 'summary.md'}")
