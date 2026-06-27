import pandas as pd
import json
import traceback
from tools.csv_loader import get_dataframe

def execute_code(code: str) -> str:
    df = get_dataframe()

    if df is None:
        return json.dumps({
            "status": "error",
            "message": "No CSV loaded. Call load_csv first."
        })

    # Fix escaped newlines — model sometimes sends \\n instead of real newlines
    code = code.replace("\\n", "\n").replace("\\t", "\t")

    # Block attempts to re-read CSV — df is already loaded
    if "pd.read_csv" in code or "read_csv" in code:
        code = "\n".join(
            line for line in code.split("\n")
            if "read_csv" not in line and "import pandas" not in line
        )

    local_vars = {"df": df.copy(), "pd": pd, "result": None}

    try:
        exec(code, {"__builtins__": __builtins__}, local_vars)

        result = local_vars.get("result", None)

        if result is None:
            return json.dumps({
                "status": "success",
                "output": "Code ran but result was not set. Add result = ... at the end.",
            })

        if isinstance(result, pd.DataFrame):
            # Format numbers as integers to avoid scientific notation
            for col in result.select_dtypes(include='float').columns:
                result[col] = result[col].round(0).astype(int)
            return json.dumps({
                "status": "success",
                "output": result.to_string(),
                "shape":  list(result.shape)
            })
        elif isinstance(result, pd.Series):
            if result.dtype == 'float64':
                result = result.round(0).astype(int)
            return json.dumps({
                "status": "success",
                "output": result.to_string()
            })
        else:
            return json.dumps({
                "status": "success",
                "output": str(result)
            })
    except Exception:
        return json.dumps({
            "status":  "error",
            "message": traceback.format_exc()
        })