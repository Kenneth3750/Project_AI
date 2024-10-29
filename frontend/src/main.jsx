import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { ChatProvider, useChat } from "./hooks/useChat";
import { NotificationProvider } from './components/NotificationContext';
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <NotificationProvider>
      <ChatProvider>
        <App />
      </ChatProvider>
    </NotificationProvider>
  </React.StrictMode>
);

export { useChat };