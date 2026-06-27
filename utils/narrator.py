from utils.llm_client import chat

NARRATOR_SYSTEM = """You are a senior data analyst writing an executive insight report.

You will be given:
- The original question asked by the user
- The raw analysis results (numbers, tables, aggregations)
- Whether a chart was generated and its filename

Write a concise, professional insight report with exactly these four sections:

## 📌 Summary
One sentence answer to the question directly.

## 📊 Key Numbers
Bullet points of the most important figures from the analysis.
Format numbers clearly (e.g. ₹82,45,000 not 8245000).

## 💡 Insight
2-3 sentences interpreting what the numbers mean for the business.
Point out trends, outliers, or comparisons worth noting.

## ✅ Recommendation
One actionable recommendation based on the data.

Keep the entire report under 200 words. Be specific, not generic.
"""


def generate_narrative(
    question: str,
    agent_answer: str,
    trace_steps: list,
    charts: list
) -> str:

    observations = []
    for step in trace_steps:
        if step["type"] == "observation":
            observations.append(step["content"])

    chart_info = (
        f"A chart was generated and saved as: {', '.join(charts)}"
        if charts else
        "No chart was generated."
    )

    narrator_prompt = f"""
Question asked: {question}

Raw analysis results from the agent:
{agent_answer}

Key observations from tool calls:
{chr(10).join(f'- {o[:300]}' for o in observations[-4:])}

Chart status: {chart_info}

Now write the structured insight report.
"""

    messages = [
        {"role": "system", "content": NARRATOR_SYSTEM},
        {"role": "user",   "content": narrator_prompt}
    ]

    response = chat(messages, use_narrator=True)
    return response.choices[0].message.content