import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { EffectName } from "./timeline";

const ORANGE = "#FF8C2A";
const CREAM = "#F5F0E6";
const INK = "#111111";

type P = { f: number; d: number; w: number; h: number };

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// Live cursor: seta anda até um ponto e clica.
const LiveCursor: React.FC<P> = ({ f, d, w, h }) => {
  const x = interpolate(f, [0, d * 0.7], [w * 0.2, w * 0.6], clamp);
  const y = interpolate(f, [0, d * 0.7], [h * 0.8, h * 0.4], clamp);
  const click = interpolate(f, [d * 0.7, d * 0.85], [0, 1], clamp);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: x - 30 * click, top: y - 30 * click, width: 60 * click, height: 60 * click,
        borderRadius: "50%", border: `3px solid ${ORANGE}`, opacity: 1 - click }} />
      <svg style={{ position: "absolute", left: x, top: y }} width="36" height="44" viewBox="0 0 36 44">
        <path d="M2 2 L2 34 L11 26 L17 40 L23 37 L17 24 L30 24 Z" fill="#fff" stroke={INK} strokeWidth="2" />
      </svg>
    </AbsoluteFill>
  );
};

// Clone row: a linha se duplica para baixo.
const CloneRow: React.FC<P> = ({ f, d, w, h }) => (
  <AbsoluteFill>
    {[0, 1, 2].map((i) => {
      const s = spring({ frame: f - i * 8, fps: 30, config: { damping: 200 } });
      return (
        <div key={i} style={{ position: "absolute", left: w * 0.1, top: h * 0.3 + i * 60, width: w * 0.8, height: 48,
          background: i === 0 ? CREAM : "rgba(245,240,230,0.7)", borderRadius: 10, opacity: s,
          transform: `translateX(${(1 - s) * -40}px)`, display: "flex", alignItems: "center", padding: "0 16px",
          color: INK, fontFamily: "sans-serif", fontWeight: 700 }}>
          {i === 0 ? "linha original" : "clone"}
        </div>
      );
    })}
  </AbsoluteFill>
);

// Day dial: mostrador girando.
const DayDial: React.FC<P> = ({ f, d, w, h }) => {
  const rot = interpolate(f, [0, d], [0, 540], clamp);
  const s = Math.min(w, h) * 0.45;
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <div style={{ width: s, height: s, borderRadius: "50%", border: `6px solid ${ORANGE}`, background: "rgba(17,17,17,0.6)",
        transform: `rotate(${rot}deg)`, position: "relative" }}>
        <div style={{ position: "absolute", left: "50%", top: 8, width: 6, height: s / 2 - 16, background: CREAM,
          transform: "translateX(-50%)", borderRadius: 3 }} />
      </div>
    </AbsoluteFill>
  );
};

// Predict keys: teclas acendem em sequência com a sugestão.
const PredictKeys: React.FC<P> = ({ f, d, w, h }) => {
  const keys = ["A", "S", "D", "F", "G"];
  const active = Math.floor((f / d) * keys.length);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: w * 0.1, bottom: h * 0.14, display: "flex", gap: 10 }}>
        {keys.map((k, i) => (
          <div key={k} style={{ width: 52, height: 52, borderRadius: 10, display: "flex", alignItems: "center",
            justifyContent: "center", fontFamily: "sans-serif", fontWeight: 800,
            background: i === active ? ORANGE : CREAM, color: INK }}>{k}</div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

// Orbit ring: um ponto orbita um anel.
const OrbitRing: React.FC<P> = ({ f, d, w, h }) => {
  const r = Math.min(w, h) * 0.3;
  const ang = interpolate(f, [0, d], [0, 360 * 1.5], clamp) * (Math.PI / 180);
  const cx = w / 2, cy = h * 0.42;
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: cx - r, top: cy - r, width: 2 * r, height: 2 * r, borderRadius: "50%",
        border: `2px solid ${CREAM}` }} />
      <div style={{ position: "absolute", left: cx + Math.cos(ang) * r - 9, top: cy + Math.sin(ang) * r - 9, width: 18,
        height: 18, borderRadius: "50%", background: ORANGE }} />
    </AbsoluteFill>
  );
};

// Code body: trecho de código digitado.
const CodeBody: React.FC<P> = ({ f, d, w, h }) => {
  const lines = ["const efeito = aplicar();", "video.zoom(1.12);", "legenda.render(texto);", "exportar(9x16);"];
  const chars = Math.floor(interpolate(f, [0, d * 0.8], [0, lines.join("\n").length], clamp));
  const text = lines.join("\n").slice(0, chars);
  return (
    <AbsoluteFill>
      <pre style={{ position: "absolute", left: w * 0.08, top: h * 0.2, right: w * 0.08, margin: 0, padding: 16,
        background: "rgba(17,17,17,0.85)", color: CREAM, borderRadius: 12, fontSize: 18, fontFamily: "monospace",
        whiteSpace: "pre-wrap" }}>{text}</pre>
    </AbsoluteFill>
  );
};

