import os

from anthropic import Anthropic

_client: Anthropic | None = None

MODEL = os.environ.get("MOGUMI_CLAUDE_MODEL", "claude-sonnet-5")

# 100万トークンあたりの価格(USD)。https://docs.claude.com/en/docs/about-claude/pricing (2026-06時点)
MODEL_PRICING_PER_MTOK = {
    "claude-sonnet-5": {"input": 2.00, "output": 10.00},
    "claude-opus-5": {"input": 5.00, "output": 25.00},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
}

MENU_PROPOSAL_TOOL = {
    "name": "propose_menu",
    "description": "提案する献立全体(複数品)を構造化データとして返す",
    "input_schema": {
        "type": "object",
        "properties": {
            "dishes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "role": {"type": "string", "description": "主菜/副菜/汁物 など"},
                    },
                    "required": ["name", "role"],
                },
            },
            "timeline": {
                "type": "array",
                "description": "献立全体を通した調理タイムライン(手順)",
                "items": {
                    "type": "object",
                    "properties": {
                        "step": {"type": "integer"},
                        "dish": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["step", "dish", "description"],
                },
            },
            "nutrition_per_serving": {
                "type": "object",
                "properties": {
                    "calories_kcal": {"type": "number"},
                    "protein_g": {"type": "number"},
                    "fat_g": {"type": "number"},
                    "carb_g": {"type": "number"},
                },
            },
            "estimated_cost_yen_per_serving": {"type": "number"},
            "tags": {
                "type": "object",
                "properties": {
                    "protein": {"type": "array", "items": {"type": "string"}},
                    "cuisine": {"type": "array", "items": {"type": "string"}},
                    "cooking_method": {"type": "array", "items": {"type": "string"}},
                    "style": {"type": "array", "items": {"type": "string"}},
                },
            },
            "reasoning": {
                "type": "string",
                "description": "冷蔵庫の在庫・直近の献立との被り回避・ユーザーの希望をどう反映したかの説明",
            },
        },
        "required": ["dishes", "timeline", "nutrition_per_serving", "tags", "reasoning"],
    },
}


def get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def _cost_usd(usage) -> float | None:
    pricing = MODEL_PRICING_PER_MTOK.get(MODEL)
    if pricing is None:
        return None
    return (
        usage.input_tokens * pricing["input"] + usage.output_tokens * pricing["output"]
    ) / 1_000_000


def _print_usage(usage, cost_usd: float | None) -> None:
    if cost_usd is None:
        print(
            f"[mogumi] Claude API使用量: input={usage.input_tokens} "
            f"output={usage.output_tokens} tokens(料金表未登録のモデルのため費用は算出せず)"
        )
        return
    print(
        f"[mogumi] Claude API使用量: input={usage.input_tokens} output={usage.output_tokens} "
        f"tokens, 今回の費用 ≈ ${cost_usd:.4f}"
    )


def propose_menu(prompt: str) -> tuple[dict, dict]:
    """献立提案データと、今回のAPI呼び出しの使用量({input_tokens, output_tokens, cost_usd})を返す。"""
    client = get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        tools=[MENU_PROPOSAL_TOOL],
        tool_choice={"type": "tool", "name": "propose_menu"},
        messages=[{"role": "user", "content": prompt}],
    )
    usage = response.usage
    cost_usd = _cost_usd(usage)
    _print_usage(usage, cost_usd)
    usage_info = {
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cost_usd": cost_usd,
    }
    for block in response.content:
        if block.type == "tool_use" and block.name == "propose_menu":
            return block.input, usage_info
    raise RuntimeError("Claude did not return a propose_menu tool call")
