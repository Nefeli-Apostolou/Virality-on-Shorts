"""
tools.py

Collection of utility functions used across the notebooks in this project.
Import functions from this file into a notebook like this:

    from tools import filter_active_publishers
"""

import pandas as pd
import numpy as np



# Filters

def filter_active_publishers(
    df,
    platform_name,
    publisher_col,
    date_col,
    min_videos_per_year
):
    """
    Keeps only publishers who posted at least `min_videos_per_year`
    videos in EVERY year from 2022 to 2026.

    Parameters
    ----------
    df : pandas.DataFrame
        The raw DataFrame to filter. Must contain at least the columns
        referenced by `publisher_col` and `date_col`.

    platform_name : str
        Name of the platform (e.g. "YouTube", "TikTok").
        Used only to label the printed output, does not affect filtering.

    publisher_col : str
        Name of the column in `df` identifying the publisher/channel
        (e.g. "channel_name" or "publisher_id"). Video counts and
        filtering are grouped by this column.

    date_col : str
        Name of the column in `df` containing the video's publish date.
        It will be converted to datetime (UTC) to extract the year.

    min_videos_per_year : int
        Minimum number of videos required in each year (2022-2026).
        A publisher is considered "active" only if in ALL years it
        published a number of videos >= this threshold.

    Returns
    -------
    df_active : pandas.DataFrame
        Subset of `df` containing only rows from active publishers.

    active_publishers : pandas.DataFrame
        Table with one row per active publisher and the minimum number
        of videos published in a single year (column "min_videos").

    counts : pandas.DataFrame
        Full publisher x year table with video counts (including zeros
        for missing combinations), useful for debugging or further analysis.
    """

    df = df.copy()

    # Convert date column
    df[date_col] = pd.to_datetime(df[date_col], utc=True, errors="coerce")
    df["year"] = df[date_col].dt.year
    df = df[df["year"].between(2022, 2026)].copy()

    # Count videos per publisher and year
    counts = (
        df.groupby([publisher_col, "year"])
          .size()
          .reset_index(name="n_videos")
    )

    # Create complete publisher-year table
    years = sorted(df["year"].unique())

    full_index = pd.MultiIndex.from_product(
        [df[publisher_col].unique(), years],
        names=[publisher_col, "year"]
    )

    counts = (
        counts.set_index([publisher_col, "year"])
              .reindex(full_index, fill_value=0)
              .reset_index()
    )

    # Keep publishers satisfying the threshold in ALL years
    active_publishers = (
        counts.groupby(publisher_col)["n_videos"]
              .min()
              .reset_index(name="min_videos")
    )

    active_publishers = active_publishers[
        active_publishers["min_videos"] >= min_videos_per_year
    ]

    active_list = active_publishers[publisher_col].tolist()

    # Filter original dataframe
    df_active = df[df[publisher_col].isin(active_list)].copy()

    print(f"\n{platform_name}")
    print("-" * len(platform_name))
    print(f"Original publishers: {df[publisher_col].nunique()}")
    print(f"Active publishers:   {len(active_list)}")
    print(f"Original videos:     {len(df):,}")
    print(f"Remaining videos:    {len(df_active):,}")

    return df_active, active_publishers, counts



