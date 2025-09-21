"""
Redis service for managing conversation history.

This module provides functions to store and retrieve conversation history
using Redis as the storage backend.
"""

import json
from typing import Any
from datetime import datetime, UTC

import redis
from redis.exceptions import RedisError

from app.core.settings import get_settings
from app.core.logging import get_logger, log_system_event

# Configure logging
logger = get_logger(__name__)


class RedisService:
    """Redis service for conversation history management."""

    def __init__(self, settings=None):
        """
        Initialize Redis connection using application settings.

        Args:
            settings: Optional settings instance. If None, will use get_settings()
        """
        if settings is None:
            settings = get_settings()

        self.settings = settings

        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.get_redis_password(),
                decode_responses=True,
                socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                retry_on_error=[TimeoutError, ConnectionError],
            )
            # Test connection
            self.redis_client.ping()
            logger.info(
                f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}"
            )
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def add_message_to_history(
        self, conversation_id: str, user_message: str, agent_response: str
    ) -> bool:
        """
        Add a message exchange to conversation history.

        Args:
            conversation_id: Unique identifier for the conversation
            user_message: The user's message
            agent_response: The agent's response

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create message entry
            message_entry = {
                "timestamp": datetime.now(UTC),
                "user_message": user_message,
                "agent_response": agent_response,
            }

            # Use Redis list to store conversation history
            # Key format: "conversation:{conversation_id}"
            key = f"conversation:{conversation_id}"

            # Add message to the end of the list
            self.redis_client.rpush(key, json.dumps(message_entry))

            # Set expiration for the conversation using settings TTL
            self.redis_client.expire(key, self.settings.REDIS_CONVERSATION_TTL)

            logger.info(f"Added message to conversation {conversation_id}")
            return True

        except RedisError as e:
            logger.error(f"Failed to add message to history: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error adding message to history: {e}")
            return False

    def get_history(self, conversation_id: str) -> list[dict[str, Any]]:
        """
        Retrieve conversation history.

        Args:
            conversation_id: Unique identifier for the conversation

        Returns:
            list[dict[str, Any]]: List of message exchanges in chronological order
        """
        try:
            key = f"conversation:{conversation_id}"

            # Get all messages from the list
            messages = self.redis_client.lrange(key, 0, -1)

            # Parse JSON messages
            history = []
            for message_json in messages:
                try:
                    message_data = json.loads(message_json)
                    history.append(message_data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse message JSON: {e}")
                    continue

            logger.info(
                f"Retrieved {len(history)} messages for conversation {conversation_id}"
            )
            return history

        except RedisError as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting conversation history: {e}")
            return []

    def clear_history(self, conversation_id: str) -> bool:
        """
        Clear conversation history.

        Args:
            conversation_id: Unique identifier for the conversation

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            key = f"conversation:{conversation_id}"
            result = self.redis_client.delete(key)
            logger.info(f"Cleared history for conversation {conversation_id}")
            return result > 0
        except RedisError as e:
            logger.error(f"Failed to clear conversation history: {e}")
            return False

    def get_conversation_count(self, conversation_id: str) -> int:
        """
        Get the number of messages in a conversation.

        Args:
            conversation_id: Unique identifier for the conversation

        Returns:
            int: Number of messages in the conversation
        """
        try:
            key = f"conversation:{conversation_id}"
            return self.redis_client.llen(key)
        except RedisError as e:
            logger.error(f"Failed to get conversation count: {e}")
            return 0


# Global Redis service instance (lazy initialization)
redis_service = None


def _get_redis_service() -> RedisService | None:
    """Get Redis service instance with lazy initialization."""
    global redis_service
    if redis_service is None:
        try:
            redis_service = RedisService()
        except Exception as e:
            logger.warning(f"Redis service unavailable: {e}")
            return None
    return redis_service


# Convenience functions for direct use
def add_message_to_history(
    conversation_id: str, user_message: str, agent_response: str
) -> bool:
    """
    Add a message exchange to conversation history.

    Args:
        conversation_id: Unique identifier for the conversation
        user_message: The user's message
        agent_response: The agent's response

    Returns:
        bool: True if successful, False otherwise
    """
    service = _get_redis_service()
    if service is None:
        logger.warning("Redis service unavailable, message not stored")
        return False
    return service.add_message_to_history(conversation_id, user_message, agent_response)


def get_history(conversation_id: str) -> list[dict[str, Any]]:
    """
    Retrieve conversation history.

    Args:
        conversation_id: Unique identifier for the conversation

    Returns:
        list[dict[str, Any]]: list of message exchanges in chronological order
    """
    service = _get_redis_service()
    if service is None:
        logger.warning("Redis service unavailable, returning empty history")
        return []
    return service.get_history(conversation_id)
