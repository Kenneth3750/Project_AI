import React, { createContext, useContext, useEffect, useState } from "react";

//const backendUrl = "http://localhost:3000";

const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const chat = async (message) => {
    setLoading(true);
    const data = await fetch("/audio_prueba", {
      method: "POST",
      headers: {
      "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });
    const resp = (await data.json()).messages;
    setMessages((messages) => [...messages, ...resp]);
    setLoading(false);
  };
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState();
  const [loading, setLoading] = useState(false);
  const [cameraZoomed, setCameraZoomed] = useState(true);
  const onMessagePlayed = () => {
    setMessages((messages) => messages.slice(1));
  };

  useEffect(() => {
    if (messages.length > 0) {
      const message = messages[0];
      setMessage(message);
      const audio = new Audio("data:audio/mp3;base64," + message.audio);
      audio.play();
      audio.onended = () => {
        onMessagePlayed();
        if (messages.length === 1) {
          window.initRecognition(); // Suponiendo que esta es la función que deseas llamar
        }
      };
    } else {
      setMessage(null);
    }
  }, [messages]);

  return (
    <ChatContext.Provider
      value={{
        chat,
        message,
        onMessagePlayed,
        loading,
        cameraZoomed,
        setCameraZoomed,
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