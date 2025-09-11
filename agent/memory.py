"""
Memory management for agent working memory and execution traces.
"""

import orjson
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .types import ScenarioInput, ToolResult, Hypothesis, AgentContext


class WorkingMemory:
    """Manages agent's working memory during execution."""
    
    def __init__(self, scenario: ScenarioInput, scenario_dir: str, flags: Dict[str, Any]):
        self.scenario = scenario
        self.scenario_dir = scenario_dir
        self.flags = flags
        self.step = 0
        self.previous_results: Dict[str, ToolResult] = {}
        self.hypotheses: Dict[str, Hypothesis] = {}
        self.trace: List[Dict[str, Any]] = []
        
    def get_context(self) -> AgentContext:
        """Get current agent context."""
        return AgentContext(
            scenario=self.scenario,
            scenario_dir=self.scenario_dir,
            flags=self.flags,
            step=self.step,
            previous_results=self.previous_results,
            hypotheses=self.hypotheses
        )
    
    def advance_step(self) -> None:
        """Advance to next step."""
        self.step += 1
    
    def update_hypotheses(self, new_hypotheses: Dict[str, Hypothesis]) -> None:
        """Update current hypotheses."""
        self.hypotheses = new_hypotheses
    
    def add_tool_result(self, tool_name: str, result: ToolResult) -> None:
        """Add tool result to memory."""
        self.previous_results[tool_name] = result
    
    def add_trace_entry(self, entry_type: str, data: Dict[str, Any]) -> None:
        """Add entry to execution trace."""
        trace_entry = {
            'timestamp': datetime.now().isoformat(),
            'step': self.step,
            'type': entry_type,
            'data': data
        }
        self.trace.append(trace_entry)
    
    def get_trace(self) -> List[Dict[str, Any]]:
        """Get complete execution trace."""
        return self.trace.copy()


class TraceManager:
    """Manages persistent trace storage."""
    
    def __init__(self, trace_dir: str = "./trace"):
        self.trace_dir = Path(trace_dir)
        self.trace_dir.mkdir(exist_ok=True)
    
    def save_trace(self, memory: WorkingMemory, final_action: Optional[Dict[str, Any]] = None) -> str:
        """Save execution trace to file."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trace_file = self.trace_dir / f"{timestamp}.json"
        
        trace_data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'scenario': memory.scenario.model_dump(),
                'scenario_dir': memory.scenario_dir,
                'flags': memory.flags,
                'total_steps': memory.step
            },
            'execution_trace': memory.get_trace(),
            'final_state': {
                'hypotheses': {name: hyp.model_dump() for name, hyp in memory.hypotheses.items()},
                'tool_results': {name: result.model_dump() for name, result in memory.previous_results.items()},
                'final_action': final_action
            }
        }
        
        # Save using orjson for better performance
        with open(trace_file, 'wb') as f:
            f.write(orjson.dumps(trace_data, option=orjson.OPT_INDENT_2))
        
        return str(trace_file)
    
    def load_trace(self, trace_file: str) -> Dict[str, Any]:
        """Load execution trace from file."""
        with open(trace_file, 'rb') as f:
            return orjson.loads(f.read())