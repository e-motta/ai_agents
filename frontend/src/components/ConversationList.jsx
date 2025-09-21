import React from "react";

const ConversationList = ({
  conversations,
  currentConversationId,
  onSelectConversation,
  onCreateNewConversation,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div className="w-64 bg-gray-100 p-4">
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="bg-gray-200 h-12 rounded-lg"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="w-64 bg-gray-100 border-r border-gray-200 flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">Conversas</h2>
        <button
          onClick={onCreateNewConversation}
          className="w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          + Nova Conversa
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <p className="text-sm">Nenhuma conversa ainda</p>
          </div>
        ) : (
          <div className="p-2">
            {conversations.map((conversationId) => (
              <button
                key={conversationId}
                onClick={() => onSelectConversation(conversationId)}
                className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                  currentConversationId === conversationId
                    ? "bg-blue-100 text-blue-800 border border-blue-200"
                    : "hover:bg-gray-200 text-gray-700"
                }`}
              >
                <div className="text-sm font-medium">
                  Conversa {conversationId}
                </div>
                <div className="text-xs text-gray-500">
                  ID: {conversationId}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ConversationList;
