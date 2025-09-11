#!/bin/bash
# Smoke test script for Amazon Seller AI Agent
# Tests different scenarios and shows summary results

echo "🧪 Amazon Seller AI Agent - Smoke Test"
echo "========================================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to run a scenario and extract key results
run_scenario() {
    local scenario_file=$1
    local scenario_name=$2
    
    echo -e "${BLUE}Testing: $scenario_name${NC}"
    echo "----------------------------------------"
    
    # Run the agent and capture output
    if python demo.py --scenario "$scenario_file" > temp_output.txt 2>&1; then
        # Extract key information from output
        echo -e "${GREEN}✅ Execution: SUCCESS${NC}"
        
        # Extract final action summary (look for strategy and confidence)
        strategy=$(grep -o '"strategy": "[^"]*"' temp_output.txt | cut -d'"' -f4 | head -1)
        primary_hyp=$(grep -o '"primary_hypothesis": "[^"]*"' temp_output.txt | cut -d'"' -f4 | head -1)
        confidence=$(grep -o '"confidence": [0-9.]*' temp_output.txt | cut -d':' -f2 | tr -d ' ' | head -1)
        total_steps=$(grep -o '"total_steps": [0-9]*' temp_output.txt | cut -d':' -f2 | tr -d ' ' | head -1)
        
        echo "📋 Strategy: ${strategy:-unknown}"
        echo "🎯 Primary Issue: ${primary_hyp:-unknown}"
        echo "🎲 Confidence: ${confidence:-0.00}"
        echo "🔄 Steps: ${total_steps:-0}"
        
        # Extract final belief rankings (top 3)
        echo "🧠 Final Beliefs:"
        python3 -c "
import re, json
with open('temp_output.txt', 'r') as f:
    content = f.read()
    
# Find all_hypotheses section
match = re.search(r'\"all_hypotheses\":\s*\{([^}]+)\}', content)
if match:
    hyp_text = '{' + match.group(1) + '}'
    try:
        hyp_data = json.loads(hyp_text)
        for name, score in sorted(hyp_data.items(), key=lambda x: x[1], reverse=True)[:3]:
            clean_name = name.replace('h1_', '').replace('h2_', '').replace('h3_', '').replace('h4_', '').replace('h5_', '').replace('_', ' ').title()
            print(f'   • {clean_name}: {score:.2f}')
    except:
        print('   • Unable to parse beliefs')
else:
    print('   • No belief data found')
"
        
    else
        echo -e "${RED}❌ Execution: FAILED${NC}"
        echo "Error details:"
        tail -5 temp_output.txt | sed 's/^/   /'
    fi
    
    echo
    rm -f temp_output.txt
}

# Test different scenarios
echo "Running smoke tests for all scenarios..."
echo

# Test 1: Low Impressions
if [ -f "scenarios/scenario_low_impr.json" ]; then
    run_scenario "scenarios/scenario_low_impr.json" "Low Impressions Scenario"
else
    echo -e "${YELLOW}⚠️  scenario_low_impr.json not found${NC}"
fi

# Test 2: High Click Low Conversion
if [ -f "scenarios/scenario_high_click_low_conv.json" ]; then
    run_scenario "scenarios/scenario_high_click_low_conv.json" "High Click Low Conversion"
else
    echo -e "${YELLOW}⚠️  scenario_high_click_low_conv.json not found${NC}"
fi

# Test 3: High ACOS
if [ -f "scenarios/scenario_high_acos.json" ]; then
    run_scenario "scenarios/scenario_high_acos.json" "High ACOS Scenario"
else
    echo -e "${YELLOW}⚠️  scenario_high_acos.json not found${NC}"
fi

echo "========================================"
echo -e "${GREEN}🎉 Smoke test completed!${NC}"
echo
echo "To test error handling, run:"
echo "python demo.py --scenario scenarios/scenario_low_impr.json --break-competitor"
echo