"""
TOUR 4: Grafana Dashboards - JSON Dashboard Definitions
========================================================
Purpose: Pre-built Grafana dashboards for production monitoring

Dashboards included:
1. Infrastructure Dashboard - CPU, Memory, Disk, Network
2. Database Dashboard - Queries, Latency, Connections, Errors
3. API Performance Dashboard - Request rate, latency, errors, throughput
4. Business Metrics Dashboard - Orders, invoices, payments, revenue

Format: JSON-compatible with Grafana 8.0+
Export to Grafana via: POST /api/dashboards/db with JSON

Architecture:
- Panels: Graph, Stat, Gauge, Table, Heatmap
- Data sources: Prometheus (for metrics)
- Templating: Variable substitution for multi-env support
- Alerting: Alert rules attached to panels
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class GrafanaTarget:
    """Grafana query target for Prometheus"""
    expr: str
    legendFormat: str = ""
    refId: str = "A"
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v}


@dataclass
class GrafanaPanel:
    """Grafana panel definition"""
    title: str
    targets: List[GrafanaTarget]
    type: str = "graph"
    gridPos: Dict[str, int] = None
    id: int = 1
    
    def __post_init__(self):
        if self.gridPos is None:
            self.gridPos = {"h": 8, "w": 12, "x": 0, "y": 0}


class GrafanaDashboards:
    """
    Manages Grafana dashboard JSON definitions
    
    Can export dashboards for import into Grafana
    """

    def __init__(self, datasource_uid: str = "prometheus"):
        """
        Initialize dashboard builder
        
        Args:
            datasource_uid: Prometheus datasource UID in Grafana
        """
        self.datasource_uid = datasource_uid

    def _create_graph_panel(
        self,
        title: str,
        query: str,
        legend: str = "",
        x: int = 0,
        y: int = 0,
        panel_id: int = 1
    ) -> Dict[str, Any]:
        """Create a graph panel"""
        return {
            "title": title,
            "type": "graph",
            "id": panel_id,
            "gridPos": {"h": 8, "w": 12, "x": x, "y": y},
            "targets": [{
                "expr": query,
                "legendFormat": legend,
                "refId": "A",
                "interval": "",
                "step": 60
            }],
            "datasource": {"type": "prometheus", "uid": self.datasource_uid},
            "options": {
                "legend": {
                    "calcs": ["mean", "max"],
                    "displayMode": "table",
                    "placement": "bottom"
                },
                "tooltip": {"mode": "multi"}
            },
            "fieldConfig": {
                "defaults": {
                    "custom": {"drawStyle": "line", "fillOpacity": 0, "showPoints": "never"}
                }
            }
        }

    def _create_stat_panel(
        self,
        title: str,
        query: str,
        unit: str = "short",
        x: int = 0,
        y: int = 0,
        panel_id: int = 1
    ) -> Dict[str, Any]:
        """Create a stat panel (single number)"""
        return {
            "title": title,
            "type": "stat",
            "id": panel_id,
            "gridPos": {"h": 6, "w": 4, "x": x, "y": y},
            "targets": [{
                "expr": query,
                "refId": "A"
            }],
            "datasource": {"type": "prometheus", "uid": self.datasource_uid},
            "options": {
                "colorMode": "background",
                "orientation": "auto",
                "textMode": "auto"
            },
            "fieldConfig": {
                "defaults": {
                    "unit": unit,
                    "custom": {}
                }
            }
        }

    def _create_gauge_panel(
        self,
        title: str,
        query: str,
        min: float = 0,
        max: float = 100,
        x: int = 0,
        y: int = 0,
        panel_id: int = 1
    ) -> Dict[str, Any]:
        """Create a gauge panel"""
        return {
            "title": title,
            "type": "gauge",
            "id": panel_id,
            "gridPos": {"h": 6, "w": 4, "x": x, "y": y},
            "targets": [{
                "expr": query,
                "refId": "A"
            }],
            "datasource": {"type": "prometheus", "uid": self.datasource_uid},
            "options": {
                "orientation": "auto",
                "showThresholdLabels": False,
                "showThresholdMarkers": True
            },
            "fieldConfig": {
                "defaults": {
                    "min": min,
                    "max": max,
                    "unit": "percent",
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 70},
                            {"color": "red", "value": 90}
                        ]
                    }
                }
            }
        }

    def _create_dashboard(
        self,
        title: str,
        description: str,
        panels: List[Dict[str, Any]],
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """Create a complete dashboard"""
        return {
            "dashboard": {
                "title": title,
                "description": description,
                "tags": tags or ["erp-fabs", "tour4"],
                "timezone": "UTC",
                "uid": title.lower().replace(" ", "-"),
                "version": 1,
                "panels": panels,
                "refresh": "30s",
                "time": {
                    "from": "now-6h",
                    "to": "now"
                },
                "templating": {
                    "list": [
                        {
                            "name": "environment",
                            "type": "query",
                            "datasource": {"type": "prometheus", "uid": self.datasource_uid},
                            "query": 'label_values(up, job)',
                            "current": {"text": "All", "value": "$__all"},
                            "multi": True
                        }
                    ]
                }
            },
            "overwrite": True
        }

    # ========================================================================
    # DASHBOARD 1: INFRASTRUCTURE
    # ========================================================================

    def get_infrastructure_dashboard(self) -> Dict[str, Any]:
        """
        Infrastructure Dashboard
        - CPU usage, Memory, Disk I/O, Network throughput
        - Service uptime, Process count
        """
        panels = [
            # CPU Gauge
            self._create_gauge_panel(
                "CPU Usage %",
                "erp_fabs_ci_cpu_percent",
                min=0, max=100,
                x=0, y=0, panel_id=1
            ),
            
            # Memory Gauge
            self._create_gauge_panel(
                "Memory Usage %",
                "(erp_fabs_ci_memory_bytes{type='heap'} / 8589934592) * 100",
                min=0, max=100,
                x=4, y=0, panel_id=2
            ),
            
            # Service Uptime Stat
            self._create_stat_panel(
                "Service Uptime",
                "erp_fabs_ci_uptime_seconds",
                unit="s",
                x=8, y=0, panel_id=3
            ),
            
            # Memory Trend
            self._create_graph_panel(
                "Memory Usage Trend",
                'erp_fabs_ci_memory_bytes{type="heap"}',
                legend="{{type}}",
                x=0, y=6, panel_id=4
            ),
            
            # CPU Trend
            self._create_graph_panel(
                "CPU Usage Trend",
                "erp_fabs_ci_cpu_percent",
                legend="CPU %",
                x=12, y=6, panel_id=5
            ),
            
            # Disk Usage
            self._create_graph_panel(
                "Disk Usage",
                'erp_fabs_ci_disk_bytes{mount="/"}',
                legend="{{mount}}",
                x=0, y=14, panel_id=6
            ),
        ]
        
        return self._create_dashboard(
            "Infrastructure Dashboard",
            "System-level metrics: CPU, Memory, Disk, Network",
            panels,
            tags=["infrastructure", "system"]
        )

    # ========================================================================
    # DASHBOARD 2: DATABASE
    # ========================================================================

    def get_database_dashboard(self) -> Dict[str, Any]:
        """
        Database Dashboard
        - Query count by operation, Query latency
        - Connection pool status, Slow queries
        - Error rate
        """
        panels = [
            # Query Rate
            self._create_graph_panel(
                "Query Rate (per minute)",
                "rate(erp_fabs_ci_db_queries_total[1m])",
                legend="{{operation}} - {{collection}}",
                x=0, y=0, panel_id=1
            ),
            
            # Query Latency P50/P90/P99
            self._create_graph_panel(
                "Query Latency Percentiles",
                'histogram_quantile(0.95, rate(erp_fabs_ci_db_query_duration_seconds_bucket[5m]))',
                legend="p95 {{operation}} {{collection}}",
                x=12, y=0, panel_id=2
            ),
            
            # Active Connections Gauge
            self._create_gauge_panel(
                "Active DB Connections",
                "erp_fabs_ci_db_connections_active",
                min=0, max=100,
                x=0, y=8, panel_id=3
            ),
            
            # Available Connections
            self._create_stat_panel(
                "Available Connections",
                "erp_fabs_ci_db_connections_available",
                unit="short",
                x=4, y=8, panel_id=4
            ),
            
            # Slow Queries Counter
            self._create_graph_panel(
                "Slow Queries (>100ms)",
                "rate(erp_fabs_ci_db_slow_queries_total[5m])",
                legend="{{operation}} {{collection}}",
                x=8, y=8, panel_id=5
            ),
            
            # Database Errors
            self._create_graph_panel(
                "Database Errors",
                "rate(erp_fabs_ci_db_errors_total[5m])",
                legend="{{error_type}} {{operation}}",
                x=0, y=16, panel_id=6
            ),
        ]
        
        return self._create_dashboard(
            "Database Dashboard",
            "MongoDB metrics: Queries, Latency, Connections, Errors",
            panels,
            tags=["database", "mongodb"]
        )

    # ========================================================================
    # DASHBOARD 3: API PERFORMANCE
    # ========================================================================

    def get_api_performance_dashboard(self) -> Dict[str, Any]:
        """
        API Performance Dashboard
        - HTTP request rate, response time distribution
        - Error rate by endpoint, Active connections
        - Request/response size
        """
        panels = [
            # Total Requests Stat
            self._create_stat_panel(
                "Total Requests",
                "increase(erp_fabs_ci_http_requests_total[1h])",
                unit="short",
                x=0, y=0, panel_id=1
            ),
            
            # Error Rate %
            self._create_stat_panel(
                "Error Rate %",
                "(rate(erp_fabs_ci_http_requests_total{status=~'5..'}[5m]) / rate(erp_fabs_ci_http_requests_total[5m])) * 100",
                unit="percent",
                x=4, y=0, panel_id=2
            ),
            
            # P95 Latency
            self._create_stat_panel(
                "P95 Latency",
                "histogram_quantile(0.95, rate(erp_fabs_ci_http_request_duration_seconds_bucket[5m]))",
                unit="s",
                x=8, y=0, panel_id=3
            ),
            
            # Request Rate by Method
            self._create_graph_panel(
                "Request Rate by Method",
                "rate(erp_fabs_ci_http_requests_total[1m])",
                legend="{{method}} {{endpoint}}",
                x=0, y=8, panel_id=4
            ),
            
            # Response Time Distribution
            self._create_graph_panel(
                "Response Time Percentiles",
                'histogram_quantile(vector([0.5, 0.9, 0.99]), rate(erp_fabs_ci_http_request_duration_seconds_bucket[5m]))',
                legend="{{quantile}} {{method}}",
                x=12, y=8, panel_id=5
            ),
            
            # Error Rate by Endpoint
            self._create_graph_panel(
                "Error Rate by Endpoint",
                "rate(erp_fabs_ci_http_errors_total[5m])",
                legend="{{status}} {{endpoint}}",
                x=0, y=16, panel_id=6
            ),
            
            # Active Connections
            self._create_graph_panel(
                "Active Connections",
                "erp_fabs_ci_http_connections_active",
                legend="{{endpoint}}",
                x=12, y=16, panel_id=7
            ),
        ]
        
        return self._create_dashboard(
            "API Performance Dashboard",
            "HTTP metrics: Requests, Latency, Errors, Throughput",
            panels,
            tags=["api", "performance"]
        )

    # ========================================================================
    # DASHBOARD 4: BUSINESS METRICS
    # ========================================================================

    def get_business_metrics_dashboard(self) -> Dict[str, Any]:
        """
        Business Metrics Dashboard
        - Orders (created, pending, status distribution)
        - Invoices (created, paid, overdue)
        - Payments (total, success rate by method)
        - Revenue, Stock value
        """
        panels = [
            # Orders Today Stat
            self._create_stat_panel(
                "Orders Today",
                "increase(erp_fabs_ci_orders_created_total[24h])",
                unit="short",
                x=0, y=0, panel_id=1
            ),
            
            # Pending Orders
            self._create_stat_panel(
                "Pending Orders",
                "erp_fabs_ci_orders_pending_total",
                unit="short",
                x=4, y=0, panel_id=2
            ),
            
            # Revenue Today
            self._create_stat_panel(
                "Revenue (24h)",
                "increase(erp_fabs_ci_revenue_total[24h])",
                unit="currencyUSD",
                x=8, y=0, panel_id=3
            ),
            
            # Orders by Status
            self._create_graph_panel(
                "Orders by Status",
                "increase(erp_fabs_ci_orders_created_total[24h])",
                legend="{{status}}",
                x=0, y=8, panel_id=4
            ),
            
            # Invoices Created
            self._create_graph_panel(
                "Invoices Created",
                "rate(erp_fabs_ci_invoices_created_total[1d])",
                legend="{{status}}",
                x=12, y=8, panel_id=5
            ),
            
            # Payments by Method
            self._create_graph_panel(
                "Payments by Method",
                "rate(erp_fabs_ci_payments_total[1d])",
                legend="{{method}} - {{status}}",
                x=0, y=16, panel_id=6
            ),
            
            # Stock Value
            self._create_stat_panel(
                "Stock Value",
                "erp_fabs_ci_stock_value_total",
                unit="currencyUSD",
                x=12, y=16, panel_id=7
            ),
        ]
        
        return self._create_dashboard(
            "Business Metrics Dashboard",
            "Business logic: Orders, Invoices, Payments, Revenue, Stock",
            panels,
            tags=["business", "sales", "finance"]
        )

    # ========================================================================
    # EXPORT METHODS
    # ========================================================================

    def get_all_dashboards(self) -> List[Dict[str, Any]]:
        """Get all 4 dashboards"""
        return [
            self.get_infrastructure_dashboard(),
            self.get_database_dashboard(),
            self.get_api_performance_dashboard(),
            self.get_business_metrics_dashboard(),
        ]

    def export_dashboard_json(self, dashboard_dict: Dict[str, Any], pretty: bool = True) -> str:
        """Export dashboard as JSON string"""
        return json.dumps(
            dashboard_dict,
            indent=2 if pretty else None,
            sort_keys=True
        )

    def export_all_dashboards_json(self, pretty: bool = True) -> Dict[str, str]:
        """Export all dashboards as JSON strings"""
        dashboards = self.get_all_dashboards()
        return {
            f"dashboard_{i+1}.json": self.export_dashboard_json(d, pretty)
            for i, d in enumerate(dashboards)
        }

    def save_dashboards_to_files(self, output_dir: str = ".") -> None:
        """Save all dashboards to JSON files"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        dashboards_json = self.export_all_dashboards_json()
        for filename, json_content in dashboards_json.items():
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w') as f:
                f.write(json_content)
            print(f"✓ Saved {filename}")


# Example usage for testing
if __name__ == "__main__":
    builder = GrafanaDashboards()
    
    # Get all dashboards
    dashboards = builder.get_all_dashboards()
    print(f"✓ Generated {len(dashboards)} dashboards:")
    
    for i, dashboard in enumerate(dashboards, 1):
        title = dashboard['dashboard']['title']
        print(f"  {i}. {title}")
    
    # Export to files
    print("\nExporting dashboards to JSON...")
    builder.save_dashboards_to_files("./grafana_dashboards")
    
    # Show sample of first dashboard
    print("\n" + "="*60)
    print("First Dashboard Structure (excerpt):")
    print("="*60)
    sample = builder.export_dashboard_json(dashboards[0])
    print(sample[:400] + "\n...")
