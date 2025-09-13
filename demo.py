#!/usr/bin/env python3
"""
Demo CLI for Amazon Seller AI Agent.

Usage:
    python demo.py --scenario scenarios/scenario_low_impr.json
    python demo.py --scenario scenarios/scenario_low_impr.json --break-competitor
"""

import json
import sys
import argparse
from pathlib import Path

import orjson
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)  # Override existing environment variables
except ImportError:
    pass  # dotenv not available, continue with system env vars

from agent.loop import AgentLoop
from agent.types import ScenarioInput

console = Console()


def load_scenario(scenario_path: str) -> tuple[ScenarioInput, str]:
    """Load scenario configuration and determine data directory."""
    
    scenario_file = Path(scenario_path)
    if not scenario_file.exists():
        console.print(f"[red]Error: Scenario file not found: {scenario_path}[/red]")
        sys.exit(1)
    
    # Load scenario data
    try:
        with open(scenario_file, 'rb') as f:
            scenario_data = orjson.loads(f.read())
        scenario_input = ScenarioInput(**scenario_data)
    except Exception as e:
        console.print(f"[red]Error loading scenario: {e}[/red]")
        sys.exit(1)
    
    # Determine mock data directory from filename
    scenario_name = scenario_file.stem.replace('scenario_', '')
    mock_dir = Path('mock') / scenario_name
    
    if not mock_dir.exists():
        console.print(f"[red]Error: Mock data directory not found: {mock_dir}[/red]")
        console.print(f"[yellow]Available directories: {[d.name for d in Path('mock').iterdir() if d.is_dir()]}[/yellow]")
        sys.exit(1)
    
    return scenario_input, str(mock_dir)


def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        description="Amazon Seller AI Agent Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python demo.py --scenario scenarios/scenario_low_impr.json
    python demo.py --scenario scenarios/scenario_high_acos.json --mode campaign
    python demo.py --scenario scenarios/scenario_low_impr.json --break-competitor
        """
    )
    
    parser.add_argument(
        '--scenario',
        type=str,
        required=True,
        help='Path to scenario JSON file'
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['keyword', 'campaign'],
        default='keyword',
        help='Ads metrics analysis mode (default: keyword)'
    )
    
    parser.add_argument(
        '--break-competitor',
        action='store_true',
        help='Simulate competitor tool failure for testing fallback'
    )
    
    parser.add_argument(
        '--break-audit',
        action='store_true',
        help='Simulate listing audit tool failure for testing fallback'
    )
    
    parser.add_argument(
        '--break-inventory',
        action='store_true',
        help='Simulate inventory tool failure for testing fallback'
    )
    
    parser.add_argument(
        '--break-ads',
        action='store_true',
        help='Simulate ads metrics tool failure for testing fallback'
    )
    
    parser.add_argument(
        '--no-openai',
        action='store_true',
        help='Skip OpenAI enhanced report generation'
    )
    
    parser.add_argument(
        '--lang',
        type=str,
        choices=['en', 'zh-tw'],
        default='en',
        help='Report language (en=English, zh-tw=Traditional Chinese)'
    )
    
    args = parser.parse_args()
    
    # Load scenario and determine data directory
    scenario_input, mock_dir = load_scenario(args.scenario)
    
    # Prepare flags for agent
    flags = {
        'ads_mode': args.mode,
        'break_competitor': args.break_competitor,
        'break_audit': args.break_audit,
        'break_inventory': args.break_inventory,
        'break_ads': args.break_ads
    }
    
    # Show startup information
    console.print(Panel(
        f"""**🤖 Amazon Seller AI Agent**

**Scenario:** {Path(args.scenario).name}
**Goal:** {scenario_input.goal}
**ASIN:** {scenario_input.asin}
**Lookback Days:** {scenario_input.lookback_days}
**Data Source:** {mock_dir}
**Ads Mode:** {args.mode}
**Language:** {'Traditional Chinese' if args.lang == 'zh-tw' else 'English'}
**Test Flags:** {', '.join([f for f in [
    'Competitor failure enabled' if args.break_competitor else None,
    'Audit failure enabled' if args.break_audit else None, 
    'Inventory failure enabled' if args.break_inventory else None,
    'Ads metrics failure enabled' if args.break_ads else None,
    'Skip OpenAI reports' if args.no_openai else None
] if f]) or 'None'}
""",
        title="Agent Initialization",
        title_align="left",
        border_style="bold blue"
    ))
    
    if scenario_input.notes:
        console.print(f"[dim]Note: {scenario_input.notes}[/dim]\n")
    
    # Initialize and run agent
    try:
        agent = AgentLoop()
        
        console.print("[bold green]🚀 Starting Agent Execution...[/bold green]\n")
        
        result = agent.run(
            scenario_input=scenario_input,
            scenario_dir=mock_dir,
            flags=flags
        )
        
        # Show results summary
        console.print("\n" + "="*80 + "\n")
        
        console.print(Panel(
            f"""**🎯 EXECUTION SUMMARY**

