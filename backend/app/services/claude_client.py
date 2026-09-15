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
                        "ingredients": {
                            "type": "array",
                            "description": "この品目で使う食材名のリスト(分量や切り方は不要、名前のみ)",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["name", "role", "ingredients"],
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


def _cost_usd(usage, model: str) -> float | None:
    pricing = MODEL_PRICING_PER_MTOK.get(model)
    if pricing is None:
        return None
    return (
        usage.input_tokens * pricing["input"] + usage.output_tokens * pricing["output"]
    ) / 1_000_000


def _print_usage(usage, cost_usd: float | None, label: str = "Claude API使用量") -> None:
    if cost_usd is None:
        print(
            f"[mogumi] {label}: input={usage.input_tokens} "
            f"output={usage.output_tokens} tokens(料金表未登録のモデルのため費用は算出せず)"
        )
        return
    print(
        f"[mogumi] {label}: input={usage.input_tokens} output={usage.output_tokens} "
        f"tokens, 今回の費用 ≈ ${cost_usd:.5f}"
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
    cost_usd = _cost_usd(usage, MODEL)
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


CLASSIFY_INGREDIENT_MODEL = "claude-haiku-4-5"

# 冷蔵庫・パントリー共通の食材/食品カテゴリ語彙。
# frontend/src/pages/FridgePage.tsx, PantryPage.tsx の CATEGORY_ORDER と揃えること。
CATEGORY_VOCAB = ["野菜", "肉", "魚介", "卵・乳製品", "主食", "果物", "調味料", "油", "乾物・缶詰", "その他"]

CLASSIFY_INGREDIENT_TOOL = {
    "name": "classify_ingredient",
    "description": "食材名を分類し、表記揺れ(カタカナ/漢字/送り仮名など)を吸収した正規化名を返す",
    "input_schema": {
        "type": "object",
        "properties": {
            "canonical_name": {
                "type": "string",
                "description": "表記揺れを吸収した正規化名(基本はひらがな表記。例: 人参→にんじん)",
            },
            "category": {
                "type": "string",
                "enum": CATEGORY_VOCAB,
            },
        },
        "required": ["canonical_name", "category"],
    },
}


def classify_ingredient(name: str) -> dict:
    """未知の食材名をLLMで1回だけ分類する(呼び出し側でマスターにキャッシュする想定)。"""
    client = get_client()
    response = client.messages.create(
        model=CLASSIFY_INGREDIENT_MODEL,
        max_tokens=256,
        tools=[CLASSIFY_INGREDIENT_TOOL],
        tool_choice={"type": "tool", "name": "classify_ingredient"},
        messages=[{"role": "user", "content": f"次の食材名を分類してください: {name}"}],
    )
    usage = response.usage
    cost_usd = _cost_usd(usage, CLASSIFY_INGREDIENT_MODEL)
    _print_usage(usage, cost_usd, label="食材分類API使用量")
    for block in response.content:
        if block.type == "tool_use" and block.name == "classify_ingredient":
            return block.input
    raise RuntimeError("Claude did not return a classify_ingredient tool call")


CLASSIFY_DISH_GENRE_MODEL = "claude-haiku-4-5"

# 料理のジャンル語彙。献立の被り回避判定(#24)で「カレーが続いている」等を検出するのに使う。
DISH_GENRE_VOCAB = [
    "カレー",
    "丼",
    "シチュー",
    "鍋",
    "汁物・スープ",
    "麺類",
    "炒め物",
    "揚げ物",
    "焼き物",
    "煮物",
    "サラダ",
    "ご飯もの",
    "パスタ",
    "グラタン・オーブン料理",
    "蒸し料理",
    "その他",
]

CLASSIFY_DISH_GENRE_TOOL = {
    "name": "classify_dish_genre",
    "description": "料理名を分類し、表記揺れを吸収した正規化名とざっくりしたジャンルを返す",
    "input_schema": {
        "type": "object",
        "properties": {
            "canonical_name": {
                "type": "string",
                "description": "表記揺れを吸収した正規化名(基本はそのままの料理名でよいが、余計な修飾語は削る)",
            },
            "genre": {
                "type": "string",
                "enum": DISH_GENRE_VOCAB,
                "description": "キーマカレー/バターチキンカレー/ほうれん草カレーは全て「カレー」のように、大きなくくりで分類する",
            },
        },
        "required": ["canonical_name", "genre"],
    },
}


def classify_dish_genre(dish_name: str) -> dict:
    """未知の料理名をLLMで1回だけジャンル分類する(呼び出し側でマスターにキャッシュする想定)。"""
    client = get_client()
    response = client.messages.create(
        model=CLASSIFY_DISH_GENRE_MODEL,
        max_tokens=256,
        tools=[CLASSIFY_DISH_GENRE_TOOL],
        tool_choice={"type": "tool", "name": "classify_dish_genre"},
        messages=[{"role": "user", "content": f"次の料理名をジャンル分類してください: {dish_name}"}],
    )
    usage = response.usage
    cost_usd = _cost_usd(usage, CLASSIFY_DISH_GENRE_MODEL)
    _print_usage(usage, cost_usd, label="料理ジャンル分類API使用量")
    for block in response.content:
        if block.type == "tool_use" and block.name == "classify_dish_genre":
            return block.input
    raise RuntimeError("Claude did not return a classify_dish_genre tool call")