def filter_active_publisher_years(
    df,
    platform_name,
    publisher_col,
    date_col,
    min_videos_per_year
):
    """
    Keeps only publisher-year groups with at least `min_videos_per_year` videos.
    A publisher can be retained in some years and excluded in others.
    """

    df = df.copy()

    # Convert date column
    df[date_col] = pd.to_datetime(df[date_col], utc=True, errors="coerce")
    df["year"] = df[date_col].dt.year
    df = df[df["year"].between(2022, 2026)].copy()

    # Count videos per publisher-year
    counts = (
        df.groupby([publisher_col, "year"])
          .size()
          .reset_index(name="n_videos")
    )

    # Identify active publisher-year combinations
    active_publisher_years = counts[
        counts["n_videos"] >= min_videos_per_year
    ].copy()

    # Keep only videos belonging to active publisher-year combinations
    df_active = df.merge(
        active_publisher_years[[publisher_col, "year"]],
        on=[publisher_col, "year"],
        how="inner"
    )

    df_active["platform"] = platform_name
    active_publisher_years["platform"] = platform_name
    counts["platform"] = platform_name

    print(f"\n{platform_name}")
    print("-" * len(platform_name))
    print(f"Original videos:              {len(df):,}")
    print(f"Original publishers:          {df[publisher_col].nunique():,}")
    print(f"Videos after filtering:       {len(df_active):,}")
    print(f"Unique publishers retained:   {df_active[publisher_col].nunique():,}")
    
    print("\nPublisher-years retained by year:")
    print(
        active_publisher_years["year"]
        .value_counts()
        .sort_index()
    )

    return df_active, active_publisher_years, counts


# Virality Coefficients

def bootstrap_virality_coefficients(
    df,
    platform_name,
    publisher_col,
    year_col,
    views_col="views",
    sample_size=30,
    n_bootstrap=100,
    random_state=42
):
    """
    Computes a bootstrap-based Virality Coefficient for each publisher-year.

    VC = max(views) / median(views)

    For each publisher-year:
    - draw `sample_size` videos with replacement
    - compute max / median
    - repeat `n_bootstrap` times
    - store the median VC and bootstrap uncertainty
    """

    rng = np.random.default_rng(random_state)
    results = []

    for (publisher, year), group in df.groupby([publisher_col, year_col]):

        views = group[views_col].dropna().to_numpy()

        # Remove zero or negative views to avoid division problems
        views = views[views > 0]

        if len(views) < sample_size:
            continue

        vc_values = []
        median_values = []
        max_values = []

        for _ in range(n_bootstrap):
            sample = rng.choice(
                views,
                size=sample_size,
                replace=True
            )

            sample_median = np.median(sample)
            sample_max = np.max(sample)

            if sample_median > 0:
                vc_values.append(sample_max / sample_median)
                median_values.append(sample_median)
                max_values.append(sample_max)

        if len(vc_values) == 0:
            continue

        results.append({
            "platform": platform_name,
            "publisher": publisher,
            "year": year,
            "n_videos": len(views),

            "typical_views": np.median(median_values),
            "viral_views": np.median(max_values),

            "virality_coefficient": np.median(vc_values),
            "vc_bootstrap_sd": np.std(vc_values, ddof=1),
            "vc_ci_lower": np.percentile(vc_values, 2.5),
            "vc_ci_upper": np.percentile(vc_values, 97.5)
        })

    return pd.DataFrame(results)



def zscore_per_video(
    df,
    platform_name,
    publisher_col,
    year_col,
    views_col="views",
    sample_size=30,
    random_state=42
):
    """
    Per ogni video, calcola lo z-score delle sue views rispetto a un campione
    casuale di `sample_size` video estratti dallo stesso anno.

    z = (views_video - mean(campione)) / std(campione)
    """

    rng = np.random.default_rng(random_state)
    all_results = []

    for year, year_group in df.groupby(year_col):

        views_pool = year_group[views_col].dropna().to_numpy()
        views_pool = views_pool[views_pool > 0]

        if len(views_pool) < sample_size:
            continue

        # campione di riferimento per stimare mean/std di quell'anno
        sample = rng.choice(views_pool, size=sample_size, replace=False)
        sample_mean = np.mean(sample)
        sample_std = np.std(sample, ddof=1)

        if sample_std == 0:
            continue

        # calcola lo z-score per OGNI video di quell'anno rispetto al campione
        year_data = year_group.copy()
        year_data = year_data[year_data[views_col] > 0]

        year_data["platform"] = platform_name
        year_data["sample_mean"] = sample_mean
        year_data["sample_std"] = sample_std
        year_data["zscore"] = (year_data[views_col] - sample_mean) / sample_std

        all_results.append(year_data)

    if len(all_results) == 0:
        return pd.DataFrame()

    return pd.concat(all_results, ignore_index=True)