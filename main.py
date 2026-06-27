import json
import groq as groq_module
from utils.llm_client import chat
from tools.tool_schemas import TOOL_SCHEMAS
from tools.csv_loader import load_csv
from tools.code_executor import execute_code
from tools.chart_generator import generate_chart
from utils.narrator import generate_narrative
from tools.forecaster import forecast

TOOL_REGISTRY = {
    "load_csv":       load_csv,
    "execute_code":   execute_code,
    "generate_chart": generate_chart,
    "forecast":       forecast,
}

SYSTEM_PROMPT = """You are a Data Analyst Agent. Use ReAct: Thought then Action.
IMPORTANT: Never write plans or outlines. Always immediately call a tool after each Thought. If you know what to do, DO IT — call the tool now.

Tools:
1. load_csv(filepath) — call FIRST always
2. execute_code(code) — pandas code, always end with result=...
3. generate_chart(code, filename) — matplotlib, use ax/fig/COLORS/apply_style, no plt.show()
4. forecast(periods, date_col, value_col, freq) — Prophet forecasting for future predictions

Rules:
- The dataframe is already loaded as `df` — NEVER use pd.read_csv() or import statements
- Always compute revenue first: df['revenue'] = df['units_sold'] * df['unit_price']
- Always end execute_code with result = ...
- Use simple groupby: df.groupby('col')['col2'].sum() — never use .apply() with lambda
- CRITICAL: generate_chart code MUST recompute all data from df from scratch
- CRITICAL: Never call plt.savefig(), plt.show(), plt.figure(), plt.subplots() in generate_chart
- CRITICAL: Always call apply_style(ax, 'title') as the last line in generate_chart
- Use forecast tool when user asks about predictions, future trends, or next N months
- Final answer must include: ## Key Findings, ## Numbers, ## Insight

Example of correct generate_chart code:
df['revenue'] = df['units_sold'] * df['unit_price']
data = df.groupby('sales_rep')['revenue'].sum()
ax.bar(data.index, data.values, color=COLORS[:len(data)])
apply_style(ax, 'Revenue by Sales Rep')"""
class AgentTrace:
    def __init__(self):
        self.steps = []

    def add_step(self, step_type: str, content: str,
                 tool_name: str = None, tool_args: dict = None):
        step = {
            "step":      len(self.steps) + 1,
            "type":      step_type,
            "content":   content,
            "tool_name": tool_name,
            "tool_args": tool_args or {},
        }
        self.steps.append(step)
        self._print_step(step)

    def _print_step(self, step: dict):
        icons = {
            "thought":     "🧠 THOUGHT",
            "action":      "🔧 ACTION",
            "observation": "👁️  OBSERVATION",
            "answer":      "✅ FINAL ANSWER",
            "error":       "❌ ERROR",
        }
        label = icons.get(step["type"], step["type"].upper())
        print(f"\n[Step {step['step']}] {label}")
        if step["tool_name"]:
            print(f"  Tool: {step['tool_name']}")
        if step["tool_args"]:
            for k, v in step["tool_args"].items():
                if k == "code":
                    for line in v.strip().split("\n"):
                        print(f"    {line}")
                else:
                    print(f"  {k}: {v}")
        print(f"  {step['content'][:400]}")


def extract_thought(content: str, trace: AgentTrace):
    if not content:
        return
    for line in content.split("\n"):
        line = line.strip()
        if line.lower().startswith("thought:"):
            thought = line[len("thought:"):].strip()
            if thought:
                trace.add_step("thought", thought)
            return
    if content.strip():
        trace.add_step("thought", content.strip()[:300])


def _trim(tool_result: str) -> str:
    """Trim tool result before adding to message history to save tokens."""
    try:
        data = json.loads(tool_result)
        if "preview" in data:
            data.pop("preview", None)
            data.pop("null_counts", None)
            return json.dumps(data)
        if "output" in data and len(str(data["output"])) > 600:
            data["output"] = str(data["output"])[:600] + "...[truncated]"
            return json.dumps(data)
        return tool_result
    except Exception:
        return tool_result[:800]


