from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector import retriever

model = OllamaLLM(model="llama3.2")

template = """
  You are an expert in answering questions about agriculture in Brazil's south.

  Base your answers in the following information: {info}

  Here is the question for you to answer: {question}   
"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

while True:
    print("n\n---------------------------------------------")
    question = input("Faça uma pergunta sobre agricultura (S para sair): ")
    if question == "S" or question == "s":
        break         

    info = retriever.invoke(question)
    result = chain.invoke({"info": info, "question": question})
    print(result)