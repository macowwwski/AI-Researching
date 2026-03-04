from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector import retriever
from MCP import check_planting_conditions_sync
import re

model = OllamaLLM(model="llama3.2")

template = """
Você é um especialista em agricultura e responde em português brasileiro.

INFORMAÇÕES SOBRE CULTIVOS (do banco de dados):
{info}

CONDIÇÕES CLIMÁTICAS ATUAIS (tempo real):
{weather_info}

PERGUNTA DO USUÁRIO: {question}

INSTRUÇÕES:
- Combine as informações técnicas das culturas COM as condições climáticas atuais
- Se o clima não for favorável para a cultura mencionada, AVISE o usuário
- Use dados específicos (números, datas, medidas) quando disponíveis
- Seja direto e prático
- Sempre responda em português brasileiro

RESPOSTA:"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

print("=" * 70)
print("🌱 COOPERAAGRO - SISTEMA INTELIGENTE DE RECOMENDAÇÃO DE PLANTIO")
print("=" * 70)
print("\n✨ Novo: Sistema integrado com dados climáticos em tempo real!")
print("\nDigite 'q' para sair")
print("\nExemplos de perguntas:")
print("  - Posso plantar alho agora em Curitiba?")
print("  - As condições estão boas para plantar tomate?")
print("  - Qual o melhor cultivo para o clima atual da minha região?")
print()

# Configuração padrão da cidade (você pode pedir ao usuário)
DEFAULT_CITY = "Curitiba"
user_city = input(f"Qual sua cidade? (Enter para usar '{DEFAULT_CITY}'): ").strip()
if not user_city:
    user_city = DEFAULT_CITY

print(f"\n✓ Configurado para: {user_city}")
print(f"💡 Dica: O sistema agora consulta o clima de {user_city} automaticamente!\n")

while True:
    print("-" * 70)
    question = input("Sua pergunta: ").strip()
    
    if question.lower() in ['q', 'quit', 'sair']:
        print("\n👋 Até logo!")
        break
    
    if not question:
        print("⚠ Por favor, faça uma pergunta válida.")
        continue
    
    try:
        # 1. BUSCAR INFORMAÇÕES DO RAG
        print("\n🔍 Buscando informações técnicas...", end=" ")
        info_docs = retriever.invoke(question, k=2)
        print(f"✓")
        
        if info_docs:
            culturas = [doc.metadata.get('cultura', '?') for doc in info_docs]
            print(f"📚 Culturas encontradas: {', '.join(set(culturas))}")
        
        info = "\n\n---\n\n".join([doc.page_content for doc in info_docs])
        
        # 2. BUSCAR DADOS CLIMÁTICOS (MCP)
        # Verificar se a pergunta envolve "agora", "hoje", "clima", "condições"
        keywords_clima = ['agora', 'hoje', 'clima', 'condições', 'tempo', 'posso plantar']
        needs_weather = any(keyword in question.lower() for keyword in keywords_clima)
        
        weather_info = ""
        if needs_weather or not info.strip():
            print(f"🌤️ Consultando clima de {user_city}...", end=" ")
            try:
                weather_info = check_planting_conditions_sync(user_city)
                print("✓")
            except Exception as e:
                print(f"\n⚠️ Não foi possível obter dados climáticos: {e}")
                weather_info = "Dados climáticos indisponíveis no momento."
        else:
            weather_info = "(Dados climáticos não necessários para esta pergunta)"
        
        # 3. GERAR RESPOSTA COMBINANDO RAG + MCP
        print("\n💭 Analisando e gerando recomendação...\n")
        
        result = chain.invoke({
            "info": info if info.strip() else "Nenhuma informação específica encontrada no banco de dados.",
            "weather_info": weather_info,
            "question": question
        })
        
        print("─" * 70)
        print("🤖 Recomendação:")
        print(result)
        print()
        
    except KeyboardInterrupt:
        print("\n\n👋 Interrompido pelo usuário. Até logo!")
        break
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        print("\nVerifique se:")
        print("  1. O Ollama está rodando (ollama serve)")
        print("  2. Os modelos estão baixados")
        print("  3. O arquivo .env está configurado com OPENWEATHER_API_KEY")
        print()