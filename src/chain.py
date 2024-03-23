from langchain_core.language_models.chat_models import BaseChatModel
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_pinecone import PineconeVectorStore
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CohereRerank
from langchain import VectorDBQAWithSourcesChain

QUERY_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""You are an AI language model assistant. Your task is to generate 3 
    different versions of the given user question to retrieve relevant documents from a vector 
    database. By generating multiple perspectives on the user question, your goal is to help
    the user overcome some of the limitations of the distance-based similarity search. 
    Provide these alternative questions separated by newlines.
    Original question: {question}""",
)

RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are an intelligent and supportive virtual advisor, specialized in guiding University of Florida (UF) students 
    through their academic journey. Your expertise encompasses class selection, scheduling, understanding prerequisites, and aligning 
    courses with the student's major and academic year, including previously completed courses. Your responses should be precise, insightful, 
    and directly applicable to the student's queries.
    
    When the information provided does not cover a question, your response should be: "I'm sorry, but I don't have information on that topic." 
    If the context lacks the details needed to formulate a response, kindly reply with: "I'm sorry, but I couldn't find any relevant information on that."
    
    Maintain relevance and steer clear of digressions. Your primary goal is to facilitate a smooth and informed academic planning process for UF students.
    Context: {context}
    Question: {question}"""
)


class Question(BaseModel):
    __root__: str

def get_chain(
        model: BaseChatModel, 
        vectorstore: PineconeVectorStore, 
        top_k: int = 10, 
        top_n: int = 3,
        multiquery: bool = False,
        rerank: bool = False
    ):
    """Build a chain"""
    print("Building chain")

    # retrieve the top k docs from the db
    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})


    if multiquery:
        # translate the query into new queries 
        retriever = MultiQueryRetriever.from_llm(
            retriever=retriever, llm=model, prompt=QUERY_PROMPT
        )
        
    if rerank:
        # reranks docs and uses the top n docs in final response
        compressor = CohereRerank(top_n=top_n)
        retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=retriever
        )

    # https://python.langchain.com/docs/use_cases/question_answering/sources
    chain = (
        # RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
        RunnablePassthrough()
        | RAG_PROMPT                 # pass retrieved docs (context) + question into the RAG_PROMPT
        | model                      # pass the prompt into the LLM
        | StrOutputParser()          # return output
    )

    chain_with_source = RunnableParallel(
        {"context": retriever, "question": RunnablePassthrough()}
    ).assign(answer=chain)
    return chain_with_source.with_types(input_type=Question)