import React from "react";
import Message from "./Message";

const MessageList = ({ messages, isLoading }) => {
  if (isLoading) {
    return (
      <div className="flex-1 p-4">
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="flex justify-start">
                <div className="bg-gray-200 h-16 w-3/4 rounded-lg"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!messages || messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="text-center text-gray-500">
          <div className="text-4xl mb-4">💬</div>
          <p>Nenhuma mensagem ainda.</p>
          <p className="text-sm">Envie uma mensagem para começar a conversa!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((msg, index) => (
        <Message
          key={index}
          message={msg.user_message || msg.message}
          isUser={!!msg.user_message}
          timestamp={msg.timestamp}
          agent={msg.agent_response ? "LLM" : msg.router_decision}
          isPending={msg.isPending}
        />
      ))}
      {messages.some((msg) => msg.isPending) && (
        <div className="flex justify-start">
          <div className="bg-gray-200 px-4 py-2 rounded-lg">
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
              <span className="text-sm text-gray-600">Processando...</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MessageList;
