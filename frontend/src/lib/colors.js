// Tiny deterministic color hash (used as fallback)
export function hashColor(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = (h << 5) - h + str.charCodeAt(i);
    h |= 0;
  }
  const r = (h >> 16) & 0xff;
  const g = (h >> 8) & 0xff;
  const b = h & 0xff;
  return `#${[r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

export const EXP_COLORS = {
  entry: "#4A90E2",
  mid: "#F5A623",
  senior: "#D0021B",
};

/**
 * Bright lo-fi palette used in the Applicants City green scene.
 * Each color is high-luminance so no tower ever reads as solid black
 * against the dark forest-green ground/sky.
 */
export const APPLICANT_CITY_COLORS = {
  entry: "#5BE3A3",  // bright mint
  mid: "#F5D547",    // amber/yellow
  senior: "#FF7A59", // warm orange-red
};
