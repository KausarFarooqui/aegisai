import * as THREE from "three";
import type { GraphNodeType } from "@/api/types";

/**
 * Generates a radial-gradient glow texture on a canvas, used as a Sprite
 * material. Sprites always face the camera regardless of orbit angle,
 * which is exactly the "point of light in space" look a constellation
 * needs — a flat 3D star mesh would look wrong from most angles, but a
 * glowing sprite reads as a star from every angle, same as real starlight.
 */
function createGlowTexture(hexColor: string): THREE.Texture {
  const size = 128;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d")!;

  const gradient = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  gradient.addColorStop(0, hexColor);
  gradient.addColorStop(0.2, hexColor);
  gradient.addColorStop(1, "rgba(0,0,0,0)");

  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, size, size);

  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;
  return texture;
}

// Cache textures/materials per color — created once, reused for every node
// of that type, instead of regenerating a canvas per node.
const glowTextureCache = new Map<string, THREE.Texture>();
function getGlowTexture(hexColor: string): THREE.Texture {
  if (!glowTextureCache.has(hexColor)) {
    glowTextureCache.set(hexColor, createGlowTexture(hexColor));
  }
  return glowTextureCache.get(hexColor)!;
}

const NODE_COLOR: Record<GraphNodeType, string> = {
  process: "#ffffff",
  activity: "#8ea0b8",
  role: "#6f8fd6",
  skill: "#4fb3a9",
  ai_opportunity: "#f5cf6b",
};

const NODE_SIZE: Record<GraphNodeType, number> = {
  process: 7,
  activity: 3.5,
  role: 4,
  skill: 4,
  ai_opportunity: 10,
};

/**
 * Builds the Three.js object for one node, keyed by its AEGISAI graph type.
 * AI opportunities are true glow sprites (the "stars"); everything else is
 * a small unlit sphere — bright flat color against the dark canvas reads
 * as "glowing" without depending on scene lighting being configured a
 * particular way, which matters since this couldn't be visually verified
 * in the environment it was built in.
 */
export function createNodeObject(nodeType: GraphNodeType, isFocused: boolean): THREE.Object3D {
  const color = NODE_COLOR[nodeType];

  if (nodeType === "ai_opportunity") {
    const sprite = new THREE.Sprite(
      new THREE.SpriteMaterial({
        map: getGlowTexture(color),
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      }),
    );
    const scale = isFocused ? NODE_SIZE.ai_opportunity * 2.2 : NODE_SIZE.ai_opportunity * 1.6;
    sprite.scale.set(scale, scale, 1);
    return sprite;
  }

  const geometry = new THREE.SphereGeometry(isFocused ? NODE_SIZE[nodeType] * 1.6 : NODE_SIZE[nodeType], 12, 12);
  const material = new THREE.MeshBasicMaterial({ color });
  return new THREE.Mesh(geometry, material);
}
