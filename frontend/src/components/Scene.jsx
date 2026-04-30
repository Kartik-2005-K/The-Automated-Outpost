/**
 * components/Scene.jsx — Main Three.js 3D scene using @react-three/fiber.
 *
 * Renders:
 *  - Isometric ground plane with a 30×30 grid
 *  - Static obstacle meshes (walls/rocks)
 *  - Resource nodes (pulsing spheres)
 *  - NPC capsules with floating name labels
 *  - NPC path lines
 *  - Influence overlay heatmap (toggleable)
 *  - Base structure at map centre
 */
import React, { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Text, Line } from '@react-three/drei'
import * as THREE from 'three'
import { useGameStore } from '../store/useGameStore'

const GRID_W = 30
const GRID_H = 30
const CELL   = 1       // metres per cell
const BASE   = [14, 0, 14]

// ── Resource colours ──
const RES_COLOR = { Food: '#39ff85', Fuel: '#ffa040', Scrap: '#aab4c8' }
const RES_EMIT  = { Food: '#1a7a3a', Fuel: '#7a4500', Scrap: '#3a4050' }

// ──────────────────────────────────────────────
// Ground plane
// ──────────────────────────────────────────────
function Ground() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow position={[14.5, -0.05, 14.5]}>
      <planeGeometry args={[GRID_W, GRID_H, GRID_W, GRID_H]} />
      <meshStandardMaterial
        color="#0a1525"
        wireframe={false}
        roughness={0.9}
        metalness={0.1}
      />
    </mesh>
  )
}

// Grid lines
function GridLines() {
  const points = useMemo(() => {
    const lines = []
    for (let i = 0; i <= GRID_W; i++) {
      lines.push([[i, 0.005, 0], [i, 0.005, GRID_H]])
    }
    for (let j = 0; j <= GRID_H; j++) {
      lines.push([[0, 0.005, j], [GRID_W, 0.005, j]])
    }
    return lines
  }, [])

  return (
    <>
      {points.map((pts, i) => (
        <Line
          key={i}
          points={pts}
          color="#182840"
          lineWidth={0.5}
          opacity={0.6}
          transparent
        />
      ))}
    </>
  )
}

// ──────────────────────────────────────────────
// Base structure
// ──────────────────────────────────────────────
function BaseStructure() {
  const meshRef = useRef()
  useFrame((_, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.2
    }
  })
  return (
    <group position={BASE}>
      {/* Platform */}
      <mesh position={[0, 0.1, 0]} receiveShadow>
        <cylinderGeometry args={[2.5, 3, 0.2, 8]} />
        <meshStandardMaterial color="#112040" metalness={0.8} roughness={0.3} />
      </mesh>
      {/* Central core */}
      <mesh position={[0, 0.9, 0]} castShadow>
        <boxGeometry args={[1.5, 1.6, 1.5]} />
        <meshStandardMaterial color="#1a3060" metalness={0.7} roughness={0.2} emissive="#0a1840" />
      </mesh>
      {/* Spinning ring */}
      <mesh ref={meshRef} position={[0, 1.4, 0]}>
        <torusGeometry args={[1.2, 0.06, 8, 32]} />
        <meshStandardMaterial color="#40a0ff" emissive="#1060c0" emissiveIntensity={0.8} />
      </mesh>
      {/* Top antenna */}
      <mesh position={[0, 2.2, 0]}>
        <cylinderGeometry args={[0.04, 0.04, 1.0]} />
        <meshStandardMaterial color="#40a0ff" emissive="#40a0ff" emissiveIntensity={0.5} />
      </mesh>
      {/* Glow light */}
      <pointLight color="#4060ff" intensity={1.2} distance={8} decay={2} position={[0, 1.5, 0]} />
    </group>
  )
}

