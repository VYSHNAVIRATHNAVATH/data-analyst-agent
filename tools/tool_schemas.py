TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "load_csv",
            "description": (
                "Load a CSV file from disk into memory. "
                "Always call this first before any analysis. "
                "Returns column names, data types, row count, and a 3-row preview."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the CSV file, e.g. data/sales_data.csv"
                    }
                },
                "required": ["filepath"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "execute_code",
            "description": (
                "Execute Python/pandas code to analyze the loaded dataframe. "
                "The dataframe is available as `df`. "
                "ALWAYS set `result = ...` at the end to capture output. "
                "Use this for filtering, grouping, aggregating, statistics, calculations. "
                "WARNING: This tool only accepts ONE argument: code. "
                "Do NOT pass filename or any other argument to this tool."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": (
                            "Valid Python code using pandas. "
                            "The dataframe is available as `df`. "
                            "The final line MUST assign output to `result`."
                        )
                    }
                },
                "required": ["code"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "generate_chart",
            "description": (
                "Generate a styled matplotlib chart and save as PNG. "
                "Variables available inside your code: df (DataFrame), plt, ax, fig, COLORS (list), apply_style(ax, title). "
                "NEVER call plt.figure() or plt.subplots() — ax and fig are pre-created. "
                "NEVER call plt.show(). "
                "Always call apply_style(ax, 'Your Chart Title') at the end of your code. "
                "Example bar chart: ax.bar(x, y, color=COLORS[:len(x)]); apply_style(ax, 'Title')"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": (
                            "Matplotlib code. ax and fig are pre-created. "
                            "Use ax.bar(), ax.plot(), ax.scatter(), ax.pie(), ax.hist() etc. "
                            "You may use COLORS for consistent styling. "
                            "Always finish with apply_style(ax, 'descriptive title')."
                        )
                    },
                    "filename": {
                        "type": "string",
                        "description": (
                            "PNG filename to save the chart, e.g. revenue_by_category.png. "
                            "Use snake_case and .png extension."
                        )
                    }
                },
                "required": ["code"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "forecast",
            "description": (
                "Forecast future values using Facebook Prophet time-series forecasting. "
                "Use this when the user asks about predictions, future trends, or forecasts. "
                "Automatically computes revenue = units_sold * unit_price if needed. "
                "Returns monthly forecast numbers and saves a forecast chart PNG. "
                "Always call load_csv first before using this tool."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "periods": {
                        "type": "integer",
                        "description": "Number of days to forecast ahead. Default 90 for ~3 months."
                    },
                    "date_col": {
                        "type": "string",
                        "description": "Name of the date column. Default: 'date'"
                    },
                    "value_col": {
                        "type": "string",
                        "description": "Column to forecast. Use 'revenue' for revenue forecasting, 'units_sold' for units. Default: 'revenue'"
                    },
                    "freq": {
                        "type": "string",
                        "description": "Frequency of forecast. Use 'D' for daily, 'W' for weekly, 'M' for monthly. Default: 'D'"
                    }
                },
                "required": []
            }
        }
    }
]