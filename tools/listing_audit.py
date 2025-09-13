import orjson
from pathlib import Path
from typing import Dict, Any

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from .base import BaseTool, wrap_call
from agent.errors import DataMissingError
from agent.types import ToolResult


class ListingAuditTool(BaseTool):
    """Tool for auditing product listing quality and optimization."""
    
    def __init__(self):
        super().__init__("listing_audit", timeout_s=5)
    
    @wrap_call
    def run(self, ctx: Dict[str, Any]) -> ToolResult:
        """
        Audit product listing quality and identify optimization opportunities.
        
        Expected context:
        - scenario_dir: Path to scenario data directory
        - flags: Dict that may contain 'break_audit' for testing
        """
        # Check for test mode break
        flags = ctx.get('flags', {})
        if flags.get('break_audit', False):
            raise DataMissingError("Simulated audit data unavailable (test mode)")
        
        scenario_dir = Path(ctx['scenario_dir'])
        file_path = scenario_dir / 'listing_audit.json'
        
        if not file_path.exists():
            raise DataMissingError(f"Listing audit file not found: {file_path}")
        
        # Load raw data
        with open(file_path, 'rb') as f:
            raw_data = orjson.loads(f.read())
        
        # Extract key metrics
        title_kws_coverage = raw_data.get('title_kws_coverage', 0)
        main_image_score = raw_data.get('main_image_score', 0)
        a_plus_content = raw_data.get('a_plus', False)
        rating = raw_data.get('rating', 0)
        review_count = raw_data.get('reviews', 0)
        
        # Analyze listing quality
        quality_issues = []
        recommendations = []
        overall_score = 0
        
        # Title keyword coverage analysis
        if title_kws_coverage < 0.7:
            quality_issues.append('Poor keyword coverage in title')
            recommendations.append('Optimize title with relevant keywords')
        else:
            overall_score += 20
        
        # Main image quality analysis
        if main_image_score < 0.8:
            quality_issues.append('Main image quality below standards')
            recommendations.append('Improve main product image quality')
        else:
            overall_score += 20
        
        # A+ Content analysis
        if not a_plus_content:
            quality_issues.append('Missing A+ Content')
            recommendations.append('Add A+ Content to improve conversion')
        else:
            overall_score += 15
        
        # Reviews and rating analysis
        if rating < 4.0:
            quality_issues.append('Low product rating affects conversion')
            recommendations.append('Address quality issues to improve rating')
        else:
            overall_score += 15
        
        if review_count < 100:
            quality_issues.append('Low review count reduces trust')
            recommendations.append('Implement review generation strategy')
        elif review_count >= 500:
            overall_score += 15
        else:
            overall_score += 10
        
        # Calculate conversion impact potential
        conversion_impact = self._assess_conversion_impact(
            title_kws_coverage, main_image_score, a_plus_content, rating, review_count
        )
        
        analysis_data = {
            'raw_data': raw_data,
            'listing_analysis': {
                'overall_quality_score': overall_score,
                'quality_grade': self._get_quality_grade(overall_score),
                'quality_issues': quality_issues,
                'recommendations': recommendations,
                'conversion_impact': conversion_impact,
                'optimization_priority': self._get_optimization_priority(quality_issues)
            },
            'detailed_scores': {
                'title_optimization': title_kws_coverage,
                'image_quality': main_image_score,
                'content_completeness': 1.0 if a_plus_content else 0.0,
                'social_proof': min(rating / 5.0, 1.0),
                'review_volume': min(review_count / 1000, 1.0)
            }
        }
        
        return ToolResult(
            name=self.name,
            ok=True,
            data=analysis_data,
            meta={
                'source': str(file_path),
                'quality_grade': self._get_quality_grade(overall_score),
                'latency_ms': 0  # Will be set by wrap_call
            }
        )
    
    def _get_quality_grade(self, score: int) -> str:
        """Convert quality score to letter grade."""
        if score >= 80:
            return 'A'
        elif score >= 65:
            return 'B'
        elif score >= 50:
            return 'C'
        elif score >= 35:
            return 'D'
        else:
            return 'F'
    
    def _assess_conversion_impact(self, title_coverage: float, image_score: float, 
                                 a_plus: bool, rating: float, reviews: int) -> str:
        """Assess potential impact of listing improvements on conversion."""
        low_factors = 0
        
        if title_coverage < 0.7:
            low_factors += 1
        if image_score < 0.8:
            low_factors += 1
        if not a_plus:
            low_factors += 1
        if rating < 4.0:
            low_factors += 1
        if reviews < 100:
            low_factors += 1
        
        if low_factors >= 3:
            return 'high_impact_potential'
        elif low_factors >= 2:
            return 'medium_impact_potential'
        else:
            return 'low_impact_potential'
    
    def _get_optimization_priority(self, issues: list) -> str:
        """Determine optimization priority based on issues."""
        critical_issues = ['Low product rating affects conversion', 
                          'Poor keyword coverage in title']
        
        if any(issue in issues for issue in critical_issues):
            return 'high'
        elif len(issues) >= 2:
            return 'medium'
        else:
            return 'low'