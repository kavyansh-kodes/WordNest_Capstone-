import asyncio
import streamlit as st
from typing import TypedDict, Annotated, Optional, Any
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_groq import ChatGroq
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage,AIMessage
from tools import (get_n_random_words, get_n_random_words_by_difficulty_level,
translate_words,generate_examples_and_text,explain_grammar)
from profile_tools import (get_user_profile, set_learning_goal, get_learning_goal,
save_learned_words,get_learned_words,get_personalized_words,get_personalized_words_by_difficulty)

key = st.secrets["GROQ_API_KEY"]

local_tools = [ get_n_random_words, get_n_random_words_by_difficulty_level, translate_words,
generate_examples_and_text, explain_grammar,
get_user_profile,set_learning_goal, get_learning_goal, save_learned_words, get_learned_words,
get_personalized_words,get_personalized_words_by_difficulty ]

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    username: Optional[str]
    source_language: Optional[str]
    number_of_words: Optional[int]
    word_difficulty: Optional[str]
    target_language: Optional[str]

async def setup_tools():
    return [*local_tools]

def assistant(state: AgentState):
    sys_msg = SystemMessage(content=f"""
    You are an intelligent language-learning assistant. 
    Your purpose is to help users learn vocabulary in different languages through personalized and adaptive learning.
    Current username: {state.get("username")}
    
    AVAILABLE TOOLS

    Vocabulary Tools:
    1. get_n_random_words(language: str, n: int)
       - Generates random vocabulary words.

    2. get_n_random_words_by_difficulty_level(language: str,difficulty_level: str,n: int)
       - Generates random vocabulary words filtered by difficulty.
       - Supported levels:
         beginner
         intermediate
         advanced

    3. translate_words(random_words: list,source_language: str,target_language: str)
       - Translates generated vocabulary words.

    4. generate_examples_and_text(words: list,source_language: str,target_language: str)
       - Generates example sentences.
       - Generates a short practice text.

    Profile & Memory Tools:
    5. get_user_profile(username: str)
       - Retrieves the user's profile.

    6. set_learning_goal(username: str, goal: str)
       - Sets or updates a learning goal.

    7. get_learning_goal(username: str)
       - Retrieves the current learning goal.

   8. save_learned_words(
       username: str,
       language: str,
       words: dict
   )
   - Stores learned words in the format:
     {{
         "Haus":"House",
         "Hund":"Dog"
     }}
    9. get_learned_words(username: str,language: str)
       - Retrieves previously learned words.

    Adaptive Learning Tools:
    10. get_personalized_words(username: str,language: str,n: int)
        - Generates vocabulary words the user has NOT learned before.

    11. get_personalized_words_by_difficulty(
        username: str, language: str, difficulty_level: str,n: int ) 
        - Generates unseen vocabulary words filtered by difficulty.

    --------------------------------------------------
    VOCABULARY GENERATION RULES
    --------------------------------------------------
If a username is available:
- Prefer get_personalized_words().
- Prefer get_personalized_words_by_difficulty() when difficulty is specified.
- Avoid repeating previously learned words.
- Use the adaptive tools whenever possible.

If a username is NOT available:
- Use get_n_random_words().
- Use get_n_random_words_by_difficulty_level().

    --------------------------------------------------
    VOCABULARY LEARNING WORKFLOW
    --------------------------------------------------
    Whenever a user requests vocabulary:
    Step 1: Generate vocabulary words.
    Step 2: Translate the generated words.
    Step 3: Generate example sentences.
    Step 4: Generate a short practice paragraph.
    Do not stop after generating words.
    Do not stop after translating words.
    
    Always provide:
    - Vocabulary words
    - Translations
    - Example sentences
    - Practice paragraph
    - Paragraph translation
    --------------------------------------------------
    PROFILE MANAGEMENT RULES
    --------------------------------------------------
    Users may:
    - View their profile
    - Set learning goals
    - View learning goals
    - Continue previous learning sessions
    Use the profile tools whenever appropriate.
    --------------------------------------------------
    ADAPTIVE LEARNING RULES
    --------------------------------------------------
   When a user has a profile:
- Personalize vocabulary selection.
- Avoid repeating already learned words.
- Use profile information when available.
- Consider the user's learning goals when responding.

    --------------------------------------------------
    EXAMPLES
    --------------------------------------------------
    User: Give me 10 beginner German words translated to English.
    Workflow:
    get_personalized_words_by_difficulty
    → translate_words
    → save_learned_words
    → generate_examples_and_text
    User: Give me 20 advanced Spanish words.
    Workflow:
    get_personalized_words_by_difficulty
    → translate_words
    → save_learned_words
    → generate_examples_and_text
    User: Give me 15 random Japanese words.
    Workflow:
    get_personalized_words
    → translate_words
    → save_learned_words
    → generate_examples_and_text
    User: My goal is to reach conversational German in 6 months.
    Workflow: set_learning_goal
    User: What is my learning goal?
    Workflow: get_learning_goal
    User: Show me my profile.
    Workflow: get_user_profile
    """)

    tools = assistant.tools if hasattr(assistant, "tools") else []
    llm = ChatGroq(model="qwen/qwen3-32b", groq_api_key=key)
    llm_with_tools = llm.bind_tools(tools)
    try:
        msgs = [llm_with_tools.invoke([sys_msg] + state["messages"])]
    except Exception as e:
        msgs = [AIMessage(content="Model temporarily overloaded. Please try again.")]
    return {"messages": msgs,
            "username": state.get("username"),
            "source_language": state.get("source_language"),
            "number_of_words": state.get("number_of_words"),
            "word_difficulty": state.get("word_difficulty"),
            "target_language": state.get("target_language")}

async def build_graph() -> CompiledStateGraph[Any, Any, Any, Any]:
    """" Build the state graph with properly initialized tools """
    tools = await setup_tools()
    assistant.tools = local_tools
    builder = StateGraph(AgentState)
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", tools_condition)
    builder.add_edge("tools", "assistant")
    return builder.compile()

async def main():
    """ Main async function to run the application."""
    react_graph = await build_graph()
    user_prompt = ("Get 10 beginner words in German, translated to English."
                   "The translation of the words should be in English script")
    messages = [HumanMessage(content=user_prompt)]
    result = await react_graph.ainvoke({
        "messages": messages,"username":"Kavyansh" ,"source_language": None, "number_of_words": None,
        "word_difficulty": None, "target_language": None})
    print("\n")
    print("=" * 80)
    print("FINAL RESPONSE")
    print("=" * 80)
    print("\n")
    print(result["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())
