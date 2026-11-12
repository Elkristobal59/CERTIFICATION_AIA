from typing import Any, Dict, Tuple
import pandas as pd
import pandera.pandas as pa

TRANSACTION_SCHEMA = pa.DataFrameSchema(
    {
        "trans_num": pa.Column(str, pa.Check.str_length(min_value=1), nullable=False, coerce=True),
        "amt": pa.Column(float, pa.Check.ge(0.0), nullable=False, coerce=True),
        "merchant": pa.Column(str, pa.Check.str_length(min_value=1), nullable=False, coerce=True),
        "category": pa.Column(str, pa.Check.str_length(min_value=1), nullable=False, coerce=True),
        "lat": pa.Column(float, pa.Check.in_range(-90.0, 90.0), nullable=False, coerce=True),
        "long": pa.Column(float, pa.Check.in_range(-180.0, 180.0), nullable=False, coerce=True),
        "merch_lat": pa.Column(float, pa.Check.in_range(-90.0, 90.0), nullable=False, coerce=True),
        "merch_long": pa.Column(float, pa.Check.in_range(-180.0, 180.0), nullable=False, coerce=True),
    },
    strict=False,
)


def _format_schema_errors(err: pa.errors.SchemaErrors) -> str:
    cases = err.failure_cases
    parts = [f"{row['column']}={row['failure_case']} ({row['check']})" for _, row in cases.head(3).iterrows()]
    return "Pandera SchemaError: " + " | ".join(parts)


def validate_transaction_record(tx: Any) -> Tuple[bool, str]:
    """Valide une transaction unitaire temps réel via Pandera DataFrameSchema."""
    if not isinstance(tx, dict):
        return False, "Payload invalide : objet JSON dict attendu"
    df_row = pd.DataFrame([tx])
    try:
        TRANSACTION_SCHEMA.validate(df_row, lazy=True)
        return True, "OK"
    except pa.errors.SchemaErrors as err:
        return False, _format_schema_errors(err)
    except Exception as exc:
        return False, f"Pandera Validation Exception: {exc}"


def validate_transactions_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Sépare un lot Bronze en lignes conformes et lignes rejetées (quarantaine)."""
    if df.empty:
        return df.copy(), pd.DataFrame()
    try:
        validated = TRANSACTION_SCHEMA.validate(df, lazy=True)
        return validated, pd.DataFrame()
    except pa.errors.SchemaErrors as err:
        bad_indices = sorted({int(i) for i in err.failure_cases["index"].dropna().unique()})
        rejected_df = df.loc[df.index.isin(bad_indices)].copy()
        if not rejected_df.empty:
            reason_map = (
                err.failure_cases.dropna(subset=["index"])
                .groupby("index")
                .apply(lambda g: " | ".join(f"{r['column']}:{r['check']}" for _, r in g.iterrows()))
            )
            rejected_df["error_reason"] = rejected_df.index.map(lambda idx: reason_map.get(idx, "Pandera failure"))
        valid_df = df.drop(index=bad_indices).copy()
        return valid_df, rejected_df

