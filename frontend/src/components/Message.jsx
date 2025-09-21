import React from "react";

const Message = ({ message, isUser, timestamp, agent, isPending = false }) => {
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return "";
    const date = new Date(timestamp);
    return date.toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
          isUser ? "bg-blue-500 text-white" : "bg-gray-200 text-gray-800"
        } ${isPending ? "opacity-70" : ""}`}
      >
        <div className="text-sm">{message}</div>
        {timestamp && (
          <div
            className={`text-xs mt-1 ${
              isUser ? "text-blue-100" : "text-gray-500"
            }`}
          >
            {formatTimestamp(timestamp)}
          </div>
        )}
        {agent && !isUser && (
          <div className="text-xs mt-1 text-gray-500">Agent: {agent}</div>
        )}
        {isPending && (
          <div className="text-xs mt-1 text-gray-500">Enviando...</div>
        )}
      </div>
    </div>
  );
};

export default Message;
