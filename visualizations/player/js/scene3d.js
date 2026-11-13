// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The player's 3-D environment (owner, 2026-10-27; RULES.md §2.10), shared by every 3-D world: the apparatus (plates
// with apertures, beams, targets, spheres, points), computed fields (a volume by ray marching, vector glyphs), computed
// paths revealed as the run's time reaches them, gyroscope triads, marks, arrows, a moving body, and up to three slice
// planes placed in the scene at any orientation, moved and turned with a gizmo or by parameters. Every element can be
// switched off on its own. Drawing only: what the planes show is computed by the run (view command "plane").
// Coordinates: physics (x, y, z) with z the depth; on screen z runs to the right, y up (three.js X = z, Y = y, Z = -x).
//
// The rendering contract (review UX-3d, 2026-11-04; RULES.md §2.10):
// * depth: everything opaque (solids, lines, slice planes) writes depth; the volume's march ends at the depth of the
//   opaque scene (a depth pass into a texture) and is split at the nearest translucent surface, so that the cloud in
//   front of an object covers it and the cloud behind it is hidden; translucent surfaces show their nearest layer
//   (a depth-only twin drawn just before each) and are drawn far to near by their nearest point;
// * solids are lit by a light that moves with the camera (spheres as exact sphere impostors, arrows as a lit shaft and
//   cone, lines a few pixels wide, particles as round shaded points); data surfaces (slices, panels, targets) are not
//   lit: their colour is the value;
// * views follow the scene's "up" (a frame U up, R right, F toward the viewer), 2-D worlds open from above;
// * the camera is fitted to the box's corners after the layout settles and again on every resize or box change until the
//   experimenter moves it; after that nothing but the experimenter moves it.
import * as THREE from "three";
import { OrbitControls } from "/static/vendor/three-0.185.1/OrbitControls.js";
import { TransformControls } from "/static/vendor/three-0.185.1/TransformControls.js";
import { t } from "./i18n.js";
import { el, fill, num } from "./ui.js";

export const PLANE_COLORS = { 1: "#ff8a1f", 2: "#22b8ff", 3: "#d65cff" };
export const P2T = (p) => new THREE.Vector3(p[2], p[1], -p[0]);
export const T2P = (v) => [-v.z, v.y, v.x];

// one colour map for the whole environment (a dark-to-light sequential map; values 0..1)
export const LUT = (() => {
  const stops = [[0, 0, 4], [28, 16, 68], [79, 18, 123], [129, 37, 129], [181, 54, 122], [229, 80, 100],
                 [251, 135, 97], [254, 194, 135], [252, 253, 191]];
  const out = new Uint8ClampedArray(256 * 3);
  for (let i = 0; i < 256; i++) {
    const f = i / 255 * (stops.length - 1), k = Math.min(Math.floor(f), stops.length - 2), w = f - k;
    for (let c = 0; c < 3; c++) out[3 * i + c] = stops[k][c] * (1 - w) + stops[k + 1][c] * w;
  }
  return out;
})();

// value (relative to the peak) -> 0..1 on the chosen scale; the log scale starts at `floor`
export function transfer(v, scale, floor = 1e-6) {
  if (!(v >= 0)) return NaN;
  if (scale === "log") return Math.max(0, 1 - Math.log10(Math.max(v, 1e-30)) / Math.log10(floor));
  if (scale === "sqrt") return Math.sqrt(v);
  return Math.min(1, v);
}

export const SCALES = [["sqrt", t("amplitude")], ["lin", t("intensity")], ["log", t("logarithm")]];

// the cut of a plane (origin o, normal n, in-plane axes u, v) by the box: polygon in (s, t), sorted around its centre
export function planeBox(o, n, u, v, box) {
  const [lo, hi] = box, C = [];
  for (const x of [lo[0], hi[0]]) for (const y of [lo[1], hi[1]]) for (const z of [lo[2], hi[2]]) C.push([x, y, z]);
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  // corners on the plane once each, then strict crossings inside the edges (as lfphys.core.geometry.plane_cut)
  const d = C.map((c) => dot(sub(c, o), n)), scale = Math.max(...[0, 1, 2].map((i) => hi[i] - lo[i]));
  const on = d.map((x) => Math.abs(x) <= 1e-12 * scale);
  const pts = C.filter((c, i) => on[i]);
  for (let a = 0; a < 8; a++) for (let b = a + 1; b < 8; b++) {
    if ([0, 1, 2].filter((i) => C[a][i] !== C[b][i]).length !== 1 || on[a] || on[b]) continue;
    if (d[a] * d[b] < 0) { const f = d[a] / (d[a] - d[b]); pts.push([0, 1, 2].map((i) => C[a][i] + (C[b][i] - C[a][i]) * f)); }
  }
  const st = pts.map((p) => [dot(sub(p, o), u), dot(sub(p, o), v)]);
  if (st.length < 3) return [];
  const cs = st.reduce((a, p) => [a[0] + p[0] / st.length, a[1] + p[1] / st.length], [0, 0]);
  return st.sort((a, b) => Math.atan2(a[1] - cs[1], a[0] - cs[0]) - Math.atan2(b[1] - cs[1], b[0] - cs[0]));
}

// the in-plane axes the engine uses (lfphys.core.geometry.Plane.horizontal): u horizontal, v towards the depth
export function horizontalAxes(n) {
  const L = Math.hypot(...n); n = n.map((c) => c / L);
  let h = [-n[1], n[0], 0];  // z x n
  if (Math.hypot(h[0], h[1]) < 1e-12) h = [1, 0, 0];
  const hl = Math.hypot(...h); h = h.map((c) => c / hl);
  let v = [n[1] * h[2] - n[2] * h[1], n[2] * h[0] - n[0] * h[2], n[0] * h[1] - n[1] * h[0]];
  if (v[2] < -1e-12 || (Math.abs(v[2]) <= 1e-12 && v[1] < 0 && Math.abs(n[2]) < 1 - 1e-12)) { h = h.map((c) => -c); v = v.map((c) => -c); }
  return { n, u: h, v };
}

export function normalFromAngles(thetaDeg, phiDeg) {
  const tt = thetaDeg * Math.PI / 180, p = phiDeg * Math.PI / 180;
  return [Math.sin(tt) * Math.cos(p), Math.sin(tt) * Math.sin(p), Math.cos(tt)];
}
export function anglesOfNormal(n) {
  const L = Math.hypot(...n);
  const theta = Math.acos(Math.max(-1, Math.min(1, n[2] / L))) * 180 / Math.PI;
  let phi = Math.atan2(n[1], n[0]) * 180 / Math.PI;
  if (phi < 0) phi += 360;
  return { theta, phi };
}

// --- small vector helpers (physics arrays) ---------------------------------------------------------------------------
const vdot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const vcross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const vunit = (a) => { const L = Math.hypot(...a) || 1; return a.map((c) => c / L); };
const vlin = (...terms) => [0, 1, 2].map((i) => terms.reduce((s, [k, v]) => s + k * v[i], 0));

// the scene's frame from its "up": U up, R to the right on screen, F toward the viewer of the default views (for y up:
// R = z, the depth that runs to the right, F = -x; for z up: R = x, F = -y) (review UX-3d A3, A14)
export function axesOfUp(up) {
  const U = vunit(up);
  let R = Math.abs(U[2]) > 0.9 ? [1, 0, 0] : [0, 0, 1];
  R = vunit(vlin([1, R], [-vdot(R, U), U]));
  return { U, R, F: vcross(R, U) };
}

function lutTexture() {
  const d = new Uint8Array(256 * 4);
  for (let i = 0; i < 256; i++) { d[4 * i] = LUT[3 * i]; d[4 * i + 1] = LUT[3 * i + 1]; d[4 * i + 2] = LUT[3 * i + 2]; d[4 * i + 3] = 255; }
  const tt = new THREE.DataTexture(d, 256, 1, THREE.RGBAFormat);
  tt.magFilter = THREE.LinearFilter; tt.minFilter = THREE.LinearFilter; tt.needsUpdate = true;
  return tt;
}

// free the GPU memory of an object tree (geometries, materials, their textures): removing an object from the scene does
// not; the player rebuilds the scene from the record whenever the history goes back (STATUS V29, V32). Geometries
// shared by many objects (arrow parts, quads) are kept.
function disposeTree(obj) {
  if (!obj) return;
  obj.traverse((o) => {
    if (o.geometry && !o.geometry.userData.shared) o.geometry.dispose();
    const mats = Array.isArray(o.material) ? o.material : o.material ? [o.material] : [];
    for (const m of mats) {
      if (m.userData && m.userData.shared) continue;
      for (const v of Object.values(m)) if (v && v.isTexture && !v.userData.shared) v.dispose();
      if (m.uniforms) for (const u of Object.values(m.uniforms)) if (u && u.value && u.value.isTexture && !u.value.userData.shared) u.value.dispose();
      m.dispose();
    }
    if (o.isInstancedMesh) o.dispose();
  });
  if (obj.userData) for (const v of Object.values(obj.userData)) if (v && v.isTexture && !v.userData.shared) v.dispose();
}

// --- labels: a fixed size in pixels, hidden behind solids (review UX-3d A9) ------------------------------------------
// `px` is the label's height in CSS pixels; `center` the anchor in the label ([0, 1]²; e.g. [0.5, 1.6]: centred, below
// the point); the scale is set from the canvas's height by the scene (updateLabelScale)
function labelSprite(text, color = "#c8d0da", px = 16, center = [0.5, 0.5], onTop = false) {
  text = t(text);  // a msgid or a text the world sent (T)
  const c = document.createElement("canvas"), g = c.getContext("2d");
  g.font = "28px system-ui"; const w = Math.ceil(g.measureText(text).width) + 12;
  c.width = w; c.height = 40;
  g.font = "28px system-ui"; g.fillStyle = color; g.textBaseline = "middle"; g.fillText(text, 6, 20);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, depthTest: !onTop, depthWrite: false, transparent: true, sizeAttenuation: false }));
  s.center.set(center[0], center[1]);
  s.userData.label = { px, aspect: w / 40 };
  s.renderOrder = 10;
  return s;
}

// --- shaders -------------------------------------------------------------------------------------------------------------
// a light that moves with the camera: from the viewer, a little up and to the left (view space)
const LIGHT_DIR = "normalize(vec3(-0.35, 0.45, 1.0))";
// lit solids and surfaces (vertex or instance colours, instancing optional): colour * (ambient + diffuse * N.L) + specular
const LIT_VERT = `
uniform vec3 uColor;
varying vec3 vN; varying vec3 vCol; varying vec3 vView;
void main() {
  vec3 col = uColor;
#ifdef USE_COLOR
  col *= color.rgb;
#endif
#ifdef USE_INSTANCING_COLOR
  col *= instanceColor;
#endif
  vCol = col;
  vec4 p = vec4(position, 1.0); vec3 n = normal;
#ifdef USE_INSTANCING
  p = instanceMatrix * p; n = transpose(inverse(mat3(instanceMatrix))) * n;
#endif
  vec4 mv = modelViewMatrix * p;
  vView = mv.xyz; vN = normalMatrix * n;
  gl_Position = projectionMatrix * mv;
}`;
const LIT_FRAG = `
uniform float uOpacity; uniform vec3 uShade;
varying vec3 vN; varying vec3 vCol; varying vec3 vView;
void main() {
  vec3 n = normalize(vN);
  if (!gl_FrontFacing) n = -n;
  vec3 L = ${LIGHT_DIR}, V = normalize(-vView);
  float dif = max(dot(n, L), 0.0), spec = pow(max(dot(n, normalize(L + V)), 0.0), 48.0);
  gl_FragColor = vec4(vCol * (uShade.x + uShade.y * dif) + uShade.z * spec, uOpacity);
  #include <colorspace_fragment>
}`;
const DEPTH_ONLY_FRAG = `void main() { gl_FragColor = vec4(0.0); }`;
// shading presets: [ambient, diffuse, specular]; a value surface keeps its colour where it faces the viewer
const SOLID = [0.32, 0.78, 0.22], VALUE_SURFACE = [0.6, 0.45, 0.0];
function litMaterial({ color = 0xffffff, vertexColors = false, opacity = 1, side = THREE.FrontSide, shade = SOLID } = {}) {
  return new THREE.ShaderMaterial({
    vertexShader: LIT_VERT, fragmentShader: LIT_FRAG, vertexColors, side,
    transparent: opacity < 1, depthWrite: opacity >= 1,
    uniforms: { uColor: { value: new THREE.Color(color) }, uOpacity: { value: opacity }, uShade: { value: new THREE.Vector3(...shade) } } });
}

// spheres as exact impostors (one quad per sphere, instanced): the quad covers the sphere's silhouette as seen from the
// eye, the fragment intersects the eye ray with the sphere, shades it and writes its true depth (no tessellation: round
// at any zoom; spheres that intersect, intersect correctly)
const SPH_VERT = `
uniform vec3 uColor;
varying vec3 vCenter; varying float vRadius; varying vec3 vPos; varying vec3 vCol;
void main() {
  vec3 col = uColor;
#ifdef USE_INSTANCING_COLOR
  col *= instanceColor;
#endif
  vCol = col;
  vec4 c = vec4(0.0, 0.0, 0.0, 1.0); float r = 1.0;
#ifdef USE_INSTANCING
  c = instanceMatrix * c; r = length(instanceMatrix[0].xyz);
#endif
  vec4 cv = modelViewMatrix * c;
  r *= length(modelViewMatrix[0].xyz);
  float dist = length(cv.xyz);
  vec3 toC = cv.xyz / max(dist, 1e-30);
  vec3 up = abs(toC.y) < 0.99 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0);
  vec3 ex = normalize(cross(toC, up)), ey = cross(ex, toC);  // the quad faces the eye (front-facing)
  vec3 q;
  if (dist > r * 1.0001) {
    float sa = r / dist, ta = sa / sqrt(1.0 - sa * sa), dq = dist - r;
    q = toC * dq + (ex * position.x + ey * position.y) * dq * ta * 1.05;
  } else {
    q = cv.xyz + (ex * position.x + ey * position.y) * r * 2.0;
  }
  vCenter = cv.xyz; vRadius = r; vPos = q;
  gl_Position = projectionMatrix * vec4(q, 1.0);
}`;
const SPH_FRAG = `
uniform vec3 uShade; uniform mat4 projectionMatrix;
varying vec3 vCenter; varying float vRadius; varying vec3 vPos; varying vec3 vCol;
void main() {
  vec3 rd = normalize(vPos);
  float b = dot(rd, vCenter), c = dot(vCenter, vCenter) - vRadius * vRadius, h = b * b - c;
  if (h < 0.0) discard;
  float t = b - sqrt(h);
  if (t <= 0.0) t = b + sqrt(h);
  vec3 p = rd * t, n = normalize(p - vCenter);
  vec4 clip = projectionMatrix * vec4(p, 1.0);
  gl_FragDepth = 0.5 * clip.z / clip.w + 0.5;
  vec3 L = ${LIGHT_DIR}, V = -rd;
  float dif = max(dot(n, L), 0.0), spec = pow(max(dot(n, normalize(L + V)), 0.0), 48.0);
  gl_FragColor = vec4(vCol * (uShade.x + uShade.y * dif) + uShade.z * spec, 1.0);
  #include <colorspace_fragment>
}`;

// lines with a width in pixels (a quad per segment, its four vertices carrying both ends, with round ends): a segment
// from iA to iB, `corner` (x: which end, y: which side) places the vertex; colours per segment end (PER_COLOR) or one
// colour; optional dimming of the far half of a sphere's lines (SPHERE_DIM: the wire globe's front and back are told
// apart). Written for this player from the usual screen-space construction. Not instanced: software GL draws thousands
// of instances many times slower than the same quads as plain vertices (v15's rays: 50 ms against 1.6 ms).
const WIDE_VERT = `
uniform vec2 uRes; uniform float uWidth; uniform vec3 uColor; uniform vec4 uSphere;
attribute vec3 iA; attribute vec3 iB; attribute vec3 corner;
#ifdef PER_COLOR
attribute vec3 iCA; attribute vec3 iCB;
#endif
varying vec3 vCol; varying vec3 vUvw; varying float vLen; varying float vDim;
void main() {
  vec4 a = modelViewMatrix * vec4(iA, 1.0), b = modelViewMatrix * vec4(iB, 1.0);
  float nearZ = -(projectionMatrix[3][2] / (projectionMatrix[2][2] - 1.0)) * 1.0001;  // the near plane's view z
  if (a.z > nearZ && b.z > nearZ) { gl_Position = vec4(0.0, 0.0, 2.0, 1.0); vCol = vec3(0.0); vUvw = vec3(0.0); vLen = 0.0; vDim = 1.0; return; }
  if (a.z > nearZ) a = mix(a, b, (nearZ - a.z) / (b.z - a.z));
  if (b.z > nearZ) b = mix(b, a, (nearZ - b.z) / (a.z - b.z));
  vec4 ca = projectionMatrix * a, cb = projectionMatrix * b;
  vec2 sa = ca.xy / ca.w * 0.5 * uRes, sb = cb.xy / cb.w * 0.5 * uRes;
  vec2 dir = sb - sa; float L = length(dir);
  dir = L > 1e-6 ? dir / L : vec2(1.0, 0.0);
  vec2 nrm = vec2(-dir.y, dir.x);
  float hw = 0.5 * uWidth;
  bool atB = corner.x > 0.5;
  vec4 c = atB ? cb : ca;
  vec2 off = nrm * corner.y * hw + dir * (atB ? hw : -hw);
  c.xy += off / (0.5 * uRes) * c.w;
  gl_Position = c;
  vUvw = vec3(atB ? L + hw : -hw, corner.y * hw, 1.0) * c.w;
  vLen = L;
#ifdef PER_COLOR
  vCol = atB ? iCB : iCA;
#else
  vCol = uColor;
#endif
  vDim = 1.0;
#ifdef SPHERE_DIM
  vec3 pw = (modelMatrix * vec4(atB ? iB : iA, 1.0)).xyz;
  vec3 nrmS = normalize(pw - uSphere.xyz), toEye = normalize(cameraPosition - pw);
  vDim = dot(nrmS, toEye) >= 0.0 ? 1.0 : 0.28;
#endif
}`;
const WIDE_FRAG = `
uniform vec2 uRes; uniform float uWidth; uniform float uOpacity;
varying vec3 vCol; varying vec3 vUvw; varying float vLen; varying float vDim;
void main() {
  vec2 uv = vUvw.xy / vUvw.z;
  float hw = 0.5 * uWidth;
  float d = uv.x < 0.0 ? length(uv) : (uv.x > vLen ? length(vec2(uv.x - vLen, uv.y)) : abs(uv.y));
  if (d > hw + 0.01) discard;
  gl_FragColor = vec4(vCol, uOpacity * vDim);
  #include <colorspace_fragment>
}`;
// particles as round shaded points (a disc with a sphere's shading), sized in world units
const PTS_VERT = `
uniform float uSize; uniform float uScale;
varying vec3 vCol;
void main() {
  vCol = color.rgb;
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  gl_Position = projectionMatrix * mv;
  gl_PointSize = max(3.0, uSize * uScale / max(-mv.z, 1e-30));
}`;
const PTS_FRAG = `
varying vec3 vCol;
void main() {
  vec2 q = gl_PointCoord * 2.0 - 1.0; float r2 = dot(q, q);
  if (r2 > 1.0) discard;
  vec3 n = vec3(q.x, -q.y, sqrt(1.0 - r2)), L = ${LIGHT_DIR};
  gl_FragColor = vec4(vCol * (0.42 + 0.68 * max(dot(n, L), 0.0)), 1.0);
  #include <colorspace_fragment>
}`;