// Post wall: grade de posts que surgem.
const PostWall: React.FC<P> = ({ f, w, h }) => (
  <AbsoluteFill>
    {Array.from({ length: 9 }).map((_, i) => {
      const s = spring({ frame: f - i * 3, fps: 30, config: { damping: 12 } });
      const col = i % 3, row = Math.floor(i / 3);
      return (
        <div key={i} style={{ position: "absolute", left: w * 0.1 + col * (w * 0.27), top: h * 0.25 + row * (w * 0.27),
          width: w * 0.24, height: w * 0.24, borderRadius: 10, background: i % 2 ? ORANGE : CREAM,
          transform: `scale(${s})` }} />
      );
    })}
  </AbsoluteFill>
);

// Letter dive: letras entram em profundidade.
const LetterDive: React.FC<P> = ({ f, w, h }) => {
  const word = "EFEITO";
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <div style={{ display: "flex", gap: 4 }}>
        {word.split("").map((c, i) => {
          const s = spring({ frame: f - i * 4, fps: 30, config: { damping: 200 } });
          return (
            <span key={i} style={{ fontSize: w * 0.14, fontWeight: 900, color: i % 2 ? ORANGE : CREAM,
              fontFamily: "sans-serif", transform: `scale(${2.5 - 1.5 * s})`, opacity: s, display: "inline-block" }}>{c}</span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// Comment drop: balões caem do topo.
const CommentDrop: React.FC<P> = ({ f, w, h }) => (
  <AbsoluteFill>
    {["Que legal!", "Como faço?", "Top demais"].map((t, i) => {
      const s = spring({ frame: f - i * 10, fps: 30, config: { damping: 10 } });
      return (
        <div key={i} style={{ position: "absolute", left: w * 0.12 + i * 20, top: h * 0.08 + i * 70 * s,
          padding: "10px 16px", borderRadius: 18, background: CREAM, color: INK, fontFamily: "sans-serif",
          fontWeight: 600, opacity: s }}>{t}</div>
      );
    })}
  </AbsoluteFill>
);

// Layer explode: camadas se afastam.
const LayerExplode: React.FC<P> = ({ f, d, w, h }) => {
  const off = interpolate(f, [0, d * 0.6], [0, 60], clamp);
  return (
    <AbsoluteFill>
      {[-1, 0, 1].map((k) => (
        <div key={k} style={{ position: "absolute", left: w * 0.2, top: h * 0.3 + k * off, width: w * 0.6, height: 120,
          borderRadius: 14, border: `2px solid ${ORANGE}`, background: "rgba(245,240,230,0.12)" }} />
      ))}
    </AbsoluteFill>
  );
};

// Sketch words: palavras aparecem com traço sublinhado.
const SketchWords: React.FC<P> = ({ f, d, w, h }) => {
  const words = ["ideia", "efeito", "pronto"];
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 12 }}>
      {words.map((t, i) => {
        const on = f > (d / words.length) * i;
        return (
          <div key={t} style={{ color: CREAM, fontFamily: "sans-serif", fontSize: w * 0.09, fontWeight: 800,
            opacity: on ? 1 : 0, position: "relative" }}>
            {t}
            <div style={{ height: 4, background: ORANGE, width: on ? "100%" : "0%", transition: "width 0.2s" }} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// Blade slice: lâmina diagonal varre a tela.
const BladeSlice: React.FC<P> = ({ f, d, w, h }) => {
  const x = interpolate(f, [0, d], [-w, w * 1.5], clamp);
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <div style={{ position: "absolute", left: x, top: -h * 0.2, width: 14, height: h * 1.4, background: ORANGE,
        transform: "rotate(18deg)" }} />
    </AbsoluteFill>
  );
};

// Head stack: barras empilhadas (camadas da cabeça).
const HeadStack: React.FC<P> = ({ f, w, h }) => (
  <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-start", paddingTop: h * 0.12, gap: 8 }}>
    {[0.8, 0.6, 0.4].map((k, i) => {
      const s = spring({ frame: f - i * 6, fps: 30, config: { damping: 200 } });
      return <div key={i} style={{ width: w * k * s, height: 22, borderRadius: 8, background: i === 0 ? ORANGE : CREAM }} />;
    })}
  </AbsoluteFill>
);

// Bank note: cédula com "R$" desliza.
const BankNote: React.FC<P> = ({ f, d, w, h }) => {
  const x = interpolate(f, [0, d * 0.4], [w, w * 0.12], clamp);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: x, top: h * 0.6, width: w * 0.7, height: w * 0.36, borderRadius: 10,
        background: "#2E7D4F", color: CREAM, display: "flex", alignItems: "center", justifyContent: "center",
        fontFamily: "sans-serif", fontWeight: 900, fontSize: w * 0.12, transform: "rotate(-6deg)" }}>R$ 197</div>
    </AbsoluteFill>
  );
};

// Voice note: barras de voz em laranja.
const VoiceNote: React.FC<P> = ({ f, w, h }) => (
  <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: h * 0.08 }}>
    <div style={{ display: "flex", alignItems: "center", gap: 4, height: 80 }}>
      {Array.from({ length: 28 }).map((_, i) => {
        const amp = 0.5 + 0.5 * Math.sin((f + i * 4) / 3);
        return <div key={i} style={{ width: 5, height: 10 + amp * 70, background: ORANGE, borderRadius: 3 }} />;
      })}
    </div>
  </AbsoluteFill>
);

// Impact frame: flash branco e linhas radiais.
const ImpactFrame: React.FC<P> = ({ f, w, h }) => {
  const flash = interpolate(f, [0, 4, 10], [0.9, 0.6, 0], clamp);
  const scale = interpolate(f, [0, 12], [0.6, 1.2], clamp);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: "#fff", opacity: flash }} />
      <svg style={{ position: "absolute", left: 0, top: 0 }} width={w} height={h}>
        {Array.from({ length: 24 }).map((_, i) => {
          const a = (i / 24) * Math.PI * 2;
          const r1 = Math.min(w, h) * 0.2 * scale, r2 = Math.max(w, h) * 0.9 * scale;
          return <line key={i} x1={w / 2 + Math.cos(a) * r1} y1={h / 2 + Math.sin(a) * r1}
            x2={w / 2 + Math.cos(a) * r2} y2={h / 2 + Math.sin(a) * r2} stroke={INK} strokeWidth={3} opacity={1 - f / 14} />;
        })}
      </svg>
    </AbsoluteFill>
  );
};

