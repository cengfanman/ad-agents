# Amazon Seller AI Agent

An autonomous AI Agent that helps Amazon sellers diagnose advertising performance issues through dynamic decision-making and tool selection.

## Project Goal

This project demonstrates Agent architecture (not workflow) by implementing an autonomous system that:
- Observes current context and data
- Forms and updates hypotheses about problems
- Dynamically selects appropriate tools based on information gain
- Adapts strategy based on evidence gathered
- Provides actionable recommendations

## Core Design Philosophy

### Hypothesis-Driven Reasoning Architecture

**This Agent adopts a hypothesis-driven reasoning architecture:**

1. **Multi-Hypothesis Parallel Tracking** - Agent simultaneously maintains multiple possible problem hypotheses
2. **Dynamic Tool Selection** - Selects the most appropriate diagnostic tools based on current belief state
3. **Evidence Accumulation Updates** - Updates confidence levels for each hypothesis after each tool execution
4. **Adaptive Decision Making** - Adjusts next strategy based on new evidence

### Technical Architecture Highlights

- **Modular Tool System**: ads_metrics, listing_audit, competitor, inventory, etc.
- **Bayesian Belief Updates**: Quantifies uncertainty for scientific decision-making
- **Complete Execution Tracking**: Detailed records of every decision process
- **AI-Enhanced Report Generation**: Uses OpenAI GPT-4o to generate in-depth analysis reports with Chinese and English support

## Quick Start

1. **Setup Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run Different Scenarios**
   ```bash
   # Test low impressions scenario - agent should prioritize bid analysis
   python demo.py --scenario scenarios/scenario_low_impr.json
   
   # Test high ACOS scenario - agent should focus on broad match waste
   python demo.py --scenario scenarios/scenario_high_acos.json
   
   # Test conversion issues - agent should prioritize listing quality
   python demo.py --scenario scenarios/scenario_high_click_low_conv.json
   
   ```

3. **Test Error Handling**
   ```bash
   # Simulate competitor tool failure to see fallback behavior
   python demo.py --scenario scenarios/scenario_low_impr.json --break-inventory
   ```

## Expected Outputs

Different scenarios should lead to different agent behavior:

- **Low Impressions** → Agent prioritizes `ads_metrics` then `competitor` (bid/competition issues)
- **High ACOS** → Agent focuses on `ads_metrics` to identify waste, may check `listing_audit`
- **Low Conversion** → Agent prioritizes `listing_audit` then `competitor` (quality/competition)

## Project Structure

```
amazon-agent/
├─ agent/                 # Core agent logic
│  ├─ loop.py            # Observe→Think→Act main loop (≥3 rounds)
│  ├─ policy.py          # Hypothesis management, belief updates, tool selection
│  ├─ memory.py          # Working memory and trace recording
│  ├─ reasoning.py       # Structured logging and reasoning display
│  ├─ errors.py          # Error handling and fallback strategies
│  └─ types.py           # Data type definitions
├─ tools/                # Agent tools
│  ├─ base.py           # Tool interface and common functionality
│  ├─ ads_metrics.py    # Advertisement metrics analysis
│  ├─ inventory.py      # Inventory status checking
│  ├─ listing_audit.py  # Product listing quality audit
│  └─ competitor.py     # Competitor analysis
├─ mock/                # Mock data for different scenarios
├─ scenarios/           # Scenario definitions
├─ trace/              # Agent execution traces (auto-generated)
├─ scripts/            # Testing and utility scripts
└─ demo.py             # Main CLI interface
```

## Tools & Data Schema

### Available Tools

| Tool | Purpose | Input Schema | Key Outputs |
|------|---------|--------------|-------------|
| **ads_metrics** | Analyze keyword/campaign performance | `mode: 'keyword'|'campaign'` | CTR, ACOS, impression patterns, conversion issues |
| **competitor** | Market competition analysis | Standard context | Price positioning, market saturation, competitive pressure |
| **listing_audit** | Product listing quality check | Standard context | Quality score, optimization recommendations, conversion impact |
| **inventory** | Stock level and availability | Standard context | Days of inventory, stockout risk, ad spend impact |

### Data Placement

Mock data should be placed in `mock/<scenario_name>/` directories:
- `ads_keywords.json` - Keyword performance metrics (impressions, clicks, CPC, ACOS)
- `ads_campaign.json` - Campaign-level performance data  
- `inventory.json` - Stock levels and restock information
- `listing_audit.json` - Listing quality scores and audit results
- `competitor.json` - Competitive landscape analysis