// ──────────────────────────────────────────────
// Obstacle meshes
// ──────────────────────────────────────────────
function Obstacles({ grid }) {
  const obstacles = useMemo(() => {
    const obs = []
    for (let y = 0; y < GRID_H; y++) {
      for (let x = 0; x < GRID_W; x++) {
        if (grid[y * GRID_W + x] === 0) {
          const isEdge = x === 0 || y === 0 || x === GRID_W-1 || y === GRID_H-1
          obs.push({ x, y, isEdge })
        }
      }
    }
    return obs
  }, [grid])

  return (
    <>
      {obstacles.map(({ x, y, isEdge }) => (
        <mesh key={`obs_${x}_${y}`} position={[x + 0.5, isEdge ? 0.5 : 0.4, y + 0.5]} castShadow>
          <boxGeometry args={isEdge ? [1, 1, 1] : [0.8, 0.8, 0.8]} />
          <meshStandardMaterial
            color={isEdge ? '#0d1e38' : '#1a2840'}
            metalness={0.6}
            roughness={0.4}
            emissive={isEdge ? '#060e1a' : '#0a1428'}
          />
        </mesh>
      ))}
    </>
  )
}

// ──────────────────────────────────────────────
// Resource nodes
// ──────────────────────────────────────────────
function ResourceNode({ resource }) {
  const meshRef = useRef()
  useFrame((state) => {
    if (meshRef.current) {
      const t = state.clock.elapsedTime
      meshRef.current.position.y = 0.4 + Math.sin(t * 1.5 + resource.position[0]) * 0.08
      meshRef.current.scale.setScalar(0.95 + Math.sin(t * 2 + resource.position[1]) * 0.05)
    }
  })

  if (!resource.quantity || resource.quantity <= 0) return null
  const [rx, ry] = resource.position
  const col  = RES_COLOR[resource.type] || '#888'
  const emit = RES_EMIT[resource.type]  || '#333'

  return (
    <group position={[rx + 0.5, 0, ry + 0.5]}>
      <mesh ref={meshRef} castShadow>
        <sphereGeometry args={[0.22, 12, 12]} />
        <meshStandardMaterial color={col} emissive={emit} emissiveIntensity={0.7} metalness={0.4} roughness={0.3} />
      </mesh>
      <pointLight color={col} intensity={0.4} distance={3} decay={2} position={[0, 0.4, 0]} />
      <Text
        position={[0, 0.8, 0]}
        fontSize={0.18}
        color={col}
        anchorX="center"
        anchorY="bottom"
        font="https://fonts.gstatic.com/s/jetbrainsmono/v18/tDbY2o-flEEny0FZhsfKu5WU4zr3E_BX0PnT8RD8yKxTOlOTkqs.woff2"
      >
        {resource.type[0]}×{resource.quantity}
      </Text>
    </group>
  )
}

// ──────────────────────────────────────────────
// NPC
// ──────────────────────────────────────────────
function NPCMesh({ npc, showPaths }) {
  const meshRef = useRef()
  const [px, py] = npc.position

  useFrame((state) => {
    if (meshRef.current) {
      const t = state.clock.elapsedTime
      meshRef.current.position.y = 0.55 + Math.abs(Math.sin(t * 3.5 + px)) * 0.04
    }
  })

  const isMoving = npc.path && npc.path.length > 1
  const goalBgColor = {
    Survive: '#ff4d6d',
    Rest: '#1e90ff',
    MaintainSocial: '#c084fc',
    RepairBase: '#ff8c42',
    Idle: '#4a6080',
  }[npc.current_goal] || '#4a6080'

  // Convert 2D path to 3D
  const pathPoints = useMemo(() => {
    if (!npc.path || npc.path.length < 2) return []
    return npc.path.map(([x, y]) => [x + 0.5, 0.12, y + 0.5])
  }, [npc.path])

  return (
    <group position={[px + 0.5, 0, py + 0.5]}>
      {/* Body capsule */}
      <mesh ref={meshRef} castShadow>
        <capsuleGeometry args={[0.2, 0.5, 8, 16]} />
        <meshStandardMaterial
          color={npc.color}
          emissive={npc.color}
          emissiveIntensity={0.3}
          metalness={0.2}
          roughness={0.5}
        />
      </mesh>

      {/* Glow */}
      <pointLight color={npc.color} intensity={0.5} distance={3} decay={2} position={[0, 0.5, 0]} />

      {/* Name + goal label */}
      <Text
        position={[0, 1.3, 0]}
        fontSize={0.22}
        color={npc.color}
        anchorX="center"
        anchorY="bottom"
        outlineWidth={0.02}
        outlineColor="#000"
      >
        {npc.name}
      </Text>
      <Text
        position={[0, 1.05, 0]}
        fontSize={0.14}
        color={goalBgColor}
        anchorX="center"
        anchorY="bottom"
        outlineWidth={0.01}
        outlineColor="#000"
      >
        [{npc.current_goal}]
      </Text>

      {/* Path line */}
      {showPaths && pathPoints.length >= 2 && (
        <Line
          points={pathPoints}
          color={npc.color}
          lineWidth={1.5}
          opacity={0.5}
          transparent
        />
      )}
    </group>
  )
}

