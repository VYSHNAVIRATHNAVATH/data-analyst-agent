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


def forecast(periods: int = 90, date_col: str = "date",
             value_col: str = "revenue", freq: str = "D") -> str:
    """
    Forecast future values using Facebook Prophet.
    Automatically computes revenue = units_sold * unit_price if value_col is revenue.
    Returns forecast data + saves a chart PNG.
    """
    df = get_dataframe()

    if df is None:
        return json.dumps({
            "status": "error",
            "message": "No CSV loaded. Call load_csv first."
        })

    try:
        from prophet import Prophet
    except ImportError:
        return json.dumps({
            "status": "error",
            "message": "Prophet not installed. Run: pip install prophet"
        })

    try:
        df = df.copy()

        # Auto-compute revenue if needed
        if value_col == "revenue" and "revenue" not in df.columns:
            if "units_sold" in df.columns and "unit_price" in df.columns:
                df["revenue"] = df["units_sold"] * df["unit_price"]
            else:
                return json.dumps({
                    "status": "error",
                    "message": "Cannot compute revenue. Need units_sold and unit_price columns."
                })

        # Validate columns exist
        if date_col not in df.columns:
            return json.dumps({
                "status": "error",
                "message": f"Date column '{date_col}' not found. Available: {list(df.columns)}"
            })

        if value_col not in df.columns:
            return json.dumps({
                "status": "error",
                "message": f"Value column '{value_col}' not found. Available: {list(df.columns)}"
            })

        # Parse dates
        df[date_col] = pd.to_datetime(df[date_col])

        # Aggregate by date — Prophet needs one value per date
        daily = df.groupby(date_col)[value_col].sum().reset_index()
        daily.columns = ["ds", "y"]
        daily = daily.sort_values("ds").reset_index(drop=True)

        if len(daily) < 2:
            return json.dumps({
                "status": "error",
                "message": "Need at least 2 data points to forecast."
            })

        # Fit Prophet model
        model = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=False,
            daily_seasonality=False,
            seasonality_mode="additive"
        )
        model.fit(daily)

        # Make future dataframe
        # Fix deprecated pandas frequency aliases
        freq_map = {"M": "ME", "Y": "YE", "Q": "QE", "A": "YE"}
        freq = freq_map.get(freq, freq)
        future = model.make_future_dataframe(periods=periods, freq=freq)
        forecast_df = model.predict(future)

        # Extract forecast summary
        future_only = forecast_df[forecast_df["ds"] > daily["ds"].max()]
        summary = future_only[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
        summary["ds"] = summary["ds"].dt.strftime("%Y-%m-%d")
        summary["yhat"] = summary["yhat"].round(0).astype(int)
        summary["yhat_lower"] = summary["yhat_lower"].round(0).astype(int)
        summary["yhat_upper"] = summary["yhat_upper"].round(0).astype(int)

        # Monthly summary for readable output
        forecast_df["month"] = pd.to_datetime(forecast_df["ds"]).dt.to_period("M")
        monthly = forecast_df[forecast_df["ds"] > daily["ds"].max()].groupby("month").agg(
            predicted=("yhat", "sum"),
            lower=("yhat_lower", "sum"),
            upper=("yhat_upper", "sum")
        ).reset_index()
        monthly["month"] = monthly["month"].astype(str)
        monthly["predicted"] = monthly["predicted"].round(0).astype(int)
        monthly["lower"] = monthly["lower"].round(0).astype(int).clip(lower=0)
        monthly["upper"] = monthly["upper"].round(0).astype(int)
        # ── Generate chart ────────────────────────────────────
        fig, ax = plt.subplots(figsize=(12, 5))

        # Historical data
        ax.plot(daily["ds"], daily["y"],
                color=COLORS[0], linewidth=2, label="Historical", marker="o", markersize=4)

        # Forecast line
        future_dates = pd.to_datetime(forecast_df["ds"])
        ax.plot(future_dates, forecast_df["yhat"],
                color=COLORS[1], linewidth=2, linestyle="--", label="Forecast")

        # Confidence interval
        ax.fill_between(
            future_dates,
            forecast_df["yhat_lower"],
            forecast_df["yhat_upper"],
            color=COLORS[1], alpha=0.15, label="Confidence interval"
        )

        # Divider line between historical and forecast
        ax.axvline(x=daily["ds"].max(), color="#CCCCCC",
                   linestyle=":", linewidth=1.5, label="Forecast start")

        # Styling
        ax.set_title(f"{value_col.title()} Forecast — Next {periods} Days",
                     fontsize=14, fontweight="bold", pad=14, color="#222222")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#CCCCCC")
        ax.spines["bottom"].set_color("#CCCCCC")
        ax.tick_params(colors="#555555", labelsize=9)
        ax.yaxis.grid(True, linestyle="--", alpha=0.4, color="#DDDDDD")
        ax.set_axisbelow(True)
        ax.legend(fontsize=10, framealpha=0.5)
        plt.xticks(rotation=30)
        plt.tight_layout()

        chart_path = os.path.join(OUTPUT_DIR, f"forecast_{value_col}.png")
        plt.savefig(chart_path, dpi=150, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        plt.close()

        return json.dumps({
            "status":      "success",
            "chart_path":  chart_path,
            "monthly_forecast": monthly.to_dict(orient="records"),
            "message": f"Forecast complete. Predicted {periods} days ahead.",
            "last_historical_date": daily["ds"].max().strftime("%Y-%m-%d"),
            "forecast_summary": monthly[["month", "predicted"]].to_dict(orient="records")
        })

    except Exception:
        plt.close()
        return json.dumps({
            "status":  "error",
            "message": traceback.format_exc()
        })