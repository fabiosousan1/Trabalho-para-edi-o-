import React from "react";
import { Composition } from "remotion";
import { Edicao, TOTAL_FRAMES } from "./Edicao";

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Edicao"
    component={Edicao}
    durationInFrames={TOTAL_FRAMES}
    fps={30}
    width={478}
    height={850}
  />
);
