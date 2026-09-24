"""
マルチエージェントレビューサービス
"""
import time
from typing import Dict, Any, List
from app.services.gemini_client import GeminiClient
from app.services.review_prompts import (
    AGENT_A_INSTRUCTION as SHARED_AGENT_A_INSTRUCTION,
    AGENT_B_INSTRUCTION as SHARED_AGENT_B_INSTRUCTION,
    build_agent_a_prompt,
    build_agent_b_prompt,
)
from app.logger import get_logger

logger = get_logger(__name__)


class MultiAgentReviewer:
    """Agent A（書類生成）とAgent B（倫理審査委員）の2回応酬を制御"""
    
    AGENT_A_INSTRUCTION = SHARED_AGENT_A_INSTRUCTION
    AGENT_B_INSTRUCTION = SHARED_AGENT_B_INSTRUCTION

    def __init__(self, client: GeminiClient):
        self.client = client
    
    async def _agent_b_review(
        self, 
        form_data: Dict[str, Any], 
        research_plan: str
    ) -> Dict[str, Any]:
        """Agent B: 倫理審査委員としてレビュー"""
        logger.info("Agent B (審査委員): レビュー開始")
        start_time = time.time()
        
        prompt = build_agent_b_prompt(form_data, research_plan)

        result = await self.client.generate_json(prompt, self.AGENT_B_INSTRUCTION)
        elapsed = time.time() - start_time
        issues = result.get("issues", [])
        logger.info(f"Agent B (審査委員): レビュー完了 ({elapsed:.2f}秒)")
        logger.info(f"  指摘件数: {len(issues)}")
        for issue in issues[:3]:  # 最初の3件のみログ出力
            logger.info(f"  - [{issue.get('severity', 'N/A')}] {issue.get('category', 'N/A')}: {issue.get('description', '')[:50]}...")
        return result
    
    async def _agent_a_revise(
        self,
        form_data: Dict[str, Any],
        issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Agent A: 指摘を反映して修正"""
        logger.info(f"Agent A (起案者): 修正開始 (指摘: {len(issues)}件)")
        start_time = time.time()
        
        prompt = build_agent_a_prompt(form_data, issues)

        result = await self.client.generate_json(prompt, self.AGENT_A_INSTRUCTION)
        elapsed = time.time() - start_time
        logger.info(f"Agent A (起案者): 修正完了 ({elapsed:.2f}秒)")
        return result
    
    async def run_full_review(
        self,
        form_data: Dict[str, Any],
        research_plan: str
    ) -> Dict[str, Any]:
        """2回応酬の完全レビューを実行"""
        logger.info("=" * 60)
        logger.info("マルチエージェントレビュー 開始 (2ラウンド)")
        total_start = time.time()
        all_issues = []
        
        # Round 1
        logger.info("-" * 40)
        logger.info("[ラウンド 1/2] 開始")
        round1_review = await self._agent_b_review(form_data, research_plan)
        all_issues.extend(round1_review.get("issues", []))
        revised_data = await self._agent_a_revise(form_data, round1_review.get("issues", []))
        logger.info(f"[ラウンド 1/2] 完了 (累計指摘: {len(all_issues)}件)")
        
        # Round 2
        logger.info("-" * 40)
        logger.info("[ラウンド 2/2] 開始")
        round2_review = await self._agent_b_review(revised_data, research_plan)
        all_issues.extend(round2_review.get("issues", []))
        final_data = await self._agent_a_revise(revised_data, round2_review.get("issues", []))
        logger.info(f"[ラウンド 2/2] 完了 (累計指摘: {len(all_issues)}件)")
        
        total_elapsed = time.time() - total_start
        logger.info("-" * 40)
        logger.info(f"マルチエージェントレビュー 完了 (合計: {total_elapsed:.2f}秒, 指摘: {len(all_issues)}件)")
        logger.info("=" * 60)
        
        return {
            "status": "completed",
            "round": 2,
            "issues": all_issues,
            "revised_data": final_data,
            "summary": round2_review.get("summary", "レビュー完了")
        }
