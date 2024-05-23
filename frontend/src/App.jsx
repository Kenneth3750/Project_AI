import { Loader } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Leva } from "leva";
import { Experience } from "./components/Experience";
import { UI } from "./components/UI";
import React from 'react';
import { ChatEventListener } from './hooks/useChat';

function App() {
  return (
    <>
      <ChatEventListener />
      <Loader />
      <Leva  hidden/>
      <UI  />
      <Canvas shadows camera={{ position: [0, 0, 1], fov: 30 }}>
        <Experience />
      </Canvas>
    </>
  );
}

export default App;
