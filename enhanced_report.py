"""Enhanced report generation with OpenAI integration for human-friendly analysis."""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class EnhancedReportGenerator:
    """Generate enhanced human-friendly reports using OpenAI."""
    
    def __init__(self):
        self.openai_client = None
        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
    
    def generate_enhanced_report(self, result: dict, scenario_input, trace_data: dict = None) -> Optional[str]:
        """Generate an enhanced report with human-friendly analysis and visualizations."""
        
        if not self.openai_client:
            return None
            
        try:
            # Prepare context data
            context = self._prepare_analysis_context(result, scenario_input, trace_data)
            
            # Generate human-friendly analysis
            analysis = self._generate_analysis_with_ai(context)
            
            if analysis:
                # Generate the enhanced markdown report
                enhanced_report = self._create_enhanced_markdown(analysis, result, scenario_input, trace_data)
                
                # Save to file
                return self._save_report(enhanced_report, scenario_input.asin)
                
        except Exception as e:
            print(f"[dim yellow]⚠️  Enhanced report generation failed: {str(e)}[/dim yellow]")
            import traceback
            print(f"[dim]Full traceback: {traceback.format_exc()}[/dim]")
            return None
        
        return None
    
    def _prepare_analysis_context(self, result: dict, scenario_input, trace_data: dict) -> str:
        """Prepare detailed step-by-step execution context for AI analysis."""
        
        goal = scenario_input.goal
        asin = scenario_input.asin
        
        # Extract detailed execution steps
        execution_details = []
        if trace_data and 'execution_trace' in trace_data:
            step_counter = 0
            current_step = {}
            
            for entry in trace_data['execution_trace']:
                entry_type = entry['type']
                data = entry['data']
                
                if entry_type == 'decision' and 'selected_tool' in data:
                    step_counter += 1
                    current_step = {
                        'step': step_counter,
                        'tool': data['selected_tool'],
                        'reasoning': data.get('reasoning', 'No reasoning provided')
                    }
                
                elif entry_type == 'action' and 'result' in data and current_step:
                    tool_result = data['result']
                    current_step['success'] = tool_result['ok']
                    current_step['findings'] = tool_result.get('data', {})
                    current_step['error'] = tool_result.get('error', '') if not tool_result['ok'] else None
                    
                elif entry_type == 'update' and 'belief_changes' in data and current_step:
                    current_step['belief_changes'] = data['belief_changes']
                    # Step is complete, add it to execution details
                    execution_details.append(current_step)
                    current_step = {}
        
        # Format execution steps for AI
        steps_text = ""
        for step_info in execution_details:
            status = "✅ Success" if step_info.get('success') else "❌ Failed"
            steps_text += f"""
Step {step_info['step']}: {step_info['tool']} {status}
- Reasoning: {step_info.get('reasoning', 'No reasoning')}
- Findings: {self._format_findings(step_info.get('findings', {}))}
"""
            if step_info.get('error'):
                steps_text += f"- Error: {step_info['error']}\n"
            
            # Add belief changes
            if step_info.get('belief_changes'):
                steps_text += "- Belief Updates:\n"
                for hyp, changes in step_info['belief_changes'].items():
                    old = changes.get('old', 0)
                    new = changes.get('new', 0)
                    if abs(new - old) > 0.01:
                        arrow = "↗️" if new > old else "↘️"
                        steps_text += f"  * {hyp}: {old:.2f} → {new:.2f} {arrow}\n"
            steps_text += "\n"
        
        context = f"""
Amazon Advertising Agent Execution Analysis:

ASIN: {asin}
Goal: {goal}

Please analyze this step-by-step execution and provide insights into the agent's reasoning process, what it discovered at each step, and how it arrived at its conclusions.

DETAILED EXECUTION STEPS:
{steps_text}

Focus on explaining:
1. The agent's decision-making process at each step
2. What each tool revealed and why it was important
3. How the agent's understanding evolved through the process
4. Any challenges or errors encountered and how they were handled
"""
        return context
    
    def _format_findings(self, findings: dict) -> str:
        """Format tool findings in a readable way."""
        if not findings:
            return "No specific findings recorded"
        
        # Extract key metrics and information
        key_info = []
        for key, value in findings.items():
            if key in ['quality_score', 'grade', 'issues_found']:
                key_info.append(f"{key.replace('_', ' ')}: {value}")
            elif key in ['total_impressions', 'overall_ctr', 'overall_acos']:
                key_info.append(f"{key.replace('_', ' ')}: {value}")
            elif key in ['competitive_pressure', 'price_positioning']:
                key_info.append(f"{key.replace('_', ' ')}: {value}")
        
        return "; ".join(key_info) if key_info else str(findings)[:100]
    
    def _generate_analysis_with_ai(self, context: str) -> Optional[dict]:
        """Use OpenAI to generate human-friendly analysis."""
        
        prompt = f"""You are analyzing the step-by-step execution of an AI agent that diagnoses Amazon advertising issues. Focus on explaining the agent's reasoning process and what it discovered at each step.

{context}

Please provide a detailed analysis structured as follows:

1. EXECUTION_OVERVIEW: Brief summary of the agent's overall approach and methodology
2. STEP_BY_STEP_ANALYSIS: Detailed explanation of what happened at each step, why the agent made each decision, and what it learned
3. REASONING_EVOLUTION: How the agent's understanding evolved through the process - what changed its mind and why
4. DISCOVERY_INSIGHTS: Key discoveries made during execution and their significance 
5. PROCESS_EVALUATION: Assessment of the agent's decision-making process and any noteworthy aspects

Focus on:
- The agent's thought process and reasoning
- What each tool revealed and why it was significant
- How evidence was evaluated and integrated
- The logical flow from observation to conclusion
- Any adaptive behavior when plans changed

Write as if explaining to someone who wants to understand how AI reasoning works step-by-step.
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful Amazon advertising consultant who explains complex data in simple business terms."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            return self._parse_ai_response(content)
            
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            return None
    
    def _parse_ai_response(self, content: str) -> dict:
        """Parse the AI response into structured components."""
        # Simple fallback: if parsing fails, use the whole content as execution overview
        sections = {
            'EXECUTION_OVERVIEW': content.strip()[:500] + '...',
            'STEP_BY_STEP_ANALYSIS': '• Agent executed systematic analysis of advertising performance',
            'REASONING_EVOLUTION': 'Agent updated beliefs based on evidence collected during execution',
            'DISCOVERY_INSIGHTS': 'Key insights were discovered through iterative tool execution',
            'PROCESS_EVALUATION': 'Agent demonstrated effective reasoning and evidence integration'
        }
        
        # Try to parse structured content if available
        keywords = ['EXECUTION_OVERVIEW', 'STEP_BY_STEP_ANALYSIS', 'REASONING_EVOLUTION', 'DISCOVERY_INSIGHTS', 'PROCESS_EVALUATION']
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Check if this line contains any keyword
            found_keyword = None
            for keyword in keywords:
                if keyword.replace('_', ' ').upper() in line.upper() or keyword.upper() in line.upper():
                    found_keyword = keyword
                    break
            
            if found_keyword:
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = found_keyword
                # Extract content after keyword (remove markdown, numbers, colons)
                after_keyword = line
                for sep in [':', '**', '*', '1.', '2.', '3.', '4.', '5.']:
                    if sep in after_keyword:
                        parts = after_keyword.split(sep)
                        if len(parts) > 1:
                            after_keyword = sep.join(parts[1:])
                current_content = [after_keyword.strip()] if after_keyword.strip() else []
            elif current_section and line:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _create_enhanced_markdown(self, analysis: dict, result: dict, scenario_input, trace_data: dict) -> str:
        """Create the enhanced markdown report."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Generate ASCII chart placeholder based on AI suggestion
        chart_placeholder = self._generate_ascii_chart(result, analysis.get('CHART_SUGGESTION', ''))
        
        report = f"""# 🤖 AI Agent Execution Analysis
**ASIN:** {scenario_input.asin} | **Goal:** {scenario_input.goal} | **Generated:** {timestamp}

---

## 🎯 Execution Overview

{analysis.get('EXECUTION_OVERVIEW', 'Agent executed systematic analysis of advertising performance.')}

**Final Confidence Level:** {result.get('confidence', 0):.0%} | **Total Steps:** {result.get('total_steps', 'Unknown')}

---

## 🔍 Step-by-Step Analysis

{analysis.get('STEP_BY_STEP_ANALYSIS', 'Detailed step analysis not available.')}

---

## 📈 Agent's Reasoning Evolution

{analysis.get('REASONING_EVOLUTION', 'Reasoning evolution not documented.')}

---

## 💡 Key Discoveries

{analysis.get('DISCOVERY_INSIGHTS', 'Key discoveries not documented.')}

---

## 🏁 Final Hypothesis Rankings

{chart_placeholder}

**Agent's Conclusion:** {result.get('primary_hypothesis', 'Unknown').replace('_', ' ').title()}

### Final Actions Recommended:
{chr(10).join([f"- {rec}" for rec in result.get('recommendations', [])[:3]])}

---

## 🔬 Process Evaluation

{analysis.get('PROCESS_EVALUATION', 'Process evaluation not available.')}

---

## 🔧 Execution Trace

### Tools Executed:
{self._get_detailed_tools_trace(trace_data)}

### Hypothesis Confidence Evolution:
{chr(10).join([f"- **{name.replace('_', ' ').title()}:** {belief:.0%}" for name, belief in result.get('all_hypotheses', {}).items()])}

---

*🤖 This report analyzes AI agent execution with step-by-step reasoning powered by OpenAI GPT-3.5*
"""
        
        return report
    
    def _generate_ascii_chart(self, result: dict, chart_suggestion: str) -> str:
        """Generate a simple ASCII chart based on hypothesis confidence scores."""
        
        hypotheses = result.get('all_hypotheses', {})
        if not hypotheses:
            return "No data available for visualization."
        
        # Create a simple horizontal bar chart
        chart_lines = ["```", "Hypothesis Confidence Levels:"]
        chart_lines.append("")
        
        # Sort by confidence
        sorted_hyps = sorted(hypotheses.items(), key=lambda x: x[1], reverse=True)
        
        for name, confidence in sorted_hyps[:5]:  # Top 5
            # Format name
            display_name = name.replace('h1_', '').replace('h2_', '').replace('h3_', '').replace('h4_', '').replace('h5_', '').replace('_', ' ').title()
            
            # Create bar (each ■ represents ~10%)
            bar_length = int(confidence * 10)
            bar = "■" * bar_length + "□" * (10 - bar_length)
            
            # Format line
            chart_lines.append(f"{display_name:<20} │{bar}│ {confidence:.0%}")
        
        chart_lines.extend(["", "```"])
        
        if 'chart' in chart_suggestion.lower() or 'bar' in chart_suggestion.lower():
            return "\n".join(chart_lines)
        else:
            return "\n".join(chart_lines) + f"\n\n*Suggested visualization: {chart_suggestion}*"
    
    def _get_tools_summary(self, trace_data: dict) -> str:
        """Get summary of tools used in execution."""
        if not trace_data or 'execution_trace' not in trace_data:
            return "Unknown"
            
        tools = set()
        for entry in trace_data['execution_trace']:
            if entry['type'] == 'action' and 'tool' in entry['data']:
                tools.add(entry['data']['tool'])
        
        return ", ".join(sorted(tools))
    
    def _get_detailed_tools_trace(self, trace_data: dict) -> str:
        """Get detailed trace of tool execution."""
        if not trace_data or 'execution_trace' not in trace_data:
            return "No execution trace available"
        
        trace_lines = []
        step_num = 0
        
        for entry in trace_data['execution_trace']:
            if entry['type'] == 'decision' and 'selected_tool' in entry['data']:
                step_num += 1
                tool = entry['data']['selected_tool']
                reasoning = entry['data'].get('reasoning', 'No reasoning provided')
                trace_lines.append(f"**Step {step_num}:** Selected `{tool}`")
                trace_lines.append(f"- *Reasoning:* {reasoning}")
            
            elif entry['type'] == 'action' and 'result' in entry['data']:
                result = entry['data']['result']
                status = "✅ Success" if result['ok'] else "❌ Failed"
                trace_lines.append(f"- *Result:* {status}")
                if not result['ok'] and 'error' in result:
                    trace_lines.append(f"- *Error:* {result['error']}")
                trace_lines.append("")
        
        return "\n".join(trace_lines)
    
    def _save_report(self, report_content: str, asin: str) -> str:
        """Save the enhanced report to a markdown file."""
        
        # Create reports directory
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{asin}_{timestamp}.md"
        filepath = reports_dir / filename
        
        # Save file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return str(filepath)


def generate_enhanced_report(result: dict, scenario_input, trace_data: dict = None) -> Optional[str]:
    """Main function to generate enhanced report."""
    generator = EnhancedReportGenerator()
    return generator.generate_enhanced_report(result, scenario_input, trace_data)