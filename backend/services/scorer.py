import logging

from backend.schemas.simulation import (
    StandardsCheckResult,
    TaskResult,
    TaskScoreEvaluation,
)
from backend.services.llm.base import LLMProvider
from backend.services.tasks.registry import TaskDefinition

logger = logging.getLogger("axo_agent.scorer")

STANDARDS_WEIGHTS = {
    "robots_txt": 0.25,
    "llms_txt": 0.15,
    "schema_org": 0.25,
    "meta_tags": 0.15,
    "agents_json": 0.10,
    "security": 0.10,
}

SCORE_EVAL_PROMPT = """\
You are an evaluator scoring how well an AI agent completed a web research task.

TASK: {task_name} — {task_display_name}
TARGET WEBSITE: {url}

AGENT'S RESULT:
- Found: {found}
- Confidence: {confidence}
- Summary: {summary}
- Findings: {findings}
- Issues: {issues}
- Tool calls used: {tool_calls}

SCORING CRITERIA:
- found_score (0-40): Did the agent actually find the requested information? 0 if not found, 40 if clearly found with specific data.
- confidence_score (0-25): How reliable and specific is the data? Vague/generic = low. Exact numbers/names/URLs = high.
- accessibility_score (0-20): How easy was it to locate? 20 = found on first page. 0 = required max steps or failed completely. Consider tool_calls used: 1-2 calls = 20, 3 = 15, 4 = 10, 5 = 5.
- data_quality_score (0-15): How complete and actionable is the extracted data? Empty = 0. Partial = 5-10. Comprehensive = 15.

IMPORTANT:
- Score based ONLY on what the agent actually reported. Do not use your own knowledge.
- If the agent says "NOT FOUND", found_score MUST be 0.
- Be strict — vague summaries without specific data should score low on quality.
"""


