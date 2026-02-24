# VETORIZAÇÃO DOS DOCUMENTOS DE CONTEXTO

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma # database
from langchain_core.documents import Document
import os
import pandas as pd

# Ler CSV
df = pd.read_csv("Info_Plantio.csv")  # Ajuste o nome se necessário
print(f"CSV carregado: {len(df)} culturas encontradas")

# Configurar embeddings
embeddings = OllamaEmbeddings(model="nomic-embed-text-v2-moe")

db_location = "./chroma_langchain_db"
add_documents = not os.path.exists(db_location)

if add_documents:
    print("Criando banco vetorial...")
    documents = []
    ids = []

    # CRIAR DOCUMENTOS COM TODAS AS INFORMAÇÕES NO page_content
    for i, row in df.iterrows():
        # Construir texto completo com TODAS as informações
        page_content = f"""
Cultura: {row['Cultura']}

Informações de Plantio:
- Época de Plantio: {row['EpocaPlantio']}
- Espaçamento entre Linhas: {row['EspacamentoLinhas']}
- Espaçamento entre Plantas: {row['EspacamentoPlantas']}
- Técnica utilizada: {row['TipoPlantio']}

Informações de Colheita:
- Tempo até Colheita: {row['TempoColheita']}
- Produção Esperada: {row['Producao']}

"""
        
        document = Document(
            page_content=page_content.strip(),
            # page_content=row["Cultura"],
            metadata={
                "cultura": row["Cultura"],
                "tempo_colheita": row["TempoColheita"],
                "producao": row["Producao"]
            },
            id=str(i)
        )
        ids.append(str(i))
        documents.append(document)
    
    print(f"✓ {len(documents)} documentos criados")

# Criar/carregar vector store
vector_store = Chroma(
    collection_name="informacoes_plantio",
    persist_directory=db_location,
    embedding_function=embeddings
)

if add_documents:
    print("Adicionando documentos ao banco vetorial...")
    vector_store.add_documents(documents=documents, ids=ids)
    print(f"✓ Banco vetorial criado em {db_location}")
else:
    print(f"✓ Banco vetorial carregado de {db_location}")

# Configurar retriever
retriever = vector_store.as_retriever(
    search_kwargs={"k": 3}  # Reduzido para 3 para respostas mais focadas
)

print("✓ Retriever configurado e pronto!")

# TESTE (executar só quando rodar este arquivo diretamente)
if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTE DO SISTEMA RAG")
    print("="*60)
    
    test_questions = [
        "Qual o espaçamento entre linhas para alho?",
        "Quanto tempo leva para colher abóbora?"
    ]
    
    for question in test_questions:
        print(f"\n❓ Pergunta: {question}")
        results = retriever.invoke(question)
        
        if results:
            print(results)
            print(f"✓ Encontrados {len(results)} resultado(s)")
            print(f"📄 Melhor resultado:")
            print(results[0].page_content[:200] + "...")
        else:
            print("❌ Nenhum resultado encontrado!")