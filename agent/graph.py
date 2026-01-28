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

# ============================================================
# GLOBAL STATE для Dashboard (real-time в памяти)
# ============================================================
CURRENT_CHAT_STATE = {}
CURRENT_SEARCH_STATE = {}


# ============================================================
# LEVEL 2: Search Agent State (одноразовый для каждого поиска)
# ============================================================
class SearchState(TypedDict):
    search_query: str
    messages: List[dict]
    iteration_count: int
    max_iterations: int
    search_history: List[dict]  # БЕЗ operator.add - одноразовый
    accumulated_results: List[dict]  # БЕЗ operator.add - одноразовый
    search_list: List[dict]  # Хронология: [{"type": "user_message"|"model_answer"|"search_result", "content": ...}]
    action: str
    reasoning: str
    search_request: dict
    final_answer: str
    answer: str


# ============================================================
# LEVEL 1: Chat Agent State (долгоживущий для диалога)
# ============================================================
class ChatState(TypedDict):
    user_query: str
    chat_id: int
    messages: Annotated[List[dict], operator.add]  # Формат для LLM: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]


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


# ============================================================
# SEARCH AGENT NODES (Level 2)
# ============================================================
def plan_initial_search(state: SearchState) -> dict:  # type: ignore
    global CURRENT_SEARCH_STATE
    print(state)
    """Claude планирует первый поиск"""
    user_message = (f"Запрос пользователя: {state['search_query']}\n"
                    f"Текущая дата: {datetime.now().strftime('%Y-%m-%d')}")

    print(f"------------ User message ------------\n"
          f"{user_message}\n"
          f"--------------------------------------\n")

    response = call_claude(INITIAL_SEARCH_PROMPT, user_message)
    print(f"-------------- Response --------------\n"
          f"{response}\n"
          f"--------------------------------------\n")


    parsed = parse_json_response(response)

    # Создаем search_list записи
    search_list = state.get("search_list", [])
    search_list.append({
        "type": "user_message",
        "content": state['search_query']
    })
    search_list.append({
        "type": "model_answer",
        "content": f"Action: {parsed.get('action', 'answer')}\nReasoning: {parsed.get('reasoning', '')}"
    })

    result = {
        "action": parsed.get("action", "answer"),
        "reasoning": parsed.get("reasoning", ""),
        "search_request": parsed.get("search_request"),
        "iteration_count": 1,
        "search_list": search_list,
        "answer": parsed.get("answer", ""),
    }

    # Обновляем глобальный state для dashboard
    CURRENT_SEARCH_STATE.update(state)
    CURRENT_SEARCH_STATE.update(result)

    return result


async def execute_search(state: SearchState) -> dict:  # type: ignore
    global CURRENT_SEARCH_STATE
    print(state)
    """Выполняет поиск через RAG API"""

    # Добавляем в search_list запрос к API
    search_list = state.get("search_list", [])
    search_list.append({
        "type": "api_request",
        "content": json.dumps(state["search_request"], ensure_ascii=False, indent=2)
    })

    result = await call_rag_api(state["search_request"])

    results = result.get("results", [])

    print(f"------------ Search results ------------\n"
          f"{result}\n"
          f"----------------------------------------\n")

    # Дедупликация
    existing_ids = {
        (r.get("call_id"), r.get("chunk_text", r.get("summary", "")))
        for r in state.get("accumulated_results", [])
    }

    new_results = [
        r for r in results
        if (r.get("call_id"), r.get("chunk_text", r.get("summary", ""))) not in existing_ids
    ]

    # Добавляем к существующим результатам (вручную, без operator.add)
    updated_results = state.get("accumulated_results", []) + new_results
    updated_history = state.get("search_history", []) + [{
        "iteration": state["iteration_count"],
        "search_params": state["search_request"],
        "total_found": len(results),
        "avg_score": result.get("avg_score", 0)
    }]

    # Добавляем в search_list
    search_list = state.get("search_list", [])

    # Формируем краткое описание найденных результатов
    results_preview = ""
    for i, r in enumerate(new_results[:3], 1):  # Показываем топ-3
        call_id = r.get("call_id", "unknown")
        summary = r.get("summary", "")[:150] if r.get("summary") else ""
        chunk = r.get("chunk_text", "")[:150] if r.get("chunk_text") else ""
        content = summary or chunk or "No content"
        results_preview += f"\n{i}. [{call_id}] {content}..."

    if len(new_results) > 3:
        results_preview += f"\n... и еще {len(new_results) - 3} результатов"

    search_list.append({
        "type": "search_result",
        "content": f"Found: {len(results)} results | Avg score: {result.get('avg_score', 0):.3f} | New: {len(new_results)}{results_preview}"
    })

    result_dict = {
        "accumulated_results": updated_results,
        "search_history": updated_history,
        "search_list": search_list
    }

    # Обновляем глобальный state для dashboard
    CURRENT_SEARCH_STATE.update(state)
    CURRENT_SEARCH_STATE.update(result_dict)

    return result_dict


