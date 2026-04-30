/**
 * store/useGameStore.js — Zustand global state store.
 * Receives world state from WebSocket and exposes slices to components.
 */
import { create } from 'zustand'

export const useGameStore = create((set, get) => ({
  // Connection
  connected: false,
  setConnected: (v) => set({ connected: v }),

  // World state from backend
  tick: 0,
  baseIntegrity: 100,
  npcs: [],
  resources: [],
  events: [],
  grid: [],
  influenceMap: [],

  // Interaction logs (client-side rolling buffer)
  logs: [],
  addLog: (entry) => set((s) => ({
    logs: [entry, ...s.logs].slice(0, 50),
  })),

  // UI toggles
  showInfluence: false,
  showPaths: true,
  toggleInfluence: () => set((s) => ({ showInfluence: !s.showInfluence })),
  togglePaths: () => set((s) => ({ showPaths: !s.showPaths })),

  // Update entire world state from websocket payload
  applyWorldState: (data) => {
    const prev = get();
    // Detect new social events by comparing NPC statuses
    data.npcs?.forEach((npc) => {
      const old = prev.npcs.find((n) => n.id === npc.id);
      if (old && old.status !== npc.status && npc.status.includes('💬')) {
        set((s) => ({
          logs: [
            { tick: data.tick, text: npc.status.replace('💬 ', ''), npc: npc.name },
            ...s.logs,
          ].slice(0, 50),
        }));
      }
    });

    set({
      tick:           data.tick ?? 0,
      baseIntegrity:  data.base_integrity ?? 100,
      npcs:           data.npcs ?? [],
      resources:      data.resources ?? [],
      events:         data.events ?? [],
      grid:           data.grid ?? [],
      influenceMap:   data.influence_map ?? [],
    });
  },
}))
