import React, { createContext, useContext, useEffect, useState } from "react";

//const backendUrl = "http://localhost:3000";

const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const [playedMessageIds, setPlayedMessageIds] = useState(new Set());
  const chat = async (message) => {
    setLoading(true);
    const data = await fetch("/audio", {
      method: "POST",
      headers: {
      "Content-Type": "application/json",
      }, 
      body: JSON.stringify({ message }),
    });
    const resp = (await data.json());
    if (resp.error) {
      console.error(resp.error);
      setLoading(false);
      window.stopRecognition();
      alert("An error ocurred: " + resp.error);
      return;
    }
    const respMessages = resp.messages;
    const respDisplayResponses = resp.display_responses;
    console.log("mensajes:", respMessages);
    console.log("display:", respDisplayResponses);
    setPlayedMessageIds(new Set());
    setMessages((messages) => [...messages, ...respMessages]);

    if (!Array.isArray(respDisplayResponses)) {
      console.error("respDisplayResponses is not an array");
    } else {
      if (respDisplayResponses.length > 0) {
        setDisplayResponses(respDisplayResponses);
      }
    }
    setLoading(false);
  };
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState();
  const [loading, setLoading] = useState(false);
  const [cameraZoomed, setCameraZoomed] = useState(true);
  const [displayResponses, setDisplayResponses] = useState([]);
  const onMessagePlayed = () => {
    setMessages((messages) => messages.slice(1));
  };

  useEffect(() => {
    if (messages.length > 0) {
      setMessage(messages[0]);
    } else {
      setMessage(null);
    }
  }, [messages]);

  return (
    <ChatContext.Provider
      value={{
        chat,
        message,
        messages,
        onMessagePlayed,
        loading,
        cameraZoomed,
        setCameraZoomed,
        displayResponses,
        playedMessageIds,
        setPlayedMessageIds,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};

export const ChatEventListener = () => {
  const { chat } = useContext(ChatContext);

  useEffect(() => {
    const handleChatEvent = async (event) => {
     await chat(event.detail);
    };

    window.addEventListener('chat', handleChatEvent);

    return () => {
      window.removeEventListener('chat', handleChatEvent);
    };
  }, [chat]);

  return null; // Este componente no necesita renderizar nada
};