"""
Weather MCP Server - Servidor MCP para dados meteorológicos
Fornece informações climáticas em tempo real para recomendações de plantio
"""

import asyncio
import os
from dotenv import load_dotenv
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

load_dotenv()

# Configuração da API 
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

app = Server("weather-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Lista as ferramentas disponíveis no servidor"""
    return [
        Tool(
            name="get_current_weather",
            description="Obtém o clima atual de uma cidade. Retorna temperatura, umidade, descrição e sensação térmica.",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Nome da cidade",
                        "default": "Campo Mourão"
                    },
                    "country_code": {
                        "type": "string",
                        "description": "Código do país",
                        "default": "BR"
                    }
                },
                "required": ["city"]
            }
        ),
        Tool(
            name="get_weather_forecast",
            description="Obtém a previsão do tempo para os próximos 5 dias.",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Nome da cidade"
                    },
                    "country_code": {
                        "type": "string",
                        "description": "Código do país",
                        "default": "BR"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Número de dias de previsão (1-5)",
                        "default": 3
                    }
                },
                "required": ["city"]
            }
        ),
        Tool(
            name="check_planting_conditions",
            description="Analisa se as condições climáticas atuais são adequadas para plantio. Considera temperatura, umidade e chuva.",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Nome da cidade"
                    },
                    "country_code": {
                        "type": "string",
                        "description": "Código do país",
                        "default": "BR"
                    }
                },
                "required": ["city"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Executa a ferramenta solicitada"""
    
    if not OPENWEATHER_API_KEY:
        return [TextContent(
            type="text",
            text="ERRO: Chave da API OpenWeather não configurada. Verificar OPENWEATHER_API_KEY no arquivo .env"
        )]
    
    try:
        if name == "get_current_weather":
            result = await get_current_weather(
                arguments.get("city"),
                arguments.get("country_code", "BR")
            )
        elif name == "get_weather_forecast":
            result = await get_weather_forecast(
                arguments.get("city"),
                arguments.get("country_code", "BR"),
                arguments.get("days", 3)
            )
        elif name == "check_planting_conditions":
            result = await check_planting_conditions(
                arguments.get("city"),
                arguments.get("country_code", "BR")
            )
        else:
            result = f"Ferramenta desconhecida: {name}"
        
        return [TextContent(type="text", text=result)]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Erro ao buscar dados climáticos: {str(e)}"
        )]

async def get_current_weather(city: str, country_code: str = "BR") -> str:
    """Busca clima atual na API OpenWeatherMap"""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": f"{city},{country_code}",
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",  # Celsius
        "lang": "pt_br"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    
    # Formatar resposta
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    description = data["weather"][0]["description"]
    wind_speed = data["wind"]["speed"]
    
    result = f"""
🌤️ CLIMA ATUAL EM {city.upper()}:

Temperatura: {temp}°C (sensação: {feels_like}°C)
Umidade: {humidity}%
Condição: {description.capitalize()}
Vento: {wind_speed} m/s

💡 Contexto para agricultura:
- Umidade relativa: {"Alta" if humidity > 70 else "Moderada" if humidity > 50 else "Baixa"}
- Temperatura: {"Adequada para maioria das culturas" if 15 <= temp <= 30 else "Fora da faixa ideal para muitas culturas"}
"""
    return result.strip()

async def get_weather_forecast(city: str, country_code: str = "BR", days: int = 3) -> str:
    """Busca previsão do tempo"""
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": f"{city},{country_code}",
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "pt_br"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    
    # Agrupar previsões por dia
    forecasts = {}
    for item in data["list"][:days * 8]:  # 8 previsões por dia (a cada 3h)
        date = item["dt_txt"].split()[0]
        if date not in forecasts:
            forecasts[date] = {
                "temp_max": item["main"]["temp_max"],
                "temp_min": item["main"]["temp_min"],
                "humidity": item["main"]["humidity"],
                "description": item["weather"][0]["description"],
                "rain": item.get("rain", {}).get("3h", 0)
            }
        else:
            forecasts[date]["temp_max"] = max(forecasts[date]["temp_max"], item["main"]["temp_max"])
            forecasts[date]["temp_min"] = min(forecasts[date]["temp_min"], item["main"]["temp_min"])
    
    result = f"📅 PREVISÃO PARA {city.upper()} - PRÓXIMOS {len(forecasts)} DIAS:\n\n"
    
    for date, forecast in list(forecasts.items())[:days]:
        result += f"Data: {date}\n"
        result += f"  Temperatura: {forecast['temp_min']:.1f}°C a {forecast['temp_max']:.1f}°C\n"
        result += f"  Umidade: {forecast['humidity']}%\n"
        result += f"  Condição: {forecast['description'].capitalize()}\n"
        if forecast['rain'] > 0:
            result += f"  Chuva: {forecast['rain']}mm\n"
        result += "\n"
    
    return result.strip()

async def check_planting_conditions(city: str, country_code: str = "BR") -> str:
    """Analisa condições para plantio"""
    # Buscar clima atual e previsão
    current = await get_current_weather(city, country_code)
    
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": f"{city},{country_code}",
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
    
    temp = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    rain = data.get("rain", {}).get("1h", 0)
    
    # Análise simples
    conditions = []
    
    if 15 <= temp <= 30:
        conditions.append("✅ Temperatura adequada para a maioria das culturas")
    elif temp < 15:
        conditions.append("⚠️ Temperatura baixa - evite culturas sensíveis ao frio")
    else:
        conditions.append("⚠️ Temperatura alta - prefira culturas tolerantes ao calor")
    
    if 50 <= humidity <= 80:
        conditions.append("✅ Umidade ideal para plantio")
    elif humidity < 50:
        conditions.append("⚠️ Umidade baixa - planeje irrigação adequada")
    else:
        conditions.append("⚠️ Umidade muito alta - risco de doenças fúngicas")
    
    if rain > 0:
        conditions.append("🌧️ Chuva prevista - adie o plantio se o solo já estiver úmido")
    else:
        conditions.append("✅ Sem chuva prevista - bom momento para plantar")
    
    result = f"""
🌱 ANÁLISE DE CONDIÇÕES PARA PLANTIO EM {city.upper()}:

{current}

📊 AVALIAÇÃO:
{chr(10).join(conditions)}

💡 RECOMENDAÇÃO GERAL:
{"Condições favoráveis para plantio!" if len([c for c in conditions if "✅" in c]) >= 2 else "Condições parcialmente favoráveis - ajuste o manejo conforme necessário"}
"""
    return result.strip()

async def main():
    """Inicializa o servidor MCP"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())