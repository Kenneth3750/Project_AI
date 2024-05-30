import { Loader } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Leva } from "leva";
import { Experience } from "./components/Experience";
import { UI } from "./components/UI";
import SubtitlesContext from './components/subtitiles';
import React, {useState} from 'react';
import { ChatEventListener } from './hooks/useChat';

function App() {
  const [subtitles, setSubtitles] = useState('');
  return (
    <>
      <ChatEventListener />
      <Loader />
      <Leva  hidden/>
      <SubtitlesContext.Provider value={{ subtitles, setSubtitles }}>
        <UI  />
        <Canvas shadows camera={{ position: [0, 0, 1], fov: 30 }}>
          <Experience />
        </Canvas>
      </SubtitlesContext.Provider>
    </>
  );
}

export default App;
