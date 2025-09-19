"""
Math Agent module for solving mathematical expressions using LangChain.
"""

import os
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from app.security.prompts import MATH_AGENT_SYSTEM_PROMPT


def solve_math(query: str) -> str:
    """
    Solve a mathematical expression using an LLM calculator.

    Args:
        query (str): The mathematical expression to evaluate

    Returns:
        str: The numerical result as a string

    Raises:
        ValueError: If the query cannot be evaluated or if API key is missing
    """
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    # Initialize the LLM
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=api_key)

    # Create messages
    messages = [
        SystemMessage(content=MATH_AGENT_SYSTEM_PROMPT),
        HumanMessage(content=f"Evaluate this mathematical expression: {query}"),
    ]

    try:
        # Get response from LLM
        response = llm.invoke(messages)
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
