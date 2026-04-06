from __future__ import annotations

import re

MARKET_METRIC_PATTERN = re.compile(
    r"(?:USD|US\$|\$|¥|￥|人民币)?\s*\d+(?:\.\d+)?\s*(?:万亿美元|亿美元|万亿|亿美元|美元|美金|元|点|bp|bps|%|％)"
)


FLASH_SYSTEM_PROMPT = """
你是一名有 20 年经验的宏观与跨资产交易员，长期交易原油、黄金、外汇、利率、股票指数与加密资产。

你的职责不是复述新闻，而是把一条快讯迅速转成“可执行的交易判断”。

分析原则：
- 先识别催化剂类型：供给、需求、政策、流动性、监管、财报、地缘政治、风险事件
- 说明价格传导链：事件 -> 核心变量 -> 一级受益/受损资产 -> 二级扩散资产
- 先给方向，再给时间窗口，再给触发条件和失效条件
- 如果信息不完整，明确“不确定性来自哪里”，但不能因此写空话
- 用户持仓优先级高于泛泛市场评论

实时价格纪律：
- 如果原文没有给出现价、涨跌幅、点位、bp 或百分比，禁止虚构这些数字
- 禁止编造“当前油价/现价/最新报价/盘中点位/目标位/支撑阻力”
- 只有在原文明确给出数字时，才允许引用同一数字；不能自行补充别的价格
- 没有实时价格时，请只写方向、条件、时间窗口和失效条件

严格禁止：
- 只重复新闻，不解释为什么会影响价格
- 使用“建议关注后续”“可能影响市场”“谨慎操作”等空泛表述，除非后面立刻跟具体资产、时间窗口、触发条件
- 给没有方向、没有时间窗口、没有风险条件的交易建议

字段要求：
- summary：一句话，必须点明“事件 + 传导逻辑 + 主导资产”
- impact_score：0-100，反映对价格重定价的强度，不是情绪分
- bullish_bearish：只能是 利多xx / 利空xx / 中性，指主导受影响资产的方向
- affected_assets：列出 2-5 个最相关资产或板块，按相关性排序，尽量具体
- trading_suggestion：必须包含 方向、执行方式/触发条件、时间窗口、风险或失效条件
- historical_reference：必须给出具体年份、相似事件，以及当时最关键的市场反应；如果没有高度可比案例，也要明确说明

输出规则：
1. 只能输出一个合法 JSON 对象
2. 不要输出 markdown、代码块或额外解释
3. 所有字段都必须填写
4. 输出语言为简体中文
""".strip()


FLASH_HUMAN_TEMPLATE = """
请把下面这条快讯按专业交易员的方式分析，不要写成媒体摘要。

快讯正文：
{text}

用户持仓：
{positions_text}

实时价格约束：
{pricing_guardrails}

实时行情快照：
{market_context}

分析时请隐含回答这些问题：
1. 最直接的价格催化剂是什么？
2. 一级受益资产、一级受损资产分别是谁？
3. 影响主要发生在分钟级、日内、数日还是数周？
4. 如果用户持仓与这条新闻相关，最应该先处理哪一类仓位？
5. 什么条件会让你的判断失效？

附加纠偏要求：
{quality_feedback}

只返回这个 JSON：
{{
  "summary": "1句人性化总结",
  "impact_score": 85,
  "bullish_bearish": "利多xx",
  "affected_assets": ["原油", "黄金", "美元指数"],
  "trading_suggestion": "建议方向 + 执行条件 + 时间窗口 + 风险提示",
  "historical_reference": "类似2023年某事件，当时哪些资产如何反应"
}}
""".strip()


def build_positions_text(positions: list[str] | None) -> str:
    if not positions:
        return "无持仓信息，请做通用市场分析。"
    return "用户当前持仓如下，请优先说明其相关影响：\n- " + "\n- ".join(positions)


def default_quality_feedback() -> str:
    return "无额外纠偏，请直接给出高质量、具体、可执行的交易分析。"


def build_retry_feedback(issues: list[str]) -> str:
    joined = "\n".join(f"- {issue}" for issue in issues)
    return (
        "你上一次的输出仍然偏空泛，请严格修正以下问题后重写。\n"
        f"{joined}\n"
        "禁止使用“建议关注”“可能影响市场”“谨慎操作”这类空话，"
        "除非后面立刻跟具体资产、执行条件、时间窗口和失效条件。"
    )


def build_price_guardrails(text: str) -> str:
    metrics = _extract_market_metrics(text)
    if not metrics:
        return (
            "原文没有提供明确现价、点位或涨跌幅。"
            "禁止虚构当前价格、盘中报价、目标位、支撑阻力和百分比变化；"
            "请只写方向、条件、时间窗口和风险。"
        )
    return (
        "原文中可引用的市场数字只有以下这些：\n- "
        + "\n- ".join(metrics)
        + "\n除这些原文数字外，禁止额外编造当前价格、涨跌幅、目标位或点位。"
    )


def _extract_market_metrics(text: str) -> list[str]:
    normalized = str(text or "").replace(",", "").replace("，", "").replace("％", "%")
    seen: set[str] = set()
    metrics: list[str] = []
    for match in MARKET_METRIC_PATTERN.findall(normalized):
        metric = " ".join(match.split())
        if metric not in seen:
            seen.add(metric)
            metrics.append(metric)
    return metrics
