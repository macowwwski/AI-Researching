"""
MCP Package - Model Context Protocol para dados climáticos
"""

from .weather_MCP_client import (
    WeatherMCPClient,
    get_weather_sync,
    check_planting_conditions_sync
)

__all__ = [
    'WeatherMCPClient',
    'get_weather_sync', 
    'check_planting_conditions_sync'
]