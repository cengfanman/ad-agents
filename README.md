# Amazon Seller AI Agent

An autonomous AI Agent that helps Amazon sellers diagnose advertising performance issues through dynamic decision-making and tool selection.

## Project Goal

This project demonstrates Agent architecture (not workflow) by implementing an autonomous system that:
- Observes current context and data
- Forms and updates hypotheses about problems
- Dynamically selects appropriate tools based on information gain
- Adapts strategy based on evidence gathered
- Provides actionable recommendations

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
   python demo.py --scenario scenarios/scenario_low_impr.json --break-competitor
   ```

4. **Run All Scenarios (Smoke Test)**
   ```bash
   ./scripts/smoke.sh
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
3. **Act**: Select the most informative tool to run next, or terminate if confident enough

### Belief System & Information Gain
- Maintains confidence scores (0.0-1.0) for 5 core hypotheses about ad performance issues
- Evidence strength mapping: strong (+0.2), medium (+0.1), weak (+0.05), counter (-0.1)
- Tool selection based on information gain potential rather than fixed order
- Different scenario goals lead to different initial belief distributions

### Tool Selection Heuristics
- **High belief in H1 (Low Bids)** → prioritize `ads_metrics` to analyze bid performance
- **High belief in H2 (Keyword Coverage)** → use `ads_metrics` + `listing_audit` for keyword analysis  
- **High belief in H3 (Competitor Pressure)** → prioritize `competitor` tool
- **High belief in H4 (Listing Quality)** → use `listing_audit` first
- **High belief in H5 (Broad Match Waste)** → analyze with `ads_metrics`

### Termination Criteria
- **High Confidence**: belief ≥ 0.7 in primary hypothesis
- **Minimum Exploration**: At least 3 decision cycles completed
- **Tool Exhaustion**: All relevant tools used with inconclusive results
- **Maximum Iterations**: Hard limit at 5 steps to prevent infinite loops

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

# Simulated failure - competitor tool fails, agent adapts
python demo.py --scenario scenarios/scenario_low_impr.json --break-competitor
```

**Expected Fallback Behavior:**
1. Competitor tool fails with DataMissingError
2. Agent displays fallback suggestion: "Use listing_audit to check competitiveness"
3. Agent continues execution with alternative tools
4. Final recommendations adapt based on available data

## Testing & Validation

```bash
# Run comprehensive smoke test
./scripts/smoke.sh

# Test individual scenarios
python demo.py --scenario scenarios/scenario_low_impr.json          # → Should focus on bids/competition
python demo.py --scenario scenarios/scenario_high_acos.json         # → Should focus on waste reduction  
python demo.py --scenario scenarios/scenario_high_click_low_conv.json # → Should focus on listing quality
```

## Video Demo Script (5-8 minutes)

### Segment 1: Design Rationale (1-2 min)
- "This is an AI Agent, not a workflow - it makes autonomous decisions"
- "Show observe-think-act loop with dynamic tool selection"
- "Belief system updates based on evidence, not fixed rules"

### Segment 2: Different Paths Demo (3-4 min)  
- **Command 1**: `python demo.py --scenario scenarios/scenario_low_impr.json`
  - Show agent prioritizing ads_metrics → competitor (bid/competition focus)
  - Point out belief updates and reasoning
- **Command 2**: `python demo.py --scenario scenarios/scenario_high_acos.json`  
  - Show different tool selection (ads_metrics first for waste analysis)
  - Highlight different final recommendations

### Segment 3: Error Handling (1-2 min)
- **Command 3**: `python demo.py --scenario scenarios/scenario_low_impr.json --break-competitor`
- Show graceful degradation and fallback suggestions
- Demonstrate agent continues with alternative strategy

### Key Points to Emphasize
- **Decision logs**: Point out "DECIDE" sections showing tool selection reasoning
- **Belief updates**: Highlight how evidence changes hypothesis confidence  
- **Final rankings**: Show how different scenarios lead to different hypothesis rankings
- **Actionable output**: JSON + Markdown recommendations ready for implementation# ad-agents
