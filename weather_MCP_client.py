"""
Cliente MCP para integrar dados climáticos ao sistema RAG
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class WeatherMCPClient:
    """Cliente para se comunicar com o Weather MCP Server"""
    
    def __init__(self):
        self.session = None
        self.tools = []
    
    async def connect(self):
        """Conecta ao servidor MCP"""
        server_params = StdioServerParameters(
            command="python",
            args=["weather_mcp_server.py"],
            env=None
        )
        
        # Contexto assíncrono para manter a conexão
        self.stdio_transport = stdio_client(server_params)
        self.read_stream, self.write_stream = await self.stdio_transport.__aenter__()
        
        self.session = ClientSession(self.read_stream, self.write_stream)
        await self.session.__aenter__()
        
        # Inicializar sessão
        await self.session.initialize()
        
        # Listar ferramentas disponíveis
        response = await self.session.list_tools()
        self.tools = response.tools
        
        print(f"✓ Conectado ao Weather MCP Server")
        print(f"✓ {len(self.tools)} ferramentas disponíveis")
        
        return self
    
    async def disconnect(self):
        """Desconecta do servidor"""
        if self.session:
            await self.session.__aexit__(None, None, None)
        if self.stdio_transport:
            await self.stdio_transport.__aexit__(None, None, None)
    
    async def get_current_weather(self, city: str, country_code: str = "BR") -> str:
        """Obtém clima atual"""
        result = await self.session.call_tool(
            "get_current_weather",
            arguments={"city": city, "country_code": country_code}
        )
        return result.content[0].text
    
    async def get_weather_forecast(self, city: str, country_code: str = "BR", days: int = 3) -> str:
        """Obtém previsão do tempo"""
        result = await self.session.call_tool(
            "get_weather_forecast",
            arguments={"city": city, "country_code": country_code, "days": days}
        )
        return result.content[0].text
    
    async def check_planting_conditions(self, city: str, country_code: str = "BR") -> str:
        """Verifica condições para plantio"""
        result = await self.session.call_tool(
            "check_planting_conditions",
            arguments={"city": city, "country_code": country_code}
        )
        return result.content[0].text

# Funções síncronas para usar no main.py
def get_weather_sync(city: str) -> str:
    """Wrapper síncrono para buscar clima"""
    async def _get():
        client = WeatherMCPClient()
        try:
            await client.connect()
            result = await client.get_current_weather(city)
            return result
        finally:
            await client.disconnect()
    
    return asyncio.run(_get())

def check_planting_conditions_sync(city: str) -> str:
    """Wrapper síncrono para verificar condições de plantio"""
    async def _check():
        client = WeatherMCPClient()
        try:
            await client.connect()
            result = await client.check_planting_conditions(city)
            return result
        finally:
            await client.disconnect()
    
    return asyncio.run(_check())

# Teste standalone
async def test_weather_mcp():
    """Teste do cliente MCP"""
    print("="*60)
    print("🧪 TESTE DO WEATHER MCP CLIENT")
    print("="*60)
    
    client = WeatherMCPClient()
    
    try:
        await client.connect()
        
        # Teste 1: Clima atual
        print("\n1️⃣ Testando get_current_weather...")
        weather = await client.get_current_weather("Curitiba")
        print(weather)
        
        # Teste 2: Condições de plantio
        print("\n2️⃣ Testando check_planting_conditions...")
        conditions = await client.check_planting_conditions("Curitiba")
        print(conditions)
        
        # Teste 3: Previsão
        print("\n3️⃣ Testando get_weather_forecast...")
        forecast = await client.get_weather_forecast("Curitiba", days=3)
        print(forecast)
        
        print("\n" + "="*60)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_weather_mcp())