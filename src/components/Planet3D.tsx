import { useEffect, useMemo, useRef, useState } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { Line, PerformanceMonitor } from '@react-three/drei'
import * as THREE from 'three'

export type Body3D = 'earth' | 'moon' | 'mars'
export type Mode3D = 'side' | 'rise'
type Quality = 'high' | 'low'
type Mask = { w: number; h: number; data: Uint8ClampedArray }

const LAND_THRESHOLD = 30
const mouse = { x: 0, y: 0 }

const PAL: Record<Body3D, { a: string; b: string; c: string; solid: string; glow: [number, number, number] }> = {
  earth: { a: '#4DA3FF', b: '#2F7BE0', c: '#E8ECF4', solid: '#071A3D', glow: [0.3, 0.64, 1.0] },
  moon: { a: '#C9D1E0', b: '#8E98AD', c: '#F2F5FB', solid: '#090d18', glow: [0.62, 0.78, 1.0] },
  mars: { a: '#E5835A', b: '#A8472B', c: '#F4C9A8', solid: '#140a08', glow: [1.0, 0.55, 0.35] },
}

/* ---------- shaders ---------- */
const dotsVert = /* glsl */ `
uniform float uTime;
uniform float uScale;
uniform float uAlpha;
uniform vec3 uLight;
attribute float aSize;
attribute float aPhase;
varying vec3 vColor;
varying float vA;
void main() {
  vec3 n = normalize(normalMatrix * position);
  float lit = 0.3 + 0.95 * max(dot(n, normalize(uLight)), 0.0);
  float facing = smoothstep(-0.15, 0.35, n.z);
  float tw = 0.85 + 0.15 * sin(uTime * 1.3 + aPhase);
  vA = mix(0.15, 1.0, facing) * tw * uAlpha;
  vColor = color * lit;
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  gl_PointSize = aSize * uScale / -mv.z;
  gl_Position = projectionMatrix * mv;
}`
const dotsFrag = /* glsl */ `
varying vec3 vColor;
varying float vA;
void main() {
  float d = length(gl_PointCoord - vec2(0.5));
  if (d > 0.5) discard;
  gl_FragColor = vec4(vColor, smoothstep(0.5, 0.0, d) * vA);
}`
const glowVert = /* glsl */ `
varying vec2 vUv;
void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`
const glowFrag = /* glsl */ `
uniform vec3 uColor;
uniform float uStrength;
varying vec2 vUv;
void main() {
  float d = length(vUv - 0.5) * 2.0;
  float outer = 1.0 - smoothstep(0.625, 1.0, d);
  float inner = smoothstep(0.5, 0.625, d);
  float body = (1.0 - smoothstep(0.6, 0.625, d)) * 0.05;
  float i = pow(outer, 2.5) * inner * uStrength + body;
  gl_FragColor = vec4(uColor, 1.0) * i;
}`

function makeDotsMaterial(light: [number, number, number], alpha: number) {
  return new THREE.ShaderMaterial({
    uniforms: { uTime: { value: 0 }, uScale: { value: 20 }, uAlpha: { value: alpha }, uLight: { value: new THREE.Vector3(...light) } },
    vertexShader: dotsVert, fragmentShader: dotsFrag, vertexColors: true,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  })
}

function loadMask(): Promise<Mask | null> {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => {
      const w = 512, h = 256
      const c = document.createElement('canvas')
      c.width = w; c.height = h
      const ctx = c.getContext('2d')
      if (!ctx) return resolve(null)
      ctx.drawImage(img, 0, 0, w, h)
      resolve({ w, h, data: ctx.getImageData(0, 0, w, h).data })
    }
    img.onerror = () => resolve(null)
    img.src = '/textures/earth.jpg'
  })
}

