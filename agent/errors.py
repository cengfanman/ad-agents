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


def recommend_fallback(tool_name: str, used_tools: set = None, available_tools: set = None) -> str:
    """Provide context-aware fallback recommendations when a tool fails."""
    if used_tools is None:
        used_tools = set()
    if available_tools is None:
        available_tools = {'ads_metrics', 'competitor', 'listing_audit', 'inventory'}
    
    # Find unused tools
    unused_tools = available_tools - used_tools - {tool_name}
    
    # Tool-specific fallback strategies
    fallback_strategies = {
        'ads_metrics': {
            'purpose': 'performance analysis',
            'alternatives': ['listing_audit', 'competitor', 'inventory'],
            'explanation': 'Focus on listing quality or competitive factors'
        },
        'competitor': {
            'purpose': 'competitive analysis', 
            'alternatives': ['listing_audit', 'inventory'],
            'explanation': 'Assess internal factors like listing quality and stock levels'
        },
        'listing_audit': {
            'purpose': 'quality assessment',
            'alternatives': ['ads_metrics', 'competitor'],
            'explanation': 'Focus on performance metrics or competitive positioning'
        },
        'inventory': {
            'purpose': 'availability check',
            'alternatives': ['ads_metrics', 'competitor', 'listing_audit'],
            'explanation': 'Continue with performance and competitive analysis'
        }
    }
    
    strategy = fallback_strategies.get(tool_name)
    if not strategy:
        return "Try alternative analysis approaches"
    
    # Find available alternatives from the strategy
    relevant_alternatives = [tool for tool in strategy['alternatives'] if tool in unused_tools]
    
    if relevant_alternatives:
        tool_list = ", ".join(relevant_alternatives)
        return f"Try {tool_list} to {strategy['explanation'].lower()}"
    elif unused_tools:
        # If no relevant alternatives, suggest any unused tool
        remaining = ", ".join(unused_tools)
        return f"Continue with remaining tools: {remaining}"
    else:
        # All tools used or failed
        return f"All tools explored. Proceed with analysis based on available data for {strategy['purpose']}"