def evaluate_and_decide(state: SearchState) -> dict:  # type: ignore
    global CURRENT_SEARCH_STATE
    print(state)
    """Claude решает: search или answer"""
    user_message = f"""Запрос пользователя: {state['search_query']}

Итерация: {state['iteration_count']}/{state['max_iterations']}

История поисков:
{json.dumps(state.get('search_history', []), ensure_ascii=False, indent=2)}

Накоплено результатов: {len(state.get('accumulated_results', []))}

Результаты:
{json.dumps(state.get('accumulated_results', [])[:-1], ensure_ascii=False, indent=2)}

Что делать: search или answer?"""

    print(f"------------ User message ------------\n"
          f"{user_message}\n"
          f"--------------------------------------\n")

    response = call_claude(EVALUATE_DECIDE_PROMPT, user_message)
    print(f"-------------- Response --------------\n"
          f"{response}\n"
          f"--------------------------------------\n")

    parsed = parse_json_response(response)

    # Добавляем в search_list
    search_list = state.get("search_list", [])
    search_list.append({
        "type": "model_answer",
        "content": f"Action: {parsed.get('action', 'answer')}\nReasoning: {parsed.get('reasoning', '')}"
    })

    result = {
        "action": parsed.get("action", "answer"),
        "reasoning": parsed.get("reasoning", ""),
        "search_request": parsed.get("search_request"),
        "iteration_count": state["iteration_count"] + 1,
        "search_list": search_list,
        "answer": parsed.get("answer", "")
    }

    # Обновляем глобальный state для dashboard
    CURRENT_SEARCH_STATE.update(state)
    CURRENT_SEARCH_STATE.update(result)

    return result

def just_answer(state: SearchState) -> dict:

    response = state.get('answer', 'не указана')
    # Добавляем в search_list полный финальный ответ
    search_list = state.get("search_list", [])
    search_list.append({
        "type": "final_answer",
        "content": response
    })

    result = {
        "final_answer": response,
        "search_list": search_list
    }

    # Обновляем глобальный state для dashboard
    CURRENT_SEARCH_STATE.update(state)
    CURRENT_SEARCH_STATE.update(result)

    return result


