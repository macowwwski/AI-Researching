# VETORIZAÇÃO DOS DOCUMENTOS DE CONTEXTO

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma # database
from langchain_core.documents import Document
import os
import pandas as pd

df = pd.read_csv("Info_Plantio.csv") # dataframe
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

db_location = "./chroma_langchain_db"
add_documents = not os.path.exists(db_location) # checar se já existe - se existe, já está vetorizado

if add_documents:
    documents = []
    ids = []

    # PERSONALIZAR DE ACORDO COM CSV
    for i, row in df.iterrows():
        page_content = f"""
Cultura: {row['Cultura']}

Informações de Plantio:
- Época de Plantio: {row['EpocaPlantio']}
- Espaçamento entre Linhas: {row['EspacamentoLinhas']}
- Espaçamento entre Plantas: {row['EspacamentoPlantas']}

Informações de Colheita:
- Tempo até Colheita: {row['TempoColheita']}
- Produção Esperada: {row['Producao']}
"""     

        document = Document(
            page_content=page_content.strip(),
            metadata={
            "cultura": row["Cultura"],
            "tempo_colheita": row["TempoColheita"],
            "producao": row["Producao"]
            },
            id=str(i)
        )
        ids.append(str(i))
        documents.append(document)


vector_store = Chroma(
    collection_name="informacoes_plantio",
    persist_directory=db_location,
    embedding_function=embeddings
)

if add_documents:
    vector_store.add_documents(documents=documents, ids=ids)


retriever = vector_store.as_retriever(
    search_kwargs={"k": 3}
)