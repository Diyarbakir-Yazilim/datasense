import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from prompts.manager import PromptManager
from agents.output_parser import DataCleaningDecision

# Load environment variables (like GEMINI_API_KEY)
load_dotenv()

def get_data_cleaning_decision(data_metadata: str) -> dict:
    """
    Invokes the LLM to get data cleaning decisions based on the provided metadata.
    Returns a dictionary representing the structured data cleaning decisions.
    """
    # 1. Initialize the LLM based on available API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    if openai_key and openai_key != "your-openai-api-key-here" and openai_key.strip():
        llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
    elif google_key and google_key != "your-gemini-api-key-here" and google_key.strip():
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)
    elif groq_key and groq_key.strip():
        # Fallback to Groq if added later
        from langchain_groq import ChatGroq
        llm = ChatGroq(model="llama3-70b-8192", temperature=0.0)
    else:
        raise ValueError("No valid API key found for OpenAI, Google Gemini, or Groq in the environment.")
    
    # 2. Bind the LLM to output our Pydantic schema
    # Modern LangChain approach replacing manual StructuredOutputParser
    structured_llm = llm.with_structured_output(DataCleaningDecision)
    
    # 3. Load the appropriate prompt using PromptManager
    prompt_manager = PromptManager()
    prompt_template_str, version_id = prompt_manager.get_prompt("data_cleaning")
    
    # 4. Prepare the prompt template
    prompt = PromptTemplate(
        template=prompt_template_str,
        input_variables=["data_metadata"]
    )
    
    # 5. Create the chain (Prompt -> LLM with Structured Output)
    chain = prompt | structured_llm
    
    # 6. Invoke the chain and get the structured Pydantic object
    decision: DataCleaningDecision = chain.invoke({"data_metadata": data_metadata})
    
    # 7. Return as a dictionary for easy consumption by the backend API
    decision_dict = decision.model_dump()
    decision_dict["prompt_version"] = version_id
    
    return decision_dict
