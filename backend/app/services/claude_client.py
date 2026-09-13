import os

from anthropic import Anthropic

_client: Anthropic | None = None

MODEL = os.environ.get("MOGUMI_CLAUDE_MODEL", "claude-sonnet-5")

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


def propose_menu(prompt: str) -> dict:
    client = get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        tools=[MENU_PROPOSAL_TOOL],
        tool_choice={"type": "tool", "name": "propose_menu"},
        messages=[{"role": "user", "content": prompt}],
    )
    for block in response.content:
        if block.type == "tool_use" and block.name == "propose_menu":
            return block.input
    raise RuntimeError("Claude did not return a propose_menu tool call")
