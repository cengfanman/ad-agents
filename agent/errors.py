"""Custom exceptions and fallback recommendations for the agent."""

class ToolTimeoutError(Exception):
    """Raised when a tool operation times out."""
    pass


class DataMissingError(Exception):
    """Raised when required data files are missing."""
    pass


class ConflictError(Exception):
    """Raised when conflicting data or hypotheses are detected."""
    pass


def recommend_fallback(tool_name: str) -> str:
    """Provide fallback recommendations when a tool fails."""
    fallbacks = {
        'ads_metrics': "Consider using listing_audit to check product appeal, or inventory to verify availability",
        'competitor': "Use listing_audit to check competitiveness, or ads_metrics to focus on internal performance",
        'listing_audit': "Use ads_metrics to check keyword performance, or competitor to assess market position",
        'inventory': "Continue with ads_metrics and competitor analysis to assess external factors"
    }
    
    return fallbacks.get(tool_name, "Try alternative tools or manual analysis")