import { Loader } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Leva } from "leva";
import { Experience } from "./components/Experience";
import { UI } from "./components/UI";
import SubtitlesContext from './components/subtitles';
import React, { useState } from 'react';
import { ChatEventListener } from './hooks/useChat';
import PermissionHandler from "./components/PermissionHandler";

function App() {
  const [subtitles, setSubtitles] = useState('');
  const [permissionsGranted, setPermissionsGranted] = useState(false);

  const handlePermissionsGranted = () => {
    setPermissionsGranted(true);
  };

  return (
    <>
        <>
          <ChatEventListener />
          <Loader />
          
          <SubtitlesContext.Provider value={{ subtitles, setSubtitles }}>
            <Leva hidden />
            <UI/>
            <Canvas shadows camera={{ position: [0, 0, 1], fov: 30 }}>
              <Experience />
            </Canvas>
          </SubtitlesContext.Provider>
        </>
    </>
  );
}

export default App;