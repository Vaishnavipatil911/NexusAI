"""
Workflow Engine — runs multi-step pipelines where each step's output
feeds into the next step as input.

Example workflow definition:
    steps = [
        WorkflowStep(tool="csv",        params={"file": <bytes>}),
        WorkflowStep(tool="summarizer", params={}, input_key="result"),
    ]
    engine = WorkflowEngine()
    result = engine.run(steps)
"""

from __future__ import annotations
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.tool_registry import get_registry

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    tool: str                          # registered tool name
    params: Dict[str, Any] = field(default_factory=dict)
    input_key: Optional[str] = None   # key from previous step's output to inject
    output_alias: Optional[str] = None  # rename output for next step


@dataclass
class StepResult:
    tool: str
    success: bool
    result: Any
    elapsed_ms: int
    error: Optional[str] = None


@dataclass
class WorkflowResult:
    steps: List[StepResult]
    final_result: Any
    total_ms: int
    success: bool

    def summary(self) -> str:
        lines = [f"**Workflow completed in {self.total_ms}ms**\n"]
        for i, s in enumerate(self.steps, 1):
            status = "✅" if s.success else "❌"
            lines.append(f"{status} Step {i} — **{s.tool}** ({s.elapsed_ms}ms)")
            if not s.success and s.error:
                lines.append(f"   Error: {s.error}")
        lines.append("\n---\n")
        lines.append(str(self.final_result))
        return "\n".join(lines)


# ── Pre-built workflow templates ─────────────────────────────────────────────

WORKFLOW_TEMPLATES: Dict[str, List[WorkflowStep]] = {
    "csv_to_summary": [
        WorkflowStep(tool="csv",        params={},              output_alias="csv_stats"),
        WorkflowStep(tool="summarizer", params={},              input_key="result"),
    ],
    "code_and_hash": [
        WorkflowStep(tool="code",   params={},             output_alias="code_out"),
        WorkflowStep(tool="hash",   params={"algorithm": "sha256"}, input_key="result"),
    ],
}


class WorkflowEngine:
    """Executes a list of WorkflowSteps sequentially, passing outputs forward."""

    def run(self, steps: List[WorkflowStep], initial_params: Dict[str, Any] = None) -> WorkflowResult:
        registry = get_registry()
        results: List[StepResult] = []
        context: Dict[str, Any] = dict(initial_params or {})
        last_output: Any = None
        workflow_start = time.time()

        for step in steps:
            meta = registry.get(step.tool)
            if meta is None:
                sr = StepResult(tool=step.tool, success=False, result=None,
                                elapsed_ms=0, error=f"Tool '{step.tool}' not found in registry")
                results.append(sr)
                logger.warning(f"Workflow: unknown tool '{step.tool}'")
                break

            # Build params: merge step params + context + piped input
            run_params = {**step.params}
            run_params.update(context)
            if step.input_key and last_output is not None:
                # inject previous result under the expected key
                run_params[step.input_key] = last_output
            elif last_output is not None and step.input_key is None:
                # auto-inject as "text" if no explicit key given
                run_params.setdefault("text", str(last_output))

            t0 = time.time()
            try:
                tool_instance = meta.cls()
                output = tool_instance.safe_run(**run_params)
                elapsed = int((time.time() - t0) * 1000)
                last_output = output.get("result", output)
                sr = StepResult(tool=step.tool, success=output.get("success", True),
                                result=last_output, elapsed_ms=elapsed)
                if step.output_alias:
                    context[step.output_alias] = last_output
            except Exception as e:
                elapsed = int((time.time() - t0) * 1000)
                logger.error(f"Workflow step '{step.tool}' raised: {e}")
                sr = StepResult(tool=step.tool, success=False, result=None,
                                elapsed_ms=elapsed, error=str(e))
                results.append(sr)
                break

            results.append(sr)

        total_ms = int((time.time() - workflow_start) * 1000)
        all_ok = all(r.success for r in results)
        return WorkflowResult(steps=results, final_result=last_output,
                              total_ms=total_ms, success=all_ok)

    def run_template(self, template_name: str, initial_params: Dict[str, Any] = None) -> WorkflowResult:
        if template_name not in WORKFLOW_TEMPLATES:
            raise ValueError(f"Unknown workflow template: '{template_name}'. "
                             f"Available: {list(WORKFLOW_TEMPLATES.keys())}")
        return self.run(WORKFLOW_TEMPLATES[template_name], initial_params)