"""
Main agent loop implementing Observe → Think → Act cycle.
"""

import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from .types import ScenarioInput, ToolResult, Evidence
from .policy import PolicyEngine
from .memory import WorkingMemory, TraceManager
from .reasoning import ReasoningDisplay
from .errors import recommend_fallback

# Import tools
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from tools.ads_metrics import AdsMetricsTool
from tools.competitor import CompetitorTool
from tools.listing_audit import ListingAuditTool
from tools.inventory import InventoryTool


class AgentLoop:
    """Main agent execution loop."""
    
    def __init__(self):
        self.policy = PolicyEngine()
        self.display = ReasoningDisplay()
        self.trace_manager = TraceManager()
        
        # Initialize tools
        self.tools = {
            'ads_metrics': AdsMetricsTool(),
            'competitor': CompetitorTool(),
            'listing_audit': ListingAuditTool(),
            'inventory': InventoryTool()
        }
    
    def run(self, scenario_input: ScenarioInput, scenario_dir: str, flags: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the main agent loop.
        
        Args:
            scenario_input: Scenario configuration
            scenario_dir: Path to scenario data directory
            flags: Optional flags for testing/debugging
            
        Returns:
            Final action plan and results
        """
        if flags is None:
            flags = {}
        
        # Initialize memory
        memory = WorkingMemory(scenario_input, scenario_dir, flags)
        
        # Initialize hypotheses
        memory.update_hypotheses(self.policy.initialize_hypotheses(scenario_input))
        memory.add_trace_entry('initialization', {
            'initial_hypotheses': {name: hyp.model_dump() for name, hyp in memory.hypotheses.items()},
            'scenario': scenario_input.model_dump(),
            'flags': flags
        })
        
        # Main execution loop (minimum 3 steps, maximum 5)
        for step in range(1, 6):
            memory.advance_step()
            
            # OBSERVE: Gather current context
            ctx = memory.get_context()
            self.display.show_observe(step, {
                'scenario': scenario_input.model_dump(),
                'previous_results': {name: {'ok': result.ok, 'name': result.name} 
                                  for name, result in memory.previous_results.items()}
            })
            
            memory.add_trace_entry('observe', {
                'step': step,
                'context_summary': self._summarize_context(ctx)
            })
            
            # THINK: Display current hypotheses
            self.display.show_hypotheses(memory.hypotheses)
            
            # DECIDE: Select next action
            should_stop, stop_reason = self.policy.should_stop(memory.hypotheses, ctx)
            
            if should_stop and step >= 3:
                self.display.show_decision(None, stop_reason)
                memory.add_trace_entry('decision', {
                    'action': 'stop',
                    'reasoning': stop_reason,
                    'final_step': True
                })
                break
            
            # Select tool
            selected_tool = self.policy.select_next_tool(memory.hypotheses, ctx)
            
            if not selected_tool:
                stop_reason = "No more informative tools available"
                self.display.show_decision(None, stop_reason)
                memory.add_trace_entry('decision', {
                    'action': 'stop',
                    'reasoning': stop_reason,
                    'no_tool_available': True
                })
                break
            
            # Show decision
            decision_reasoning = self._explain_tool_choice(selected_tool, memory.hypotheses)
            self.display.show_decision(selected_tool, decision_reasoning)
            
            memory.add_trace_entry('decision', {
                'selected_tool': selected_tool,
                'reasoning': decision_reasoning
            })
            
            # ACT: Execute selected tool
            tool_result = self._execute_tool(selected_tool, ctx)
            self.display.show_tool_result(tool_result)
            
            # Store result
            memory.add_tool_result(selected_tool, tool_result)
            memory.add_trace_entry('action', {
                'tool': selected_tool,
                'result': tool_result.model_dump()
            })
            
            # Handle tool failure with fallback
            if not tool_result.ok:
                fallback_suggestion = recommend_fallback(selected_tool)
                self.display.console.print(f"[yellow]💡 Fallback suggestion: {fallback_suggestion}[/yellow]")
                
                memory.add_trace_entry('fallback', {
                    'failed_tool': selected_tool,
                    'error': tool_result.error,
                    'suggestion': fallback_suggestion
                })
                
                # Continue with next iteration rather than stopping
                continue
            
            # EVALUATE: Update beliefs based on evidence
            evidence_list = self._extract_evidence(tool_result)
            old_beliefs = {name: hyp.belief for name, hyp in memory.hypotheses.items()}
            
            updated_hypotheses = self.policy.update_beliefs(memory.hypotheses, evidence_list)
            new_beliefs = {name: hyp.belief for name, hyp in updated_hypotheses.items()}
            
            memory.update_hypotheses(updated_hypotheses)
            
            # Show belief updates
            self.display.show_belief_update(
                [ev.model_dump() if hasattr(ev, 'model_dump') else ev for ev in evidence_list],
                old_beliefs,
                new_beliefs
            )
            
            memory.add_trace_entry('update', {
                'evidence': [ev.model_dump() if hasattr(ev, 'model_dump') else ev for ev in evidence_list],
                'belief_changes': {
                    name: {'old': old_beliefs.get(name, 0), 'new': new_beliefs.get(name, 0)}
                    for name in new_beliefs.keys()
                }
            })
        
        # Generate final action plan
        final_action = self.policy.decide_action(memory.hypotheses, memory.get_context())
        self.display.show_final_action(final_action)
        
        memory.add_trace_entry('final_action', final_action)
        
        # Save trace
        trace_file = self.trace_manager.save_trace(memory, final_action)
        
        # Add trace file to results
        final_action['trace_file'] = trace_file
        final_action['total_steps'] = memory.step
        
        return final_action
    
    def _execute_tool(self, tool_name: str, ctx) -> ToolResult:
        """Execute a tool with error handling."""
        if tool_name not in self.tools:
            return ToolResult(
                name=tool_name,
                ok=False,
                data={},
                meta={'error_type': 'tool_not_found'},
                error=f"Tool {tool_name} not found"
            )
        
        tool = self.tools[tool_name]
        
        # Prepare context for tool
        tool_ctx = {
            'scenario_dir': ctx.scenario_dir,
            'flags': ctx.flags
        }
        
        # Add tool-specific context
        if tool_name == 'ads_metrics':
            tool_ctx['mode'] = ctx.flags.get('ads_mode', 'keyword')
        
        try:
            return tool.run(tool_ctx)
        except Exception as e:
            # This should be caught by the tool's wrap_call decorator,
            # but provide a safety fallback
            return ToolResult(
                name=tool_name,
                ok=False,
                data={},
                meta={'error_type': 'unexpected_error'},
                error=f"Unexpected error: {str(e)}"
            )
    
    def _extract_evidence(self, tool_result: ToolResult) -> List[Evidence]:
        """Extract evidence from tool results to update beliefs."""
        if not tool_result.ok:
            return []
        
        evidence_list = []
        tool_name = tool_result.name
        data = tool_result.data
        
        if tool_name == 'ads_metrics':
            # Evidence for ads metrics analysis
            if 'aggregated_metrics' in data:
                metrics = data['aggregated_metrics']
                total_impressions = metrics.get('total_impressions', 0)
                avg_ctr = metrics.get('avg_ctr', 0)
                overall_acos = metrics.get('overall_acos')
                
                # Low impressions evidence
                if total_impressions < 3000:
                    evidence_list.append(Evidence(
                        tool_name=tool_name,
                        strength='strong',
                        hypothesis_name='h1_low_bids',
                        description=f'Low total impressions ({total_impressions:,}) suggests bid issues',
                        data_point=total_impressions
                    ))
                
                if total_impressions < 5000:
                    evidence_list.append(Evidence(
                        tool_name=tool_name,
                        strength='medium',
                        hypothesis_name='h2_keyword_coverage',
                        description=f'Limited impressions may indicate poor keyword coverage',
                        data_point=total_impressions
                    ))
                
                # CTR evidence
                if avg_ctr < 0.015:
                    evidence_list.append(Evidence(
                        tool_name=tool_name,
                        strength='medium',
                        hypothesis_name='h4_listing_quality',
                        description=f'Low CTR ({avg_ctr:.3f}) suggests listing quality issues',
                        data_point=avg_ctr
                    ))
                
                # ACOS evidence
                if overall_acos and overall_acos > 1.0:
                    evidence_list.append(Evidence(
                        tool_name=tool_name,
                        strength='strong',
                        hypothesis_name='h5_broad_match_waste',
                        description=f'High ACOS ({overall_acos:.2f}) indicates inefficient spending',
                        data_point=overall_acos
                    ))
            
            # Performance issues evidence
            if 'performance_issues' in data:
                issues = data['performance_issues']
                no_conv_keywords = issues.get('no_conversion_keywords', 0)
                total_keywords = issues.get('total_keywords', 1)
                
                if no_conv_keywords / total_keywords > 0.6:
                    evidence_list.append(Evidence(
                        tool_name=tool_name,
                        strength='strong',
                        hypothesis_name='h5_broad_match_waste',
                        description=f'High ratio of non-converting keywords ({no_conv_keywords}/{total_keywords})',
                        data_point=no_conv_keywords / total_keywords
                    ))
        
        elif tool_name == 'competitor':
            if 'competitive_analysis' in data:
                analysis = data['competitive_analysis']
                pressure = analysis.get('competitive_pressure', 'unknown')
                
                if pressure in ['high', 'medium']:
                    evidence_list.append(Evidence(
                        tool_name=tool_name,
                        strength='strong' if pressure == 'high' else 'medium',
                        hypothesis_name='h3_competitor_pressure',
                        description=f'Competitive pressure is {pressure}',
                        data_point=pressure
                    ))
        
        elif tool_name == 'listing_audit':
            if 'listing_analysis' in data:
                analysis = data['listing_analysis']
                quality_score = analysis.get('overall_quality_score', 0)
                issues_count = len(analysis.get('quality_issues', []))
                
                if quality_score < 50:
                    evidence_list.append(Evidence(
                        tool_name=tool_name,
                        strength='strong',
                        hypothesis_name='h4_listing_quality',
                        description=f'Low quality score ({quality_score}/100) with {issues_count} issues',
                        data_point=quality_score
                    ))
                elif quality_score < 70:
                    evidence_list.append(Evidence(
                        tool_name=tool_name,
                        strength='medium',
                        hypothesis_name='h4_listing_quality',
                        description=f'Moderate quality score ({quality_score}/100)',
                        data_point=quality_score
                    ))
        
        elif tool_name == 'inventory':
            if 'inventory_analysis' in data:
                analysis = data['inventory_analysis']
                days_remaining = analysis.get('days_remaining', 0)
                
                if days_remaining < 14:
                    # Low inventory might affect ad performance
                    evidence_list.append(Evidence(
                        tool_name=tool_name,
                        strength='weak',
                        hypothesis_name='h1_low_bids',
                        description=f'Low inventory ({days_remaining} days) may justify reduced bids',
                        data_point=days_remaining
                    ))
        
        return evidence_list
    
    def _explain_tool_choice(self, tool_name: str, hypotheses: Dict[str, Any]) -> str:
        """Explain why a specific tool was chosen."""
        top_hypothesis = max(hypotheses.values(), key=lambda h: h.belief)
        
        explanations = {
            'ads_metrics': f'Analyzing advertising data to investigate {top_hypothesis.name} (belief: {top_hypothesis.belief:.2f})',
            'competitor': f'Checking competitive landscape for {top_hypothesis.name} (belief: {top_hypothesis.belief:.2f})',
            'listing_audit': f'Auditing listing quality related to {top_hypothesis.name} (belief: {top_hypothesis.belief:.2f})',
            'inventory': f'Verifying inventory status impact on {top_hypothesis.name} (belief: {top_hypothesis.belief:.2f})'
        }
        
        return explanations.get(tool_name, f'Selected {tool_name} for further investigation')
    
    def _summarize_context(self, ctx) -> Dict[str, Any]:
        """Create a summary of current context for trace."""
        return {
            'step': ctx.step,
            'goal': ctx.scenario.goal,
            'tools_used': list(ctx.previous_results.keys()),
            'top_hypothesis': max(ctx.hypotheses.values(), key=lambda h: h.belief).name if ctx.hypotheses else None
        }