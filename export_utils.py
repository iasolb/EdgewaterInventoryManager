"""
Export utilities for admin pages.

Ensures CSV exports match the canonical column order defined in SQLAlchemy models,
so exported files can be directly re-imported as backups without manual column reordering.
"""

import pandas as pd
from sqlalchemy import inspect as sa_inspect


def get_model_column_order(model_class) -> list[str]:
    """
    Extract column names from a SQLAlchemy model in declaration order.

    Returns the columns in the exact order they appear in models.py,
    which matches the database schema / expected import order.
    """
    mapper = sa_inspect(model_class)
    return [col.key for col in mapper.columns]


def export_csv(df: pd.DataFrame, model_class) -> str:
    """
    Export a DataFrame to CSV string with columns ordered to match the model schema.

    Columns present in the model are placed first (in model order),
    any extra columns in the DataFrame (e.g. from joins/views) are appended at the end.
    Columns in the model but missing from the DataFrame are skipped.
    """
    model_cols = get_model_column_order(model_class)

    # Model columns that exist in the dataframe, in model order
    ordered = [c for c in model_cols if c in df.columns]

    # Any extra columns not in the model (preserve their existing order)
    extras = [c for c in df.columns if c not in model_cols]

    return df[ordered + extras].to_csv(index=False)
