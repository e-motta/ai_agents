import React from "react";

const ErrorNotification = ({ error, onDismiss }) => {
  if (!error) return null;

  return (
    <div className="fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 max-w-md">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="text-xl">⚠️</div>
          <div>
            <div className="font-semibold">Erro</div>
            <div className="text-sm">{error}</div>
          </div>
        </div>
        <button
          onClick={onDismiss}
          className="ml-4 text-white hover:text-gray-200 focus:outline-none"
        >
          ✕
        </button>
      </div>
    </div>
  );
};

export default ErrorNotification;
