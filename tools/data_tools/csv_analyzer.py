"""data_tools — CSV analyzer and chart generator."""

from __future__ import annotations
import io
from typing import Any, Dict, Optional

import pandas as pd

from core.tool_registry import BaseTool, register_tool


# ── 1. CSV Analyzer ───────────────────────────────────────────────────────────

@register_tool(
    name="csv",
    display_name="📊 CSV Analyzer",
    category="data_tools",
    description="Analyze CSV files and generate statistics",
    keywords=["csv", "data", "spreadsheet", "statistics", "analyze", "dataset", "columns"],
    input_type="file",
)
class CSVAnalyzerTool(BaseTool):

    def run(self, file: bytes = None, filename: str = "data.csv", **kwargs) -> dict:
        if file is None:
            return {"success": False, "result": "❌ No file provided."}
        try:
            df = pd.read_csv(io.BytesIO(file))
        except Exception as e:
            return {"success": False, "result": f"❌ Could not parse CSV: {e}"}

        rows, cols = df.shape
        num_cols  = df.select_dtypes(include="number").columns.tolist()
        text_cols = df.select_dtypes(include="object").columns.tolist()
        missing   = int(df.isnull().sum().sum())
        dup_rows  = int(df.duplicated().sum())

        lines = [
            f"📊 **CSV Analysis: `{filename}`**\n",
            f"**Shape:** {rows:,} rows × {cols} columns",
            f"**Missing values:** {missing}",
            f"**Duplicate rows:** {dup_rows}",
            f"**Numeric columns ({len(num_cols)}):** {', '.join(num_cols) or 'None'}",
            f"**Text columns ({len(text_cols)}):** {', '.join(text_cols) or 'None'}",
            "",
            "**Numeric Statistics:**",
        ]
        stats: Dict[str, Any] = {}
        if num_cols:
            desc = df[num_cols].describe().round(3)
            for col in num_cols:
                s = desc[col]
                lines.append(
                    f"• **{col}**: min={s['min']}, max={s['max']}, "
                    f"mean={s['mean']:.3f}, std={s['std']:.3f}, median={s['50%']}"
                )
                stats[col] = {"min": s["min"], "max": s["max"],
                              "mean": round(s["mean"], 3), "std": round(s["std"], 3)}
        else:
            lines.append("• No numeric columns found.")

        # Top-value counts for text columns
        if text_cols:
            lines.append("\n**Top values (text columns):**")
            for col in text_cols[:3]:
                top = df[col].value_counts().head(3)
                top_str = ", ".join(f"`{v}` ({c})" for v, c in top.items())
                lines.append(f"• **{col}**: {top_str}")

        return {
            "success": True,
            "result": "\n".join(lines),
            "shape": [rows, cols],
            "columns": list(df.columns),
            "numeric_columns": num_cols,
            "stats": stats,
            "dataframe": df,   # available for in-process workflow steps
        }


# ── 2. Chart Generator ────────────────────────────────────────────────────────

@register_tool(
    name="chart",
    display_name="📈 Chart Generator",
    category="data_tools",
    description="Generate charts from data (used in multi-step workflows)",
    keywords=["chart", "plot", "graph", "visualize", "bar", "line", "histogram"],
    input_type="form",
)
class ChartGeneratorTool(BaseTool):
    """
    Generates a Plotly figure dict from a DataFrame or dict of series data.
    Intended for use inside the Workflow Engine; the Streamlit UI renders
    the returned figure with st.plotly_chart().
    """

    def run(
        self,
        data: Optional[Any] = None,          # pd.DataFrame or dict
        chart_type: str = "bar",
        x_col: str = "",
        y_col: str = "",
        title: str = "Chart",
        **kwargs,
    ) -> dict:
        try:
            import plotly.express as px
        except ImportError:
            return {"success": False, "result": "❌ plotly not installed. Run: pip install plotly"}

        if data is None:
            return {"success": False, "result": "❌ No data provided."}

        # Accept DataFrame or plain dict
        if isinstance(data, dict):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            return {"success": False, "result": "❌ data must be a DataFrame or dict."}

        if df.empty:
            return {"success": False, "result": "❌ Data is empty."}

        num_cols = df.select_dtypes(include="number").columns.tolist()
        if not num_cols:
            return {"success": False, "result": "❌ No numeric columns to chart."}

        y = y_col if y_col in df.columns else num_cols[0]
        x = x_col if x_col in df.columns else df.index.astype(str)

        chart_map = {
            "bar":       px.bar,
            "line":      px.line,
            "scatter":   px.scatter,
            "histogram": lambda df, x, y, **kw: px.histogram(df, x=y, **kw),
            "box":       px.box,
        }
        fn = chart_map.get(chart_type, px.bar)

        try:
            if chart_type == "histogram":
                fig = fn(df, x=x, y=y, title=title)
            else:
                fig = fn(df, x=x, y=y, title=title)
            return {
                "success": True,
                "result": f"📈 Chart generated: **{title}** ({chart_type})",
                "figure": fig,
            }
        except Exception as e:
            return {"success": False, "result": f"❌ Chart error: {e}"}