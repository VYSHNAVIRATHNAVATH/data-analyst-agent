import pandas as pd
import json

# Global variable — the loaded dataframe lives here during a session
_dataframe = None
_filename = ""

def load_csv(filepath: str) -> str:
    """
    Load a CSV file into memory and return a summary the agent can read.
    """
    global _dataframe, _filename

    try:
        _dataframe = pd.read_csv(filepath)
        _filename = filepath

        summary = {
            "status": "success",
            "filename": filepath,
            "rows": len(_dataframe),
            "columns": list(_dataframe.columns),
            "dtypes": {col: str(_dataframe[col].dtype) for col in _dataframe.columns},
            "preview": _dataframe.head(3).to_dict(orient="records"),
            "null_counts": _dataframe.isnull().sum().to_dict()
        }
        return json.dumps(summary, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def get_dataframe() -> pd.DataFrame:
    """Return the currently loaded dataframe."""
    return _dataframe


def get_schema_hint() -> str:
    """Return a compact schema string for injecting into prompts."""
    if _dataframe is None:
        return "No CSV loaded yet."
    dtypes = {col: str(_dataframe[col].dtype) for col in _dataframe.columns}
    return f"Columns: {dtypes} | Rows: {len(_dataframe)} | File: {_filename}"