// ──────────────────────────────────────────────
// Influence overlay heatmap
// ──────────────────────────────────────────────
function InfluenceOverlay({ influenceMap, visible }) {
  const meshRef = useRef()

  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(GRID_W, GRID_H, GRID_W - 1, GRID_H - 1)
    return geo
  }, [])

  useMemo(() => {
    if (!influenceMap || !influenceMap.length) return
    const colors = []
    for (let y = 0; y < GRID_H; y++) {
      for (let x = 0; x < GRID_W; x++) {
        const v = influenceMap[y * GRID_W + x] || 0
        colors.push(v, 0, 0)   // red channel = danger
      }
    }
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3))
  }, [influenceMap, geometry])

  if (!visible) return null

  return (
    <mesh
      ref={meshRef}
      rotation={[-Math.PI / 2, 0, 0]}
      position={[14.5, 0.06, 14.5]}
      geometry={geometry}
    >
      <meshBasicMaterial
        vertexColors
        transparent
        opacity={0.45}
        depthWrite={false}
      />
    </mesh>
  )
}

// ──────────────────────────────────────────────
// Main Scene component
// ──────────────────────────────────────────────
export default function Scene() {
  const { npcs, resources, events, grid, influenceMap, showInfluence, showPaths } = useGameStore()

  return (
    <Canvas
      shadows
      camera={{
        position: [20, 24, 20],
        fov: 50,
        near: 0.1,
        far: 200,
      }}
      gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping }}
      style={{ width: '100%', height: '100%' }}
    >
      {/* Lighting */}
      <ambientLight intensity={0.15} color="#1a2840" />
      <directionalLight
        position={[20, 30, 10]}
        intensity={0.8}
        color="#c8d8ff"
        castShadow
        shadow-mapSize={[2048, 2048]}
      />
      <hemisphereLight skyColor="#0a1830" groundColor="#050810" intensity={0.4} />

      {/* Stars */}
      {useMemo(() => (
        Array.from({ length: 120 }).map((_, i) => (
          <mesh key={i} position={[
            (Math.random() - 0.5) * 120,
            20 + Math.random() * 40,
            (Math.random() - 0.5) * 120,
          ]}>
            <sphereGeometry args={[0.05 + Math.random() * 0.1, 4, 4]} />
            <meshBasicMaterial color="#ffffff" opacity={0.4 + Math.random() * 0.6} transparent />
          </mesh>
        ))
      ), [])}

      {/* Scene geometry */}
      <Ground />
      <GridLines />
      <BaseStructure />

      {grid.length > 0 && <Obstacles grid={grid} />}

      {resources.map((r) => (
        <ResourceNode key={r.id} resource={r} />
      ))}

      {npcs.map((npc) => (
        <NPCMesh key={npc.id} npc={npc} showPaths={showPaths} />
      ))}

      <InfluenceOverlay influenceMap={influenceMap} visible={showInfluence} />

      {/* Orbit controls — isometric feel */}
      <OrbitControls
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        minDistance={8}
        maxDistance={60}
        maxPolarAngle={Math.PI / 2.5}
        target={[14.5, 0, 14.5]}
      />

      {/* Fog */}
      <fog attach="fog" args={['#050810', 60, 120]} />
    </Canvas>
  )
}