class Scorer:
    """Hybrid scorer — LLM evaluates task results, deterministic for standards."""

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def score_task(
        self, task: TaskDefinition, worker_result: dict, url: str
    ) -> TaskResult:
        """Use LLM to evaluate the quality of a task result."""
        output = worker_result.get("output", {})
        tool_calls = worker_result.get("tool_call_count", 0)
        success = worker_result.get("success", False)

        if not success:
            return TaskResult(
                task_name=task.name,
                found=False,
                confidence=0,
                accessibility=0,
                data_quality=0,
                score=0,
                findings=[],
                issues=output.get("issues", ["Agent failed to complete task"]),
                steps_taken=tool_calls,
                raw_data=worker_result,
            )

        found = output.get("found", False)
        findings_list = output.get("findings", [])
        issues_list = output.get("issues", [])
        summary = output.get("summary", "")
        confidence_str = output.get("confidence", "none")

        # Format findings for the evaluation prompt
        findings_text = "\n".join(
            f"  - {f.get('content', f) if isinstance(f, dict) else str(f)}"
            for f in findings_list
        ) or "  (none)"

        issues_text = "\n".join(
            f"  - {i}" for i in issues_list
        ) or "  (none)"

        eval_prompt = SCORE_EVAL_PROMPT.format(
            task_name=task.name,
            task_display_name=task.display_name,
            url=url,
            found=found,
            confidence=confidence_str,
            summary=summary,
            findings=findings_text,
            issues=issues_text,
            tool_calls=tool_calls,
        )

        # Ask LLM to score with structured output
        try:
            scored_llm = self.llm.with_structured_output(TaskScoreEvaluation)
            evaluation: TaskScoreEvaluation = await scored_llm.ainvoke(eval_prompt)

            found_score = max(0, min(40, evaluation.found_score))
            confidence_score = max(0, min(25, evaluation.confidence_score))
            accessibility_score = max(0, min(20, evaluation.accessibility_score))
            quality_score = max(0, min(15, evaluation.data_quality_score))

        except Exception as e:
            logger.warning(f"LLM scoring failed for {task.name}, using fallback: {e}")
            # Fallback to simple heuristic if LLM fails
            found_score = 40 if found else 0
            confidence_score = {"high": 25, "medium": 15, "low": 5}.get(confidence_str, 0)
            accessibility_score = max(0, 20 - (tool_calls * 4))
            quality_score = min(15, len(findings_list) * 5)

        total = found_score + confidence_score + accessibility_score + quality_score

        finding_strings = [
            f.get("content", str(f)) if isinstance(f, dict) else str(f)
            for f in findings_list
        ]

        return TaskResult(
            task_name=task.name,
            found=found,
            confidence=confidence_score,
            accessibility=accessibility_score,
            data_quality=quality_score,
            score=min(total, 100),
            findings=finding_strings,
            issues=issues_list,
            steps_taken=tool_calls,
            raw_data=worker_result,
        )

    def calculate_standards_score(
        self, checks: list[StandardsCheckResult]
    ) -> float:
        """Weighted average of standards checks. Deterministic — no LLM."""
        if not checks:
            return 0.0
        total = 0.0
        weight_sum = 0.0
        for check in checks:
            w = STANDARDS_WEIGHTS.get(check.check_name, 0.1)
            total += check.score * w
            weight_sum += w
        return round(total / weight_sum, 1) if weight_sum > 0 else 0.0

    def calculate_overall(
        self,
        task_results: list[TaskResult],
        standards_results: list[StandardsCheckResult],
        task_definitions: list[TaskDefinition],
    ) -> tuple[float, str]:
        """Overall = (task_score × 0.60) + (standards_score × 0.40)."""
        task_score = 0.0
        if task_results and task_definitions:
            total_weight = sum(td.weight for td in task_definitions)
            for result in task_results:
                td = next(
                    (t for t in task_definitions if t.name == result.task_name),
                    None,
                )
                if td and total_weight > 0:
                    task_score += result.score * (td.weight / total_weight)

        standards_score = self.calculate_standards_score(standards_results)
        overall = round((task_score * 0.60) + (standards_score * 0.40), 1)

        # Bonuses
        all_found = all(r.found for r in task_results) if task_results else False
        no_blocks = not any(
            "blocked" in str(r.issues).lower() for r in task_results
        )
        if all_found:
            overall = min(100, overall + 5)
        if no_blocks and task_results:
            overall = min(100, overall + 3)

        grade = self._grade(overall)
        return overall, grade

    def generate_recommendations(
        self,
        task_results: list[TaskResult],
        standards_results: list[StandardsCheckResult],
    ) -> list[str]:
        """Generate actionable recommendations from results."""
        recs = []

        for tr in task_results:
            if not tr.found:
                recs.append(
                    f"Make {tr.task_name} information easily discoverable — "
                    f"AI agents could not find it"
                )
            if tr.score < 50 and tr.found:
                recs.append(
                    f"Improve {tr.task_name} page structure — agent found it "
                    f"but with low confidence/quality"
                )
            if tr.steps_taken >= 5:
                recs.append(
                    f"Simplify navigation to {tr.task_name} — agent needed "
                    f"maximum steps to locate it"
                )
            if "blocked" in str(tr.issues).lower():
                recs.append(
                    f"Review bot protection — agents cannot access "
                    f"{tr.task_name} content"
                )

        for sc in standards_results:
            if sc.score == 0 and sc.check_name == "llms_txt":
                recs.append(
                    "Add an llms.txt file to help AI agents understand your site"
                )
            if sc.score == 0 and sc.check_name == "agents_json":
                recs.append(
                    "Add /.well-known/agents.json to declare agent capabilities"
                )
            if sc.score < 50 and sc.check_name == "schema_org":
                recs.append(
                    "Add JSON-LD structured data (Organization, Product, FAQ) "
                    "for better AI comprehension"
                )
            if sc.score < 50 and sc.check_name == "robots_txt":
                recs.append(
                    "Add AI-specific user-agent rules to robots.txt "
                    "(GPTBot, ClaudeBot, PerplexityBot)"
                )

        if not recs:
            recs.append(
                "Site is well-structured for AI agent navigation — maintain "
                "current standards"
            )

        return recs[:10]

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 90:
            return "A"
        if score >= 75:
            return "B"
        if score >= 60:
            return "C"
        if score >= 40:
            return "D"
        return "F"