### Evidence Collection

The agent automatically extracts evidence from tool results:
- **Strong Evidence** (+0.2): Clear indicators (e.g., ACOS > 1.0 for waste hypothesis)
- **Medium Evidence** (+0.1): Moderate indicators (e.g., CTR < 0.015 for quality issues)  
- **Weak Evidence** (+0.05): Minor indicators (e.g., low inventory affecting bids)
- **Counter Evidence** (-0.1): Evidence against hypothesis

## Tool System Overview

The agent is equipped with 4 specialized diagnostic tools, each designed for specific analysis functions:

### 1. Ads Metrics Tool - Advertisement Data Analysis
- **Function**: Analyzes keyword and campaign performance data
- **Output**: CTR, CVR, ACOS, impression metrics, and conversion issues
- **Intelligent Analysis**: Automatically identifies inefficient keywords and high-cost problems
- **Use Cases**: Foundation diagnosis for all advertising problems

### 2. Competitor Tool - Market Competition Analysis
- **Function**: Evaluates market competition pressure and positioning
- **Output**: Price competitiveness, advertising competition intensity, quality benchmarks
- **Intelligent Analysis**: Quantifies competitive pressure, identifies threats and opportunities
- **Use Cases**: Traffic issues, pricing strategy problems

### 3. Listing Audit Tool - Product Page Quality Review
- **Function**: Comprehensive evaluation of product listing quality
- **Output**: Title optimization, image quality, A+ content, rating analysis
- **Intelligent Analysis**: Calculates conversion impact potential, provides optimization recommendations
- **Use Cases**: Low conversion rates, product competitiveness issues

### 4. Inventory Tool - Stock Status Monitoring
- **Function**: Monitors inventory levels and restocking status
- **Output**: Days of inventory, stockout risk, restocking timeline
- **Intelligent Analysis**: Assesses impact on advertising strategy
- **Use Cases**: Abnormal advertising performance, inventory constraint issues

### Tool Collaboration Mechanism

The agent doesn't simply call tools, but engages in intelligent collaboration:
- **Dynamic Selection**: Chooses most relevant tools based on current hypotheses
- **Result Integration**: Synthesizes results from multiple tools for comprehensive analysis
- **Hypothesis Updates**: Adjusts problem hypotheses based on tool results
- **Strategy Adaptation**: Modifies next actions based on new evidence

## Evaluation Criteria Mapping

### Agent Architecture (60%)

| Criterion | Implementation |
|-----------|----------------|
| **Dynamic Decision Ability** | Policy engine selects tools based on current hypothesis confidence and information gain potential |
| **Reasoning Visibility** | Structured console logging shows observe/think/decide/act phases with belief updates |
| **Tool Usage** | Agent autonomously chooses from 4+ tools based on hypothesis strength and context |
| **Error Recovery** | Fallback mechanisms when tools fail, with alternative strategies |

### Engineering Implementation (40%)

| Criterion | Implementation |
|-----------|----------------|
| **Code Quality** | Modular architecture, type hints, clear separation of concerns |
| **Executability** | Single command demo with clear logging and trace output |
| **Time Management** | Focused on core Agent loop rather than peripheral features |

## Architecture Design

### Why Agent vs Workflow
- **Workflow**: Fixed sequence of operations (e.g., always run ads_metrics → competitor → listing_audit)
- **Agent**: Dynamic decision-making based on current beliefs and information gain potential

The agent demonstrates true autonomy by:
- Forming hypotheses about potential issues based on scenario goals
- Selecting tools dynamically based on which can provide the most informative evidence
- Updating beliefs as evidence is collected, changing strategy accordingly
- Adapting to tool failures with fallback strategies

### Core Loop: Observe → Think → Act
1. **Observe**: Gather context from scenario, previous tool results, and current state
2. **Think**: Update hypothesis confidence scores based on collected evidence  
3. **Decide**: Display tool mapping with usage status and select next tool
4. **Act**: Execute selected tool and collect evidence, or terminate if confident enough

**Enhanced Decision Display:**
- **Tool Mapping Table**: Shows hypothesis → tools mapping with real-time status
- **Usage Tracking**: Visual indicators (✓) for completed tools  
- **Hypothesis Status Identifiers**:
  - 🔍 marks the currently investigated hypothesis
  - ⭐ marks the highest-confidence hypothesis