// the volume: ray marched through the box's content, ended at the depth of the opaque scene (uDepthA) and split at the
// nearest translucent surface (uDepthB): part 1 is the cloud behind that surface (drawn before the translucent objects),
// part 2 the cloud in front of it (drawn after them), part 0 the whole ray. The opacity per step is
// 1 - exp(-v² τ uNorm dt): τ (the density slider) is the optical depth of the densest column of the volume along a box
// axis (uNorm = 1 / that column's ∫v² ds), so that the same slider position means the same in every world and box
// (review UX-3d A10). A per-pixel offset of the first step removes banding at few steps (A11).
const VOL_VERT = `out vec3 vWorld;
void main() { vec4 w = modelMatrix * vec4(position, 1.0); vWorld = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`;
const VOL_FRAG = `precision highp float; precision highp sampler3D;
uniform sampler3D uVol; uniform sampler2D uLut; uniform vec3 uMin; uniform vec3 uMax; uniform vec3 uCMin; uniform vec3 uCMax;
uniform vec3 uCam; uniform vec3 uFwd; uniform float uDensity; uniform float uNorm; uniform float uThreshold; uniform int uSteps;
uniform sampler2D uDepthA; uniform sampler2D uDepthB; uniform vec2 uRes; uniform float uNear; uniform float uFar;
uniform int uPart; uniform float uUseDepth; uniform float uDiag;
in vec3 vWorld; out vec4 outColor;
float rayDist(float depth, float cosA) {
  float z = (uNear * uFar) / ((uFar - uNear) * depth - uFar);
  return -z / max(cosA, 1e-6);
}
void main() {
  vec3 d = normalize(vWorld - uCam);
  vec3 inv = 1.0 / d;
  vec3 lo = max(uMin, uCMin), hi = min(uMax, uCMax);
  vec3 t0 = (lo - uCam) * inv, t1 = (hi - uCam) * inv;
  vec3 tn = min(t0, t1), tf = max(t0, t1);
  float a0 = max(max(max(tn.x, tn.y), tn.z), 0.0), a1 = min(min(tf.x, tf.y), tf.z);
  if (a0 >= a1) discard;
  vec2 uv = gl_FragCoord.xy / uRes;
  float cosA = dot(d, uFwd);
  float s0 = a0, s1 = a1;
  if (uUseDepth > 0.5) {
    s1 = min(s1, rayDist(texture(uDepthA, uv).r, cosA));
    if (uPart != 0) {
      float tB = rayDist(texture(uDepthB, uv).r, cosA);
      if (uPart == 1) s0 = max(s0, tB); else s1 = min(s1, tB);
    }
  }
  if (s0 >= s1) discard;
  float dt = uDiag / float(uSteps);  // one step length for every ray: a short ray takes fewer steps
  float jit = fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453);
  float k0 = max(0.0, ceil((s0 - a0) / dt - jit));
  float w = uDensity * uNorm * dt;
  vec4 acc = vec4(0.0);
  for (int i = 0; i < 1024; i++) {
    float t = a0 + (k0 + float(i) + jit) * dt;
    if (t >= s1) break;
    vec3 p = uCam + d * t;
    vec3 q = (p - uMin) / (uMax - uMin);
    float v = texture(uVol, vec3(q.y, 1.0 - q.z, q.x)).r;
    if (v <= uThreshold) continue;
    vec3 c = texture(uLut, vec2(v, 0.5)).rgb;
    float a = 1.0 - exp(-v * v * w);
    acc.rgb += (1.0 - acc.a) * c * a; acc.a += (1.0 - acc.a) * a;
    if (acc.a > 0.985) break;
  }
  outColor = acc;
}`;
// a slice plane: opaque (it writes depth: crossing planes are right at every pixel, the volume in front is drawn over it);
// a plane not pointed at is darkened, not made transparent (review UX-3d A2)
const PLANE_VERT = `out vec2 vUv; out vec3 vWorld;
void main() { vUv = uv; vec4 w = modelMatrix * vec4(position, 1.0); vWorld = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`;
const PLANE_FRAG = `precision highp float; precision highp sampler3D;
uniform sampler2D uTex; uniform sampler3D uVol; uniform sampler2D uLut; uniform vec3 uMin; uniform vec3 uMax;
uniform int uMode; uniform float uHighlight; uniform vec3 uColor; uniform float uOpacity; uniform float uDim;
in vec2 vUv; in vec3 vWorld; out vec4 outColor;
void main() {
  vec4 c;
  if (uMode == 1) {
    vec3 q = (vWorld - uMin) / (uMax - uMin);
    if (any(lessThan(q, vec3(-1e-4))) || any(greaterThan(q, vec3(1.0001)))) discard;
    float v = texture(uVol, vec3(q.y, 1.0 - q.z, q.x)).r;
    c = vec4(texture(uLut, vec2(v, 0.5)).rgb, 1.0);
  } else if (uMode == 2) {
    c = vec4(uColor * 0.3, 1.0);
  } else {
    c = texture(uTex, vUv);
    if (c.a < 0.01) discard;
  }
  float e = min(min(vUv.x, 1.0 - vUv.x), min(vUv.y, 1.0 - vUv.y));
  float border = uHighlight > 0.5 ? 0.012 : 0.0;
  if (e < border) c = vec4(uColor, 1.0);
  outColor = vec4(c.rgb * uDim, 1.0);
}`;

// shared geometries (never disposed with an object)
const shared = (g) => { g.userData.shared = true; return g; };
function mergeGeometries(list) {  // non-indexed or indexed BufferGeometries with position and normal -> one indexed
  const P = [], N = [], I = [];
  let base = 0;
  for (const g0 of list) {
    const g = g0.index ? g0 : g0.toNonIndexed();
    const p = g.attributes.position.array, n = g.attributes.normal.array, cnt = p.length / 3;
    P.push(...p); N.push(...n);
    if (g.index) for (const i of g.index.array) I.push(base + i); else for (let i = 0; i < cnt; i++) I.push(base + i);
    base += cnt;
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute("position", new THREE.Float32BufferAttribute(P, 3));
  out.setAttribute("normal", new THREE.Float32BufferAttribute(N, 3));
  out.setIndex(I);
  return out;
}
// an arrow from 0 to 1 along +y: a shaft and a cone (vector glyphs; scaled uniformly by the length)
const GLYPH_GEO = shared(mergeGeometries([
  new THREE.CylinderGeometry(0.035, 0.035, 0.64, 10, 1, false).translate(0, 0.32, 0),
  new THREE.ConeGeometry(0.1, 0.36, 14, 1, false).translate(0, 0.82, 0)]));
const SHAFT_GEO = shared(new THREE.CylinderGeometry(1, 1, 1, 12, 1, false).translate(0, 0.5, 0));
const HEAD_GEO = shared(new THREE.ConeGeometry(0.5, 1, 18, 1, false).translate(0, -0.5, 0));
const QUAD_GEO = shared(new THREE.PlaneGeometry(2, 2));
const WIDE_CORNERS = [0, -1, 0, 0, 1, 0, 1, -1, 0, 1, 1, 0];  // one wide segment's vertices: x = which end, y = which side
const WIDE_INDEX = [0, 2, 1, 1, 2, 3];

// a lit arrow (shaft and cone) with ArrowHelper's methods: setDirection, setLength(length, headLength, headWidth),
// setColor; its length along the direction from the group's position
function arrow3d(dir, origin, length, color, headLength, headWidth) {
  const g = new THREE.Group();
  const mat = litMaterial({ color });
  const shaft = new THREE.Mesh(SHAFT_GEO, mat), head = new THREE.Mesh(HEAD_GEO, mat);
  const tip = new THREE.Group(); tip.add(shaft, head); g.add(tip);
  g.userData.arrowParts = { shaft, head, tip, mat };
  g.position.copy(origin || new THREE.Vector3());
  g.setDirection = (d) => {
    const v = d.clone().normalize();
    tip.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), v.lengthSq() ? v : new THREE.Vector3(0, 1, 0));
  };
  g.setLength = (len, hl = 0.2 * len, hw = 0.2 * hl) => {
    hl = Math.min(hl, len * 0.9);
    const sr = Math.max(hw * 0.13, len * 0.006);
    shaft.scale.set(sr, Math.max(len - hl, 1e-9), sr);
    head.scale.set(hw, hl, hw); head.position.set(0, len, 0);
  };
  g.setColor = (c) => mat.uniforms.uColor.value.set(c);
  g.setDirection(dir || new THREE.Vector3(1, 0, 0));
  g.setLength(length || 1, headLength ?? 0.2 * (length || 1), headWidth ?? 0.2 * (headLength ?? 0.2 * (length || 1)));
  return g;
}

const VIEWS = [["iso", t("Iso"), t("Isometric (F — show the content)")], ["side", t("Side"), ""],
               ["top", t("Top"), ""], ["beam", t("From the source"), ""], ["back", t("From the target"), ""]];

// layers of three.js used by the passes: L0 opaque (depth pass), L1 the volume, L2 translucent surfaces, L4 their
// depth-only twins (the split of the volume)
const L_OPAQUE = 0, L_VOLUME = 1, L_TRANS = 2, L_TWIN = 4;
const L_OVER = 5;  // the experimenter's markers (a selected object, the ghost of a drag): drawn last, over everything

// a ring as a sprite texture (the marker of a selected object or a ghost: a circle that faces the camera)
function ringTexture(dashed) {
  const c = document.createElement("canvas"); c.width = c.height = 128;
  const g = c.getContext("2d");
  g.strokeStyle = "#ffffff"; g.lineWidth = 7;
  if (dashed) g.setLineDash([14, 10]);
  g.beginPath(); g.arc(64, 64, 58, 0, 2 * Math.PI); g.stroke();
  if (dashed) { g.setLineDash([]); g.fillStyle = "rgba(255,255,255,0.18)"; g.beginPath(); g.arc(64, 64, 55, 0, 2 * Math.PI); g.fill(); }
  const tt = new THREE.CanvasTexture(c); tt.colorSpace = THREE.SRGBColorSpace;
  return tt;
}

