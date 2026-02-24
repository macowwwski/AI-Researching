"""
Teste isolado do retriever para verificar se está buscando dados do CSV
"""

from vector import retriever, vector_store

print("="*60)
print("🧪 TESTE DO RETRIEVER")
print("="*60)

test_questions = [
    "Quais culturas eu poderia plantar agora e colher em até 100 dias?",
    "Berinjela?",
    "Qual o espaçamento entre linhas para alho?",
    "Quanto tempo leva para colher abóbora?"
]

for question in test_questions:
    print(f"\n❓ Pergunta: {question}")
    print("-"*60)
    
    # Buscar documentos
    results = vector_store.similarity_search_with_score(question, k=3)
    
    print(f"📚 Documentos encontrados: {len(results)}")
    print(results)
    if results:
        # Mostrar o primeiro resultado completo
        print(f"\n📄 Melhor resultado (score mais alto):")
        print(results[0][0].page_content)
        
        # Mostrar metadados
        print(f"\n🏷️ Metadados:")
        print(results[0][0].metadata)
    else:
        print("❌ PROBLEMA: Nenhum documento encontrado!")
        print("   O banco vetorial pode estar vazio ou mal configurado")

print("\n" + "="*60)