- **Status Ratios**: Shows tool completion ratios (e.g., 1/2, 2/2) for each hypothesis
- **Detailed Reasoning**: Explains hypothesis selection logic and tool choice rationale

### Belief System & Information Gain
- Maintains confidence scores (0.0-1.0) for 5 core hypotheses about ad performance issues
- Evidence strength mapping: strong (+0.2), medium (+0.1), weak (+0.05), counter (-0.1)
- Tool selection based on information gain potential rather than fixed order
- Different scenario goals lead to different initial belief distributions

### Tool Selection Heuristics

The agent uses a hypothesis-to-tool mapping system for optimal information gain:

| Hypothesis | Primary Tools | Secondary Tools | Selection Logic |
|------------|---------------|-----------------|-----------------|
| **H1: Low Bids** | `ads_metrics` | - | Direct bid performance analysis |
| **H2: Keyword Coverage** | `ads_metrics` | `listing_audit` | Keyword performance + content analysis |
| **H3: Competitor Pressure** | `competitor` | `ads_metrics` | Market analysis first, then performance |
| **H4: Listing Quality** | `listing_audit` | `competitor` | Quality audit + competitive context |
| **H5: Broad Match Waste** | `ads_metrics` | - | Direct keyword waste analysis |

**Tool Selection Process:**
1. Rank hypotheses by confidence (belief score)
2. Select tools from top 2 hypotheses' preferred tools
3. Prefer unused tools for maximum information gain
4. Fall back to any unused tool if preferred tools exhausted

### Termination Criteria

The agent uses a sophisticated multi-layer stopping mechanism:

**1. Minimum Exploration Requirement (Hard Requirement)**
- Forces at least 3 decision cycles regardless of confidence level (assignment requirement)
- Prevents premature conclusions from limited data
- Ensures sufficient evidence collection and analysis

**2. Very High Confidence (≥ 0.8) + Minimum Steps**
- Terminates when primary hypothesis reaches 80%+ confidence AND at least 3 steps completed
- Indicates overwhelming evidence for a specific issue

**3. High Confidence (≥ 0.7) + Tool Completion + Minimum Steps**  
- Stops when primary hypothesis reaches 70%+ confidence AND
- All preferred tools for that hypothesis have been executed AND
- At least 3 decision cycles have been completed

**4. Maximum Iteration Limits**
- Hard limit at 5 steps to prevent infinite loops
- Ensures timely completion even with inconclusive evidence

**5. Tool Exhaustion**
- Stops when no more informative tools are available
- Graceful termination when evidence gathering is complete

**Example Decision Flow:**
```
Step 1: Confidence 0.8 → Continue (minimum 3 steps required)
Step 2: Confidence 0.8 → Continue (minimum 3 steps required)  
Step 3: Confidence 0.8+ → Stop (minimum requirement met + high confidence)

Assignment Hard Requirement: Must complete at least 3 decision iterations regardless of confidence
```

### Error Handling & Fallbacks
- Tool timeouts with automatic retry (1 retry with exponential backoff)
- Graceful degradation when tools fail (continue with alternative tools)
- Fallback recommendations: competitor failure → use listing_audit + ads_metrics
- Test mode flag `--break-competitor` to simulate failures

## Error Handling Demonstration

The agent includes comprehensive error handling:

```bash
# Normal execution - should complete successfully
python demo.py --scenario scenarios/scenario_low_impr.json

# Simulated failure - inventory tool fails, agent adapts
python demo.py --scenario scenarios/scenario_low_impr.json --break-inventory
```

**Expected Fallback Behavior:**
1. Competitor tool fails with DataMissingError
2. Agent displays fallback suggestion: "Use listing_audit to check competitiveness"
3. Agent continues execution with alternative tools
4. Final recommendations adapt based on available data

## Testing & Validation

```bash

# Test individual scenarios
python demo.py --scenario scenarios/scenario_low_impr.json          # → Should focus on bids/competition
python demo.py --scenario scenarios/scenario_high_acos.json         # → Should focus on waste reduction  
python demo.py --scenario scenarios/scenario_high_click_low_conv.json # → Should focus on listing quality
python demo.py --scenario scenarios/scenario_low_impr.json --break-inventory # Simulated failure - inventory tool fails, agent adapts
```

# ad-agents
