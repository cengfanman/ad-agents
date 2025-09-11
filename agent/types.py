from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel


class ScenarioInput(BaseModel):
    """Input scenario definition for agent execution."""
    asin: str
    goal: Literal['increase_impressions', 'improve_conversion', 'reduce_acos']
    lookback_days: int
    notes: Optional[str] = None


class ToolResult(BaseModel):
    """Standardized result from tool execution."""
    name: str
    ok: bool
    data: Dict[str, Any]
    meta: Dict[str, Any]  # Contains latency_ms, source, etc.
    error: Optional[str] = None


class Hypothesis(BaseModel):
    """Represents a belief about potential issues."""
    name: str
    belief: float  # 0.0 to 1.0 confidence level
    rationale: str


class AgentContext(BaseModel):
    """Current context for agent decision making."""
    scenario: ScenarioInput
    scenario_dir: str
    flags: Dict[str, Any]
    step: int
    previous_results: Dict[str, ToolResult]
    hypotheses: Dict[str, Hypothesis]


class Evidence(BaseModel):
    """Evidence collected from tool results."""
    tool_name: str
    strength: Literal['strong', 'medium', 'weak', 'counter']
    hypothesis_name: str
    description: str
    data_point: Any