function buildDots(body: Body3D, count: number, R: number, mask: Mask | null) {
  const pal = PAL[body]
  const pos = new Float32Array(count * 3)
  const col = new Float32Array(count * 3)
  const size = new Float32Array(count)
  const phase = new Float32Array(count)
  const A = new THREE.Color(pal.a), B = new THREE.Color(pal.b), C = new THREE.Color(pal.c)
  const tmp = new THREE.Color()
  const craters = Array.from({ length: 16 }, () => {
    const u = Math.random() * 2 - 1, t = Math.random() * Math.PI * 2, s = Math.sqrt(1 - u * u)
    return { v: new THREE.Vector3(s * Math.cos(t), u, s * Math.sin(t)), r: 0.12 + Math.random() * 0.22 }
  })
  const p = new THREE.Vector3()
  let n = 0, guard = 0

  while (n < count && guard < count * 40) {
    guard++
    const u = Math.random() * 2 - 1, th = Math.random() * Math.PI * 2, s = Math.sqrt(1 - u * u)
    p.set(s * Math.cos(th), u, s * Math.sin(th))
    const lat = Math.asin(u)
    const lon = Math.atan2(-p.z, p.x)
    let bright = 1

    if (body === 'earth') {
      let isLand = true
      if (mask) {
        const uu = (lon + Math.PI) / (2 * Math.PI)
        const vv = (Math.PI / 2 - lat) / Math.PI
        const px = Math.min(mask.w - 1, Math.floor(uu * mask.w))
        const py = Math.min(mask.h - 1, Math.floor(vv * mask.h))
        isLand = mask.data[(py * mask.w + px) * 4] > LAND_THRESHOLD
        if (!isLand && Math.random() > 0.55) continue
      }
      tmp.copy(isLand ? A : B)
      if (isLand && Math.random() < 0.15) tmp.lerp(C, 0.5)
      size[n] = isLand ? 0.9 + Math.random() * 0.8 : 0.6 + Math.random() * 0.5
    } else {
      let m = 1
      for (const c of craters) {
        const d = p.angleTo(c.v) / c.r
        if (d < 1) m = Math.min(m, 0.35 + 0.65 * d * d)
        else if (d < 1.25) m = Math.max(m, 1.35)
      }
      const noise = 0.7 + 0.3 * Math.sin(p.x * 7 + p.y * 3) * Math.sin(p.z * 6 - p.x * 2)
      bright = m * noise
      tmp.copy(A).lerp(B, Math.random() * 0.5)
      if (Math.random() < 0.08) tmp.lerp(C, 0.6)
      size[n] = 0.8 + Math.random() * 0.9
    }
    pos[n * 3] = p.x * R; pos[n * 3 + 1] = p.y * R; pos[n * 3 + 2] = p.z * R
    col[n * 3] = tmp.r * bright; col[n * 3 + 1] = tmp.g * bright; col[n * 3 + 2] = tmp.b * bright
    phase[n] = Math.random() * Math.PI * 2
    n++
  }
  const g = new THREE.BufferGeometry()
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3))
  g.setAttribute('color', new THREE.BufferAttribute(col, 3))
  g.setAttribute('aSize', new THREE.BufferAttribute(size, 1))
  g.setAttribute('aPhase', new THREE.BufferAttribute(phase, 1))
  g.setDrawRange(0, n)
  return { geometry: g, count: n }
}

function ringPoints(cy: number, rx: number, ry: number): [number, number, number][] {
  return Array.from({ length: 161 }, (_, i) => {
    const a = (i / 160) * Math.PI * 2
    return [rx * Math.cos(a), cy + ry * Math.sin(a), 0]
  })
}

/* ---------- scene ---------- */
type SceneProps = { body: Body3D; mode: Mode3D; markers: boolean; moon: boolean; reduce: boolean; mobile: boolean; quality: Quality }

