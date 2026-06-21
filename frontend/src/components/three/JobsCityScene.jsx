import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useThree, useFrame } from "@react-three/fiber";
import { OrbitControls, Stars } from "@react-three/drei";
import * as THREE from "three";
import USAMap from "./USAMap";
import CompanyBuildings from "./CompanyBuildings";
import { api } from "@/lib/api";

/**
 * Smoothly tween camera + orbit-controls target whenever flyTarget changes.
 * flyTarget = [worldX, worldZ, zoomTier, salt] — salt forces re-trigger.
 */
function CameraFly({ flyTarget, focusedWorldPos, controlsRef }) {
  const { camera } = useThree();
  const tweenRef = useRef(null);

  useEffect(() => {
    if (!flyTarget) return;
    const [tx, tz, zoom] = flyTarget;
    const startPos = camera.position.clone();
    const startTarget = controlsRef.current?.target?.clone() || new THREE.Vector3(0, 0, 0);
    const offsets = zoom === "close"
      ? { dx: 6, dy: 14, dz: 9, ty: 3 }
      : { dx: 12, dy: 24, dz: 18, ty: 2 };
    const endTarget = new THREE.Vector3(tx, offsets.ty, tz);
    const endPos = new THREE.Vector3(tx + offsets.dx, offsets.dy, tz + offsets.dz);
    tweenRef.current = { t: 0, startPos, endPos, startTarget, endTarget };
    if (controlsRef.current) controlsRef.current.autoRotate = false;
  }, [flyTarget, camera, controlsRef]);

  // Auto-rotate around the focused tower until user interacts
  useEffect(() => {
    if (!controlsRef.current) return;
    if (focusedWorldPos) {
      controlsRef.current.autoRotate = true;
      controlsRef.current.autoRotateSpeed = 0.5;
    } else {
      controlsRef.current.autoRotate = false;
    }
  }, [focusedWorldPos, controlsRef]);

  useFrame((_, dt) => {
    const w = tweenRef.current;
    if (!w) return;
    w.t = Math.min(1, w.t + dt * 0.8);
    const e = 1 - Math.pow(1 - w.t, 3);
    camera.position.lerpVectors(w.startPos, w.endPos, e);
    if (controlsRef.current) {
      controlsRef.current.target.lerpVectors(w.startTarget, w.endTarget, e);
      controlsRef.current.update();
    }
    if (w.t >= 1) {
      tweenRef.current = null;
      if (controlsRef.current && focusedWorldPos) {
        controlsRef.current.autoRotate = true;
      }
    }
  });
  return null;
}

export default function JobsCityScene({
  onCompanyClick,
  selected,
  query = "",
  flyTarget,
  onCitiesLoaded,
}) {
  const [cities, setCities] = useState(null);
  const controlsRef = useRef(null);

  useEffect(() => {
    api
      .get("/jobs-city/buildings")
      .then((r) => {
        setCities(r.data.cities);
        onCitiesLoaded?.(r.data.cities);
      })
      .catch(() => setCities([]));
  }, [onCitiesLoaded]);

  const focusedWorldPos = useMemo(() => {
    if (!selected) return null;
    return [selected.x, 0, selected.z];
  }, [selected]);

  return (
    <Canvas
      className="three-canvas"
      shadows
      camera={{ position: [0, 50, 70], fov: 45, near: 0.1, far: 500 }}
      gl={{ antialias: true }}
    >
      <color attach="background" args={["#190B1C"]} />
      <fog attach="fog" args={["#190B1C", 70, 230]} />

      <hemisphereLight args={["#FFC371", "#3a1f30", 0.7]} />
      <directionalLight
        position={[30, 50, 25]}
        intensity={1.4}
        color={"#FF7B54"}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-left={-80}
        shadow-camera-right={80}
        shadow-camera-top={60}
        shadow-camera-bottom={-60}
      />
      <pointLight position={[-40, 25, 30]} intensity={0.7} color="#FF5F6D" />
      <ambientLight intensity={0.22} color={"#FFB24C"} />

      <Stars
        radius={250}
        depth={50}
        count={3000}
        factor={4}
        saturation={0}
        fade
        speed={0.5}
      />

      <Suspense fallback={null}>
        <USAMap accent="#FFB24C" />
        {cities && (
          <CompanyBuildings
            cities={cities}
            onCompanyClick={onCompanyClick}
            selected={selected}
            query={query}
          />
        )}
      </Suspense>

      <CameraFly flyTarget={flyTarget} focusedWorldPos={focusedWorldPos} controlsRef={controlsRef} />

      <OrbitControls
        ref={controlsRef}
        enablePan
        minDistance={15}
        maxDistance={200}
        maxPolarAngle={Math.PI / 2.05}
        target={[0, 0, 0]}
      />
    </Canvas>
  );
}
