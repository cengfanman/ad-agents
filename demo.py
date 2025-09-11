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
    
    args = parser.parse_args()
    
    # Load scenario and determine data directory
    scenario_input, mock_dir = load_scenario(args.scenario)
    
    # Prepare flags for agent
    flags = {
        'ads_mode': args.mode,
        'break_competitor': args.break_competitor
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
**Test Flags:** {'Competitor failure enabled' if args.break_competitor else 'None'}
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
        markdown_summary = generate_markdown_summary(result, scenario_input)
        console.print(Panel(markdown_summary, border_style="dim"))
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Agent execution interrupted by user[/yellow]")
        sys.exit(1)
        
    except Exception as e:
        console.print(f"\n[red]❌ Agent execution failed: {e}[/red]")
        console.print(f"[dim]Error type: {type(e).__name__}[/dim]")
        sys.exit(1)


def generate_markdown_summary(result: dict, scenario: ScenarioInput) -> str:
    """Generate a markdown summary of results."""
    
    recommendations = result.get('recommendations', [])
    rec_text = "\n".join([f"- {rec}" for rec in recommendations[:3]])  # Top 3 recommendations
    
    hypothesis_text = ""
    all_hyps = result.get('all_hypotheses', {})
    if all_hyps:
        hypothesis_text = "\n".join([f"- {name}: {belief:.2f}" for name, belief in list(all_hyps.items())[:3]])
    
    markdown = f"""# Amazon Ads Analysis - {scenario.asin}

**Goal:** {scenario.goal}  
**Analysis Date:** Today  
**Confidence Level:** {result.get('confidence', 0):.2f}

## Primary Finding
**Issue:** {result.get('primary_hypothesis', 'Unknown').replace('_', ' ').title()}  
**Risk Level:** {result.get('risk_level', 'unknown').upper()}

## Top Recommendations
{rec_text}

## Hypothesis Confidence Scores
{hypothesis_text}

---
*Generated by AI Agent in {result.get('total_steps', 0)} analysis steps*
"""
    
    return markdown


if __name__ == '__main__':
    main()