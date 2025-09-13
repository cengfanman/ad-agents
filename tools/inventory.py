import orjson
from pathlib import Path
from typing import Dict, Any

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from .base import BaseTool, wrap_call
from agent.errors import DataMissingError
from agent.types import ToolResult


class InventoryTool(BaseTool):
    """Tool for checking inventory status and availability."""
    
    def __init__(self):
        super().__init__("inventory", timeout_s=5)
    
    @wrap_call
    def run(self, ctx: Dict[str, Any]) -> ToolResult:
        """
        Check inventory status and stock levels.
        
        Expected context:
        - scenario_dir: Path to scenario data directory
        - flags: Dict that may contain 'break_inventory' for testing
        """
        # Check for test mode break
        flags = ctx.get('flags', {})
        if flags.get('break_inventory', False):
            raise DataMissingError("Simulated inventory data unavailable (test mode)")
        
        scenario_dir = Path(ctx['scenario_dir'])
        file_path = scenario_dir / 'inventory.json'
        
        if not file_path.exists():
            raise DataMissingError(f"Inventory file not found: {file_path}")
        
        # Load raw data
        with open(file_path, 'rb') as f:
            raw_data = orjson.loads(f.read())
        
        # Calculate derived insights
        days_of_inventory = raw_data.get('days_of_inventory', 0)
        restock_eta_days = raw_data.get('restock_eta_days', 0)
        stockout_risk = raw_data.get('stockout_risk', 'unknown')
        
        # Analyze inventory health
        inventory_health = 'healthy'
        concerns = []
        
        if days_of_inventory < 14:
            inventory_health = 'critical'
            concerns.append('Low inventory may limit ad effectiveness')
        elif days_of_inventory < 30:
            inventory_health = 'warning'
            concerns.append('Inventory levels below optimal range')
        
        if stockout_risk in ['high', 'critical']:
            concerns.append(f'High stockout risk: {stockout_risk}')
        
        if restock_eta_days > days_of_inventory:
            concerns.append('Restock ETA exceeds current inventory duration')
        
        analysis_data = {
            'raw_data': raw_data,
            'inventory_analysis': {
                'days_remaining': days_of_inventory,
                'restock_timeline': restock_eta_days,
                'risk_level': stockout_risk,
                'health_status': inventory_health,
                'concerns': concerns,
                'ad_impact': self._assess_ad_impact(days_of_inventory, stockout_risk)
            }
        }
        
        return ToolResult(
            name=self.name,
            ok=True,
            data=analysis_data,
            meta={
                'source': str(file_path),
                'health_status': inventory_health,
                'latency_ms': 0  # Will be set by wrap_call
            }
        )
    
    def _assess_ad_impact(self, days_inventory: int, risk_level: str) -> str:
        """Assess how inventory status affects advertising strategy."""
        if days_inventory < 14 or risk_level in ['high', 'critical']:
            return 'reduce_ad_spend'
        elif days_inventory < 30 or risk_level == 'medium':
            return 'monitor_closely'
        else:
            return 'no_constraints'