export function createScene3D({ onPlaneEdit, onPlaneMoving, onSelect, readOnly = () => false } = {}) {
  const canvas = el("canvas", { class: "s3d-canvas" });
  const hint = el("div", { class: "s3d-hint" });
  const tools = el("div", { class: "s3d-tools" });
  const busy = el("div", { class: "s3d-busy", style: { display: "none" } });
  const legend = el("div", { class: "s3d-legend", style: { display: "none" } });
  const note = el("div", { class: "s3d-note", style: { display: "none" } });
  const root = el("div", { class: "s3d-view" }, canvas, tools, busy, legend, note, hint);
  // no preserved drawing buffer: the snapshot draws and reads in one task (review UX-3d A18)
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setClearColor(0x0b0e14, 1);
  const basePR = () => Math.min(window.devicePixelRatio || 1, 2);
  renderer.setPixelRatio(basePR());
  const scene = new THREE.Scene();
  scene.add(new THREE.AmbientLight(0xffffff, 0.7));
  const sun = new THREE.DirectionalLight(0xffffff, 1.6); sun.position.set(-3, 6, 5); scene.add(sun);
  const camera = new THREE.PerspectiveCamera(38, 1, 0.01, 1e5);
  const orbit = new OrbitControls(camera, canvas);
  orbit.enableDamping = false;
  orbit.zoomToCursor = true;   // the wheel zooms toward the point under the pointer (A6)
  orbit.zoomSpeed = 2;         // ~10 % per wheel notch in Chromium, ~5 % in Firefox
  const gizmo = new TransformControls(camera, canvas);
  gizmo.setSize(0.8); gizmo.setSpace("local");
  scene.add(gizmo.getHelper());
  const lut = lutTexture(); lut.userData.shared = true;
  const S = { box: null, layers: new Map(), userVis: new Map(), userLook: null, planes: new Map(), selected: null, highlighted: null, scale: "sqrt", floor: 1e-6,
              vol: null, volTex: null, volMat: null, desc: null, frame: null, labels: null, dragging: false,
              up: [0, 1, 0], axes: axesOfUp([0, 1, 0]), plane2d: null, userMoved: false, fit: null, interactive: false,
              frames: 0, lastMs: 0, quality: 1, frameLabels: [], cssH: 0 };
  // the passes' depth: the opaque scene (A) and the nearest translucent surface (B)
  const mkRT = () => {
    const rt = new THREE.WebGLRenderTarget(1, 1, { depthBuffer: true });
    rt.depthTexture = new THREE.DepthTexture(1, 1);
    rt.depthTexture.userData.shared = true; rt.texture.userData.shared = true;
    return rt;
  };
  const rtA = mkRT(), rtB = mkRT();
  const tmp2 = new THREE.Vector2();

  // --- the frame's draw: depth passes, adaptive quality, clipping planes, labels, translucent order ------------------
  let pending = false;
  function requestRender() { if (!pending) { pending = true; requestAnimationFrame(() => draw()); } }
  function volumeLayer() { for (const L of S.layers.values()) if (L.kind === "volume" && L.visible) return L; return null; }
  function draw(full = !S.interactive) {
    pending = false;
    const t0 = performance.now();
    const vol = volumeLayer();
    // while the camera moves, a volume is marched at half the pixels and fewer steps; at full quality when it stops (A11)
    const q = !full && vol ? 0.5 : 1;
    if (renderer.getPixelRatio() !== basePR() * q) renderer.setPixelRatio(basePR() * q);
    S.quality = q;
    updateClip();
    scene.updateMatrixWorld();
    updateLabels();
    const trans = updateTranslucent();
    renderer.getDrawingBufferSize(tmp2);
    // the pixel-dependent uniforms: wide lines (the drawing buffer's size; widths in CSS pixels times the pixel ratio)
    // and points (their scale)
    S.uRes.value.copy(tmp2);
    S.ptScale.value = tmp2.y / (2 * Math.tan(camera.fov * Math.PI / 360));
    const pr = renderer.getPixelRatio();
    for (const L of S.layers.values()) L.obj.traverse((o) => { const W = o.userData.wide; if (W) o.material.uniforms.uWidth.value = W.width * pr; });
    if (vol) {
      const helper = gizmo.getHelper(), hv = helper.visible; helper.visible = false;
      for (const rt of [rtA, rtB]) if (rt.width !== tmp2.x || rt.height !== tmp2.y) rt.setSize(tmp2.x, tmp2.y);
      camera.layers.set(L_OPAQUE);
      renderer.setRenderTarget(rtA); renderer.render(scene, camera);
      if (trans) { camera.layers.set(L_TWIN); renderer.setRenderTarget(rtB); renderer.render(scene, camera); }
      renderer.setRenderTarget(null);
      helper.visible = hv;
      const U = S.volMat.uniforms;
      U.uDepthA.value = rtA.depthTexture; U.uDepthB.value = rtB.depthTexture;
      U.uRes.value.set(tmp2.x, tmp2.y); U.uNear.value = camera.near; U.uFar.value = camera.far;
      camera.getWorldDirection(U.uFwd.value); U.uCam.value.copy(camera.position);
      U.uSteps.value = q < 1 ? 56 : S.fullSteps;
      U.uUseDepth.value = 1;
      const { back, front } = vol.obj.userData;
      back.visible = trans; front.material.uniforms.uPart.value = trans ? 2 : 0;
    }
    camera.layers.set(L_OPAQUE); camera.layers.enable(L_VOLUME); camera.layers.enable(L_TRANS); camera.layers.enable(L_OVER);
    updateMarkers();
    renderer.render(scene, camera);
    S.frames++; S.lastMs = performance.now() - t0;
  }
  S.fullSteps = 160;
  // near and far follow the camera's distance from the scene (review UX-3d A8)
  function updateClip() {
    if (!S.box) return;
    const c = S.boxCenterT, R = S.boxRadius, dc = camera.position.distanceTo(c);
    const far = dc + 2.5 * R, near = Math.max(dc - 2.5 * R, far * 2e-4);
    if (Math.abs(camera.far - far) > 1e-6 * far || Math.abs(camera.near - near) > 1e-6 * near) {
      camera.far = far; camera.near = near; camera.updateProjectionMatrix();
    }
  }
  // translucent surfaces: their order (far to near by their nearest point), and whether any is visible
  function updateTranslucent() {
    let any = false;
    const cam = camera.position, sph = new THREE.Sphere();
    const visit = (o) => {
      const tt = o.userData.translucent;
      if (!tt || !o.isMesh || !o.visible) return;
      let p = o, vis = true;
      while (p) { if (!p.visible) { vis = false; break; } p = p.parent; }
      if (!vis) return;
      const g = o.geometry; if (!g.boundingSphere) g.computeBoundingSphere();
      sph.copy(g.boundingSphere).applyMatrix4(o.matrixWorld);
      const key = sph.center.distanceTo(cam) - sph.radius;
      o.userData.sortKey = key; if (tt.twin) tt.twin.userData.sortKey = key;
      if (tt.split) any = true;
    };
    for (const L of S.layers.values()) if (L.visible) L.obj.traverse(visit);
    return any;
  }
  renderer.setTransparentSort((a, b) => {
    if (a.groupOrder !== b.groupOrder) return a.groupOrder - b.groupOrder;
    if (a.renderOrder !== b.renderOrder) return a.renderOrder - b.renderOrder;
    const ka = a.object.userData.sortKey, kb = b.object.userData.sortKey;
    if (ka !== undefined && kb !== undefined) {
      if (ka !== kb) return kb - ka;
      const ta = a.object.userData.twin ? 0 : 1, tb = b.object.userData.twin ? 0 : 1;  // a depth-only twin first
      if (ta !== tb) return ta - tb;
    }
    if (a.z !== b.z) return b.z - a.z;
    return a.id - b.id;
  });
  // labels: their size in pixels (the canvas's height), and frame labels that would overlap on screen hidden
  function updateLabelScale(s) {
    const L = s.userData.label, H = S.cssH || 1;
    const h = 2 * L.px * Math.tan(camera.fov * Math.PI / 360) / H;
    s.scale.set(h * L.aspect, h, 1);
  }
  function updateLabels() {
    const H = root.clientHeight || S.cssH;
    if (H && H !== S.cssH) { S.cssH = H; scene.traverse((o) => { if (o.isSprite && o.userData.label) updateLabelScale(o); }); }
    if (!S.frameLabels.length) return;
    const W = root.clientWidth || 1, kept = [], v = new THREE.Vector3();
    camera.updateMatrixWorld();
    placeFrameLabels();
    for (const s of S.frameLabels) {
      if (s.userData.hide) { s.visible = false; continue; }
      s.updateMatrixWorld();
      v.setFromMatrixPosition(s.matrixWorld).project(camera);
      if (v.z > 1 || v.z < -1) { s.visible = false; continue; }
      const sx = (v.x + 1) / 2 * W, sy = (1 - v.y) / 2 * H, L = s.userData.label, w = L.px * L.aspect, h = L.px;
      const r = [sx - s.center.x * w + 0.12 * h, sy - (1 - s.center.y) * h + 0.2 * h, sx + (1 - s.center.x) * w - 0.12 * h, sy + s.center.y * h - 0.2 * h];
      const hit = kept.some((k) => r[0] < k[2] && k[0] < r[2] && r[1] < k[3] && k[1] < r[3]);
      s.visible = !hit;
      if (!hit) kept.push(r);
    }
  }

  // --- interaction: the experimenter's camera is kept; full quality when it stops ----------------------------------
  let idleT = null;
  orbit.addEventListener("start", () => { S.userMoved = true; S.interactive = true; clearTimeout(idleT); });
  orbit.addEventListener("end", () => {
    clearTimeout(idleT);
    idleT = setTimeout(() => { S.interactive = false; requestRender(); }, 180);
  });
  orbit.addEventListener("change", requestRender);
  gizmo.addEventListener("change", requestRender);
  new ResizeObserver(() => {
    const w = root.clientWidth, h = root.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
    // until the experimenter moves the camera, the view is fitted again to the new size (the layout settles after the
    // first frame: a slice window, the camera window; review UX-3d A4)
    if (S.box && !S.userMoved) { S.fitted = true; refit(); }
    requestRender();
  }).observe(root);

  // --- layers: every element of the scene can be switched off on its own ---------------------------------------
  function addLayer(id, label, obj, visible = true, kind = "object") {
    label = t(label);  // a msgid or a text the world sent (T): shown in the viewer's language
    const old = S.layers.get(id);
    if (old) { scene.remove(old.obj); if (old.obj !== obj) disposeTree(old.obj); visible = old.visible; }
    if (S.userVis.has(id)) visible = S.userVis.get(id);  // the experimenter's choice survives a rebuilt scene
    obj.visible = visible;
    obj.traverse((o) => { if (o.isSprite && o.userData.label) updateLabelScale(o); });
    scene.add(obj);
    S.layers.set(id, { id, label, obj, visible, kind });
    // the panel "Scene layers" only when the set of layers changed, not when a layer's object was replaced (A17)
    if (!old || old.label !== label || old.kind !== kind) layersChanged();
    updateLegend();
    requestRender();
  }
  function setLayerVisible(id, on, user = false) {
    if (user) S.userVis.set(id, on);
    const L = S.layers.get(id); if (!L) return;
    L.visible = on; L.obj.visible = on; updateLegend(); requestRender();  // the panel's checkbox already shows it
  }
  let layersListener = () => {};
  function layersChanged() { layersListener(); }

  // translucent surfaces: a depth-only twin drawn just before the surface keeps only its nearest layer, and splits the
  // volume (layer L_TWIN); both are ordered by the surface's nearest point (review UX-3d A2)
  function makeTranslucent(mesh, { split = true } = {}) {
    const m = mesh.material;
    m.transparent = true; m.depthWrite = false; m.depthFunc = THREE.LessEqualDepth;
    const tm = m.isShaderMaterial
      ? new THREE.ShaderMaterial({ vertexShader: m.vertexShader, fragmentShader: DEPTH_ONLY_FRAG, side: m.side, uniforms: m.uniforms,
                                   vertexColors: m.vertexColors, transparent: true, colorWrite: false, depthWrite: true })
      : new THREE.MeshBasicMaterial({ side: m.side, transparent: true, colorWrite: false, depthWrite: true });
    tm.userData.twinOf = true;
    const twin = new THREE.Mesh(mesh.geometry, tm);
    twin.matrixAutoUpdate = mesh.matrixAutoUpdate; twin.matrix.copy(mesh.matrix);
    twin.position.copy(mesh.position); twin.quaternion.copy(mesh.quaternion); twin.scale.copy(mesh.scale);
    twin.frustumCulled = mesh.frustumCulled;
    twin.renderOrder = mesh.renderOrder = 2;
    // a flat surface has one layer: its twin serves only the volume's split (pass B), not the main pass
    if (isFlat(mesh.geometry)) twin.layers.set(L_TWIN);
    else { twin.layers.set(L_TRANS); twin.layers.enable(L_TWIN); }
    mesh.layers.set(L_TRANS);
    twin.userData.twin = true;
    mesh.userData.translucent = { twin, split };
    // the twin first (three draws equal keys in creation order)
    const parent = mesh.parent;
    if (parent) { parent.remove(mesh); parent.add(twin, mesh); }
    return twin;
  }
  function isFlat(geo) {  // all vertices on one plane (within 1e-6 of the size)
    const a = geo.attributes.position; if (!a || a.count < 3) return true;
    if (!geo.boundingBox) geo.computeBoundingBox();
    const size = geo.boundingBox.getSize(new THREE.Vector3()).length() || 1;
    const p0 = new THREE.Vector3().fromBufferAttribute(a, 0), p = new THREE.Vector3(), n = new THREE.Vector3();
    for (let i = 1; i < a.count && n.lengthSq() === 0; i++) {
      const u = new THREE.Vector3().fromBufferAttribute(a, i).sub(p0);
      for (let j = i + 1; j < a.count; j++) {
        const c = new THREE.Vector3().fromBufferAttribute(a, j).sub(p0).cross(u);
        if (c.length() > 1e-6 * size * size) { n.copy(c).normalize(); break; }
      }
      if (i > 4) break;
    }
    if (n.lengthSq() === 0) return true;
    for (let i = 0; i < a.count; i++) if (Math.abs(p.fromBufferAttribute(a, i).sub(p0).dot(n)) > 1e-6 * size) return false;
    return true;
  }
  function addTranslucent(group, mesh, opts) {  // add mesh (and its twin) to group
    group.add(mesh);
    makeTranslucent(mesh, opts);
    return mesh;
  }

  // wide lines: drawn by a child of a data line (the data line keeps its geometry, drawRange and colours — what the key
  // frames compare —; its own 1-px drawing is switched off). mode "strip" (a polyline) or "segments" (pairs). The child's
  // geometry holds four vertices per segment, filled from the data line from a given segment on (appends are cheap).
  function wideFrom(dataLine, { width = 2, color = null, opacity = 1, sphere = null } = {}) {
    dataLine.material.visible = false;
    const perColor = !color;
    const mat = new THREE.ShaderMaterial({
      vertexShader: WIDE_VERT, fragmentShader: WIDE_FRAG,
      defines: { ...(perColor ? { PER_COLOR: "" } : {}), ...(sphere ? { SPHERE_DIM: "" } : {}) },
      transparent: opacity < 1, depthWrite: opacity >= 1,
      uniforms: { uRes: S.uRes, uWidth: { value: width }, uColor: { value: new THREE.Color(color || 0xffffff) }, uOpacity: { value: opacity },
                  uSphere: { value: new THREE.Vector4(...(sphere || [0, 0, 0, 0])) } } });
    const w = new THREE.Mesh(new THREE.BufferGeometry(), mat);
    w.frustumCulled = false;
    w.userData.wide = { width, perColor, mode: dataLine.isLineSegments ? "segments" : "strip", cap: 0, n: 0 };
    dataLine.add(w);
    dataLine.userData.wideChild = w;
    syncWide(dataLine, 0);
    return w;
  }
  function syncWide(dataLine, from = 0) {
    const w = dataLine.userData.wideChild; if (!w) return;
    const W = w.userData.wide, geo = dataLine.geometry, seg = W.mode === "segments";
    const pos = geo.attributes.position, col = W.perColor ? geo.attributes.color : null;
    if (!pos) { w.geometry.setDrawRange(0, 0); return; }
    const total = pos.count, dr = geo.drawRange, nPts = Math.min(total, Number.isFinite(dr.count) ? dr.start + dr.count : total);
    const segs = seg ? Math.floor(nPts / 2) : Math.max(0, nPts - 1), capData = seg ? Math.floor(total / 2) : Math.max(0, total - 1);
    if (segs > W.cap || !w.geometry.attributes.iA) {  // a new geometry, large enough for the data line's buffers
      const cap = Math.max(segs, capData, 2 * W.cap, 1), g = new THREE.BufferGeometry();
      const corner = new Float32Array(12 * cap), idx = new Uint32Array(6 * cap);
      for (let k = 0; k < cap; k++) { corner.set(WIDE_CORNERS, 12 * k); for (let j = 0; j < 6; j++) idx[6 * k + j] = 4 * k + WIDE_INDEX[j]; }
      g.setAttribute("corner", new THREE.BufferAttribute(corner, 3));
      g.setAttribute("iA", new THREE.BufferAttribute(new Float32Array(12 * cap), 3));
      g.setAttribute("iB", new THREE.BufferAttribute(new Float32Array(12 * cap), 3));
      if (W.perColor) { g.setAttribute("iCA", new THREE.BufferAttribute(new Float32Array(12 * cap), 3)); g.setAttribute("iCB", new THREE.BufferAttribute(new Float32Array(12 * cap), 3)); }
      g.setIndex(new THREE.BufferAttribute(idx, 1));
      w.geometry.dispose(); w.geometry = g; W.cap = cap; from = 0;
    }
    const g = w.geometry, A = g.attributes.iA, B = g.attributes.iB, p = pos.array;
    const CA = W.perColor ? g.attributes.iCA : null, CB = W.perColor ? g.attributes.iCB : null, c = col ? col.array : null;
    from = Math.max(0, Math.min(from, segs));
    for (let s = from; s < segs; s++) {
      const a = 3 * (seg ? 2 * s : s), b = 3 * (seg ? 2 * s + 1 : s + 1);
      for (let k = 0; k < 4; k++) {
        const o = 12 * s + 3 * k;
        A.array[o] = p[a]; A.array[o + 1] = p[a + 1]; A.array[o + 2] = p[a + 2];
        B.array[o] = p[b]; B.array[o + 1] = p[b + 1]; B.array[o + 2] = p[b + 2];
        if (CA && c) { CA.array[o] = c[a]; CA.array[o + 1] = c[a + 1]; CA.array[o + 2] = c[a + 2]; CB.array[o] = c[b]; CB.array[o + 1] = c[b + 1]; CB.array[o + 2] = c[b + 2]; }
      }
    }
    // the changed part only (ranges add up until the next frame uploads them; many: the whole buffer)
    if (segs > from) for (const at of [A, B, CA, CB]) if (at) {
      if (at.updateRanges.length > 32) at.clearUpdateRanges(); else at.addUpdateRange(12 * from, 12 * (segs - from));
      at.needsUpdate = true;
    }
    g.setDrawRange(0, 6 * segs);
    W.n = segs;
  }
  S.uRes = { value: new THREE.Vector2(1, 1) };

  // --- the frame: box edges, axes and labels (A9) ----------------------------------------------------------------------
  // The labels of each axis stand on an outer edge of the box as seen now (an edge between a face toward the camera and a
  // face away from it), chosen again on every frame: the lowest such edge for an axis that runs across the screen, the
  // leftmost for one that runs up it; each label is pushed outward from the box, so that nothing inside the box covers
  // it. Ticks are not drawn along a thin axis (a 2-D world's slab).
  function buildFrame(box, units, names = ["x", "y", "z"]) {
    const g = new THREE.Group();
    const [lo, hi] = box;
    const a = P2T(lo), b = P2T(hi);
    const bb = new THREE.Box3(new THREE.Vector3(Math.min(a.x, b.x), Math.min(a.y, b.y), Math.min(a.z, b.z)),
                              new THREE.Vector3(Math.max(a.x, b.x), Math.max(a.y, b.y), Math.max(a.z, b.z)));
    const helper = new THREE.Box3Helper(bb, 0x55606e); g.add(helper);
    const size = Math.max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]);
    S.frameLabels = [];
    S.frameAx = [0, 1, 2].map((k) => {
      const thin = hi[k] - lo[k] < 0.12 * size, n = k === ((S.frameAxes || S.axes).R.findIndex((c) => Math.abs(c) > 0.5)) ? 5 : 3;
      // the box's ends, and between them round values (steps 1, 2, 5 × 10ⁿ; review LB1-p02-ux X13: −20,3; −0,625; 19,1)
      // not closer to an end than 0,3 of a step
      const vals = [];
      if (!thin) {
        const raw = (hi[k] - lo[k]) / (n - 1), e = 10 ** Math.floor(Math.log10(raw)), m = raw / e;
        const step = (m <= 1 ? 1 : m <= 2 ? 2 : m <= 5 ? 5 : 10) * e;
        vals.push(lo[k]);
        for (let j = Math.ceil(lo[k] / step); j * step < hi[k]; j++) {
          const v = Math.abs(j) < 1e-12 ? 0 : j * step;
          if (v - lo[k] > 0.3 * step && hi[k] - v > 0.3 * step) vals.push(v);
        }
        vals.push(hi[k]);
      }
      const mk = (txt, px, pri, color) => { const s = labelSprite(txt, color, px); s.userData.pri = pri; g.add(s); S.frameLabels.push(s); updateLabelScale(s); return s; };
      const ticks = vals.map((v, i) => ({ v, s: mk(num(v, 3), 14, i === 0 || i === vals.length - 1 ? 1 : 2, "#8b96a3") }));
      return { k, ticks, name: mk(t("{name}, {unit}", { name: t(names[k]), unit: t(units) }), 16, 0, "#c8d0da") };
    });
    S.frameLabels.sort((p, q) => p.userData.pri - q.userData.pri);
    S.frameBox = { lo: [...lo], hi: [...hi] };
    return g;
  }
  function placeFrameLabels() {
    if (!S.frameAx || !S.frameBox) return;
    const { lo, hi } = S.frameBox, cam = T2P(camera.position), W = root.clientWidth || 1, H = root.clientHeight || 1;
    const scr = (p) => { const v = P2T(p).project(camera); return [(v.x + 1) / 2 * W, (1 - v.y) / 2 * H, v.z]; };
    const cen = [0, 1, 2].map((i) => (lo[i] + hi[i]) / 2), cs = scr(cen);
    // a face (axis i, side lo/hi) faces the camera when the camera is beyond it
    const facing = (i, side) => (side ? cam[i] > hi[i] : cam[i] < lo[i]);
    for (const A of S.frameAx) {
      const k = A.k, [i, j] = [0, 1, 2].filter((q) => q !== k);
      const p0 = [...cen], p1 = [...cen]; p0[k] = lo[k]; p1[k] = hi[k];
      const a0 = scr(p0), a1 = scr(p1), dx = a1[0] - a0[0], dy = a1[1] - a0[1];
      const across = Math.abs(dx) >= Math.abs(dy);
      let best = null;
      for (const si of [0, 1]) for (const sj of [0, 1]) {
        const fi = facing(i, si), fj = facing(j, sj);
        if (fi === fj) continue;  // not an outer edge
        const m = [...cen]; m[i] = si ? hi[i] : lo[i]; m[j] = sj ? hi[j] : lo[j];
        const ms = scr(m), score = across ? ms[1] - 0.2 * Math.abs(ms[0] - cs[0]) : -ms[0] - 0.2 * Math.abs(ms[1] - cs[1]);
        if (!best || score > best.score) best = { m, ms, score };
      }
      const show = !!best && Math.hypot(dx, dy) > 24;
      for (const tt of A.ticks) tt.s.userData.hide = !show;
      A.name.userData.hide = !show;
      if (!show) continue;
      // outward on screen: from the box's middle toward the edge, at right angles to the axis
      let ox = best.ms[0] - cs[0], oy = best.ms[1] - cs[1];
      const L = Math.hypot(dx, dy), ux = dx / L, uy = dy / L, along = ox * ux + oy * uy;
      ox -= along * ux; oy -= along * uy;
      const ol = Math.hypot(ox, oy) || 1; ox /= ol; oy /= ol;
      const anchor = (s, gap) => {
        const Lb = s.userData.label, w = Lb.px * Lb.aspect, h = Lb.px;
        s.center.set(0.5 - ox * (0.5 + gap / w), 0.5 + oy * (0.5 + gap / h));
      };
      for (const tt of A.ticks) { const p = [...best.m]; p[k] = tt.v; tt.s.position.copy(P2T(p)); anchor(tt.s, 4); }
      const pm = [...best.m]; A.name.position.copy(P2T(pm)); anchor(A.name, A.ticks.length ? 22 : 6);
      {  // the axis's name inside the view: a longer name (a unit in another language) is not cut by the canvas's edge
        const Lb = A.name.userData.label, w = Lb.px * Lb.aspect, x = scr(pm)[0];  // (review i18n-browser F13)
        let cx = A.name.center.x;
        if (x - cx * w < 2) cx = Math.max(0, (x - 2) / w);
        if (x + (1 - cx) * w > W - 2) cx = Math.min(1, 1 - (W - 2 - x) / w);
        A.name.center.x = cx;
      }
    }
  }

  // --- the apparatus -------------------------------------------------------------------------------------------------
  function plate(o) {
    const [W, H] = o.size;
    const shape = new THREE.Shape();
    shape.moveTo(-W / 2, -H / 2); shape.lineTo(W / 2, -H / 2); shape.lineTo(W / 2, H / 2); shape.lineTo(-W / 2, H / 2); shape.lineTo(-W / 2, -H / 2);
    const outlines = [];
    for (const h of o.holes || []) {
      const p = new THREE.Path();
      if (h.rect) { const [xa, xb, ya, yb] = h.rect; p.moveTo(xa, ya); p.lineTo(xa, yb); p.lineTo(xb, yb); p.lineTo(xb, ya); p.lineTo(xa, ya); }
      else if (h.circle) { const [cx, cy, r] = h.circle; p.absarc(cx, cy, r, 0, Math.PI * 2, true); }
      shape.holes.push(p);
      outlines.push(p.getPoints(64));
    }
    const thick = 0.012 * Math.max(W, H);
    const geo = new THREE.ExtrudeGeometry(shape, { depth: thick, bevelEnabled: false, curveSegments: 48 });
    // pushed back in depth: a slice plane or a slit outline on its face is drawn, not z-fought (A19)
    const mat = new THREE.MeshStandardMaterial({ color: 0x7c8794, metalness: 0.55, roughness: 0.45, side: THREE.DoubleSide,
                                                 polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 2 });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.rotation.y = Math.PI / 2;  // shape (x, y) -> three (-Z, Y); extrusion along +X (the depth)
    mesh.position.x = (o.z || 0) - thick;
    const g = new THREE.Group(); g.add(mesh);
    const lift = 2e-3 * (S.size || 1);
    for (const pts of outlines) {
      const line = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(pts.map((q) => P2T([q.x, q.y, (o.z || 0) + lift]))),
                                      new THREE.LineBasicMaterial({ color: 0xfff2c4 }));
      g.add(line);
    }
    return g;
  }
  function imagePlane(o, nx, ny, data, opacity = 1) {
    const geo = new THREE.PlaneGeometry(o.size[0], o.size[1]);
    const tex = new THREE.DataTexture(new Uint8Array(nx * ny * 4), nx, ny, THREE.RGBAFormat);
    tex.magFilter = THREE.LinearFilter; tex.minFilter = THREE.LinearFilter;
    const mat = new THREE.MeshBasicMaterial({ map: tex, side: THREE.DoubleSide, transparent: opacity < 1, opacity });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.rotation.y = Math.PI / 2;  // local x -> -Z (physics x), local y -> Y (physics y)
    mesh.position.x = o.z || 0;
    mesh.userData = { tex, nx, ny, data, opacity };
    paintImage(mesh);
    if (opacity < 1) { const g = new THREE.Group(); g.userData = { ...mesh.userData, mesh }; addTranslucent(g, mesh); return g; }
    return mesh;
  }
  function paintImage(mesh) {
    const { tex, nx, ny, data } = mesh.userData;
    if (!data) return;
    const d = tex.image.data;
    for (let ix = 0; ix < nx; ix++) for (let iy = 0; iy < ny; iy++) {
      const v = transfer(data[ix * ny + iy], S.scale, S.floor), c = Math.max(0, Math.min(255, Math.round(255 * (v || 0))));
      const o = 4 * (iy * nx + ix);
      d[o] = LUT[3 * c]; d[o + 1] = LUT[3 * c + 1]; d[o + 2] = LUT[3 * c + 2]; d[o + 3] = 255;
    }
    tex.needsUpdate = true;
  }
  function incident(o) {
    const g = new THREE.Group();
    const [W, H] = o.size;
    const n = Math.min(24, Math.max(3, Math.round((o.z1 - o.z0) / o.lam)));
    for (let i = 0; i <= n; i++) {
      const z = o.z0 + (o.z1 - o.z0) * i / n;
      const m = new THREE.Mesh(new THREE.PlaneGeometry(W, H), new THREE.MeshBasicMaterial({ color: 0x7fb7ff, transparent: true, opacity: 0.06, side: THREE.DoubleSide, depthWrite: false }));
      m.rotation.y = Math.PI / 2; m.position.x = z; g.add(m);
    }
    const L = (o.z1 - o.z0) * 0.9;
    g.add(arrow3d(new THREE.Vector3(1, 0, 0), P2T([0, -H * 0.42, o.z0]), L, 0x7fb7ff, 0.12 * L, 0.05 * L));
    const s = labelSprite(t("incident wave (given)"), "#9cc8ff", 16, [0.5, 1.2]); s.position.copy(P2T([0, -H * 0.5, o.z0])); g.add(s);
    return g;
  }
  function disk(o) {
    const N = 128, data = new Float32Array(N * N);
    for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) {
      const x = (i / (N - 1) - 0.5) * o.size[0], y = (j / (N - 1) - 0.5) * o.size[1];
      data[i * N + j] = Math.exp(-2 * (x * x + y * y) / (o.w * o.w));  // |U|^2 of exp(-r^2/w^2)
    }
    return imagePlane(o, N, N, data, 0.85);
  }

  // a sphere drawn by its meridians and parallels over a faint lit surface (e.g. light, |beta| = 1, in velocity space):
  // the lines on its far half are dimmed, so that its front and back are told apart (A5)
  function sphere(o) {
    const g = new THREE.Group(), r = o.radius, c = P2T(o.center || [0, 0, 0]);
    const pts = [];
    const seg = (A, B) => pts.push(A.x, A.y, A.z, B.x, B.y, B.z);
    for (let k = 0; k < 12; k++) {  // meridians
      const ph = Math.PI * k / 12;
      for (let j = 0; j < 64; j++) {
        const t0 = 2 * Math.PI * j / 64, t1 = 2 * Math.PI * (j + 1) / 64;
        const p = (tt) => new THREE.Vector3(r * Math.cos(tt) * Math.cos(ph), r * Math.sin(tt), r * Math.cos(tt) * Math.sin(ph)).add(c);
        seg(p(t0), p(t1));
      }
    }
    for (let k = 1; k < 8; k++) {  // parallels
      const th = Math.PI * k / 8;
      for (let j = 0; j < 64; j++) {
        const t0 = 2 * Math.PI * j / 64, t1 = 2 * Math.PI * (j + 1) / 64;
        const p = (tt) => new THREE.Vector3(r * Math.sin(th) * Math.cos(tt), r * Math.cos(th), r * Math.sin(th) * Math.sin(tt)).add(c);
        seg(p(t0), p(t1));
      }
    }
    const geo = new THREE.BufferGeometry(); geo.setAttribute("position", new THREE.Float32BufferAttribute(pts, 3));
    const lines = new THREE.LineSegments(geo, new THREE.LineBasicMaterial({ color: 0x7fb7ff }));
    g.add(lines);
    wideFrom(lines, { width: 1.5, color: 0x7fb7ff, opacity: 0.55, sphere: [c.x, c.y, c.z, r] });
    const surf = new THREE.Mesh(new THREE.SphereGeometry(r, 48, 24), litMaterial({ color: 0x7fb7ff, opacity: 0.07, shade: [0.5, 0.6, 0.15] }));
    surf.position.copy(c);
    addTranslucent(g, surf);
    return g;
  }
  function point(o) {
    const g = new THREE.Group(), size = (S.size || 1) * 0.012;
    const m = new THREE.Mesh(new THREE.SphereGeometry(size, 20, 14), litMaterial({ color: o.color || 0xffffff }));
    m.position.copy(P2T(o.pos)); g.add(m);
    if (o.text) { const s = labelSprite(o.text, "#c8d0da", 16, [0.5, -0.4]); s.position.copy(P2T(o.pos)).add(P2T(S.axes.U).multiplyScalar(size * 1.5)); g.add(s); }
    return g;
  }

  // --- computed paths, gyroscope triads, marks, arrows, the moving body (e.g. v09) --------------------------------------
  // a polyline revealed as the run's time reaches it: points [from, from + count) of path `id` (accumulative)
  function appendPath(id, from, pts, { label = t("Path (computed)"), color = 0x4fd1c5 } = {}) {
    let P = S.paths.get(id);
    if (!P) {
      const geo = new THREE.BufferGeometry();
      const buf = new Float32Array(3 * 8192);
      geo.setAttribute("position", new THREE.BufferAttribute(buf, 3));
      geo.setDrawRange(0, 0);
      const line = new THREE.Line(geo, new THREE.LineBasicMaterial({ color }));
      line.frustumCulled = false;
      wideFrom(line, { width: 2.5, color });
      P = { line, geo, buf, n: 0 };
      S.paths.set(id, P);
      addLayer(id, label, line, true, "path");
    }
    const n = pts.length / 3, need = from + n;
    if (3 * need > P.buf.length) {
      const nb = new Float32Array(Math.max(3 * need, 2 * P.buf.length)); nb.set(P.buf);
      P.buf = nb; P.geo.setAttribute("position", new THREE.BufferAttribute(nb, 3));
    }
    for (let i = 0; i < n; i++) {
      const v = P2T([pts[3 * i], pts[3 * i + 1], pts[3 * i + 2]]);
      P.buf[3 * (from + i)] = v.x; P.buf[3 * (from + i) + 1] = v.y; P.buf[3 * (from + i) + 2] = v.z;
    }
    P.n = Math.max(P.n, need);
    P.geo.attributes.position.needsUpdate = true;
    P.geo.setDrawRange(0, P.n);
    syncWide(P.line, from - 1);
    requestRender();
  }
  const AXIS_COLORS = [new THREE.Color(0xff5a5a), new THREE.Color(0x5adc78), new THREE.Color(0x5aa0ff)];
  // small triads (accumulative): mats are 3x3 row-major, its columns the axes in physics coordinates
  function addTriads(id, pos, mats, { label = t("Gyroscope axes along the path") } = {}) {
    let L = S.layers.get(id);
    if (!L) { const g = new THREE.Group(); addLayer(id, label, g, true, "triads"); L = S.layers.get(id); }
    const n = pos.length / 3, len = (S.size || 1) * 0.035;
    const P = new Float32Array(n * 18), C = new Float32Array(n * 18);
    for (let i = 0; i < n; i++) {
      const o = P2T([pos[3 * i], pos[3 * i + 1], pos[3 * i + 2]]);
      for (let k = 0; k < 3; k++) {
        const a = P2T([mats[9 * i + k], mats[9 * i + 3 + k], mats[9 * i + 6 + k]]).multiplyScalar(len);
        const b = 18 * i + 6 * k;
        P.set([o.x, o.y, o.z, o.x + a.x, o.y + a.y, o.z + a.z], b);
        const c = AXIS_COLORS[k]; C.set([c.r, c.g, c.b, c.r, c.g, c.b], b);
      }
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(P, 3)); geo.setAttribute("color", new THREE.BufferAttribute(C, 3));
    const segs = new THREE.LineSegments(geo, new THREE.LineBasicMaterial({ vertexColors: true }));
    L.obj.add(segs);
    wideFrom(segs, { width: 2 });
    requestRender();
  }
  function setMarks(id, pos, { label = t("Marks"), color = 0xffffff } = {}) {
    const g = new THREE.Group(), size = (S.size || 1) * 0.009;
    const geo = new THREE.SphereGeometry(size, 16, 12), mat = litMaterial({ color });
    for (let i = 0; i < pos.length / 3; i++) { const m = new THREE.Mesh(geo, mat); m.position.copy(P2T([pos[3 * i], pos[3 * i + 1], pos[3 * i + 2]])); g.add(m); }
    addLayer(id, label, g, true, "marks");
  }
  function arrowObj(from, vec, color, text) {
    const g = new THREE.Group(), v = P2T(vec), L = v.length();
    if (L > 0) {
      const a = arrow3d(v.clone().normalize(), P2T(from), L, new THREE.Color(color).getHex(), Math.min(0.25 * L, (S.size || 1) * 0.04), Math.min(0.12 * L, (S.size || 1) * 0.02));
      g.add(a);
      if (text) { const s = labelSprite(text, color, 16, [0.0, 0.5]); s.position.copy(P2T(from).add(v.clone().multiplyScalar(1.04))); g.add(s); }
    }
    return g;
  }
  function setArrow(id, from, vec, { label = id, color = "#ffd23f", text = "" } = {}) {
    const g = arrowObj(from, vec, color, text);
    g.userData.vec = [...vec];  // a view may look along it (a world's view {along: id})
    addLayer(id, label, g, true, "arrow");
  }
  // the moving body: a marker, its gyroscope triad, its spin and thrust (one per world; replaced on every frame)
  function setBody(id, { pos, O, spin, thrust }, { label = t("Craft: gyroscopes, spin, thrust") } = {}) {
    let L = S.layers.get(id);
    // sized by the scene: made again when the scene's box changed since (review CK-1: through a key frame the craft
    // kept the size of the box it was first drawn with)
    if (L && L.obj.userData.size !== (S.size || 1) * 0.016) { removeLayer(id); L = null; }
    if (!L) {
      const g = new THREE.Group(), size = (S.size || 1) * 0.016;
      const ball = new THREE.Mesh(new THREE.SphereGeometry(size, 20, 14), litMaterial({ color: 0xffffff }));
      const parts = { ball, axes: [0, 1, 2].map((k) => arrow3d(new THREE.Vector3(1, 0, 0), new THREE.Vector3(), 1, AXIS_COLORS[k].getHex())),
                      spin: arrow3d(new THREE.Vector3(1, 0, 0), new THREE.Vector3(), 1, 0xffd23f),
                      thrust: arrow3d(new THREE.Vector3(1, 0, 0), new THREE.Vector3(), 1, 0xff8a1f) };
      g.add(ball, ...parts.axes, parts.spin, parts.thrust);
      parts.size = size;
      g.userData = parts;
      addLayer(id, label, g, true, "body"); L = S.layers.get(id);
    }
    const parts = L.obj.userData, o = P2T(pos), len = (S.size || 1) * 0.09;
    parts.ball.position.copy(o);
    for (let k = 0; k < 3; k++) {
      const a = P2T([O[k], O[3 + k], O[6 + k]]).normalize();
      parts.axes[k].position.copy(o); parts.axes[k].setDirection(a); parts.axes[k].setLength(len, 0.22 * len, 0.1 * len);
    }
    const sp = P2T(spin).normalize();
    parts.spin.position.copy(o); parts.spin.setDirection(sp); parts.spin.setLength(1.35 * len, 0.2 * len, 0.12 * len);
    if (thrust) { const th = P2T(thrust).normalize(); parts.thrust.position.copy(o); parts.thrust.setDirection(th); parts.thrust.setLength(0.8 * len, 0.2 * len, 0.1 * len); parts.thrust.visible = true; }
    else parts.thrust.visible = false;
    requestRender();
  }

  // --- meshes computed by the run (e.g. v10: bodies in the lab, their retarded shapes) ----------------------------------
  // pos: count x 3 physics coordinates, idx: triangles (u4), rgb: count x 3 (u1). A mesh with base "rest" keeps its
  // vertices as given and is placed by an affine map x = A q + b (transformMesh); "lab" vertices are absolute. Lit with
  // a light from the viewer (its colour kept where it faces the viewer); a translucent mesh shows its nearest layer.
  const M3 = new THREE.Matrix4().set(0, 0, 1, 0, 0, 1, 0, 0, -1, 0, 0, 0, 0, 0, 0, 1);  // physics -> three (P2T)
  function setMesh(id, pos, idx, rgb, { label = id, opacity = 1, visible = true } = {}) {
    const n = pos.length / 3, P = new Float32Array(3 * n), C = new Float32Array(3 * n);
    for (let i = 0; i < n; i++) {
      const v = P2T([pos[3 * i], pos[3 * i + 1], pos[3 * i + 2]]);
      P[3 * i] = v.x; P[3 * i + 1] = v.y; P[3 * i + 2] = v.z;
      for (let c = 0; c < 3; c++) C[3 * i + c] = Math.pow(rgb[3 * i + c] / 255, 2.2);  // sRGB -> linear
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(P, 3)); geo.setAttribute("color", new THREE.BufferAttribute(C, 3));
    geo.setIndex(new THREE.BufferAttribute(new Uint32Array(idx), 1));
    geo.computeVertexNormals();
    geo.computeBoundingSphere();
    const mat = litMaterial({ vertexColors: true, side: THREE.DoubleSide, opacity, shade: VALUE_SURFACE });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.matrixAutoUpdate = false; mesh.frustumCulled = false;
    const g = new THREE.Group(); g.add(mesh);
    let twin = null;
    if (opacity < 1) twin = makeTranslucent(mesh);
    g.userData = { mesh, twin };
    addLayer(id, label, g, visible, "mesh");
  }
  function transformMesh(id, A, b) {  // A: 3 x 3 row-major, b: 3 (physics); three = M3 (A q + b)
    const L = S.layers.get(id); if (!L || !L.obj.userData.mesh) return;
    const Am = new THREE.Matrix4().set(A[0], A[1], A[2], b[0], A[3], A[4], A[5], b[1], A[6], A[7], A[8], b[2], 0, 0, 0, 1);
    const m = M3.clone().multiply(Am).multiply(M3.clone().invert());
    for (const o of [L.obj.userData.mesh, L.obj.userData.twin]) if (o) { o.matrix.copy(m); o.matrixWorldNeedsUpdate = true; }
    requestRender();
  }
  function updateMesh(id, pos, rgb) {  // new absolute vertices (and colours) of a "lab" mesh
    const L = S.layers.get(id); if (!L || !L.obj.userData.mesh) return;
    const geo = L.obj.userData.mesh.geometry, P = geo.attributes.position.array, C = geo.attributes.color.array, n = P.length / 3;
    for (let i = 0; i < n; i++) {
      const v = P2T([pos[3 * i], pos[3 * i + 1], pos[3 * i + 2]]);
      P[3 * i] = v.x; P[3 * i + 1] = v.y; P[3 * i + 2] = v.z;
      if (rgb) for (let c = 0; c < 3; c++) C[3 * i + c] = Math.pow(rgb[3 * i + c] / 255, 2.2);
    }
    geo.attributes.position.needsUpdate = true; geo.attributes.color.needsUpdate = true;
    geo.computeVertexNormals(); geo.computeBoundingSphere();
    requestRender();
  }
  // an observer: a marker, its velocity (arrow, length ~ beta) and the lab directions from which the light at its
  // image's border arrives (the field of view as seen in the lab; computed by the run)
  function setObserver(id, { pos, beta, cone }, { label = t("Observer: velocity and field of view (in the lab)") } = {}) {
    let L = S.layers.get(id);
    // sized by the scene: made again when the scene's box changed since (else its size would depend on when the
    // layer was first drawn, not on the time shown)
    if (L && L.obj.userData.size !== (S.size || 1) * 0.012) { removeLayer(id); L = null; }
    if (!L) {
      const g = new THREE.Group(), size = (S.size || 1) * 0.012;
      const ball = new THREE.Mesh(new THREE.SphereGeometry(size, 20, 14), litMaterial({ color: 0xffffff }));
      const vel = arrow3d(new THREE.Vector3(1, 0, 0), new THREE.Vector3(), 1, 0xffd23f);
      const cone_ = new THREE.LineSegments(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: 0x7fb7ff, transparent: true, opacity: 0.55 }));
      cone_.geometry.setAttribute("position", new THREE.BufferAttribute(new Float32Array(0), 3));
      wideFrom(cone_, { width: 1.5, color: 0x7fb7ff, opacity: 0.7 });
      g.add(ball, vel, cone_); g.userData = { ball, vel, cone: cone_, size };
      addLayer(id, label, g, true, "observer"); L = S.layers.get(id);
    }
    const u = L.obj.userData, o = P2T(pos), len = (S.size || 1) * 0.15;
    u.ball.position.copy(o);
    const b = Math.hypot(...beta);
    u.vel.visible = b > 1e-9;
    if (b > 1e-9) { u.vel.position.copy(o); u.vel.setDirection(P2T(beta).normalize()); u.vel.setLength(len * (0.3 + b), 0.2 * len, 0.1 * len); }
    const pts = [];
    const n = (cone || []).length, R = (S.size || 1) * 0.25;
    for (let i = 0; i < n; i++) {
      const a = o.clone().add(P2T(cone[i]).normalize().multiplyScalar(R)), c = o.clone().add(P2T(cone[(i + 1) % n]).normalize().multiplyScalar(R));
      pts.push(o, a, a, c);
    }
    const ca = u.cone.geometry.attributes.position;
    if (ca && ca.count === pts.length) { for (let i = 0; i < pts.length; i++) ca.setXYZ(i, pts[i].x, pts[i].y, pts[i].z); ca.needsUpdate = true; }
    else { u.cone.geometry.dispose(); u.cone.geometry = new THREE.BufferGeometry().setFromPoints(pts); }
    syncWide(u.cone, 0);
    requestRender();
  }

  // a translucent box with its edges and a label: e.g. an observer, a which-path detector in a slit (v11). Physics
  // centre (x, y, z) and size (sx, sy, sz); three's axes are (z, y, -x)
  function boxObj(o) {
    const [sx, sy, sz] = o.size, c = P2T(o.center || [0, 0, 0]), color = new THREE.Color(o.color || "#ff8a1f");
    const g = new THREE.Group(), geo = new THREE.BoxGeometry(sz, sy, sx);
    const m = new THREE.Mesh(geo, litMaterial({ color, opacity: o.opacity ?? 0.3, side: THREE.DoubleSide, shade: VALUE_SURFACE }));
    const e = new THREE.LineSegments(new THREE.EdgesGeometry(geo), new THREE.LineBasicMaterial({ color }));
    m.position.copy(c); e.position.copy(c); addTranslucent(g, m); g.add(e);
    if (o.text) {
      const s = labelSprite(o.text, o.color || "#ff8a1f", 16, [0.5, -0.3]);
      s.position.copy(c.clone().add(P2T(S.axes.U).multiplyScalar(0.5 * Math.abs(vdot(S.axes.U, [sx, sy, sz]))))); g.add(s);
    }
    return g;
  }

  function buildObject(o) {
    if (o.kind === "plate") return plate(o);
    if (o.kind === "box") return boxObj(o);
    if (o.kind === "target") return imagePlane(o, 2, 2, null);
    if (o.kind === "incident") return incident(o);
    if (o.kind === "disk") return disk(o);
    if (o.kind === "sphere") return sphere(o);
    if (o.kind === "point") return point(o);
    if (o.kind === "panel") return panelObj(o);
    return null;
  }

  // the scene of a world. opts.plane2d: the axis (0, 1, 2) normal to a 2-D world's plane, declared by its view; such a
  // world opens looking at its plane from above (A3)
  function setScene(desc, { plane2d = null } = {}) {
    // a copy: setBox and setObject change the scene's description, and the header the player keeps must stay as recorded
    // (a view rebuilt at an earlier time would otherwise start from the box and the objects of a later one)
    desc = structuredClone(desc);
    S.desc = desc; setBoxState(desc.box);
    S.plane2d = Number.isInteger(plane2d) ? plane2d : null;
    S.paths = new Map();
    S.frameAxes = null;
    S.volTau0 = null;  // a new world: its volume's start look is taken again
    S.tracks = new Map();
    for (const L of S.layers.values()) { scene.remove(L.obj); disposeTree(L.obj); }
    S.layers.clear();
    setUp(desc.up || [0, 1, 0]);
    if (S.plane2d !== null) { const D = presetDirs(); S.frameAxes = { R: vunit(vcross(D.top[1], D.top[0])), U: D.top[1], F: D.top[0] }; }
    if (S.frame) { scene.remove(S.frame); disposeTree(S.frame); }
    S.frame = buildFrame(desc.box, desc.units || "", desc.coord_names);
    scene.add(S.frame);
    for (const o of desc.objects || []) {
      const obj = buildObject(o);
      if (obj) addLayer(o.id, o.label, obj, o.visible !== false);
    }
    S.layerDefaults = Object.fromEntries((desc.layers || []).map((l) => [l.id, l]));
    const views = desc.views || defaultViews();
    if (JSON.stringify(views) !== JSON.stringify(S.viewDefs)) { S.viewDefs = views; buildTools(S.extraTools); }
    updateHint();
    // the same scene rebuilt (the player rebuilds it from the record when the history goes back): keep the camera
    const boxKey = JSON.stringify(desc.box);
    if (boxKey !== S.boxKey || !S.fitted) { S.boxKey = boxKey; S.fitted = root.clientWidth > 0; view(S.viewDefs[0][0]); }
    updateLegend();
  }
  function setBoxState(box) {
    S.box = box;
    S.size = Math.max(...[0, 1, 2].map((i) => box[1][i] - box[0][i]));
    S.boxCenterT = P2T([0, 1, 2].map((i) => (box[0][i] + box[1][i]) / 2));
    S.boxRadius = 0.5 * Math.hypot(...[0, 1, 2].map((i) => box[1][i] - box[0][i])) || 1;
  }

  // a world whose region grows as its consequences are revealed (e.g. v09's trajectory) widens the box: the frame is
  // rebuilt; the camera follows only while the experimenter has not moved it, and an unchanged box changes nothing
  // (review UX-3d A7, UX-ui U1: the playground repeats its box at every record segment)
  function setBox(box) {
    if (S.box && JSON.stringify(box) === JSON.stringify(S.box)) return;
    S.desc.box = box; setBoxState(box);
    if (S.frame) { scene.remove(S.frame); disposeTree(S.frame); }
    S.frame = buildFrame(box, S.desc.units || "", S.desc.coord_names); scene.add(S.frame);
    if (!S.userMoved) refit();
    else showNote(t("The region grew — F: show the content, Shift+F: the whole region"));
    requestRender();
  }
  let noteT = null;
  function showNote(text) {
    note.textContent = text; note.style.display = "";
    clearTimeout(noteT); noteT = setTimeout(() => { note.style.display = "none"; }, 9000);
  }

  function setObjectImage(id, nx, ny, data) {
    const L = S.layers.get(id); if (!L) return;
    const old = L.obj, o = (S.desc.objects || []).find((q) => q.id === id);
    const mesh = imagePlane(o, nx, ny, data);
    addLayer(id, L.label, mesh, L.visible);
    old.geometry && old.geometry.dispose();
  }

  // --- the computed volume (ray marching) ----------------------------------------------------------------------------
  // data: Float32 values 0..1 of the peak (index iz·nx·ny + ix·ny + iy), or {amp8: true}: Uint8 amplitudes
  // √(value)·255 (the clouds of v13/v14 as sent): then a new phase is painted through a 256-entry table (A17).
  // The start look's optical depth τ (A10), fixed for the world at its first volume: `tau` (the caller's), else the
  // header's look.tau, else the header's look.density (the old density per length unit, 0.6 if none) times the
  // densest column of this first volume — the look the world was tuned to, now one τ for all its later volumes
  function setVolume(id, dims, data, { amp8 = false, tau = undefined } = {}) {
    const [nz, nx, ny] = dims;
    S.vol = { dims, data, amp8 };
    const bytes = new Uint8Array(nz * nx * ny);
    const tex = new THREE.Data3DTexture(bytes, ny, nx, nz);
    tex.format = THREE.RedFormat; tex.type = THREE.UnsignedByteType;
    tex.minFilter = THREE.LinearFilter; tex.magFilter = THREE.LinearFilter; tex.unpackAlignment = 1;
    S.volTex = tex;
    const [lo, hi] = S.box;
    const a = P2T(lo), b = P2T(hi);
    const mn = new THREE.Vector3(Math.min(a.x, b.x), Math.min(a.y, b.y), Math.min(a.z, b.z));
    const mx = new THREE.Vector3(Math.max(a.x, b.x), Math.max(a.y, b.y), Math.max(a.z, b.z));
    S.volBox = { mn, mx, lo: [...lo], hi: [...hi] };
    const geo = new THREE.BoxGeometry(mx.x - mn.x, mx.y - mn.y, mx.z - mn.z);
    const U = { uVol: { value: tex }, uLut: { value: lut }, uMin: { value: mn }, uMax: { value: mx },
                uCMin: { value: mn.clone() }, uCMax: { value: mx.clone() },
                uCam: { value: camera.position.clone() }, uFwd: { value: new THREE.Vector3(0, 0, -1) },
                uDensity: { value: 4.0 }, uNorm: { value: 1.0 }, uThreshold: { value: 0.02 }, uSteps: { value: S.fullSteps },
                uDepthA: { value: rtA.depthTexture }, uDepthB: { value: rtB.depthTexture }, uRes: { value: new THREE.Vector2(1, 1) },
                uNear: { value: camera.near }, uFar: { value: camera.far }, uUseDepth: { value: 0 }, uDiag: { value: mx.distanceTo(mn) } };
    // two parts of one march: behind the nearest translucent surface (before the translucent objects) and in front of it
    const mk = (part, order) => {
      const mat = new THREE.ShaderMaterial({
        glslVersion: THREE.GLSL3, vertexShader: VOL_VERT, fragmentShader: VOL_FRAG, side: THREE.BackSide,
        transparent: true, depthWrite: false, depthTest: false, premultipliedAlpha: true,
        uniforms: { ...U, uPart: { value: part } } });
      const m = new THREE.Mesh(geo, mat);
      m.position.copy(mn.clone().add(mx).multiplyScalar(0.5));
      m.renderOrder = order; m.layers.set(L_VOLUME); m.frustumCulled = false;
      return m;
    };
    const back = mk(1, 1), front = mk(0, 3);
    back.visible = false;
    const g = new THREE.Group(); g.add(back, front);
    g.userData = { back, front };
    S.volMat = front.material;
    const d = S.layerDefaults?.[id] || {};
    if (d.look && d.look.threshold !== undefined) U.uThreshold.value = d.look.threshold;
    paintVolume(true);
    if (S.volTau0 === null || S.volTau0 === undefined) {
      const legacy = d.look && d.look.density !== undefined ? d.look.density : 0.6;
      S.volTau0 = Math.min(40, Math.max(0.3, tau ?? d.look?.tau ?? legacy / U.uNorm.value));
    }
    U.uDensity.value = S.volTau0;
    if (S.userLook) setVolumeLook(S.userLook);  // the experimenter's look survives a rebuilt scene
    addLayer(id, d.label || id, g, d.visible !== false, "volume");
    for (const P of S.planes.values()) P.mat.uniforms.uVol.value = tex, Object.assign(P.mat.uniforms.uMin, { value: mn }), Object.assign(P.mat.uniforms.uMax, { value: mx });
  }
  // the volume's texture on the current scale; renorm: the normalisation of its density (the densest column along a box
  // axis) taken again — on a new volume or a new scale, not on a new phase of the same volume (phases on one scale)
  function paintVolume(renorm = false, repaint = true) {
    if (!S.vol || !S.volTex) return;
    const [nz, nx, ny] = S.vol.dims, src = S.vol.data, dst = S.volTex.image.data;
    let sq;  // the displayed value's square per byte (for the column integrals)
    if (!repaint) { /* the texture as it is: only its box above the threshold again */ }
    else if (S.vol.amp8) {
      const tab = new Uint8Array(256);
      for (let a = 0; a < 256; a++) { const v = transfer((a / 255) * (a / 255), S.scale, S.floor); tab[a] = Math.round(255 * (v || 0)); }
      if (S.scale === "sqrt") dst.set(src); else for (let i = 0; i < src.length; i++) dst[i] = tab[src[i]];
    } else {
      for (let i = 0; i < src.length; i++) { const v = transfer(src[i], S.scale, S.floor); dst[i] = Math.round(255 * (v || 0)); }
    }
    sq = new Float32Array(256); for (let a = 0; a < 256; a++) sq[a] = (a / 255) * (a / 255);
    // one pass: the box of the voxels above the threshold (the march skips the rest, so it is clipped to it) and, when
    // asked, the column integrals (all voxels)
    const [lo, hi] = S.volBox ? [S.volBox.lo, S.volBox.hi] : S.box;
    const tb = S.volMat ? Math.floor(255 * S.volMat.uniforms.uThreshold.value) : 0;
    const dz = (hi[2] - lo[2]) / nz, dx = (hi[0] - lo[0]) / nx, dy = (hi[1] - lo[1]) / ny;
    let z0 = nz, z1 = -1, x0 = nx, x1 = -1, y0 = ny, y1 = -1;
    const colZ = renorm ? new Float32Array(nx * ny) : null, colX = renorm ? new Float32Array(nz * ny) : null, colY = renorm ? new Float32Array(nz * nx) : null;
    let i = 0;
    for (let iz = 0; iz < nz; iz++) for (let ix = 0; ix < nx; ix++) {
      let rowY = 0;
      for (let iy = 0; iy < ny; iy++, i++) {
        const b = dst[i];
        if (!b) continue;
        if (renorm) { const s = sq[b]; colZ[ix * ny + iy] += s; colX[iz * ny + iy] += s; rowY += s; }
        if (b <= tb) continue;
        if (iz < z0) z0 = iz; if (iz > z1) z1 = iz; if (ix < x0) x0 = ix; if (ix > x1) x1 = ix; if (iy < y0) y0 = iy; if (iy > y1) y1 = iy;
      }
      if (renorm) colY[iz * nx + ix] = rowY;
    }
    if (repaint) S.volTex.needsUpdate = true;
    const U = S.volMat && S.volMat.uniforms;
    if (!U) return;
    if (renorm) {
      let mz = 0, mxx = 0, my = 0;
      for (const v of colZ) if (v > mz) mz = v; for (const v of colX) if (v > mxx) mxx = v; for (const v of colY) if (v > my) my = v;
      const col = Math.max(mz * dz, mxx * dx, my * dy);
      U.uNorm.value = col > 0 ? 1 / col : 1;
    }
    // the content box (one voxel of margin) in three's coordinates
    if (z1 < 0) { U.uCMin.value.copy(U.uMin.value); U.uCMax.value.copy(U.uMin.value); return; }
    const pl = [lo[0] + (x0 - 1) * dx, lo[1] + (y0 - 1) * dy, lo[2] + (z0 - 1) * dz], ph = [lo[0] + (x1 + 2) * dx, lo[1] + (y1 + 2) * dy, lo[2] + (z1 + 2) * dz];
    const a = P2T(pl), b = P2T(ph);
    U.uCMin.value.set(Math.min(a.x, b.x), Math.min(a.y, b.y), Math.min(a.z, b.z));
    U.uCMax.value.set(Math.max(a.x, b.x), Math.max(a.y, b.y), Math.max(a.z, b.z));
    U.uDiag.value = U.uCMax.value.clone().min(U.uMax.value).distanceTo(U.uCMin.value.clone().max(U.uMin.value));
  }
  // new values of the volume already shown, same dims (e.g. the phases of a superposition, v13/v14): the texture and
  // the mesh are kept (setVolume builds new ones); false when there is no such volume
  function updateVolume(id, data, { amp8 = false } = {}) {
    if (!S.vol || !S.volTex || S.vol.data.length !== data.length || S.vol.amp8 !== amp8 || !S.layers.has(id)) return false;
    S.vol = { dims: S.vol.dims, data, amp8 }; paintVolume(false); requestRender();
    return true;
  }
  function setVolumeLook({ density, threshold }, user = false) {
    if (user) S.userLook = { ...S.userLook, ...(density !== undefined ? { density } : {}), ...(threshold !== undefined ? { threshold } : {}) };
    if (!S.volMat) return;
    if (density !== undefined) S.volMat.uniforms.uDensity.value = density;
    if (threshold !== undefined && threshold !== S.volMat.uniforms.uThreshold.value) {
      S.volMat.uniforms.uThreshold.value = threshold;
      if (S.vol && S.volTex) paintVolume(false, false);  // the box of the voxels above the threshold again
    }
    requestRender();
  }
  // the volume's value (a fraction of the peak) at a physics point (trilinear), for previews while a plane is dragged
  function volAt(i) { const d = S.vol.data; if (!S.vol.amp8) return d[i]; const a = d[i] / 255; return a * a; }
  function sampleVolume(p) {
    if (!S.vol) return NaN;
    const [nz, nx, ny] = S.vol.dims, [lo, hi] = S.volBox ? [S.volBox.lo, S.volBox.hi] : S.box;
    const fz = (p[2] - lo[2]) / (hi[2] - lo[2]) * (nz - 1), fx = (p[0] - lo[0]) / (hi[0] - lo[0]) * (nx - 1), fy = (p[1] - lo[1]) / (hi[1] - lo[1]) * (ny - 1);
    if (fz < 0 || fx < 0 || fy < 0 || fz > nz - 1 || fx > nx - 1 || fy > ny - 1) return NaN;
    const iz = Math.min(nz - 2, Math.floor(fz)), ix = Math.min(nx - 2, Math.floor(fx)), iy = Math.min(ny - 2, Math.floor(fy));
    const wz = fz - iz, wx = fx - ix, wy = fy - iy;
    let s = 0;
    for (const [dz, az] of [[0, 1 - wz], [1, wz]]) for (const [dxi, ax] of [[0, 1 - wx], [1, wx]]) for (const [dy, ay] of [[0, 1 - wy], [1, wy]])
      s += az * ax * ay * volAt((iz + dz) * nx * ny + (ix + dxi) * ny + (iy + dy));
    return s;
  }

  // --- vector glyphs (e.g. the energy current): lit arrows (shaft and cone), updated in place when their number is kept --
  function setVectors(id, pos, vec) {
    const N = pos.length / 3;
    let mmax = 0;
    for (let i = 0; i < N; i++) mmax = Math.max(mmax, Math.hypot(vec[3 * i], vec[3 * i + 1], vec[3 * i + 2]));
    const [lo, hi] = S.box;
    const cell = Math.max(hi[0] - lo[0], hi[1] - lo[1]) / 16;
    const L0 = S.layers.get(id);
    let mesh = L0 && L0.obj.isInstancedMesh && L0.obj.count === N && L0.obj.userData.glyphs ? L0.obj : null;
    const fresh = !mesh;
    if (fresh) {
      mesh = new THREE.InstancedMesh(GLYPH_GEO, litMaterial({ color: 0xffffff }), N);
      mesh.userData = { glyphs: true, threshold: 0.03 };
    }
    Object.assign(mesh.userData, { pos, vec, mmax, cell });
    const m = new THREE.Matrix4(), q = new THREE.Quaternion(), up = new THREE.Vector3(0, 1, 0), col = new THREE.Color();
    const apply = () => {
      const { pos, vec, mmax, cell } = mesh.userData, thr = mesh.userData.threshold;
      for (let i = 0; i < N; i++) {
        const v = P2T([vec[3 * i], vec[3 * i + 1], vec[3 * i + 2]]), mag = v.length() / (mmax || 1);
        const L = mag > thr ? cell * 0.95 * Math.sqrt(mag) : 0;
        q.setFromUnitVectors(up, v.lengthSq() ? v.clone().normalize() : up);
        m.compose(P2T([pos[3 * i], pos[3 * i + 1], pos[3 * i + 2]]), q, new THREE.Vector3(L, L, L));
        mesh.setMatrixAt(i, m);
        const c = Math.round(255 * Math.sqrt(mag));
        col.setRGB(LUT[3 * c] / 255, LUT[3 * c + 1] / 255, LUT[3 * c + 2] / 255, THREE.SRGBColorSpace);
        mesh.setColorAt(i, col);
      }
      mesh.instanceMatrix.needsUpdate = true; if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
      mesh.boundingSphere = null; mesh.boundingBox = null;
      requestRender();
    };
    mesh.userData.apply = apply; apply();
    if (fresh) {
      const d = S.layerDefaults?.[id] || {};
      addLayer(id, d.label || id, mesh, d.visible === true, "vectors");
    }
  }
  function setVectorThreshold(id, thr) { const L = S.layers.get(id); if (L?.obj.userData.apply) { L.obj.userData.threshold = thr; L.obj.userData.apply(); } }

  // --- slice planes --------------------------------------------------------------------------------------------------
  function planeMaterial(id) {
    const [lo, hi] = S.box || [[0, 0, 0], [1, 1, 1]];
    const mn = S.volBox?.mn || P2T(lo), mx = S.volBox?.mx || P2T(hi);
    return new THREE.ShaderMaterial({
      glslVersion: THREE.GLSL3, vertexShader: PLANE_VERT, fragmentShader: PLANE_FRAG, side: THREE.DoubleSide,
      transparent: false, depthWrite: true,
      uniforms: { uTex: { value: new THREE.DataTexture(new Uint8Array(4), 1, 1) }, uVol: { value: S.volTex || new THREE.Data3DTexture(new Uint8Array(1), 1, 1, 1) },
                  uLut: { value: lut }, uMin: { value: mn }, uMax: { value: mx }, uMode: { value: 2 },
                  uHighlight: { value: 0 }, uColor: { value: new THREE.Color(PLANE_COLORS[id]) }, uOpacity: { value: 1 }, uDim: { value: 1 } } });
  }
  function ensurePlane(id) {
    if (S.planes.has(id)) return S.planes.get(id);
    const group = new THREE.Group();
    const mat = planeMaterial(id);
    const rect = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), mat); rect.userData.planeId = id;
    const outline = new THREE.LineLoop(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: PLANE_COLORS[id] }));
    const arrow = arrow3d(new THREE.Vector3(0, 0, 1), new THREE.Vector3(), 1, new THREE.Color(PLANE_COLORS[id]).getHex());
    const tag = labelSprite(String(id), PLANE_COLORS[id], 20, [0.5, 0.5]);
    updateLabelScale(tag);
    group.add(rect, outline, arrow, tag);
    scene.add(group);
    const P = { id, group, rect, outline, arrow, tag, mat, visible: true, data: null };
    S.planes.set(id, P);
    layersChanged();
    return P;
  }
  function placePlane(P, origin, u, v, n, poly) {
    P.origin = origin; P.u = u; P.v = v; P.n = n;
    P.group.position.copy(P2T(origin));
    P.group.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(P2T(u), P2T(v), P2T(n)));
    P.poly = poly;
    if (poly.length >= 3) {
      P.outline.geometry.dispose();
      P.outline.geometry = new THREE.BufferGeometry().setFromPoints(poly.map(([s, tt]) => new THREE.Vector3(s, tt, 0)));
      const ss = poly.map((q) => q[0]), ts = poly.map((q) => q[1]);
      P.rectST = [Math.min(...ss), Math.max(...ss), Math.min(...ts), Math.max(...ts)];
    }
    const size = S.box ? Math.max(...[0, 1, 2].map((i) => S.box[1][i] - S.box[0][i])) : 1;
    P.arrow.setLength(0.12 * size, 0.04 * size, 0.025 * size);
    const [s0, s1, t0, t1] = P.rectST || [-1, 1, -1, 1];
    P.tag.position.set(s1, t1, 0);
  }
  function fitRect(P, st) {  // st = [s0, s1, t0, t1] of the image on the plane
    const [s0, s1, t0, t1] = st;
    P.rect.scale.set(Math.max(s1 - s0, 1e-6), Math.max(t1 - t0, 1e-6), 1);
    P.rect.position.set((s0 + s1) / 2, (t0 + t1) / 2, 0);
  }
  function setPlanes(list) {
    const ids = new Set(list.map((p) => p.id));
    for (const [id, P] of S.planes) if (!ids.has(id)) {
      if (gizmo.object === P.group) gizmo.detach();
      scene.remove(P.group); P.mat.uniforms.uVol.value = null; disposeTree(P.group); S.planes.delete(id);
    }
    for (const p of list) {
      const P = ensurePlane(p.id);
      P.meta = p;
      if (!S.dragging || gizmo.object !== P.group) {
        placePlane(P, p.origin, p.u, p.v, p.normal, p.polygon);
        if (!P.data) { fitRect(P, P.rectST); P.mat.uniforms.uMode.value = S.volTex ? 1 : 2; }
      }
    }
    if (S.selected && !S.planes.has(S.selected)) select(null);
    layersChanged(); updateLegend(); requestRender();
  }
  function setPlaneImage(id, meta, I, phase) {
    const P = ensurePlane(id);
    const col = meta.approximation ? "#ff3b3b" : PLANE_COLORS[id];  // an approximate slice: red, as in its window
    P.outline.material.color.set(col); P.mat.uniforms.uColor.value.set(col);
    const [ns, nt] = [meta.s[2], meta.tt[2]];
    P.data = { meta, I, phase, ns, nt };
    paintPlane(P);
    fitRect(P, [meta.s[0], meta.s[1], meta.tt[0], meta.tt[1]]);
    P.mat.uniforms.uMode.value = 0;
    updateLegend();
    requestRender();
  }
  function paintPlane(P) {
    if (!P.data) return;
    const { I, ns, nt } = P.data;
    let tex = P.mat.uniforms.uTex.value;
    if (!tex.image || tex.image.width !== ns || tex.image.height !== nt) {
      tex.dispose();
      tex = new THREE.DataTexture(new Uint8Array(ns * nt * 4), ns, nt, THREE.RGBAFormat);
      tex.magFilter = THREE.LinearFilter; tex.minFilter = THREE.LinearFilter;
      P.mat.uniforms.uTex.value = tex;
    }
    const d = tex.image.data;
    for (let i = 0; i < ns * nt; i++) {
      const v = transfer(I[i], S.scale, S.floor);
      if (!(v >= 0)) { d[4 * i + 3] = 0; continue; }
      const c = Math.round(255 * v);
      d[4 * i] = LUT[3 * c]; d[4 * i + 1] = LUT[3 * c + 1]; d[4 * i + 2] = LUT[3 * c + 2]; d[4 * i + 3] = 255;
    }
    tex.needsUpdate = true;
  }
  function setPlaneVisible(id, on) { const P = S.planes.get(id); if (P) { P.visible = on; P.group.visible = on; updateLegend(); requestRender(); } }

  function gizmoHandles() {  // review C10: in-plane moves and the roll about the normal do not change the plane
    if (gizmo.mode === "translate") { gizmo.showX = false; gizmo.showY = false; gizmo.showZ = true; }
    else { gizmo.showX = true; gizmo.showY = true; gizmo.showZ = false; gizmo.showXYZE = false; }
  }
  gizmoHandles();

  function planeLook() {  // highlighted / selected planes: a border; the others darker while one is pointed at
    for (const P of S.planes.values()) {
      const on = P.id === S.selected || P.id === S.highlighted;
      P.mat.uniforms.uHighlight.value = on ? 1 : 0;
      P.mat.uniforms.uDim.value = S.highlighted && P.id !== S.highlighted ? 0.5 : 1;
      P.tag.material.depthTest = !(P.id === S.selected);  // the selected plane's number is seen through everything
    }
  }
  function select(id) {
    S.selected = id;
    planeLook();
    if (id && S.planes.has(id) && !readOnly()) gizmo.attach(S.planes.get(id).group); else gizmo.detach();
    onSelect && onSelect(id);
    requestRender();
  }
  function highlight(id) {
    S.highlighted = id;
    planeLook();
    requestRender();
  }

  // gizmo: moving a plane by hand; while dragging, the plane shows the volume (a preview) and the window a preview
  gizmo.addEventListener("dragging-changed", (e) => {
    orbit.enabled = !e.value;
    S.dragging = e.value;
    const P = [...S.planes.values()].find((q) => q.group === gizmo.object);
    if (!P) return;
    if (e.value) { P.mat.uniforms.uMode.value = S.volTex ? 1 : 2; requestRender(); return; }
    const { origin, normal } = groupPose(P);
    onPlaneEdit && onPlaneEdit(P.id, { origin, normal });
  });
  gizmo.addEventListener("objectChange", () => {
    const P = [...S.planes.values()].find((q) => q.group === gizmo.object);
    if (!P || !S.box) return;
    const { origin, normal } = groupPose(P);
    const ax = horizontalAxes(normal);
    const poly = planeBox(origin, ax.n, ax.u, ax.v, S.box);
    if (poly.length < 3) return;
    // keep the group's pose (the gizmo drives it); redraw the cut in the group's own axes
    const gu = T2P(new THREE.Vector3(1, 0, 0).applyQuaternion(P.group.quaternion)), gv = T2P(new THREE.Vector3(0, 1, 0).applyQuaternion(P.group.quaternion));
    const polyG = planeBox(origin, ax.n, gu, gv, S.box);
    P.outline.geometry.dispose();
    P.outline.geometry = new THREE.BufferGeometry().setFromPoints(polyG.map(([s, tt]) => new THREE.Vector3(s, tt, 0)));
    const ss = polyG.map((q) => q[0]), ts = polyG.map((q) => q[1]);
    fitRect(P, [Math.min(...ss), Math.max(...ss), Math.min(...ts), Math.max(...ts)]);
    onPlaneMoving && onPlaneMoving(P.id, { origin, normal: ax.n, u: ax.u, v: ax.v, poly });
  });
  function groupPose(P) {  // the plane as the gizmo left it; the run takes its point closest to the box centre
    const o = T2P(P.group.position.clone());
    const n = T2P(new THREE.Vector3(0, 0, 1).applyQuaternion(P.group.quaternion));
    return { origin: o, normal: n };
  }

  // picking: a click on a plane selects it, on empty space deselects; a double click puts the centre of rotation on the
  // point under the pointer (a surface, a sphere, a plane, or the volume's densest point along the ray; A6)
  let down = null;
  const ndcOf = (e) => { const r = canvas.getBoundingClientRect(); return new THREE.Vector2((e.clientX - r.left) / r.width * 2 - 1, -(e.clientY - r.top) / r.height * 2 + 1); };
  canvas.addEventListener("pointerdown", (e) => { down = [e.clientX, e.clientY]; });
  canvas.addEventListener("pointerup", (e) => {
    if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 4 || S.dragging || gizmo.dragging) { down = null; return; }
    down = null;
    const ray = new THREE.Raycaster();
    ray.setFromCamera(ndcOf(e), camera);
    const hits = ray.intersectObjects([...S.planes.values()].filter((P) => P.visible).map((P) => P.rect));
    select(hits.length ? hits[0].object.userData.planeId : null);
    root.dispatchEvent(new CustomEvent("s3dclick", { detail: { plane: hits.length ? hits[0].object.userData.planeId : null } }));
  });

  // --- direct manipulation of a world's objects (plan P16.2): a manipulator (the playground's) takes a gesture that
  // starts on one of its objects before the camera's controls see it, so that the camera never fights a drag; any
  // other gesture (on empty space, on a plane's gizmo) is the camera's or the gizmo's as before. The manipulator gives
  // down(e) -> true to take the gesture, move(e), up(e), cancel(), hover(e) -> a cursor for the pointer over the view.
  let manip = null, gest = null;
  root.addEventListener("pointerdown", (e) => {
    if (!manip || e.button !== 0 || e.target !== canvas || gizmo.dragging || gizmo.axis) return;
    if (!manip.down(e)) return;
    gest = { id: e.pointerId };
    e.stopPropagation(); e.preventDefault();
    // the press no longer moves the focus (its default is prevented): a field left focused would take the keys (Esc,
    // Delete) meant for the object
    const a = document.activeElement;
    if (a && a !== document.body && /^(INPUT|SELECT|TEXTAREA)$/.test(a.tagName)) a.blur();
    orbit.enabled = false;
    try { canvas.setPointerCapture(e.pointerId); } catch (err) { /* a synthetic pointer */ }
  }, true);
  canvas.addEventListener("pointermove", (e) => {
    if (gest) { manip.move(e); return; }
    if (manip && !e.buttons && manip.hover) { const c = manip.hover(e) || ""; if (canvas.style.cursor !== c) canvas.style.cursor = c; }
  });
  function endGesture(e, cancelled) {
    if (!gest) return;
    gest = null;
    orbit.enabled = !S.dragging;
    try { canvas.releasePointerCapture(e.pointerId); } catch (err) { /* released already */ }
    if (cancelled) manip.cancel(); else manip.up(e);
  }
  canvas.addEventListener("pointerup", (e) => { if (gest) { e.stopImmediatePropagation(); endGesture(e, false); } }, true);
  canvas.addEventListener("pointercancel", (e) => endGesture(e, true), true);
  function setManipulator(m) { manip = m || null; if (!manip) canvas.style.cursor = ""; }

  // the eye ray under a screen point (client px) in physics coordinates, and the length of one CSS pixel at a point
  function rayAt(x, y) {
    const r = canvas.getBoundingClientRect(), ray = new THREE.Raycaster();
    ray.setFromCamera(new THREE.Vector2((x - r.left) / r.width * 2 - 1, -(y - r.top) / r.height * 2 + 1), camera);
    return { origin: T2P(ray.ray.origin), dir: T2P(ray.ray.direction) };
  }
  function pixelSize(p) {
    camera.updateMatrixWorld();
    const fwd = new THREE.Vector3(); camera.getWorldDirection(fwd);
    const d = Math.max(P2T(p).sub(camera.position).dot(fwd), camera.near);
    return 2 * d * Math.tan(camera.fov * Math.PI / 360) / Math.max(1, canvas.clientHeight || root.clientHeight || 1);
  }

  // --- the experimenter's markers (not layers of the world: never in «Слои сцены», never in the key frames): the
  // selected object (a ring and its name) and the ghost of a drag (a dashed ring, a line from where the object was, the
  // throw's velocity as an arrow, the axis of an axis-bound drag). spec: {pos, radius, color, text, ghost, from, vel,
  // axis: [p0, p1]}; null removes it
  const markers = new Map();
  const ringTex = { solid: null, dashed: null };
  function dropMarker(id) {
    const M = markers.get(id); if (!M) return;
    scene.remove(M.group);
    M.group.traverse((o) => { if (o.geometry && !o.geometry.userData.shared) o.geometry.dispose(); if (o.material) { if (o.material.map && !o.material.map.userData.ring) o.material.map.dispose(); o.material.dispose(); } });
    markers.delete(id);
  }
  function overLayer(o) { o.traverse((q) => { q.layers.set(L_OVER); q.renderOrder = 30; if (q.material) { q.material.depthTest = false; q.material.depthWrite = false; q.material.transparent = true; } }); return o; }
  function setMarker(id, spec) {
    dropMarker(id);
    if (!spec || !spec.pos) { requestRender(); return; }
    const g = new THREE.Group(), c = P2T(spec.pos), color = new THREE.Color(spec.color || "#ffe066");
    const key = spec.ghost ? "dashed" : "solid";
    if (!ringTex[key]) { ringTex[key] = ringTexture(spec.ghost); ringTex[key].userData.ring = true; }
    const ring = new THREE.Sprite(new THREE.SpriteMaterial({ map: ringTex[key], color, sizeAttenuation: true }));
    ring.position.copy(c); g.add(ring);
    let label = null;
    if (spec.text) { label = labelSprite(spec.text, spec.color || "#ffe066", 15, [0.5, -0.35], true); label.position.copy(c); updateLabelScale(label); g.add(label); }
    const line = (pts, dashed) => {
      const geo = new THREE.BufferGeometry().setFromPoints(pts.map((q) => P2T(q)));
      const L = new THREE.Line(geo, dashed ? new THREE.LineDashedMaterial({ color, dashSize: (S.size || 1) * 0.015, gapSize: (S.size || 1) * 0.01 })
                                            : new THREE.LineBasicMaterial({ color }));
      if (dashed) L.computeLineDistances();
      g.add(L);
    };
    if (spec.from) line([spec.from, spec.pos], true);
    if (spec.axis) line(spec.axis, true);
    if (spec.vel && Math.hypot(...spec.vel) > 0) {
      const v = P2T(spec.vel), len = v.length();
      g.add(new THREE.ArrowHelper(v.clone().normalize(), c, len, color.getHex(), Math.min(0.3 * len, (S.size || 1) * 0.05), Math.min(0.15 * len, (S.size || 1) * 0.025)));
    }
    overLayer(g);
    scene.add(g);
    markers.set(id, { group: g, ring, label, c: c.clone(), c0: c.clone(), r: Math.max(0, +spec.radius || 0), spec });
    requestRender();
  }
  // a marker moved as a whole (the selected object moves with the world's time: nothing is rebuilt)
  function moveMarker(id, pos, radius) {
    const M = markers.get(id); if (!M || !pos) return false;
    const c = P2T(pos);
    M.group.position.copy(c).sub(M.c0);
    M.c.copy(c);
    if (radius !== undefined) M.r = Math.max(0, +radius || 0);
    requestRender();
    return true;
  }
  // a marker's ring: at least 11 px across its radius, a little wider than the object; its name above it
  function updateMarkers() {
    for (const M of markers.values()) {
      const px = pixelSize(T2P(M.c)), R = Math.max(1.25 * M.r, 11 * px);
      M.ring.scale.set(2 * R, 2 * R, 1);
      if (M.label) M.label.position.copy(M.c0).add(camera.up.clone().multiplyScalar(R * 1.05));
    }
  }
  canvas.addEventListener("dblclick", (e) => {
    const p = pickPoint(ndcOf(e));
    if (p) centerOnT(p);
  });
  const visibleChain = (o) => { for (let p = o; p; p = p.parent) if (!p.visible) return false; return true; };
  function pickPoint(ndc) {
    const ray = new THREE.Raycaster(); ray.layers.enableAll();
    ray.setFromCamera(ndc, camera);
    const cands = [];
    for (const L of S.layers.values()) {
      if (!L.visible || L.kind === "volume") continue;
      L.obj.traverse((o) => { if (o.isMesh && !o.isInstancedMesh && !o.userData.twin && o.material && o.material.visible !== false && visibleChain(o)) cands.push(o); });
    }
    for (const P of S.planes.values()) if (P.visible) cands.push(P.rect);
    let best = Infinity, hit = null;
    for (const h of ray.intersectObjects(cands, false)) if (h.distance < best) { best = h.distance; hit = h.point.clone(); }
    // sphere impostors: the exact ray-sphere intersection per instance
    const m = new THREE.Matrix4(), c = new THREE.Vector3(), s = new THREE.Vector3(), qq = new THREE.Quaternion();
    for (const L of S.layers.values()) {
      if (!L.visible || L.kind !== "spheres") continue;
      const mesh = L.obj;
      for (let i = 0; i < mesh.count; i++) {
        mesh.getMatrixAt(i, m); m.decompose(c, qq, s);
        const r = s.x, oc = ray.ray.origin.clone().sub(c), b = oc.dot(ray.ray.direction), cc = oc.lengthSq() - r * r, h = b * b - cc;
        if (h < 0) continue;
        const tt = -b - Math.sqrt(h);
        if (tt > 0 && tt < best) { best = tt; hit = ray.ray.at(tt, new THREE.Vector3()); }
      }
    }
    if (hit) return hit;
    // the volume: its densest point along the ray inside the box (above the threshold)
    const vol = volumeLayer();
    if (vol && S.vol && S.volBox) {
      const box = new THREE.Box3(S.volBox.mn, S.volBox.mx), a = new THREE.Vector3(), bpt = new THREE.Vector3();
      if (ray.ray.intersectBox(box, a)) {
        const far = new THREE.Ray(ray.ray.at(1e6 * S.boxRadius, new THREE.Vector3()), ray.ray.direction.clone().negate());
        far.intersectBox(box, bpt);
        let bv = S.volMat.uniforms.uThreshold.value ** 2, bp = null;
        for (let k = 0; k <= 200; k++) {
          const p = a.clone().lerp(bpt, k / 200), v = sampleVolume(T2P(p));
          if (v > bv) { bv = v; bp = p; }
        }
        if (bp) return bp;
      }
    }
    return null;
  }
  function centerOnT(p) {  // the centre of rotation to point p (three's coordinates), the view's direction kept
    const off = p.clone().sub(orbit.target);
    orbit.target.add(off); camera.position.add(off); orbit.update();
    S.userMoved = true;
    requestRender();
  }

  // --- camera views ----------------------------------------------------------------------------------------------------
  // the scene's "up" (a physics vector; default y): a world may give another, e.g. v15 the spin axis z (review
  // B5-kerr-v15 K8); the orbit controls keep their up from the camera's, so their frame is set again
  function setUp(up) {
    S.up = up; S.axes = axesOfUp(up);
    const u = P2T(up).normalize();
    if (camera.up.distanceTo(u) < 1e-12) return;
    camera.up.copy(u);
    orbit._quat.setFromUnitVectors(camera.up, new THREE.Vector3(0, 1, 0));  // OrbitControls (three r185) internals
    orbit._quatInverse.copy(orbit._quat).invert();
  }
  // the preset views in the scene's frame (A3, A14): direction from the centre to the camera, and for a view along "up"
  // the direction that is up on screen. A 2-D world (plane2d) looks at its plane from above, x to the right as in the
  // plane's window.
  function presetDirs() {
    const { U, R, F } = S.axes;
    if (S.plane2d === null) {
      return { iso: [vunit(vlin([1, F], [0.42, U], [-0.3, R]))], side: [F], top: [U, vlin([-1, F])], beam: [vlin([-1, R])], back: [R] };
    }
    const N = [0, 0, 0]; N[S.plane2d] = 1;
    const inPlane = [0, 1, 2].filter((k) => k !== S.plane2d).map((k) => { const e = [0, 0, 0]; e[k] = 1; return e; });
    const lying = Math.abs(vdot(U, N)) > 0.9;
    const A = lying ? inPlane[1] : vunit(vlin([1, U], [-vdot(U, N), N]));
    const R2 = vunit(vcross(A, N)), Nc = vcross(R2, A);
    return lying
      ? { iso: [vunit(vlin([0.8, Nc], [-0.52, A], [-0.18, R2]))], top: [Nc, A], side: [vlin([-1, A])] }
      : { iso: [vunit(vlin([0.85, Nc], [0.3, A], [-0.25, R2]))], top: [Nc, A], side: [R2] };
  }
  function defaultViews() {
    const n = (S.desc && S.desc.coord_names) || ["x", "y", "z"];
    const name = (v) => { let k = 0; for (let i = 1; i < 3; i++) if (Math.abs(v[i]) > Math.abs(v[k])) k = i; return n[k]; };
    const { U, R, F } = S.axes;
    if (S.plane2d !== null) {
      const D = presetDirs(), lying = Math.abs(D.top[0][S.plane2d]) > 0.5 && Math.abs(vdot(U, D.top[0])) > 0.9;
      const ax = [0, 1, 2].filter((k) => k !== S.plane2d).map((k) => n[k]);
      return [["iso", t("Iso"), t("The world's plane at an angle (F — show the content)")],
              ["top", lying ? t("Top") : t("Front"), t("The plane {a}–{b} face on, {a} to the right — as in the window", { a: t(ax[0]), b: t(ax[1]) })],
              ["side", t("Edge"), t("The world's plane edge on")]];
    }
    return [["iso", t("Iso"), t("Isometric (F — show the content)")], ["side", t("Side"), t("Side view: the plane {a}–{b}", { a: t(name(R)), b: t(name(U)) })],
            ["top", t("Top"), t("Top view, along the axis {u}: the plane {a}–{b}", { u: t(name(U)), a: t(name(R)), b: t(name(F)) })],
            ["beam", t("From the source"), t("Along the axis {a}, from its start", { a: t(name(R)) })], ["back", t("From the target"), t("Against the axis {a}", { a: t(name(R)) })]];
  }
  // fit: the camera at direction d (three, unit, from the target) such that the 8 corners of [lo, hi] (physics) are inside
  // the canvas less the toolbar and the hint (review UX-3d A4: the corners, not a bounding sphere)
  function fitTo(d, lo, hi) {
    const W = root.clientWidth || 1, H = root.clientHeight || 1;
    const m = { l: 10, r: 10, t: 44, b: 26 };
    const ndc = { x0: -1 + 2 * m.l / W, x1: 1 - 2 * m.r / W, y0: -1 + 2 * m.b / H, y1: 1 - 2 * m.t / H };
    const ty = Math.tan(camera.fov * Math.PI / 360), tx = ty * camera.aspect;
    const corners = [];
    for (const x of [lo[0], hi[0]]) for (const y of [lo[1], hi[1]]) for (const z of [lo[2], hi[2]]) corners.push(P2T([x, y, z]));
    let c = corners.reduce((a, p) => a.add(p), new THREE.Vector3()).multiplyScalar(1 / 8);
    const f = d.clone().negate(), r = new THREE.Vector3().crossVectors(f, camera.up).normalize(), u = new THREE.Vector3().crossVectors(r, f);
    const hx = (ndc.x1 - ndc.x0) / 2, hy = (ndc.y1 - ndc.y0) / 2, cx = (ndc.x1 + ndc.x0) / 2, cy = (ndc.y1 + ndc.y0) / 2;
    let D = 1;
    for (let it = 0; it < 4; it++) {
      D = 0;
      for (const p of corners) {
        const rel = p.clone().sub(c), x = rel.dot(r), y = rel.dot(u), z = rel.dot(f);
        D = Math.max(D, Math.abs(x) / (tx * hx) - z, Math.abs(y) / (ty * hy) - z, -z + 1e-6 * S.size);
      }
      // the projected box's middle to the middle of the free area
      let px0 = Infinity, px1 = -Infinity, py0 = Infinity, py1 = -Infinity;
      for (const p of corners) {
        const rel = p.clone().sub(c), z = D + rel.dot(f), x = rel.dot(r) / (z * tx), y = rel.dot(u) / (z * ty);
        px0 = Math.min(px0, x); px1 = Math.max(px1, x); py0 = Math.min(py0, y); py1 = Math.max(py1, y);
      }
      const sx = (px0 + px1) / 2 - cx, sy = (py0 + py1) / 2 - cy;
      c = c.clone().addScaledVector(r, sx * D * tx).addScaledVector(u, sy * D * ty);
    }
    camera.position.copy(c.clone().addScaledVector(d, D));
    orbit.target.copy(c);
    orbit.maxDistance = Math.max(10 * D, 4 * S.boxRadius);
    orbit.minDistance = 1e-4 * (S.size || 1);
    orbit.update();
    updateClip();
    requestRender();
  }
  // a view: a preset name, or a world's view [name, label, title, look] with look a physics direction from the scene's
  // centre to the camera or {along: id}: from behind the arrow of that layer, looking along it (v15: the observer)
  function viewDir(name) {
    const D = presetDirs();
    const def = (S.viewDefs || []).find((v) => v[0] === name), look = def && def[3];
    let d = null, upHint = null;
    if (Array.isArray(look)) d = look;
    else if (look && look.along) {
      const L = S.layers.get(look.along), v = L && L.obj.userData.vec;
      if (v) d = v.map((c) => -c);
    }
    if (!d || Math.hypot(...d) === 0) [d, upHint] = D[name] || D.iso;
    let tt = P2T(vunit(d)).normalize();
    // looking along the up direction: a small tilt keeps the camera's orientation defined, with upHint up on screen
    if (Math.abs(tt.dot(camera.up)) > 0.999999) {
      const h = P2T(upHint || vlin([-1, S.axes.F])).normalize();
      tt = tt.addScaledVector(h, -2e-3 * Math.sign(tt.dot(camera.up))).normalize();
    }
    return tt;
  }
  // the region and the apparatus in it (a screen may be wider than the region): what a view frames
  function regionBounds() {
    const b = new THREE.Box3(P2T(S.box[0]), P2T(S.box[0])).expandByPoint(P2T(S.box[1]));
    const ids = new Set(((S.desc && S.desc.objects) || []).map((o) => o.id));
    scene.updateMatrixWorld();
    for (const id of ids) {
      const L = S.layers.get(id); if (!L || !L.visible) continue;
      L.obj.traverse((o) => {
        if (!o.isMesh || o.userData.twin || !o.geometry || !visibleChain(o)) return;
        if (!o.geometry.boundingBox) o.geometry.computeBoundingBox();
        b.union(o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld));
      });
    }
    const lo = T2P(b.min), hi = T2P(b.max);
    return [[0, 1, 2].map((i) => Math.min(lo[i], hi[i])), [0, 1, 2].map((i) => Math.max(lo[i], hi[i]))];
  }
  function view(name) {
    if (!S.box) return;
    S.lastView = name;
    S.fit = { name, what: "box" };
    S.userMoved = false; note.style.display = "none";
    fitTo(viewDir(name), ...regionBounds());
  }
  // F: the visible content (what the run has drawn), Shift+F: the whole region; both from the current direction
  function contentBounds() {
    const b = new THREE.Box3(), v = new THREE.Vector3(), m = new THREE.Matrix4();
    scene.updateMatrixWorld();
    for (const L of S.layers.values()) {
      if (!L.visible) continue;
      if (L.kind === "volume") {
        const U = S.volMat && S.volMat.uniforms;
        if (U && U.uCMax.value.x > U.uCMin.value.x) b.union(new THREE.Box3(U.uCMin.value.clone().max(U.uMin.value), U.uCMax.value.clone().min(U.uMax.value)));
        continue;
      }
      L.obj.traverse((o) => {
        if (o.isSprite || o.userData.twin || o.userData.wide || !visibleChain(o) || !o.geometry) return;
        if (o.isInstancedMesh) {
          for (let i = 0; i < o.count; i++) { o.getMatrixAt(i, m); v.setFromMatrixPosition(m).applyMatrix4(o.matrixWorld); if (Number.isFinite(v.x)) b.expandByPoint(v); }
          return;
        }
        const a = o.geometry.attributes.position; if (!a) return;
        const dr = o.geometry.drawRange, n = Math.min(a.count, Number.isFinite(dr.count) ? dr.start + dr.count : a.count);
        for (let i = 0; i < n; i++) { v.fromBufferAttribute(a, i); if (!Number.isFinite(v.x)) continue; v.applyMatrix4(o.matrixWorld); b.expandByPoint(v); }
      });
    }
    if (b.isEmpty()) return null;
    const lo = T2P(b.min), hi = T2P(b.max);
    const L = [0, 1, 2].map((i) => Math.min(lo[i], hi[i])), Hh = [0, 1, 2].map((i) => Math.max(lo[i], hi[i]));
    const pad = 0.02 * (S.size || 1);
    return [L.map((x) => x - pad), Hh.map((x) => x + pad)];
  }
  function frameAll(what) {
    if (!S.box) return;
    const d = camera.position.clone().sub(orbit.target).normalize();
    const cb = what === "content" ? contentBounds() : null;
    S.fit = { dir: d.clone(), what: cb ? "content" : "box" };
    S.userMoved = false; note.style.display = "none";
    fitTo(d, ...(cb || regionBounds()));
  }
  function refit() {
    const f = S.fit || { name: "iso", what: "box" };
    if (f.name) fitTo(viewDir(f.name), ...regionBounds());
    else { const cb = f.what === "content" ? contentBounds() : null; fitTo(f.dir, ...(cb || regionBounds())); }
  }

  function setScale(scale, floor) {
    S.scale = scale;
    if (floor !== undefined) S.floor = floor;  // the log scale's floor: the same as the windows' (review C11)
    paintVolume(true);
    for (const L of S.layers.values()) if (L.obj.userData && L.obj.userData.tex) paintImage(L.obj);
    for (const P of S.planes.values()) paintPlane(P);
    for (const L of S.layers.values()) if (L.obj.userData && L.obj.userData.panelTex) paintPanel(L.obj);
    updateLegend();
    requestRender();
  }
  function setBusy(text) { busy.style.display = text ? "" : "none"; busy.textContent = text || ""; }

  // the colour bar of the scene's map, with its scale (review UX-3d A15)
  const legendCv = el("canvas", { width: 128, height: 10 });
  function updateLegend() {
    const any = !!volumeLayer() || [...S.planes.values()].some((P) => P.visible && P.data)
      || [...S.layers.values()].some((L) => L.visible && L.obj.userData && (L.obj.userData.panelTex || (L.obj.userData.tex && L.obj.userData.data)));
    legend.style.display = any ? "" : "none";
    if (!any) return;
    const g = legendCv.getContext("2d");
    for (let i = 0; i < 128; i++) { const c = Math.round(i / 127 * 255); g.fillStyle = `rgb(${LUT[3 * c]},${LUT[3 * c + 1]},${LUT[3 * c + 2]})`; g.fillRect(i, 0, 1, 10); }
    const sc = { sqrt: t("amplitude √(I/Imax)"), lin: t("intensity I/Imax"), log: t("logarithm of I/Imax") }[S.scale] || S.scale;
    const lo = S.scale === "log" ? `10^${Math.round(Math.log10(S.floor))}` : "0";
    fill(legend, el("div", { class: "s3d-legend-t" }, sc), legendCv, el("div", { class: "s3d-legend-ax" }, el("span", {}, lo), el("span", {}, t("1 (peak)"))));
  }
  function updateHint() {
    const slices = ((S.desc && S.desc.planes) || {}).max !== 0;
    hint.textContent = t("Left button — rotate · right button or Shift+left — pan · wheel — towards the cursor · double click — centre of rotation · F — all the content, Shift+F — the whole region")
      + (slices ? " · " + t("slice: click — select, W — move, E — tilt") : "");
  }

  // keyboard: W move, E rotate, F frame the content (Shift+F the region), Escape deselect, Delete remove (handled by the
  // caller through onSelect)
  root.tabIndex = 0;
  // the keys act on the whole page (after a click in a slice window too); the player's own keys are others
  document.addEventListener("keydown", (e) => {
    if (!root.isConnected || e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.target.tagName === "TEXTAREA") return;
    if (e.code === "KeyW" || e.key === "w" || e.key === "W") { gizmo.setMode("translate"); gizmoHandles(); toolsState(); }
    else if (e.code === "KeyE" || e.key === "e" || e.key === "E") { gizmo.setMode("rotate"); gizmoHandles(); toolsState(); }
    else if (e.code === "KeyF" || e.key === "f" || e.key === "F") frameAll(e.shiftKey ? "box" : "content");
    else if (e.key === "Escape") select(null);
    else return;
    e.preventDefault(); e.stopPropagation();
  });
  const modeBtns = {};
  function toolsState() { for (const [m, b] of Object.entries(modeBtns)) b.classList.toggle("on", gizmo.mode === m); }
  function buildTools(extra = []) {
    S.extraTools = extra;
    modeBtns.translate = el("button", { class: "toggle on s3d-move", title: t("Move the selected slice along its normal (arrow; W)"), onclick: () => { gizmo.setMode("translate"); gizmoHandles(); toolsState(); } }, t("✥ Move"));
    modeBtns.rotate = el("button", { class: "toggle s3d-tilt", title: t("Tilt the selected slice (two rings; E)"), onclick: () => { gizmo.setMode("rotate"); gizmoHandles(); toolsState(); } }, t("⟳ Tilt"));
    const vbtn = (name, label, title) => el("button", { title, onclick: () => view(name) }, label);
    fill(tools, ...extra, modeBtns.translate, modeBtns.rotate,
      el("span", { class: "sep" }),
      ...(S.viewDefs || VIEWS).map(([name, label, title]) => vbtn(name, label, title)),
      el("button", { title: t("Save a snapshot of the 3-D view (PNG)"), onclick: () => { draw(true); const a = el("a", { href: renderer.domElement.toDataURL("image/png"), download: "scene3d.png" }); a.click(); } }, "📷"));
  }
  buildTools();
  updateHint();

  // --- a computed field on a rectangle of any orientation (e.g. v11: |psi|^2 in the plane of a 2-D world) -------------
  // object {kind: "panel", origin (a corner), u, v (its edges, physics vectors), opacity?}; image nx along u, ny along
  // v, data index ix * ny + iy (as targets), values 0..1 drawn with the scene's scale; weak values fade out
  const vadd = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
  function panelObj(o) {
    const corners = [o.origin, vadd(o.origin, o.u), vadd(vadd(o.origin, o.u), o.v), vadd(o.origin, o.v)].map(P2T);
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(corners.flatMap((c) => [c.x, c.y, c.z])), 3));
    geo.setAttribute("uv", new THREE.BufferAttribute(new Float32Array([0, 0, 1, 0, 1, 1, 0, 1]), 2));
    geo.setIndex([0, 1, 2, 0, 2, 3]);
    const tex = new THREE.DataTexture(new Uint8Array(4), 1, 1, THREE.RGBAFormat);
    const mat = new THREE.MeshBasicMaterial({ map: tex, side: THREE.DoubleSide, transparent: true, opacity: o.opacity ?? 0.95, depthWrite: false });
    const mesh = new THREE.Mesh(geo, mat);
    const g = new THREE.Group(); addTranslucent(g, mesh);
    g.userData = { panelTex: tex, nx: 1, ny: 1, data: null, mesh };
    return g;
  }
  function paintPanel(obj) {
    const U = obj.userData, { nx, ny, data } = U;
    if (!data) return;
    const d = U.panelTex.image.data;
    for (let ix = 0; ix < nx; ix++) for (let iy = 0; iy < ny; iy++) {
      const v = transfer(data[ix * ny + iy], S.scale, S.floor), c = Math.max(0, Math.min(255, Math.round(255 * (v || 0))));
      const o = 4 * (iy * nx + ix);
      d[o] = LUT[3 * c]; d[o + 1] = LUT[3 * c + 1]; d[o + 2] = LUT[3 * c + 2]; d[o + 3] = Math.round(255 * Math.min(1, 0.06 + 1.6 * (v || 0)));
    }
    U.panelTex.needsUpdate = true;
  }
  function setPanelImage(id, nx, ny, data) {
    const L = S.layers.get(id); if (!L || !L.obj.userData.panelTex) return;
    const U = L.obj.userData;
    if (U.nx !== nx || U.ny !== ny) {
      U.panelTex.dispose();
      U.panelTex = new THREE.DataTexture(new Uint8Array(nx * ny * 4), nx, ny, THREE.RGBAFormat);
      U.panelTex.magFilter = THREE.LinearFilter; U.panelTex.minFilter = THREE.LinearFilter;
      U.mesh.material.map = U.panelTex; U.mesh.material.needsUpdate = true;
      U.nx = nx; U.ny = ny;
    }
    const first = !U.data;
    U.data = data; paintPanel(L.obj);
    if (first) updateLegend();
    requestRender();
  }
  // (re)build one object of the scene from its description (a live change of the apparatus, e.g. a slit closed)
  function setObject(o) {
    const list = S.desc.objects || (S.desc.objects = []);
    const i = list.findIndex((q) => q.id === o.id);
    if (i >= 0) list[i] = o; else list.push(o);
    const obj = buildObject(o);
    if (obj) { const L = S.layers.get(o.id); addLayer(o.id, o.label, obj, L ? L.visible : o.visible !== false); }
  }
  // many computed polylines at once (e.g. v11: Bohm trajectories), revealed as the run's time reaches them: point
  // `from` of each of the n tracks (xyz: n x 3, NaN where a track has ended or not begun); colours per track
  // (n x 3, 0..1), which may change (setTrackColors) and recolour the whole track
  function appendTracks(id, xyz, colors, { label = t("Trajectories (computed)") } = {}) {
    const n = xyz.length / 3;
    let T = S.tracks.get(id);
    if (!T) {
      const geo = new THREE.BufferGeometry(), cap = 6 * 16384;
      const pos = new Float32Array(cap), col = new Float32Array(cap);
      geo.setAttribute("position", new THREE.BufferAttribute(pos, 3)); geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
      geo.setDrawRange(0, 0);
      const line = new THREE.LineSegments(geo, new THREE.LineBasicMaterial({ vertexColors: true }));
      line.frustumCulled = false;
      wideFrom(line, { width: 1.8 });
      T = { line, geo, pos, col, segs: 0, segTrack: new Int32Array(16384), last: new Float32Array(3 * n).fill(NaN), colors: new Float32Array(3 * n) };
      S.tracks.set(id, T);
      addLayer(id, label, line, true, "tracks");
    }
    if (colors) T.colors.set(colors.subarray ? colors.subarray(0, 3 * n) : colors);
    const segs0 = T.segs;
    for (let k = 0; k < n; k++) {
      const p = [xyz[3 * k], xyz[3 * k + 1], xyz[3 * k + 2]];
      const q = [T.last[3 * k], T.last[3 * k + 1], T.last[3 * k + 2]];
      if (Number.isFinite(p[0]) && Number.isFinite(q[0])) {
        if (6 * (T.segs + 1) > T.pos.length) {
          const np_ = new Float32Array(2 * T.pos.length), nc = new Float32Array(2 * T.col.length), nt = new Int32Array(2 * T.segTrack.length);
          np_.set(T.pos); nc.set(T.col); nt.set(T.segTrack);
          T.pos = np_; T.col = nc; T.segTrack = nt;
          T.geo.setAttribute("position", new THREE.BufferAttribute(T.pos, 3)); T.geo.setAttribute("color", new THREE.BufferAttribute(T.col, 3));
        }
        const a = P2T(q), b = P2T(p), o = 6 * T.segs;
        T.pos.set([a.x, a.y, a.z, b.x, b.y, b.z], o);
        T.col.set([T.colors[3 * k], T.colors[3 * k + 1], T.colors[3 * k + 2], T.colors[3 * k], T.colors[3 * k + 1], T.colors[3 * k + 2]], o);
        T.segTrack[T.segs] = k; T.segs += 1;
      }
      T.last[3 * k] = p[0]; T.last[3 * k + 1] = p[1]; T.last[3 * k + 2] = p[2];
    }
    T.geo.attributes.position.needsUpdate = true; T.geo.attributes.color.needsUpdate = true;
    T.geo.setDrawRange(0, 2 * T.segs);
    syncWide(T.line, segs0);
    requestRender();
  }
  function setTrackColors(id, colors) {
    const T = S.tracks.get(id); if (!T) return;
    T.colors.set(colors.subarray ? colors.subarray(0, T.colors.length) : colors);
    for (let s = 0; s < T.segs; s++) {
      const k = T.segTrack[s];
      for (let e = 0; e < 2; e++) T.col.set([T.colors[3 * k], T.colors[3 * k + 1], T.colors[3 * k + 2]], 6 * s + 3 * e);
    }
    T.geo.attributes.color.needsUpdate = true; syncWide(T.line, 0); requestRender();
  }
  // polylines replaced on every call (e.g. v15: sample light rays, p01: trails): pts n x 3 with NaN between the lines,
  // colours per point (n x 3, 0..1, sRGB as named); the layer's object is kept and its buffers refilled (A17)
  function setLines(id, pts, rgb, { label = id, visible = true } = {}) {
    const n = pts.length / 3;
    let m = 0;
    for (let i = 0; i + 1 < n; i++) if (Number.isFinite(pts[3 * i]) && Number.isFinite(pts[3 * i + 3])) m++;
    const L = S.layers.get(id);
    let lines = L && L.kind === "lines" && L.obj.isLineSegments ? L.obj : null;
    let P, C;
    if (lines && lines.geometry.attributes.position.array.length >= 6 * m && lines.label === label) {
      P = lines.geometry.attributes.position.array; C = lines.geometry.attributes.color.array;
    } else {
      const cap = Math.max(6 * m, 6 * 64) * (lines ? 2 : 1);
      P = new Float32Array(cap); C = new Float32Array(cap);
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(P, 3)); geo.setAttribute("color", new THREE.BufferAttribute(C, 3));
      lines = new THREE.LineSegments(geo, new THREE.LineBasicMaterial({ vertexColors: true }));
      lines.frustumCulled = false; lines.label = label;
      wideFrom(lines, { width: 2 });
      addLayer(id, label, lines, L ? L.visible : visible, "lines");
    }
    let o = 0;
    for (let i = 0; i + 1 < n; i++) {
      if (!Number.isFinite(pts[3 * i]) || !Number.isFinite(pts[3 * i + 3])) continue;
      P[o] = pts[3 * i + 2]; P[o + 1] = pts[3 * i + 1]; P[o + 2] = -pts[3 * i];
      P[o + 3] = pts[3 * i + 5]; P[o + 4] = pts[3 * i + 4]; P[o + 5] = -pts[3 * i + 3];
      for (let k = 0; k < 6; k++) C[o + k] = Math.pow(rgb[3 * i + k], 2.2);  // sRGB -> linear, as setMesh
      o += 6;
    }
    const geo = lines.geometry;
    geo.setDrawRange(0, 2 * m);
    geo.attributes.position.needsUpdate = true; geo.attributes.color.needsUpdate = true;
    syncWide(lines, 0);
    requestRender();
  }
  // a cloud of points replaced on every call (e.g. v11: the particles now), drawn as round shaded points; NaN positions
  // are left out
  function setPoints(id, xyz, colors, { label = t("Particles now"), size = 0.006 } = {}) {
    let L = S.layers.get(id);
    const usz = (S.size || 1) * size * 0.45;  // the old squares' size on screen (three's points scale), a little larger
    if (L && L.obj.material.uniforms.uSize.value !== usz) L.obj.material.uniforms.uSize.value = usz;  // the box changed
    if (!L) {
      const geo = new THREE.BufferGeometry();
      const mat = new THREE.ShaderMaterial({ vertexShader: PTS_VERT, fragmentShader: PTS_FRAG, vertexColors: true,
                                             uniforms: { uSize: { value: usz }, uScale: S.ptScale } });
      const pts = new THREE.Points(geo, mat);
      pts.frustumCulled = false;
      addLayer(id, label, pts, true, "points"); L = S.layers.get(id);
    }
    const n = xyz.length / 3, P = [], C = [];
    for (let i = 0; i < n; i++) {
      if (!Number.isFinite(xyz[3 * i])) continue;
      const v = P2T([xyz[3 * i], xyz[3 * i + 1], xyz[3 * i + 2]]);
      P.push(v.x, v.y, v.z); C.push(colors[3 * i], colors[3 * i + 1], colors[3 * i + 2]);
    }
    const geo = L.obj.geometry;
    geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(P), 3));
    geo.setAttribute("color", new THREE.BufferAttribute(new Float32Array(C), 3));
    requestRender();
  }
  S.ptScale = { value: 1 };

  // spheres replaced on every call (a playground's bodies: lfviz.playground): pos n x 3, radius n (physics units; drawn
  // at least minFrac of the scene's size so that a star or a planet far smaller than its orbit stays visible), rgb n x 3
  // (0..1, sRGB); one instanced mesh of exact lit sphere impostors, rebuilt only when the count grows
  function setSpheres(id, pos, radius, rgb, { label = t("Bodies"), minFrac = 0.006, visible = true } = {}) {
    const n = pos.length / 3;
    let L = S.layers.get(id);
    if (L && L.obj.userData.cap < n) { removeLayer(id); L = null; }
    if (!L) {
      const mat = new THREE.ShaderMaterial({ vertexShader: SPH_VERT, fragmentShader: SPH_FRAG,
                                             uniforms: { uColor: { value: new THREE.Color(0xffffff) }, uShade: { value: new THREE.Vector3(...SOLID) } } });
      const mesh = new THREE.InstancedMesh(QUAD_GEO, mat, Math.max(8, 2 * n));
      mesh.userData.cap = Math.max(8, 2 * n);
      mesh.frustumCulled = false;
      addLayer(id, label, mesh, visible, "spheres"); L = S.layers.get(id);
    }
    const mesh = L.obj, m = new THREE.Matrix4(), c = new THREE.Color(), rmin = (S.size || 1) * minFrac;
    for (let i = 0; i < n; i++) {
      const v = P2T([pos[3 * i], pos[3 * i + 1], pos[3 * i + 2]]), r = Math.max(radius[i] || 0, rmin);
      m.makeScale(r, r, r).setPosition(v);
      mesh.setMatrixAt(i, m);
      c.setRGB(rgb[3 * i], rgb[3 * i + 1], rgb[3 * i + 2], THREE.SRGBColorSpace);
      mesh.setColorAt(i, c);
    }
    mesh.count = n;
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    requestRender();
  }

  // --- key frames of the player (player.js): the appending layers' lengths, and cutting them back to them -----------
  function removeLayer(id) {
    const L = S.layers.get(id); if (!L) return;
    scene.remove(L.obj); disposeTree(L.obj); S.layers.delete(id);
    layersChanged(); updateLegend(); requestRender();
  }
  function snapshotAppends() {
    return {
      paths: new Map([...S.paths].map(([id, P]) => [id, P.n])),
      // the drawn segments' colours too: a track is recoloured when what it shows becomes known (v11: its slit)
      tracks: new Map([...S.tracks].map(([id, T]) => [id, { segs: T.segs, last: T.last.slice(), colors: T.colors.slice(),
                                                              col: T.col.slice(0, 6 * T.segs) }])),
      triads: new Map([...S.layers.values()].filter((L) => L.kind === "triads").map((L) => [L.id, L.obj.children.length])),
    };
  }
  function restoreAppends(k) {
    for (const [id, T] of S.tracks) {  // checked first: nothing is cut when a key frame cannot be restored
      const s = k.tracks.get(id);
      if (s && s.last.length !== T.last.length) throw new Error(`tracks ${id}: another number of tracks`);
    }
    for (const [id, P] of [...S.paths]) {
      const n = k.paths.get(id);
      if (n === undefined) { removeLayer(id); S.paths.delete(id); } else { P.n = n; P.geo.setDrawRange(0, n); syncWide(P.line, n); }
    }
    for (const [id, T] of [...S.tracks]) {
      const s = k.tracks.get(id);
      if (!s) { removeLayer(id); S.tracks.delete(id); continue; }
      T.segs = s.segs; T.last = s.last.slice(); T.colors = s.colors.slice(); T.col.set(s.col, 0);
      T.geo.attributes.color.needsUpdate = true;
      T.geo.setDrawRange(0, 2 * T.segs);
      syncWide(T.line, 0);
    }
    for (const L of [...S.layers.values()]) {
      if (L.kind !== "triads") continue;
      const n = k.triads.get(L.id);
      if (n === undefined) { removeLayer(L.id); continue; }
      while (L.obj.children.length > n) { const c = L.obj.children[L.obj.children.length - 1]; L.obj.remove(c); disposeTree(c); }
    }
    requestRender();
  }

  const api = { el: root, setScene, removeLayer, snapshotAppends, restoreAppends, setSpheres, setObjectImage, setVolume, updateVolume, setVolumeLook, setVectors, setVectorThreshold, sampleVolume,
           setPlanes, setPlaneImage, setPlaneVisible, select, highlight, view, frameAll, setScale, setBusy, setLayerVisible,
           buildTools, requestRender, render: () => draw(true), appendPath, setLines, setBox, setPanelImage, setObject, appendTracks, setTrackColors, setPoints,
           volumeLook: () => ({ density: S.volMat ? S.volMat.uniforms.uDensity.value : 4, threshold: S.volMat ? S.volMat.uniforms.uThreshold.value : 0.02 }), addTriads, setMarks, setArrow, setBody, setMesh, transformMesh, updateMesh, setObserver,
           layers: () => [...S.layers.values()], planes: () => [...S.planes.values()], state: S,
           onLayersChanged: (f) => { layersListener = f; },
           // the centre of rotation on a physics point, the direction of view kept (a playground's «centre on the object»)
           centerOn: (p) => centerOnT(P2T(p)),
           // direct manipulation (plan P16.2): the manipulator, rays, pixel sizes, the camera's direction, markers
           setManipulator, rayAt, pixelSize, setMarker, moveMarker, markers: () => [...markers.keys()],
           markerSpec: (id) => { const M = markers.get(id); return M ? { ...M.spec, pos: T2P(M.c) } : null; },  // tests
           viewDir: () => { const f = new THREE.Vector3(); camera.updateMatrixWorld(); camera.getWorldDirection(f); return T2P(f); },
           project: (p) => { camera.updateMatrixWorld(); const v = P2T(p).project(camera), r = canvas.getBoundingClientRect(); return { x: r.left + (v.x + 1) / 2 * r.width, y: r.top + (1 - v.y) / 2 * r.height, z: v.z, inside: v.z > -1 && v.z < 1 }; },
           pick: (x, y) => { const r = canvas.getBoundingClientRect(); const p = pickPoint(new THREE.Vector2((x - r.left) / r.width * 2 - 1, -(y - r.top) / r.height * 2 + 1)); return p ? T2P(p) : null; },
           cameraState: () => ({ pos: T2P(camera.position), target: T2P(orbit.target), near: camera.near, far: camera.far, userMoved: S.userMoved, quality: S.quality }),
           frameStats: () => ({ frames: S.frames, lastMs: S.lastMs, quality: S.quality }),
           // tests: the drawn colour [r, g, b] at a physics point (a full-quality frame drawn and read in one task)
           pixelAt: (p) => {
             draw(true);
             const gl = renderer.getContext(), c = canvas, r = canvas.getBoundingClientRect(), [sx, sy] = api.screenOf(p), o = new Uint8Array(4);
             gl.readPixels(Math.round((sx - r.left) * c.width / r.width), Math.round(c.height - (sy - r.top) * c.height / r.height), 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, o);
             return [o[0], o[1], o[2]];
           },
           gizmoState: () => ({ mode: gizmo.mode, showX: gizmo.showX, showY: gizmo.showY, showZ: gizmo.showZ, attached: !!gizmo.object }),
           screenOf: (p) => { camera.updateMatrixWorld(); const v = P2T(p).project(camera), r = canvas.getBoundingClientRect(); return [r.left + (v.x + 1) / 2 * r.width, r.top + (1 - v.y) / 2 * r.height]; } };
  api.gpuInfo = () => ({ ...renderer.info.memory });  // GPU objects alive (tests: a rebuilt scene frees the old ones)
  root.__scene3d = api;  // for automated tests of the page
  return api;
}
