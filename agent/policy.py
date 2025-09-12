"""
Policy engine for hypothesis management, belief updates, and tool selection.
"""

from typing import Dict, List, Optional, Tuple, Any
from .types import Hypothesis, ScenarioInput, ToolResult, Evidence, AgentContext


class PolicyEngine:
    """Core policy engine for autonomous agent decision-making."""
    
    def __init__(self):
        self.evidence_strength_map = {
            'strong': 0.2,
            'medium': 0.1,
            'weak': 0.05,
            'counter': -0.1
        }
    
    def initialize_hypotheses(self, scenario: ScenarioInput) -> Dict[str, Hypothesis]:
        """Initialize hypotheses based on scenario goal."""
        base_hypotheses = {
            'h1_low_bids': Hypothesis(
                name='h1_low_bids',
                belief=0.3,
                rationale='Bid amounts may be too low to win competitive auctions'
            ),
            'h2_keyword_coverage': Hypothesis(
                name='h2_keyword_coverage',
                belief=0.25,
                rationale='Keyword coverage may be insufficient for target audience'
            ),
            'h3_competitor_pressure': Hypothesis(
                name='h3_competitor_pressure',
                belief=0.2,
                rationale='Strong competitor presence may be limiting performance'
            ),
            'h4_listing_quality': Hypothesis(
                name='h4_listing_quality',
                belief=0.25,
                rationale='Product listing quality may be affecting conversion rates'
            ),
            'h5_broad_match_waste': Hypothesis(
                name='h5_broad_match_waste',
                belief=0.15,
                rationale='Broad match keywords may be generating irrelevant traffic'
            )
        }
        
        # Adjust initial beliefs based on scenario goal
        if scenario.goal == 'reduce_acos':
            base_hypotheses['h5_broad_match_waste'].belief = 0.4
            base_hypotheses['h4_listing_quality'].belief = 0.35
        elif scenario.goal == 'increase_impressions':
            base_hypotheses['h1_low_bids'].belief = 0.45
            base_hypotheses['h2_keyword_coverage'].belief = 0.4
        elif scenario.goal == 'improve_conversion':
            base_hypotheses['h4_listing_quality'].belief = 0.5
            base_hypotheses['h3_competitor_pressure'].belief = 0.3
        
        # Normalize beliefs to ensure they sum reasonably
        self._normalize_beliefs(base_hypotheses)
        
        return base_hypotheses
    
    def update_beliefs(self, hypotheses: Dict[str, Hypothesis], evidence_list: List[Evidence]) -> Dict[str, Hypothesis]:
        """Update belief scores based on collected evidence."""
        updated_hypotheses = hypotheses.copy()
        
        for evidence in evidence_list:
            if evidence.hypothesis_name in updated_hypotheses:
                hypothesis = updated_hypotheses[evidence.hypothesis_name]
                delta = self.evidence_strength_map.get(evidence.strength, 0)
                
                # Apply evidence
                new_belief = max(0.0, min(1.0, hypothesis.belief + delta))
                
                updated_hypotheses[evidence.hypothesis_name] = Hypothesis(
                    name=hypothesis.name,
                    belief=new_belief,
                    rationale=f"{hypothesis.rationale} [Updated by {evidence.tool_name}: {evidence.description}]"
                )
        
        return updated_hypotheses
    
    def select_next_tool(self, hypotheses: Dict[str, Hypothesis], ctx: AgentContext) -> Optional[str]:
        """Select the most informative tool based on current beliefs and context."""
        
        # Get the top hypotheses by belief score
        sorted_hypotheses = sorted(hypotheses.items(), key=lambda x: x[1].belief, reverse=True)
        top_hypothesis = sorted_hypotheses[0][1] if sorted_hypotheses else None
        
        if not top_hypothesis:
            return None
        
        # Check if we already have very high confidence AND have used key tools
        if top_hypothesis.belief >= 0.8:
            return None  # Stop - very high confidence
        
        # Even with high confidence, continue if we haven't used preferred tools for top hypothesis
        used_tools = set(ctx.previous_results.keys())
        if top_hypothesis.belief >= 0.7:
            top_hyp_name = sorted_hypotheses[0][0]  # Get hypothesis name
            preferred_tools = self.get_tool_preferences().get(top_hyp_name, [])
            # Only stop if we've used all preferred tools for the top hypothesis
            if all(tool in used_tools for tool in preferred_tools):
                return None
        
        # Select tool based on information gain potential
        
        # Find best tool based on top hypothesis
        for hyp_name, hyp in sorted_hypotheses[:2]:  # Consider top 2 hypotheses
            preferred_tools = self.get_tool_preferences().get(hyp_name, [])
            
            for tool_name in preferred_tools:
                if tool_name not in used_tools:
                    return tool_name
        
        # Fallback: select any unused tool
        all_tools = {'ads_metrics', 'competitor', 'listing_audit', 'inventory'}
        unused_tools = all_tools - used_tools
        
        if unused_tools:
            return next(iter(unused_tools))
        
        return None  # All tools used
    
    def get_tool_preferences(self) -> Dict[str, List[str]]:
        """Get the mapping of hypotheses to preferred tools."""
        return {
            'h1_low_bids': ['ads_metrics', 'inventory'],
            'h2_keyword_coverage': ['ads_metrics', 'listing_audit'],
            'h3_competitor_pressure': ['competitor', 'ads_metrics'],
            'h4_listing_quality': ['listing_audit', 'competitor'],
            'h5_broad_match_waste': ['ads_metrics']
        }
    
    def should_stop(self, hypotheses: Dict[str, Hypothesis], ctx: AgentContext) -> Tuple[bool, str]:
        """Determine if agent should stop execution."""
        
        if not hypotheses:
            return True, "No hypotheses to evaluate"
        
        # Get top hypothesis
        top_hypothesis = max(hypotheses.values(), key=lambda h: h.belief)
        
        # High confidence threshold
        if top_hypothesis.belief >= 0.7:
            return True, f"High confidence in {top_hypothesis.name} (belief={top_hypothesis.belief:.2f})"
        
        # Minimum iterations
        if ctx.step >= 3:
            # Check for low marginal information gain
            if ctx.step >= 5:
                return True, f"Maximum iterations reached with top hypothesis {top_hypothesis.name} (belief={top_hypothesis.belief:.2f})"
            
            # Check if we've used all main tools
            main_tools = {'ads_metrics', 'competitor', 'listing_audit'}
            used_tools = set(ctx.previous_results.keys())
            
            if main_tools.issubset(used_tools) and top_hypothesis.belief < 0.4:
                return True, f"All main tools used with low confidence (belief={top_hypothesis.belief:.2f})"
        
        return False, ""
    
    def decide_action(self, hypotheses: Dict[str, Hypothesis], ctx: AgentContext) -> Dict[str, Any]:
        """Generate strategy recommendations based on current beliefs."""
        
        if not hypotheses:
            return {
                'strategy': 'no_action',
                'recommendations': ['Insufficient data for recommendations'],
                'confidence': 0.0,
                'risk_level': 'unknown'
            }
        
        # Get top hypotheses
        sorted_hyps = sorted(hypotheses.items(), key=lambda x: x[1].belief, reverse=True)
        top_hypothesis = sorted_hyps[0][1]
        
        # Generate recommendations based on top hypothesis
        recommendations = self._generate_recommendations(top_hypothesis.name, top_hypothesis.belief, ctx)
        
        # Assess risk level
        risk_level = self._assess_risk_level(top_hypothesis.belief, ctx)
        
        # Determine strategy type
        strategy = self._determine_strategy(top_hypothesis.name, top_hypothesis.belief)
        
        return {
            'strategy': strategy,
            'primary_hypothesis': top_hypothesis.name,
            'confidence': top_hypothesis.belief,
            'recommendations': recommendations,
            'risk_level': risk_level,
            'all_hypotheses': {name: hyp.belief for name, hyp in sorted_hyps[:3]},
            'rationale': top_hypothesis.rationale
        }
    
    def _normalize_beliefs(self, hypotheses: Dict[str, Hypothesis]) -> None:
        """Ensure beliefs are reasonable and sum appropriately."""
        total_belief = sum(h.belief for h in hypotheses.values())
        
        if total_belief > 1.5:  # Too high, scale down
            scale_factor = 1.2 / total_belief
            for name, hyp in hypotheses.items():
                hypotheses[name] = Hypothesis(
                    name=hyp.name,
                    belief=hyp.belief * scale_factor,
                    rationale=hyp.rationale
                )
    
    def _generate_recommendations(self, hypothesis_name: str, confidence: float, ctx: AgentContext) -> List[str]:
        """Generate specific recommendations based on hypothesis."""
        
        recs = {
            'h1_low_bids': [
                'Increase bid amounts for high-performing keywords',
                'Implement automated bid adjustments based on performance',
                'Focus budget on keywords with proven conversion potential'
            ],
            'h2_keyword_coverage': [
                'Expand keyword list with relevant long-tail terms',
                'Add phrase and exact match variants of performing keywords',
                'Research competitor keywords for expansion opportunities'
            ],
            'h3_competitor_pressure': [
                'Differentiate product positioning in ads and listing',
                'Focus on unique value propositions and features',
                'Consider niche keyword targeting to avoid direct competition'
            ],
            'h4_listing_quality': [
                'Optimize product title with high-performing keywords',
                'Improve main product images and add lifestyle shots',
                'Enhance product descriptions and bullet points',
                'Add or improve A+ Content'
            ],
            'h5_broad_match_waste': [
                'Convert broad match keywords to phrase or exact match',
                'Add negative keywords to filter irrelevant traffic',
                'Review search term reports and optimize accordingly'
            ]
        }
        
        base_recs = recs.get(hypothesis_name, ['Review performance data and adjust strategy'])
        
        # Adjust recommendations based on confidence
        if confidence < 0.4:
            base_recs.append('Gather more data before implementing major changes')
        elif confidence > 0.7:
            base_recs.append('Implement changes immediately with close monitoring')
        
        return base_recs
    
    def _assess_risk_level(self, confidence: float, ctx: AgentContext) -> str:
        """Assess risk level of recommendations."""
        if confidence >= 0.7:
            return 'low'
        elif confidence >= 0.5:
            return 'medium'
        else:
            return 'high'
    
    def _determine_strategy(self, hypothesis_name: str, confidence: float) -> str:
        """Determine overall strategy type."""
        if confidence >= 0.7:
            return 'focused_optimization'
        elif confidence >= 0.5:
            return 'targeted_improvement'
        else:
            return 'data_gathering'