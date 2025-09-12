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
    
    def __init__(self, language='en'):
        self.openai_client = None
        self.language = language
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
        
        if self.language == 'zh-tw':
            language_instruction = "請用繁體中文回覆，並提供豐富詳細的解釋。"
            prompt = f"""你正在分析一個用於診斷Amazon廣告問題的AI代理的逐步執行過程。作為一位專業的AI教學專家，請詳細解釋代理的推理過程，讓讀者能深入理解AI如何思考和學習。

{context}

請提供非常詳細的分析，結構化如下：

1. EXECUTION_OVERVIEW：
   - 詳細描述代理的整體策略和方法論
   - 解釋為什麼選擇這種方法來解決問題
   - 說明代理如何設定初始假設和目標

2. STEP_BY_STEP_ANALYSIS：
   - 對每一步驟進行深入分析，包括：
     * 代理在這一步的具體思考過程
     * 為什麼選擇使用特定工具
     * 工具返回的數據意味著什麼
     * 這些發現如何影響代理的下一步決策
     * 任何意外的結果以及代理如何應對

3. REASONING_EVOLUTION：
   - 詳細追蹤代理信念的變化軌跡
   - 解釋每次信念更新的邏輯依據
   - 分析代理如何整合新證據和舊知識
   - 描述代理學習和適應的過程

4. DISCOVERY_INSIGHTS：
   - 深入解釋每個關鍵發現的商業含義
   - 分析這些發現對Amazon廣告策略的影響
   - 說明代理如何從數據中提取洞察
   - 討論發現之間的相互關聯

5. PROCESS_EVALUATION：
   - 評估代理的決策品質和邏輯性
   - 分析代理處理不確定性和錯誤的能力
   - 討論代理推理過程的優點和局限性
   - 提供對AI推理機制的深度見解

6. EDUCATIONAL_INSIGHTS：
   - 從這個案例中可以學到哪些AI推理原理
   - 解釋代理行為背後的機器學習概念
   - 討論這種AI方法在其他場景的應用潛力

請用教學的語調寫作，包含豐富的解釋和例子，幫助讀者理解AI推理的複雜性和精妙之處。{language_instruction}
"""
        else:
            prompt = f"""You are analyzing the step-by-step execution of an AI agent that diagnoses Amazon advertising issues. As a professional AI education expert, provide detailed explanations that help readers deeply understand how AI thinks and learns.

{context}

Please provide a comprehensive and detailed analysis structured as follows:

1. EXECUTION_OVERVIEW:
   - Detailed description of the agent's overall strategy and methodology
   - Explain why this approach was chosen to solve the problem
   - Describe how the agent set initial hypotheses and goals

2. STEP_BY_STEP_ANALYSIS:
   - Deep analysis of each step, including:
     * The agent's specific thought process at this step
     * Why it chose to use a particular tool
     * What the tool's returned data means
     * How these findings influenced the agent's next decision
     * Any unexpected results and how the agent adapted

3. REASONING_EVOLUTION:
   - Detailed tracking of the agent's belief change trajectory
   - Explain the logical basis for each belief update
   - Analyze how the agent integrates new evidence with old knowledge
   - Describe the agent's learning and adaptation process

4. DISCOVERY_INSIGHTS:
   - In-depth explanation of the business implications of each key finding
   - Analyze how these discoveries impact Amazon advertising strategy
   - Explain how the agent extracts insights from data
   - Discuss the interconnections between findings

5. PROCESS_EVALUATION:
   - Evaluate the quality and logic of the agent's decisions
   - Analyze the agent's ability to handle uncertainty and errors
   - Discuss strengths and limitations of the agent's reasoning process
   - Provide deep insights into AI reasoning mechanisms

6. EDUCATIONAL_INSIGHTS:
   - What AI reasoning principles can be learned from this case
   - Explain the machine learning concepts behind agent behavior
   - Discuss the potential application of this AI approach in other scenarios

Write in an educational tone with rich explanations and examples to help readers understand the complexity and sophistication of AI reasoning.
"""

        try:
            system_content = "You are an expert AI educator and Amazon advertising consultant who provides detailed, educational explanations about AI reasoning and business insights." if self.language == 'en' else "你是一位專業的AI教育專家和Amazon廣告顧問，提供關於AI推理和商業洞察的詳細教學解釋。"
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
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
            'PROCESS_EVALUATION': 'Agent demonstrated effective reasoning and evidence integration',
            'EDUCATIONAL_INSIGHTS': 'This case demonstrates key principles of AI reasoning and decision-making'
        }
        
        # Try to parse structured content if available
        keywords = ['EXECUTION_OVERVIEW', 'STEP_BY_STEP_ANALYSIS', 'REASONING_EVOLUTION', 'DISCOVERY_INSIGHTS', 'PROCESS_EVALUATION', 'EDUCATIONAL_INSIGHTS']
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
        
        if self.language == 'zh-tw':
            report = f"""# 🤖 AI 代理執行分析
**ASIN:** {scenario_input.asin} | **目標:** {scenario_input.goal} | **生成時間:** {timestamp}

---

## 🎯 執行概述

{analysis.get('EXECUTION_OVERVIEW', 'AI代理執行了系統性的廣告效能分析。')}

**最終信心水準:** {result.get('confidence', 0):.0%} | **總步數:** {result.get('total_steps', '未知')}

---

## 🔍 逐步分析

{analysis.get('STEP_BY_STEP_ANALYSIS', '詳細步驟分析不可用。')}

---

## 📈 代理推理演化

{analysis.get('REASONING_EVOLUTION', '推理演化未記錄。')}

---

## 💡 關鍵發現

{analysis.get('DISCOVERY_INSIGHTS', '關鍵發現未記錄。')}

---

## 🏁 最終假設排名

{chart_placeholder}

**代理結論:** {result.get('primary_hypothesis', '未知').replace('_', ' ').title()}

### 最終建議行動:
{chr(10).join([f"- {rec}" for rec in result.get('recommendations', [])[:3]])}

---

## 🔬 過程評估

{analysis.get('PROCESS_EVALUATION', '過程評估不可用。')}

---

## 🎓 教學洞察

{analysis.get('EDUCATIONAL_INSIGHTS', 'AI推理教學洞察不可用。')}

---

## 🔧 執行追蹤

### 已執行的工具:
{self._get_detailed_tools_trace(trace_data)}

### 假設信心度演化:
{chr(10).join([f"- **{name.replace('_', ' ').title()}:** {belief:.0%}" for name, belief in result.get('all_hypotheses', {}).items()])}

---

*🤖 此報告使用OpenAI GPT-4o逐步推理分析AI代理執行過程*
"""
        else:
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

## 🎓 Educational Insights

{analysis.get('EDUCATIONAL_INSIGHTS', 'AI reasoning educational insights not available.')}

---

## 🔧 Execution Trace

### Tools Executed:
{self._get_detailed_tools_trace(trace_data)}

### Hypothesis Confidence Evolution:
{chr(10).join([f"- **{name.replace('_', ' ').title()}:** {belief:.0%}" for name, belief in result.get('all_hypotheses', {}).items()])}

---

*🤖 This report analyzes AI agent execution with step-by-step reasoning powered by OpenAI GPT-4o*
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


def generate_enhanced_report(result: dict, scenario_input, trace_data: dict = None, language='en') -> Optional[str]:
    """Main function to generate enhanced report."""
    generator = EnhancedReportGenerator(language=language)
    return generator.generate_enhanced_report(result, scenario_input, trace_data)