from __future__ import annotations

SYSTEM_PROMPT = (
    "You are an expert financial market analyst. "
    "Analyze the given news item and output ONLY a JSON object. "
    "No preamble, no explanation, no markdown fences."
)

USER_TEMPLATE = """
Portfolio context: {portfolio_context}

News headline : {title}
News content  : {content}
Published at  : {pub_time}
Source        : {source}

Output the following JSON with ALL fields filled in:
{{
  "score"          : <integer 1-10, market impact>,
  "sentiment"      : "<bullish|bearish|neutral>",
  "summary"        : "<one sentence, max 30 words>",
  "reasoning"      : "<why bullish/bearish/neutral, 50-100 words>",
  "suggestion"     : "<trade action suggestion with confidence H/M/L, max 50 words>",
  "portfolio_note" : "<how this news affects the user positions, or null>"
}}

Scoring guide: 1-3 minor, 4-6 sector-moving, 7-8 index-moving, 9-10 black-swan.
Output ONLY the JSON object.
"""


def build_prompt(title, content, pub_time, source, positions=None, language="zh"):
    if positions:
        pos_str = ", ".join(
            f"{p['ticker']}({p.get('name', p['ticker'])}) qty={p.get('quantity', 0)}"
            for p in positions
        )
    else:
        pos_str = "None"

    return USER_TEMPLATE.format(
        title=title,
        content=content or title,
        pub_time=pub_time,
        source=source,
        portfolio_context=pos_str,
    )
