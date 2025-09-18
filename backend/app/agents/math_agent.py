"""
Math Agent module for solving mathematical expressions using LangChain.
"""

import os
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage


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

    # System prompt instructing the LLM to act as a calculator
    system_prompt = """You are a mathematical calculator. Your job is to evaluate mathematical expressions and return ONLY the numerical result.

Rules:
1. Evaluate the mathematical expression provided
2. Return ONLY the final numerical result as a string
3. Do not include any explanations, steps, or additional text
4. If the expression is invalid or cannot be evaluated, return "Error"
5. Use standard mathematical notation and operations
6. Handle basic arithmetic, algebra, and other common mathematical operations

Examples:
- Input: "How much is 2 + 3" → Output: "5"
- Input: "10 * 5" → Output: "50"
- Input: "sqrt(16)" → Output: "4"
- Input: "2^3" → Output: "8"
- Input: "sin(pi/2)" → Output: "1"
"""

    # Create messages
    messages = [
        SystemMessage(content=system_prompt),
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
