"""
Math Agent module for solving mathematical expressions using LangChain.
"""

import time
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.security.prompts import MATH_AGENT_SYSTEM_PROMPT
from app.core.logging import get_logger
from app.enums import ErrorMessage

logger = get_logger(__name__)


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
    start_time = time.time()

    logger.info("Starting math evaluation", query=query, query_preview=query[:50])

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

        execution_time = time.time() - start_time

        # Validate that we got a reasonable response
        if not result or result.lower() == "error":
            logger.error(
                "Math evaluation failed - no result",
                query=query,
                execution_time=execution_time,
            )
            raise ValueError(f"{ErrorMessage.MATH_EVALUATION_FAILED}: {query}")

        try:
            # Verify that the result is a valid number.
            result_float = float(result)
            # Check for reasonable bounds
            if abs(result_float) > 1e10:  # Prevent overflow
                raise ValueError(f"Result too large: {result}")
            if result_float != result_float:  # Check for NaN
                raise ValueError(f"Invalid result: {result}")
        except ValueError:
            logger.error(
                "Math evaluation failed - non-numerical or invalid result",
                query=query,
                result=result,
                execution_time=execution_time,
            )
            raise ValueError(
                f"{ErrorMessage.MATH_NON_NUMERICAL_RESULT}: '{result}'"
            )

        logger.info(
            "Math evaluation completed",
            query=query,
            result=result,
            execution_time=execution_time,
        )

        return result

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(
            "Math evaluation error",
            query=query,
            error=str(e),
            execution_time=execution_time,
        )
        raise ValueError(
            f"{ErrorMessage.MATH_EVALUATION_FAILED} '{query}': {str(e)}"
        ) from e