def run_agent(user_question: str, csv_path: str = "data/sales_data.csv") -> dict:
    print(f"\n{'='*60}")
    print(f"❓ QUESTION: {user_question}")
    print(f"{'='*60}")

    trace          = AgentTrace()
    charts         = []
    error_count    = 0
    MAX_ERRORS     = 3
    MAX_ITERATIONS = 10

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"CSV file is at: {csv_path}\n\n"
            f"Question: {user_question}\n\n"
            f"Start with Thought, then call load_csv first."
        )}
    ]

    for iteration in range(1, MAX_ITERATIONS + 1):

        # Force a tool call on iteration 1 so the model
        # can't write a Thought and skip straight to a final answer
        forced = "required" if iteration == 1 else "auto"

        try:
            response = chat(messages, tools=TOOL_SCHEMAS, tool_choice=forced)

        except groq_module.BadRequestError as e:
            print(f"\n⚠️  Bad request on iteration {iteration}: {e}")
            messages.append({
                "role": "user",
                "content": (
                    "Your last tool call was malformed. "
                    "Retry and include ALL required arguments, "
                    "especially 'filename' for generate_chart."
                )
            })
            try:
                response = chat(messages, tools=TOOL_SCHEMAS, tool_choice="auto")
            except Exception as e2:
                trace.add_step("error", f"Retry also failed: {str(e2)[:200]}")
                break

        except Exception as e:
            trace.add_step("error", f"API error: {str(e)[:200]}")
            break

        message = response.choices[0].message

        # ── Agent calls a tool ────────────────────────────────
        if message.tool_calls:
            extract_thought(message.content, trace)

            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name":      tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                trace.add_step("action", f"Calling {tool_name}",
                               tool_name=tool_name, tool_args=tool_args)

                tool_fn     = TOOL_REGISTRY.get(tool_name)
                tool_result = (
                    tool_fn(**tool_args) if tool_fn
                    else json.dumps({"status": "error",
                                     "message": f"Unknown tool: {tool_name}"})
                )

                try:
                    rd = json.loads(tool_result)
                    if rd.get("status") == "error":
                        error_count += 1
                        trace.add_step("error", rd.get("message", "")[:300])
                    else:
                        error_count = 0
                        preview = (tool_result[:350] + "..."
                                   if len(tool_result) > 350 else tool_result)
                        trace.add_step("observation", preview)
                    if "chart_path" in rd:
                        charts.append(rd["chart_path"])
                except Exception:
                    pass

                messages.append({
                    "role":         "tool",
                    "tool_call_id": tool_call.id,
                    "content":      _trim(tool_result)
                })

            if error_count >= MAX_ERRORS:
                trace.add_step("error",
                               f"Aborting: {MAX_ERRORS} consecutive tool errors.")
                break

        # ── Agent gives final answer ──────────────────────────
        else:
            final_answer = message.content
            trace.add_step("answer", final_answer)

            print("\n🗣️  Generating insight narrative...")
            narrative = generate_narrative(
                question=user_question,
                agent_answer=final_answer,
                trace_steps=trace.steps,
                charts=charts
            )

            print(f"\n{'='*60}\n📝 INSIGHT REPORT\n{'='*60}")
            print(narrative)
            print(f"{'='*60}")
            print(f"\n📊 Charts : {charts if charts else 'None'}")
            print(f"🔁 Iterations: {iteration}")

            return {
                "answer":     final_answer,
                "narrative":  narrative,
                "charts":     charts,
                "iterations": iteration,
                "trace":      trace.steps,
            }

    return {
        "answer":     "Agent could not complete within iteration limit.",
        "narrative":  "",
        "charts":     charts,
        "iterations": MAX_ITERATIONS,
        "trace":      trace.steps,
    }


if __name__ == "__main__":
    questions = [
        "Which product category had the highest total revenue in 2024?",
        "Who is the top performing sales rep by revenue?",
        "Show monthly revenue trend for 2023 vs 2024",
        "Predict revenue for the next 3 months",
        "Which region has the highest units sold?",
    ]
    for q in questions:
        result = run_agent(q)
        print(f"\nNarrative preview:\n{result['narrative'][:300]}\n")
        print("─" * 60)