def generate_answer(state: SearchState) -> dict:  # type: ignore
    global CURRENT_SEARCH_STATE
    """Claude генерирует финальный ответ"""
    user_message = f"""Запрос: {state['search_query']}

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

    # Добавляем в search_list полный финальный ответ
    search_list = state.get("search_list", [])
    search_list.append({
        "type": "final_answer",
        "content": response
    })

    result = {
        "final_answer": response,
        "search_list": search_list
    }

    # Обновляем глобальный state для dashboard
    CURRENT_SEARCH_STATE.update(state)
    CURRENT_SEARCH_STATE.update(result)

    return result


# Conditional edge для Search Agent
def should_continue_search(state: SearchState) -> str:
    """Решает: search или answer"""
    if (state.get("action") == "search" and
        state.get("iteration_count", 0) < state.get("max_iterations", MAX_ITERATIONS)):
        return "search"
    return "answer"


# ============================================================
# BUILD SEARCH AGENT (Level 2 - одноразовый)
# ============================================================
def build_search_agent():
    """Граф для итеративного поиска - БЕЗ памяти"""
    workflow = StateGraph(SearchState)  # type: ignore

    # Nodes
    workflow.add_node("plan_initial", plan_initial_search) # type: ignore
    workflow.add_node("execute_search", execute_search) # type: ignore
    workflow.add_node("evaluate", evaluate_and_decide) # type: ignore
    workflow.add_node("generate_answer", generate_answer) # type: ignore
    workflow.add_node("just_answer", just_answer) # type: ignore

    # Edges
    workflow.set_entry_point("plan_initial")
    workflow.add_conditional_edges(
        "plan_initial",
        should_continue_search,
        {
            "search": "execute_search",
            "answer": "just_answer"
        }
    )
    workflow.add_edge("execute_search", "evaluate")
    workflow.add_conditional_edges(
        "evaluate",
        should_continue_search,
        {
            "search": "execute_search",
            "answer": "just_answer"
        }
    )
    workflow.add_edge("generate_answer", END)

    # Compile БЕЗ checkpointer - одноразовый state
    return workflow.compile()



# ============================================================
# BUILD CHAT AGENT (Level 1 - долгоживущий)
# ============================================================
def build_chat_agent():
    """Граф для диалога с пользователем - С памятью"""
    workflow = StateGraph(ChatState)  # type: ignore

    # Создаем экземпляр search_agent
    search_agent = build_search_agent()

    async def run_search(state: ChatState) -> dict:  # type: ignore
        global CURRENT_CHAT_STATE, CURRENT_SEARCH_STATE
        """Запускает Search Agent для поиска ответа"""

        CURRENT_CHAT_STATE.update({
            "user_query": state["user_query"],
            "chat_id": state["chat_id"],
            "messages": state.get("messages", []),
        })

        # Очищаем Search State перед новым поиском
        CURRENT_SEARCH_STATE.clear()

        # Запускаем одноразовый Search Agent
        search_result = await search_agent.ainvoke({ # type: ignore
            "search_query": state["user_query"],
            "messages": get_chat_messages(chat_id=state["chat_id"]),
            "iteration_count": 0,
            "max_iterations": MAX_ITERATIONS,
            "search_history": [],  # Пустые каждый раз
            "accumulated_results": [],  # Пустые каждый раз
            "search_list": [],  # Пустая хронология
            "action": "",
            "reasoning": "",
            "search_request": {},
            "final_answer": ""
        })

        print(f"✅ Search Agent вернул ответ")

        # Сохраняем в историю в формате messages для LLM
        result = {
            "messages": [{"role": "assistant", "content": search_result["final_answer"]}]
        }

        # Обновляем Chat State для dashboard
        # Важно: берем полную историю из state (включая старые записи)
        full_messages = state.get('messages', []) + result['messages']

        CURRENT_CHAT_STATE.clear()
        CURRENT_CHAT_STATE.update({
            "user_query": state["user_query"],
            "chat_id": state["chat_id"],
            "messages": full_messages,
            "messages_count": len(full_messages)
        })

        print(f"✅ Dashboard обновлен. Всего сообщений: {len(full_messages)}")

        return result

    # Единственная нода - запуск поиска
    workflow.add_node("search", run_search)  # type: ignore
    workflow.set_entry_point("search")
    workflow.add_edge("search", END)

    # save config
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)



# ============================================================
# Global agents
# ============================================================
search_agent = build_search_agent()  # Одноразовый
agent = build_chat_agent()  # Главный агент с памятью


# ============================================================
# Хелпер для получения messages в формате для LLM
# ============================================================
def get_chat_messages(chat_id: int) -> List[dict]:
    """
    Получить историю сообщений для отправки в LLM

    Returns: [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
        ...
    ]
    """
    return CURRENT_CHAT_STATE.get('messages', [])

