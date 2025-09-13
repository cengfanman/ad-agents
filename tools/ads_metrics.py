import os
import orjson
from pathlib import Path
from typing import Dict, Any

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from .base import BaseTool, wrap_call
from agent.errors import DataMissingError
from agent.types import ToolResult


class AdsMetricsTool(BaseTool):
    """Tool for analyzing advertising metrics data."""
    
    def __init__(self):
        super().__init__("ads_metrics", timeout_s=10)
    
    @wrap_call
    def run(self, ctx: Dict[str, Any]) -> ToolResult:
        """
        Analyze ads metrics based on mode (keyword or campaign).
        
        Expected context:
        - scenario_dir: Path to scenario data directory
        - mode: 'keyword' or 'campaign' (defaults to 'keyword')
        - flags: Dict that may contain 'break_ads' for testing
        """
        # Check for test mode break
        flags = ctx.get('flags', {})
        if flags.get('break_ads', False):
            raise DataMissingError("Simulated ads metrics data unavailable (test mode)")
        
        scenario_dir = Path(ctx['scenario_dir'])
        mode = ctx.get('mode', 'keyword')
        
        if mode == 'keyword':
            file_path = scenario_dir / 'ads_keywords.json'
        elif mode == 'campaign':
            file_path = scenario_dir / 'ads_campaign.json'
        else:
            raise ValueError(f"Invalid ads_metrics mode: {mode}. Must be 'keyword' or 'campaign'")
        
        if not file_path.exists():
            raise DataMissingError(f"Ads metrics file not found: {file_path}")
        
        # Load raw data
        with open(file_path, 'rb') as f:
            raw_data = orjson.loads(f.read())
        
        # Calculate derived metrics for analysis
        if mode == 'keyword':
            keywords = raw_data.get('keywords', [])
            
            # Calculate aggregated metrics
            total_impressions = sum(k.get('impressions', 0) for k in keywords)
            total_clicks = sum(k.get('clicks', 0) for k in keywords)
            total_spend = sum(k.get('spend', 0) for k in keywords)
            total_orders = sum(k.get('orders', 0) for k in keywords)
            total_revenue = sum(k.get('revenue', 0) for k in keywords)
            
            avg_ctr = total_clicks / total_impressions if total_impressions > 0 else 0
            avg_cvr = total_orders / total_clicks if total_clicks > 0 else 0
            overall_acos = total_spend / total_revenue if total_revenue > 0 else float('inf')
            
            # Analyze performance patterns
            low_impr_keywords = [k for k in keywords if k.get('impressions', 0) < 500]
            high_cpc_keywords = [k for k in keywords if k.get('cpc', 0) > 0.5]
            no_conversion_keywords = [k for k in keywords if k.get('orders', 0) == 0]
            
            analysis_data = {
                'raw_data': raw_data,
                'aggregated_metrics': {
                    'total_impressions': total_impressions,
                    'total_clicks': total_clicks,
                    'total_spend': round(total_spend, 2),
                    'total_orders': total_orders,
                    'total_revenue': round(total_revenue, 2),
                    'avg_ctr': round(avg_ctr, 4),
                    'avg_cvr': round(avg_cvr, 4),
                    'overall_acos': round(overall_acos, 2) if overall_acos != float('inf') else None
                },
                'performance_issues': {
                    'low_impression_keywords': len(low_impr_keywords),
                    'high_cpc_keywords': len(high_cpc_keywords),
                    'no_conversion_keywords': len(no_conversion_keywords),
                    'total_keywords': len(keywords)
                },
                'keyword_details': {
                    'low_impression': low_impr_keywords[:3],  # Top 3 for analysis
                    'high_cpc': high_cpc_keywords[:3],
                    'no_conversion': no_conversion_keywords[:3]
                }
            }
        else:  # campaign mode
            campaigns = raw_data.get('campaigns', [])
            analysis_data = {
                'raw_data': raw_data,
                'campaign_count': len(campaigns),
                'performance_summary': campaigns  # For campaign analysis
            }
        
        return ToolResult(
            name=self.name,
            ok=True,
            data=analysis_data,
            meta={
                'mode': mode,
                'source': str(file_path),
                'keywords_analyzed': len(keywords) if mode == 'keyword' else 0,
                'latency_ms': 0  # Will be set by wrap_call
            }
        )