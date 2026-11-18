import React from "react";
import { AbsoluteFill, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { EFFECT_COMPONENTS } from "./effects";
import { FPS, SCHEDULE } from "./timeline";

// Duração do vídeo já cortado (ffmpeg, etapa de cortes): ~72,5 s.
export const TOTAL_FRAMES = Math.round(72.5 * FPS);

const ZOOM_EVERY_S = 6;
const ZOOM_START_S = 1.5;
const ZOOM_DUR_S = 0.5;
const ZOOM_PEAK = 1.12;

const pulseAt = (t: number, centre: number, half: number) =>
  Math.max(0, 1 - Math.abs(t - centre) / half);

// Lê o frame local do Sequence e repassa ao efeito.
const Slot: React.FC<{ Comp: React.FC<{ f: number; d: number; w: number; h: number }>; d: number; w: number; h: number }> =
  ({ Comp, d, w, h }) => {
    const f = useCurrentFrame();
    return <Comp f={f} d={d} w={w} h={h} />;
  };

export const Edicao: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const t = frame / FPS;

  // Zoom periódico (batida) e flash em cada batida.
  let pulse = 0;
  for (let c = ZOOM_START_S; c < 80; c += ZOOM_EVERY_S) {
    pulse = Math.max(pulse, pulseAt(t, c, ZOOM_DUR_S / 2));
  }
  let scale = 1 + (ZOOM_PEAK - 1) * pulse;
  const flashOn = Array.from({ length: 14 }).some((_, i) => {
    const c = ZOOM_START_S + i * ZOOM_EVERY_S;
    return t >= c && t <= c + 0.12;
  });

  // Efeitos que mudam a camada base: Dolly zoom e Rack focus, nas suas janelas da linha do tempo.
  let blur = 0;
  for (const item of SCHEDULE) {
    const a = item.startS, b = item.startS + item.durS;
    if (item.name === "Dolly zoom" && t >= a && t <= b) {
      scale *= 1 + 0.18 * ((t - a) / (b - a));
    }
    if (item.name === "Rack focus" && t >= a && t <= b) {
      blur = interpolate(t, [a, (a + b) / 2, b], [0, 6, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    }
  }

  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      <AbsoluteFill style={{ transform: `scale(${scale})`, filter: blur ? `blur(${blur}px)` : undefined }}>
        <OffthreadVideo src={staticFile("base.mp4")} />
      </AbsoluteFill>
      {flashOn && <AbsoluteFill style={{ background: "#fff", opacity: 0.18 }} />}

      {SCHEDULE.map((item) => {
        const Comp = EFFECT_COMPONENTS[item.name];
        if (!Comp) return null;
        return (
          <Sequence key={item.name} from={Math.round(item.startS * FPS)} durationInFrames={Math.round(item.durS * FPS)}>
            <Slot Comp={Comp} d={Math.round(item.durS * FPS)} w={width} h={height} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
