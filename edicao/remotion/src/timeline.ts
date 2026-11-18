// Efeitos da referência, na ordem do painel. Tempos em segundos do vídeo já cortado (~72,6 s).
export type EffectName =
  | "Live cursor" | "Clone row" | "Day dial" | "Predict keys" | "Orbit ring"
  | "Code body" | "Post wall" | "Letter dive" | "Comment drop" | "Layer explode"
  | "Sketch words" | "Blade slice" | "Head stack" | "Rack focus" | "Bank note"
  | "Voice note" | "Impact frame" | "Dolly zoom" | "Press font" | "Paper tear" | "Blow away";

export const EFFECT_ORDER: EffectName[] = [
  "Live cursor", "Clone row", "Day dial", "Predict keys", "Orbit ring",
  "Code body", "Post wall", "Letter dive", "Comment drop", "Layer explode",
  "Sketch words", "Blade slice", "Head stack", "Rack focus", "Bank note",
  "Voice note", "Impact frame", "Dolly zoom", "Press font", "Paper tear", "Blow away",
];

export const FPS = 30;
export const DURATION_S = 2.6;
export const START_S = 1.0;
export const STEP_S = 3.3;

export const SCHEDULE = EFFECT_ORDER.map((name, i) => ({
  name,
  startS: START_S + i * STEP_S,
  durS: DURATION_S,
}));