// Press font: texto pula ao entrar.
const PressFont: React.FC<P> = ({ f, w, h }) => {
  const s = spring({ frame: f, fps: 30, config: { damping: 8 } });
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <div style={{ fontSize: w * 0.16, fontWeight: 900, color: ORANGE, fontFamily: "sans-serif",
        transform: `scale(${0.4 + 0.6 * s})` }}>PRESS</div>
    </AbsoluteFill>
  );
};

// Paper tear: papel branco rasga revelando.
const PaperTear: React.FC<P> = ({ f, d, w, h }) => {
  const x = interpolate(f, [0, d * 0.6], [0, w], clamp);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 0, top: h * 0.45, width: w, height: h * 0.1, background: CREAM,
        clipPath: `polygon(0 0, ${x}px 0, ${x + 12}px 50%, ${x}px 100%, 0 100%)` }} />
    </AbsoluteFill>
  );
};

// Blow away: cartão sai voando para cima e some.
const BlowAway: React.FC<P> = ({ f, d, w, h }) => {
  const x = interpolate(f, [0, d], [0, w * 0.8], clamp);
  const y = interpolate(f, [0, d], [0, -h * 0.4], clamp);
  const op = interpolate(f, [d * 0.6, d], [1, 0], clamp);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <div style={{ padding: "14px 22px", borderRadius: 14, background: CREAM, color: INK, fontFamily: "sans-serif",
        fontWeight: 800, fontSize: w * 0.07, transform: `translate(${x}px, ${y}px) rotate(${x / 20}deg)`, opacity: op }}>
        sopro
      </div>
    </AbsoluteFill>
  );
};

// Efeitos que mudam a camada base (Rack focus, Dolly zoom) ficam em Edicao.tsx.
export const EFFECT_COMPONENTS: Record<EffectName, React.FC<P> | null> = {
  "Live cursor": LiveCursor, "Clone row": CloneRow, "Day dial": DayDial, "Predict keys": PredictKeys,
  "Orbit ring": OrbitRing, "Code body": CodeBody, "Post wall": PostWall, "Letter dive": LetterDive,
  "Comment drop": CommentDrop, "Layer explode": LayerExplode, "Sketch words": SketchWords,
  "Blade slice": BladeSlice, "Head stack": HeadStack, "Rack focus": null, "Bank note": BankNote,
  "Voice note": VoiceNote, "Impact frame": ImpactFrame, "Dolly zoom": null, "Press font": PressFont,
  "Paper tear": PaperTear, "Blow away": BlowAway,
};

export { AbsoluteFill, useCurrentFrame, useVideoConfig };
