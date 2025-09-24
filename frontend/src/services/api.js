// Get API base URL from runtime configuration or fallback to build-time env var
const getApiBaseUrl = () => {
  // Try runtime configuration first (for production)
  if (window.APP_CONFIG && window.APP_CONFIG.API_BASE_URL) {
    return window.APP_CONFIG.API_BASE_URL;
  }
  // Fallback to build-time environment variable (for development)
  return import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
};

const API_BASE_URL = getApiBaseUrl();

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
    return apiRequest("/chat", {
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
    return apiRequest(`/chat/user/${userId}/conversations`);
  },

  // Get conversation history
  getConversationHistory: async (conversationId) => {
    return apiRequest(`/chat/history/${conversationId}`);
  },
};

export { ApiError };
