"""
Reasoning display module for structured agent logging.
"""

import json
from typing import Dict, Any, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.json import JSON

from .types import Hypothesis, ToolResult

console = Console()


class ReasoningDisplay:
    """Handles structured display of agent reasoning process."""
    
    def __init__(self):
        self.console = console
    
    def show_observe(self, step: int, context: Dict[str, Any]) -> None:
        """Display observation phase information."""
        
        title = f"🔍 STEP {step}: OBSERVE"
        
        content = []
        content.append("**Context Summary:**")
        content.append(f"• Goal: {context.get('scenario', {}).get('goal', 'unknown')}")
        content.append(f"• ASIN: {context.get('scenario', {}).get('asin', 'unknown')}")
        content.append(f"• Lookback Days: {context.get('scenario', {}).get('lookback_days', 'unknown')}")
        
        if context.get('previous_results'):
            content.append("\n**Previous Tool Results:**")
            for tool_name, result in context['previous_results'].items():
                # Handle both ToolResult objects and dict summaries
                if hasattr(result, 'ok'):
                    status = "✅" if result.ok else "❌"
                elif isinstance(result, dict):
                    status = "✅" if result.get('ok', True) else "❌"
                else:
                    status = "?"
                content.append(f"• {tool_name}: {status}")
        
        panel = Panel(
            "\n".join(content),
            title=title,
            title_align="left",
            border_style="blue"
        )
        
        self.console.print(panel)
    
    def show_hypotheses(self, hypotheses: Dict[str, Hypothesis]) -> None:
        """Display current hypotheses and belief scores."""
        
        title = "🧠 HYPOTHESES & BELIEFS"
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Hypothesis", style="cyan", width=20)
        table.add_column("Belief", style="yellow", width=8, justify="center")
        table.add_column("Rationale", style="white", width=50)
        
        # Sort by belief score
        sorted_hyps = sorted(hypotheses.items(), key=lambda x: x[1].belief, reverse=True)
        
        for name, hyp in sorted_hyps:
            belief_str = f"{hyp.belief:.2f}"
            
            # Color-code belief scores
            if hyp.belief >= 0.7:
                belief_style = "bold green"
            elif hyp.belief >= 0.5:
                belief_style = "bold yellow"
            else:
                belief_style = "dim white"
            
            # Truncate rationale if too long
            rationale = hyp.rationale[:45] + "..." if len(hyp.rationale) > 48 else hyp.rationale
            
            table.add_row(
                self._format_hypothesis_name(name),
                Text(belief_str, style=belief_style),
                rationale
            )
        
        panel = Panel(
            table,
            title=title,
            title_align="left",
            border_style="magenta"
        )
        
        self.console.print(panel)
    
    def show_decision(self, tool_choice: str, reasoning: str) -> None:
        """Display tool selection decision and reasoning."""
        
        title = "🎯 DECIDE: Tool Selection"
        
        if tool_choice:
            content = f"**Selected Tool:** `{tool_choice}`\n\n**Reasoning:** {reasoning}"
        else:
            content = "**Decision:** Stop execution\n\n**Reasoning:** " + reasoning
        
        panel = Panel(
            content,
            title=title,
            title_align="left",
            border_style="green"
        )
        
        self.console.print(panel)
    
    def show_tool_result(self, result: ToolResult) -> None:
        """Display tool execution results."""
        
        status_emoji = "✅" if result.ok else "❌"
        title = f"{status_emoji} RESULT: {result.name}"
        
        content = []
        
        # Show metadata
        content.append("**Execution Info:**")
        latency = result.meta.get('latency_ms', 0)
        content.append(f"• Latency: {latency}ms")
        content.append(f"• Status: {'Success' if result.ok else 'Failed'}")
        
        if result.error:
            content.append(f"• Error: {result.error}")
        
        # Show key data points (summarized)
        if result.ok and result.data:
            content.append("\n**Key Findings:**")
            key_findings = self._extract_key_findings(result.name, result.data)
            for finding in key_findings:
                content.append(f"• {finding}")
        
        border_style = "green" if result.ok else "red"
        
        panel = Panel(
            "\n".join(content),
            title=title,
            title_align="left",
            border_style=border_style
        )
        
        self.console.print(panel)
    
    def show_belief_update(self, evidence_list: List, old_beliefs: Dict[str, float], new_beliefs: Dict[str, float]) -> None:
        """Display belief updates based on evidence."""
        
        title = "📊 UPDATE: Belief Changes"
        
        content = []
        
        if evidence_list:
            content.append("**Evidence Collected:**")
            for evidence in evidence_list:
                # Handle both dict and Evidence objects
                if isinstance(evidence, dict):
                    strength = evidence.get('strength', '')
                    description = evidence.get('description', 'No description')
                else:
                    strength = getattr(evidence, 'strength', '')
                    description = getattr(evidence, 'description', 'No description')
                
                strength_emoji = {
                    'strong': '🟢',
                    'medium': '🟡',
                    'weak': '🟠',
                    'counter': '🔴'
                }.get(strength, '⚪')
                
                content.append(f"• {strength_emoji} {description}")
        
        content.append("\n**Belief Updates:**")
        for hyp_name, new_belief in new_beliefs.items():
            old_belief = old_beliefs.get(hyp_name, 0)
            change = new_belief - old_belief
            
            if abs(change) > 0.01:  # Only show significant changes
                arrow = "↗️" if change > 0 else "↘️"
                hyp_display = self._format_hypothesis_name(hyp_name)
                content.append(f"• {hyp_display}: {old_belief:.2f} → {new_belief:.2f} {arrow}")
        
        panel = Panel(
            "\n".join(content),
            title=title,
            title_align="left",
            border_style="cyan"
        )
        
        self.console.print(panel)
    
    def show_final_action(self, action_plan: Dict[str, Any]) -> None:
        """Display final action plan and recommendations."""
        
        title = "🚀 FINAL ACTION PLAN"
        
        content = []
        
        content.append(f"**Strategy:** {action_plan.get('strategy', 'unknown')}")
        content.append(f"**Primary Issue:** {self._format_hypothesis_name(action_plan.get('primary_hypothesis', 'unknown'))}")
        content.append(f"**Confidence:** {action_plan.get('confidence', 0):.2f}")
        content.append(f"**Risk Level:** {action_plan.get('risk_level', 'unknown').upper()}")
        
        recommendations = action_plan.get('recommendations', [])
        if recommendations:
            content.append("\n**Recommended Actions:**")
            for i, rec in enumerate(recommendations[:5], 1):  # Limit to 5 recommendations
                content.append(f"{i}. {rec}")
        
        # Show top hypotheses summary
        all_hyps = action_plan.get('all_hypotheses', {})
        if all_hyps:
            content.append("\n**Final Hypothesis Ranking:**")
            for hyp_name, belief in all_hyps.items():
                hyp_display = self._format_hypothesis_name(hyp_name)
                content.append(f"• {hyp_display}: {belief:.2f}")
        
        panel = Panel(
            "\n".join(content),
            title=title,
            title_align="left",
            border_style="bold green"
        )
        
        self.console.print(panel)
        
        # Add separator for clean output
        self.console.print("=" * 80)
    
    def _format_hypothesis_name(self, name: str) -> str:
        """Format hypothesis names for better readability."""
        name_map = {
            'h1_low_bids': 'Low Bid Amounts',
            'h2_keyword_coverage': 'Keyword Coverage',
            'h3_competitor_pressure': 'Competitor Pressure',
            'h4_listing_quality': 'Listing Quality',
            'h5_broad_match_waste': 'Broad Match Waste'
        }
        return name_map.get(name, name.replace('_', ' ').title())
    
    def _extract_key_findings(self, tool_name: str, data: Dict[str, Any]) -> List[str]:
        """Extract key findings from tool results for display."""
        findings = []
        
        if tool_name == 'ads_metrics':
            if 'aggregated_metrics' in data:
                metrics = data['aggregated_metrics']
                findings.append(f"Total impressions: {metrics.get('total_impressions', 0):,}")
                findings.append(f"Overall CTR: {metrics.get('avg_ctr', 0):.3f}")
                findings.append(f"Overall ACOS: {metrics.get('overall_acos', 'N/A')}")
            
            if 'performance_issues' in data:
                issues = data['performance_issues']
                findings.append(f"Low impression keywords: {issues.get('low_impression_keywords', 0)}")
                findings.append(f"No conversion keywords: {issues.get('no_conversion_keywords', 0)}")
        
        elif tool_name == 'competitor':
            if 'competitive_analysis' in data:
                analysis = data['competitive_analysis']
                findings.append(f"Competitive pressure: {analysis.get('competitive_pressure', 'unknown')}")
                findings.append(f"Price positioning: {analysis.get('price_positioning', 'unknown')}")
        
        elif tool_name == 'listing_audit':
            if 'listing_analysis' in data:
                analysis = data['listing_analysis']
                findings.append(f"Quality score: {analysis.get('overall_quality_score', 0)}/100")
                findings.append(f"Grade: {analysis.get('quality_grade', 'F')}")
                findings.append(f"Issues found: {len(analysis.get('quality_issues', []))}")
        
        elif tool_name == 'inventory':
            if 'inventory_analysis' in data:
                analysis = data['inventory_analysis']
                findings.append(f"Days remaining: {analysis.get('days_remaining', 0)}")
                findings.append(f"Health status: {analysis.get('health_status', 'unknown')}")
        
        return findings[:3]  # Limit to 3 key findings