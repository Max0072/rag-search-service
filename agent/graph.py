from typing import TypedDict, List, Annotated
import operator
import json
import httpx
from openai import OpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from datetime import datetime

from config import (
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL,
    RAG_API_URL, MAX_ITERATIONS, CLAUDE_MAX_TOKENS
)
from prompts import (
    INITIAL_SEARCH_PROMPT, EVALUATE_DECIDE_PROMPT, GENERATE_ANSWER_PROMPT
)


# State
class AgentState(TypedDict):
    user_query: str
    chat_id: int
    iteration_count: int
    max_iterations: int
    search_history: Annotated[List[dict], operator.add]
    accumulated_results: Annotated[List[dict], operator.add]
    action: str
    reasoning: str
    search_request: dict
    final_answer: str


# OpenRouter client
client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY,
    default_headers={
        "HTTP-Referer": "https://github.com/yourusername/telegram-rag-bot",
        "X-Title": "Telegram RAG Bot"
    }
)


def call_claude(system: str, user_message: str) -> str:
    """Вызов Claude через OpenRouter"""
    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        max_tokens=CLAUDE_MAX_TOKENS,
        messages=[  # type: ignore
            {"role": "system", "content": system},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message.content


def parse_json_response(text: str) -> dict:
    """Парсинг JSON из ответа Claude"""
    import re

    # Убираем markdown
    text = text.replace("```json", "").replace("```", "").strip()

    # Убираем все control characters (включая \n, \r, \t)
    # ord < 32 это все управляющие символы ASCII
    text = ''.join(char if ord(char) >= 32 else " " for char in text)

    # Пытаемся распарсить
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Если не получилось, пытаемся найти JSON в тексте
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        raise e

# def parse_json_response(text: str) -> dict:
#     """Парсинг JSON из ответа Claude"""
#     # Убираем markdown
#     text = text.replace("```json", "").replace("```", "").strip()
#     # Убираем control characters
#     text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')
#     return json.loads(text)


async def call_rag_api(search_request: dict) -> dict:
    """Вызов RAG Search API"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(RAG_API_URL, json=search_request)
        response.raise_for_status()
        return response.json()


# Nodes
def plan_initial_search(state: AgentState) -> dict:  # type: ignore
    print(state)
    """Claude планирует первый поиск"""
    user_message = (f"Запрос пользователя: {state['user_query']}\n"
                    f"Текущая дата: {datetime.now().strftime('%Y-%m-%d')}")

    print(f"------------ User message ------------\n"
          f"{user_message}\n"
          f"--------------------------------------\n")

    response = call_claude(INITIAL_SEARCH_PROMPT, user_message)
    print(f"-------------- Response --------------\n"
          f"{response}\n"
          f"--------------------------------------\n")


    parsed = parse_json_response(response)

    return {
        "action": parsed.get("action", "answer"),
        "reasoning": parsed.get("reasoning", ""),
        "search_request": parsed.get("search_request"),
        "iteration_count": 1
    }


async def execute_search(state: AgentState) -> dict:  # type: ignore
    print(state)
    """Выполняет поиск через RAG API"""
    result = await call_rag_api(state["search_request"])

    results = result.get("results", [])

    # Дедупликация
    existing_ids = {
        (r.get("call_id"), r.get("chunk_text", r.get("summary", "")))
        for r in state.get("accumulated_results", [])
    }

    new_results = [
        r for r in results
        if (r.get("call_id"), r.get("chunk_text", r.get("summary", ""))) not in existing_ids
    ]

    return {
        "accumulated_results": new_results,
        "search_history": [{
            "iteration": state["iteration_count"],
            "search_params": state["search_request"],
            "total_found": len(results),
            "avg_score": result.get("avg_score", 0)
        }]
    }


def evaluate_and_decide(state: AgentState) -> dict:  # type: ignore
    print(state)
    """Claude решает: search или answer"""
    user_message = f"""Запрос пользователя: {state['user_query']}

Итерация: {state['iteration_count']}/{state['max_iterations']}

История поисков:
{json.dumps(state.get('search_history', []), ensure_ascii=False, indent=2)}

Накоплено результатов: {len(state.get('accumulated_results', []))}

Топ-3 результата:
{json.dumps(state.get('accumulated_results', [])[:3], ensure_ascii=False, indent=2)}

Что делать: search или answer?"""

    print(f"------------ User message ------------\n"
          f"{user_message}\n"
          f"--------------------------------------\n")

    response = call_claude(EVALUATE_DECIDE_PROMPT, user_message)
    print(f"-------------- Response --------------\n"
          f"{response}\n"
          f"--------------------------------------\n")

    parsed = parse_json_response(response)

    return {
        "action": parsed.get("action", "answer"),
        "reasoning": parsed.get("reasoning", ""),
        "search_request": parsed.get("search_request"),
        "iteration_count": state["iteration_count"] + 1
    }


def generate_answer(state: AgentState) -> dict:  # type: ignore
    """Claude генерирует финальный ответ"""
    user_message = f"""Запрос: {state['user_query']}

Reasoning: {state.get('reasoning', 'не указана')}

Все найденные результаты:
{json.dumps(state.get('accumulated_results', []), ensure_ascii=False, indent=2)}

Сформируй структурированный ответ."""
    print(f"------------ User message ------------\n"
          f"{user_message}\n"
          f"--------------------------------------\n")

    response = call_claude(GENERATE_ANSWER_PROMPT, user_message)

    print(f"-------------- Response --------------\n"
          f"{response}\n"
          f"--------------------------------------\n")

    return {"final_answer": response}


# Conditional edge
def should_continue(state: AgentState) -> str:
    """Решает: search или answer"""
    if (state.get("action") == "search" and
        state.get("iteration_count", 0) < state.get("max_iterations", MAX_ITERATIONS)):
        return "search"
    return "answer"


# Build graph
def build_graph():
    workflow = StateGraph(AgentState)  # type: ignore

    # Nodes
    workflow.add_node("plan_initial", plan_initial_search) # type: ignore
    workflow.add_node("execute_search", execute_search) # type: ignore
    workflow.add_node("evaluate", evaluate_and_decide) # type: ignore
    workflow.add_node("generate_answer", generate_answer) # type: ignore

    # Edges
    workflow.set_entry_point("plan_initial")
    # workflow.add_edge("plan_initial", "execute_search")
    workflow.add_conditional_edges(
        "plan_initial",
        should_continue,
        {
            "search": "execute_search",
            "answer": "generate_answer"
        }
    )
    workflow.add_edge("execute_search", "evaluate")
    workflow.add_conditional_edges(
        "evaluate",
        should_continue,
        {
            "search": "execute_search",
            "answer": "generate_answer"
        }
    )
    workflow.add_edge("generate_answer", END)

    # Compile with memory
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# Global agent
agent = build_graph()

