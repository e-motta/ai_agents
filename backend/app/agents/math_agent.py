"""
Math Agent module for solving mathematical expressions using LangChain.
"""

from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.security.prompts import MATH_AGENT_SYSTEM_PROMPT


async def solve_math(query: str, llm: ChatOpenAI) -> str:
    """
    Solve a mathematical expression using an LLM calculator.

    Args:
        query (str): The mathematical expression to evaluate
        llm (ChatOpenAI): The LLM instance to use for calculations

    Returns:
        str: The numerical result as a string

    Raises:
        ValueError: If the query cannot be evaluated
    """

    # Create messages
    messages = [
        SystemMessage(content=MATH_AGENT_SYSTEM_PROMPT),
        HumanMessage(content=f"Evaluate this mathematical expression: {query}"),
    ]

    try:
        # Get response from LLM asynchronously
        response = await llm.ainvoke(messages)
        # Handle different response formats
        if isinstance(response.content, list):
            result = " ".join(str(item) for item in response.content).strip()
        else:
            result = response.content.strip()

        # Validate that we got a reasonable response
        if not result or result.lower() == "error":
            raise ValueError(f"Could not evaluate the expression: {query}")

        try:
            # Verify that the result is a valid number.
            float(result)
        except ValueError:
            raise ValueError(f"LLM returned a non-numerical result: '{result}'")
        return result

    except Exception as e:
        raise ValueError(
            f"Error evaluating mathematical expression '{query}': {str(e)}"
        ) from e
