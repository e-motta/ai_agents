const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const apiRequest = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;

  const config = {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      throw new ApiError(
        `HTTP error! status: ${response.status}`,
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(`Network error: ${error.message}`, 0);
  }
};

export const chatApi = {
  // Send a message to the chat
  sendMessage: async (message, userId, conversationId) => {
    return apiRequest("/api/v1/chat", {
      method: "POST",
      body: JSON.stringify({
        message,
        user_id: userId,
        conversation_id: conversationId,
      }),
    });
  },

  // Get user conversations
  getUserConversations: async (userId) => {
    return apiRequest(`/api/v1/chat/user/${userId}/conversations`);
  },

  // Get conversation history
  getConversationHistory: async (conversationId) => {
    return apiRequest(`/api/v1/chat/history/${conversationId}`);
  },
};

export { ApiError };
