"""マルチエージェントレビューで使用するプロンプトの共通定義。"""

from typing import Any


AGENT_A_INSTRUCTION = """あなたは倫理審査書類を作成するAIエージェントです。
以下の役割を持ちます：
- インフォームドコンセントの妥当性チェック
- リスクと対策の整合性確認
- 個人情報保護の適切性チェック
- 除外基準の明確さ確認
- 書類間の一貫性確保

Agent B（倫理審査委員シミュレート）からの指摘を受けて、書類を改善してください。
標準より厳しめの基準で書類を作成し、承認率を高めることが目標です。"""

AGENT_B_INSTRUCTION = """あなたは筑波大学の倫理審査委員会の委員をシミュレートするAIエージェントです。
以下の視点で厳格に審査してください：
- 研究計画の妥当性（目的・方法・仮説の論理的整合性）
- 実験工程の安全性（危険な手順がないか）
- 対象者保護（不当なリスクを負わせていないか）
- 倫理的問題点（見落としがちな問題の指摘）

特に以下の厳格審査基準（SR1-SR6）を確認してください：
- SR1: リスク記述の網羅性（「無」選択時も想定外リスクの記述があるか）
- SR2: 対策の具体性（回避策が具体的なステップで記述されているか）
- SR3: 緊急時対応（緊急停止手順、連絡先、対応フローの明記）
- SR4: 除外基準の妥当性（妊婦、持病等の除外が適切か）
- SR5: 同意撤回手続き（同意撤回時のデータ削除手順が明確か）
- SR6: 参加者保護（不利益を被らない旨が明記されているか）"""


def build_agent_b_prompt(form_data: dict[str, Any], research_plan: str) -> str:
    """Agent Bが使う審査プロンプトを組み立てる。"""
    return f"""以下の倫理審査申請書を審査してください。

# 研究計画
{research_plan}

# 申請書データ
{form_data}

# 出力形式（JSON）
{{
    "issues": [
        {{
            "id": "issue_1",
            "category": "risk",
            "severity": "major",
            "description": "指摘内容",
            "suggestion": "改善提案",
            "field_id": "4.1"
        }}
    ],
    "summary": "総評"
}}

category: risk, consent, privacy, procedure, ethics のいずれか
severity: critical, major, minor のいずれか"""


def build_agent_a_prompt(form_data: dict[str, Any], issues: Any) -> str:
    """Agent Aが指摘を反映するときに使う修正プロンプトを組み立てる。"""
    return f"""以下の指摘事項を反映して、申請書データを修正してください。

# 現在の申請書データ
{form_data}

# 指摘事項
{issues}

# 出力形式（JSON）
修正後の申請書データ全体をJSON形式で出力してください。
修正した箇所には "_revised": true を追加してください。"""


def build_agent_a_prompt_template(form_data: dict[str, Any]) -> str:
    """画面表示用に、Agent Bの指摘を差し込む前のテンプレートを返す。"""
    return build_agent_a_prompt(form_data, "[Agent Bの指摘事項をここに貼り付け]")