function Scene({ body, mode, markers, moon, reduce, mobile, quality }: SceneProps) {
  const pal = PAL[body]
  const rise = mode === 'rise'
  const R = rise ? 4 : 1.9
  const CY = rise ? -5.1 : 0
  const RX = 7.4, RY = 5.6

  const root = useRef<THREE.Group>(null)
  const spin = useRef<THREE.Group>(null)
  const orbit = useRef<THREE.Group>(null)
  const sun = useRef<THREE.Group>(null)
  const earth = useRef<THREE.Group>(null)
  const invalidate = useThree((s) => s.invalidate)
  const [mask, setMask] = useState<Mask | null | undefined>(body === 'earth' ? undefined : null)
  const [tex, setTex] = useState<THREE.Texture | null>(null)

  const material = useMemo(() => makeDotsMaterial(rise ? [-0.55, 0.75, 0.65] : [-0.6, 0.35, 0.7], rise ? 0.55 : 1), [rise])
  const moonMaterial = useMemo(() => makeDotsMaterial([-0.6, 0.35, 0.7], 1), [])
  const glowMat = useMemo(
    () => new THREE.ShaderMaterial({
      uniforms: { uColor: { value: new THREE.Vector3(...pal.glow) }, uStrength: { value: rise ? 0.8 : 0.55 } },
      vertexShader: glowVert, fragmentShader: glowFrag, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    }),
    [pal, rise],
  )

  useEffect(() => {
    if (body !== 'earth') return
    let on = true
    loadMask().then((m) => on && setMask(m))
    new THREE.TextureLoader().load('/textures/earth.jpg', (t) => {
      t.colorSpace = THREE.SRGBColorSpace
      if (on) setTex(t)
    })
    return () => { on = false }
  }, [body])

  useEffect(() => {
    if (reduce) return
    const onMove = (e: MouseEvent) => {
      mouse.x = e.clientX / window.innerWidth - 0.5
      mouse.y = e.clientY / window.innerHeight - 0.5
    }
    window.addEventListener('mousemove', onMove)
    return () => window.removeEventListener('mousemove', onMove)
  }, [reduce])

  const dots = useMemo(() => {
    if (mask === undefined) return null
    const base = body === 'earth' ? 28000 : 26000
    return buildDots(body, mobile ? Math.floor(base / 2) : base, R, mask)
  }, [mask, body, mobile, R])
  const moonDots = useMemo(() => (moon ? buildDots('moon', mobile ? 1500 : 3500, 0.38, null) : null), [moon, mobile])
  const ring1 = useMemo(() => ringPoints(CY, RX, RY), [CY])
  const ring2 = useMemo(() => ringPoints(CY, RX * 1.12, RY * 1.1), [CY])

  useEffect(() => {
    if (!dots) return
    dots.geometry.setDrawRange(0, quality === 'low' ? Math.floor(dots.count * 0.55) : dots.count)
    invalidate()
  }, [dots, quality, invalidate])

  useFrame((state, delta) => {
    const t = state.clock.elapsedTime
    material.uniforms.uTime.value = t
    material.uniforms.uScale.value = state.viewport.dpr * 20
    moonMaterial.uniforms.uTime.value = t
    moonMaterial.uniforms.uScale.value = state.viewport.dpr * 20
    if (reduce) return
    const dt = Math.min(delta, 0.1)
    if (spin.current) spin.current.rotation.y += dt * (rise ? 0.04 : (Math.PI * 2) / 90)
    if (orbit.current && !mobile) orbit.current.rotation.y += dt * ((Math.PI * 2) / 45)
    if (root.current && !rise) {
      root.current.rotation.y += (mouse.x * 0.18 - root.current.rotation.y) * 0.04
      root.current.rotation.x += (0.1 + mouse.y * 0.1 - root.current.rotation.x) * 0.04
    }
    if (rise) {
      if (sun.current) { const a = 1.57 + 0.6 * Math.sin(t * 0.1); sun.current.position.set(RX * Math.cos(a), CY + RY * Math.sin(a), 0) }
      if (earth.current) { const a = 1.57 - 0.5 * Math.sin(t * 0.08 + 1.2); earth.current.position.set(RX * 1.12 * Math.cos(a), CY + RY * 1.1 * Math.sin(a), 0) }
    }
  })

  return (
    <>
      <mesh position={[0, CY, -0.5]} material={glowMat}>
        <planeGeometry args={[R * 3.2, R * 3.2]} />
      </mesh>

      <group ref={root}>
        <group position={[0, CY, 0]} rotation={[0, 0, rise ? 0 : 0.41]}>
          <group ref={spin}>
            <mesh>
              <sphereGeometry args={[R * 0.985, 64, 64]} />
              {body === 'earth' && tex ? (
                <meshBasicMaterial map={tex} color="#9fb0c8" />
              ) : (
                <meshBasicMaterial color={pal.solid} />
              )}
            </mesh>
            {dots && <points geometry={dots.geometry} material={material} frustumCulled={false} />}
          </group>
        </group>

        {!rise && moon && moonDots && (
          <group rotation={[0.35, 0, 0.1]}>
            <group ref={orbit} rotation={[0, mobile ? 0.8 : 0, 0]}>
              <points position={[3.1, 0, 0]} geometry={moonDots.geometry} material={moonMaterial} frustumCulled={false} />
            </group>
          </group>
        )}
      </group>

      {rise && (
        <>
          <Line points={ring1} color="#ffffff" transparent opacity={0.16} lineWidth={1} />
          <Line points={ring2} color="#ffffff" transparent opacity={0.09} lineWidth={1} />
          {markers && (
            <>
              <group ref={sun} position={[0, CY + RY, 0]}>
                <mesh><circleGeometry args={[0.09, 24]} /><meshBasicMaterial color="#FFB547" /></mesh>
                <mesh><circleGeometry args={[0.35, 32]} /><meshBasicMaterial color="#FFB547" transparent opacity={0.2} depthWrite={false} blending={THREE.AdditiveBlending} /></mesh>
                <mesh><circleGeometry args={[0.8, 32]} /><meshBasicMaterial color="#FFB547" transparent opacity={0.07} depthWrite={false} blending={THREE.AdditiveBlending} /></mesh>
              </group>
              <group ref={earth} position={[0, CY + RY * 1.1, 0]}>
                <mesh><circleGeometry args={[0.075, 24]} /><meshBasicMaterial color="#4DA3FF" /></mesh>
                <mesh><circleGeometry args={[0.3, 32]} /><meshBasicMaterial color="#4DA3FF" transparent opacity={0.22} depthWrite={false} blending={THREE.AdditiveBlending} /></mesh>
              </group>
            </>
          )}
        </>
      )}
    </>
  )
}

export type Planet3DProps = { body: Body3D; mode?: Mode3D; markers?: boolean; moon?: boolean }

export default function Planet3D({ body, mode = 'side', markers = false, moon = false }: Planet3DProps) {
  const reduce = useMemo(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches, [])
  const mobile = useMemo(() => window.innerWidth < 768, [])
  const [quality, setQuality] = useState<Quality>(mobile ? 'low' : 'high')

  return (
    <Canvas
      camera={{ position: [0, 0, 9], fov: 40 }}
      dpr={[1, quality === 'high' ? 2 : 1.25]}
      frameloop={reduce ? 'demand' : 'always'}
      gl={{ antialias: false, powerPreference: 'high-performance' }}
    >
      <PerformanceMonitor onDecline={() => setQuality('low')} />
      <Scene body={body} mode={mode} markers={markers} moon={moon} reduce={reduce} mobile={mobile} quality={quality} />
    </Canvas>
  )
}
