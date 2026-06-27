import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json
import os
import traceback
from tools.csv_loader import get_dataframe

OUTPUT_DIR = "data"

COLORS = [
    "#4C72B0", "#DD8452", "#55A868", "#C44E52",
    "#8172B3", "#937860", "#DA8BC3", "#8C8C8C"
]

def _apply_style(ax, title: str):
    ax.set_title(title, fontsize=14, fontweight="bold", pad=14, color="#222222")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")
    ax.tick_params(colors="#555555", labelsize=10)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5, color="#DDDDDD")
    ax.set_axisbelow(True)


def generate_chart(code: str, filename: str = "chart.png") -> str:
    df = get_dataframe()
    if df is None:
        return json.dumps({
            "status": "error",
            "message": "No CSV loaded. Call load_csv first."
        })

    filepath = os.path.join(OUTPUT_DIR, filename)

    local_vars = {
        "df":          df.copy(),
        "pd":          pd,
        "plt":         plt,
        "COLORS":      COLORS,
        "apply_style": _apply_style,
    }

    try:
        fig, ax = plt.subplots(figsize=(10, 5))
        local_vars["fig"] = fig
        local_vars["ax"]  = ax

        exec(code, {"__builtins__": __builtins__}, local_vars)

        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        plt.close()

        return json.dumps({
            "status":     "success",
            "chart_path": filepath,
            "message":    f"Chart saved to {filepath}"
        })

    except Exception:
        plt.close()
        return json.dumps({
            "status":  "error",
            "message": traceback.format_exc()
        })