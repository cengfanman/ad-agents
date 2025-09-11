import orjson
from pathlib import Path
from typing import Dict, Any

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from .base import BaseTool, wrap_call
from agent.errors import DataMissingError
from agent.types import ToolResult


class CompetitorTool(BaseTool):
    """Tool for analyzing competitor landscape and market positioning."""
    
    def __init__(self):
        super().__init__("competitor", timeout_s=15)
    
    @wrap_call
    def run(self, ctx: Dict[str, Any]) -> ToolResult:
        """
        Analyze competitor data and market positioning.
        
        Expected context:
        - scenario_dir: Path to scenario data directory
        - flags: Dict that may contain 'break_competitor' for testing
        """
        # Check for error simulation flag
        flags = ctx.get('flags', {})
        if flags.get('break_competitor', False):
            raise DataMissingError("Simulated competitor data unavailable (test mode)")
        
        scenario_dir = Path(ctx['scenario_dir'])
        file_path = scenario_dir / 'competitor.json'
        
        if not file_path.exists():
            raise DataMissingError(f"Competitor file not found: {file_path}")
        
        # Load raw data
        with open(file_path, 'rb') as f:
            raw_data = orjson.loads(f.read())
        
        # Extract key metrics
        avg_competitor_price = raw_data.get('avg_competitor_price', 0)
        sponsored_share = raw_data.get('sponsored_share', 0)
        top_competitor_rating = raw_data.get('top_competitor_rating', 0)
        
        # Analyze competitive landscape
        competitive_pressure = self._assess_competitive_pressure(
            avg_competitor_price, sponsored_share, top_competitor_rating
        )
        
        price_positioning = self._analyze_price_positioning(avg_competitor_price)
        market_saturation = self._assess_market_saturation(sponsored_share)
        
        recommendations = []
        threats = []
        opportunities = []
        
        # Price analysis
        if price_positioning == 'significantly_higher':
            threats.append('Price disadvantage vs competitors')
            recommendations.append('Consider price optimization or value differentiation')
        elif price_positioning == 'competitive':
            opportunities.append('Price parity enables feature-based competition')
        
        # Market saturation analysis
        if market_saturation == 'high':
            threats.append('High advertising competition')
            recommendations.append('Focus on long-tail keywords and niche targeting')
        elif market_saturation == 'medium':
            opportunities.append('Moderate competition allows for strategic positioning')
        else:
            opportunities.append('Low competition enables aggressive expansion')
        
        # Quality positioning analysis
        if top_competitor_rating > 4.5:
            threats.append('Competitors have superior ratings')
            recommendations.append('Prioritize product quality improvements')
        
        analysis_data = {
            'raw_data': raw_data,
            'competitive_analysis': {
                'competitive_pressure': competitive_pressure,
                'price_positioning': price_positioning,
                'market_saturation': market_saturation,
                'threats': threats,
                'opportunities': opportunities,
                'recommendations': recommendations
            },
            'market_metrics': {
                'price_competitiveness': self._calculate_price_score(avg_competitor_price),
                'ad_competition_level': sponsored_share,
                'quality_benchmark': top_competitor_rating
            }
        }
        
        return ToolResult(
            name=self.name,
            ok=True,
            data=analysis_data,
            meta={
                'source': str(file_path),
                'competitive_pressure': competitive_pressure,
                'latency_ms': 0  # Will be set by wrap_call
            }
        )
    
    def _assess_competitive_pressure(self, price: float, ad_share: float, rating: float) -> str:
        """Assess overall competitive pressure level."""
        pressure_score = 0
        
        # Price pressure (assume our price is around $19.99 from context)
        if price < 15:
            pressure_score += 2
        elif price < 18:
            pressure_score += 1
        
        # Ad competition pressure
        if ad_share > 0.5:
            pressure_score += 2
        elif ad_share > 0.3:
            pressure_score += 1
        
        # Quality pressure
        if rating > 4.5:
            pressure_score += 2
        elif rating > 4.2:
            pressure_score += 1
        
        if pressure_score >= 4:
            return 'high'
        elif pressure_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _analyze_price_positioning(self, competitor_price: float) -> str:
        """Analyze price positioning vs competitors (assuming our price ~$19.99)."""
        our_price = 19.99  # From context in mock data
        
        if our_price > competitor_price * 1.2:
            return 'significantly_higher'
        elif our_price > competitor_price * 1.1:
            return 'slightly_higher'
        elif our_price > competitor_price * 0.9:
            return 'competitive'
        else:
            return 'lower'
    
    def _assess_market_saturation(self, sponsored_share: float) -> str:
        """Assess market saturation based on sponsored ad share."""
        if sponsored_share > 0.6:
            return 'high'
        elif sponsored_share > 0.3:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_price_score(self, competitor_price: float) -> float:
        """Calculate price competitiveness score (0-1, higher is better)."""
        our_price = 19.99
        if competitor_price == 0:
            return 0.5  # Unknown
        
        ratio = our_price / competitor_price
        if ratio <= 0.9:
            return 1.0  # We're cheaper
        elif ratio <= 1.1:
            return 0.8  # Competitive
        elif ratio <= 1.3:
            return 0.4  # Slightly expensive
        else:
            return 0.1  # Too expensive