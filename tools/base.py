import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Callable
from functools import wraps

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from agent.types import ToolResult


class BaseTool(ABC):
    """Abstract base class for all agent tools."""
    
    def __init__(self, name: str, timeout_s: int = 30):
        self.name = name
        self.timeout_s = int(os.getenv('TOOL_TIMEOUT_S', timeout_s))
    
    @abstractmethod
    def run(self, ctx: Dict[str, Any]) -> ToolResult:
        """Execute the tool with given context."""
        pass


def wrap_call(func: Callable) -> Callable:
    """Decorator to wrap tool calls with timeout, retry, and error handling."""
    
    @wraps(func)
    def wrapper(self, ctx: Dict[str, Any]) -> ToolResult:
        start_time = time.time()
        attempts = 2  # Initial attempt + 1 retry
        last_error = None
        
        for attempt in range(attempts):
            try:
                # Execute the function
                result = func(self, ctx)
                
                # Ensure result is a ToolResult
                if isinstance(result, ToolResult):
                    return result
                elif isinstance(result, dict):
                    # Convert dict to ToolResult if needed
                    elapsed_ms = int((time.time() - start_time) * 1000)
                    return ToolResult(
                        name=self.name,
                        ok=True,
                        data=result,
                        meta={
                            'latency_ms': elapsed_ms,
                            'source': f"{self.__class__.__module__}.{self.__class__.__name__}",
                            'attempt': attempt + 1
                        }
                    )
                else:
                    raise ValueError(f"Tool {self.name} returned invalid result type: {type(result)}")
                    
            except Exception as e:
                last_error = e
                elapsed_ms = int((time.time() - start_time) * 1000)
                
                # If this is the last attempt or a critical error, return failure
                if attempt == attempts - 1:
                    return ToolResult(
                        name=self.name,
                        ok=False,
                        data={},
                        meta={
                            'latency_ms': elapsed_ms,
                            'source': f"{self.__class__.__module__}.{self.__class__.__name__}",
                            'attempt': attempt + 1,
                            'error_type': type(e).__name__
                        },
                        error=str(e)
                    )
                
                # Wait before retry (exponential backoff)
                time.sleep(0.5 * (2 ** attempt))
        
        # Should never reach here, but safety fallback
        return ToolResult(
            name=self.name,
            ok=False,
            data={},
            meta={'latency_ms': int((time.time() - start_time) * 1000)},
            error=f"Unexpected failure after {attempts} attempts: {last_error}"
        )
    
    return wrapper