**Strategy:** {result.get('strategy', 'unknown')}
**Primary Issue:** {result.get('primary_hypothesis', 'unknown')}  
**Confidence:** {result.get('confidence', 0):.2f}
**Risk Level:** {result.get('risk_level', 'unknown').upper()}
**Total Steps:** {result.get('total_steps', 0)}
**Trace File:** {result.get('trace_file', 'not saved')}
""",
            title="Final Results",
            title_align="left",
            border_style="bold green"
        ))
        
        # Show JSON output for programmatic use
        console.print("\n[bold]📋 JSON Output (for programmatic use):[/bold]")
        json_output = {
            'status': 'success',
            'strategy': result.get('strategy'),
            'primary_hypothesis': result.get('primary_hypothesis'),
            'confidence': result.get('confidence'),
            'risk_level': result.get('risk_level'),
            'recommendations': result.get('recommendations', []),
            'all_hypotheses': result.get('all_hypotheses', {}),
            'total_steps': result.get('total_steps'),
            'trace_file': result.get('trace_file')
        }
        console.print(JSON.from_data(json_output))
        
        # Generate markdown summary
        console.print("\n[bold]📝 Markdown Summary:[/bold]")
        # Load the trace file that was just saved
        trace_file = result.get('trace_file')
        trace_data = None
        if trace_file:
            try:
                trace_data = agent.trace_manager.load_trace(trace_file)
            except Exception:
                trace_data = None
        
        markdown_summary = generate_markdown_summary(result, scenario_input, trace_data)
        console.print(Panel(markdown_summary, border_style="dim"))
        
        # Generate enhanced report if OpenAI is available and not skipped
        if not args.no_openai:
            try:
                from enhanced_report import generate_enhanced_report
                enhanced_report_path = generate_enhanced_report(result, scenario_input, trace_data, language=args.lang)
                if enhanced_report_path:
                    console.print(f"\n[bold green]📋 Enhanced Report Generated:[/bold green] {enhanced_report_path}")
                else:
                    console.print("[dim yellow]💡 Set OPENAI_API_KEY environment variable to generate enhanced reports[/dim yellow]")
            except Exception as e:
                console.print(f"[dim]Enhanced report generation skipped: {str(e)}[/dim]")
        else:
            console.print("[dim]OpenAI enhanced report generation skipped (--no-openai flag)[/dim]")
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Agent execution interrupted by user[/yellow]")
        sys.exit(1)
        
    except Exception as e:
        console.print(f"\n[red]❌ Agent execution failed: {e}[/red]")
        console.print(f"[dim]Error type: {type(e).__name__}[/dim]")
        sys.exit(1)


def generate_markdown_summary(result: dict, scenario: ScenarioInput, trace_data: dict = None) -> str:
    """Generate a markdown summary of results with execution flow diagram."""
    
    recommendations = result.get('recommendations', [])
    rec_text = "\n".join([f"- {rec}" for rec in recommendations[:3]])  # Top 3 recommendations
    
    hypothesis_text = ""
    all_hyps = result.get('all_hypotheses', {})
    if all_hyps:
        hypothesis_text = "\n".join([f"- {name}: {belief:.2f}" for name, belief in list(all_hyps.items())[:3]])
    
    # Generate execution flow diagram
    flow_diagram = generate_execution_flow_diagram(trace_data) if trace_data else ""
    
    markdown = f"""# Amazon Ads Analysis - {scenario.asin}

**Goal:** {scenario.goal}  
**Analysis Date:** Today  
**Confidence Level:** {result.get('confidence', 0):.2f}

## Primary Finding
**Issue:** {result.get('primary_hypothesis', 'Unknown').replace('_', ' ').title()}  
**Risk Level:** {result.get('risk_level', 'unknown').upper()}

## Execution Flow
{flow_diagram}

## Top Recommendations
{rec_text}

## Hypothesis Confidence Scores
{hypothesis_text}

---
*Generated by AI Agent in {result.get('total_steps', 0)} analysis steps*
"""
    
    return markdown


def generate_execution_flow_diagram(trace_data: dict) -> str:
    """Generate a text-based execution flow diagram from trace data."""
    if not trace_data or 'execution_trace' not in trace_data:
        return "No execution trace available"
    
    trace_entries = trace_data['execution_trace']
    steps = []
    
    # Extract step information
    current_step = 0
    tool_actions = {}
    belief_changes = {}
    
    for entry in trace_entries:
        if entry['type'] == 'decision' and 'selected_tool' in entry['data']:
            current_step += 1
            tool_name = entry['data']['selected_tool']
            tool_actions[current_step] = tool_name
        
        elif entry['type'] == 'action' and 'result' in entry['data']:
            result = entry['data']['result']
            status = "✅" if result['ok'] else "❌"
            if current_step in tool_actions:
                tool_actions[current_step] = f"{tool_actions[current_step]} {status}"
        
        elif entry['type'] == 'update' and 'belief_changes' in entry['data']:
            changes = entry['data']['belief_changes']
            significant_changes = []
            for hyp, change in changes.items():
                old = change.get('old', 0)
                new = change.get('new', 0)
                if abs(new - old) > 0.01:  # Significant change
                    arrow = "↗️" if new > old else "↘️"
                    significant_changes.append(f"{hyp}: {old:.2f}→{new:.2f}{arrow}")
            if significant_changes:
                belief_changes[current_step] = significant_changes
    
    # Create flow diagram
    flow_lines = ["```", "🔄 AGENT EXECUTION FLOW", ""]
    
    for step in range(1, current_step + 1):
        # Step header
        flow_lines.append(f"Step {step}: {tool_actions.get(step, 'Unknown')}")
        
        # Belief changes if any
        if step in belief_changes:
            for change in belief_changes[step][:2]:  # Show top 2 changes
                flow_lines.append(f"   └─ {change}")
        
        # Add connector except for last step
        if step < current_step:
            flow_lines.append("   │")
    
    flow_lines.extend(["", "```"])
    
    return "\n".join(flow_lines)


if __name__ == '__main__':
    main()