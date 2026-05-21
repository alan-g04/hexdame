# Hexdame Webapp Design

**Date:** 2026-05-21
**Status:** Approved

## Overview

Convert the existing Pygame desktop game Hexdame (hexagonal checkers) into a browser-based multiplayer webapp. The original Python/Pygame source is archived in `legacy/`. The new stack is Node.js + Socket.io (server) and vanilla HTML/CSS/JS with HTML5 Canvas (client).

## Scope

**In scope:**
- Port all game logic (hex grid, move rules, mandatory jumps, multi-jumps, king promotion) from Python to JavaScript
- Canvas-based rendering of the hex board with dark theme by default
- Intro animations: board tiles fall in, then pieces fall in (matching Pygame behavior)
- Captured-piece side panels
- vs Computer mode (random-move AI, matching current Pygame AI behavior)
- Online multiplayer via room codes (4-char code, no login required)
- Anonymous display names chosen at game start

**Out of scope (future sprints):**
- Theme/customization menu (pieces, board, background colors)
- Persistent stats or accounts
- Matchmaking queue

## Architecture

```
hexdame/
├── legacy/          # Original Pygame source (archived)
├── server/
│   ├── game/
│   │   ├── board.js     # Hex grid generation, piece placement
│   │   ├── logic.js     # Move validation, promotion, game-over detection
│   │   └── ai.js        # Random AI (mirrors Python AIPlayer)
│   ├── rooms.js         # In-memory Map of roomCode -> GameState + player sockets
│   ├── socket.js        # Socket.io event handlers
│   └── index.js         # Express + Socket.io entry point
├── client/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── canvas.js    # Hex rendering, animation engine (tile fall, piece fall, slide)
│       ├── game.js      # Client-side state mirror + input handling
│       └── socket.js    # Socket.io client wrapper + event dispatch
└── package.json
```

### Authoritative server model

The server holds canonical `GameState` per room. Clients send move intents; the server validates using `logic.js`, mutates state, and broadcasts a full state snapshot to both players. Clients never self-validate legality — they only render server-provided state and forward clicks.

## Data Model

```js
// GameState (lives server-side)
{
  board: Map<"q,r", { color: 1|2, isKing: bool }>,
  turn: 1 | 2,
  mustJump: bool,
  allPlayerMoves: Object,   // { "q,r": { moves: [], jumps: [] } }
  capturedByP1: [],         // pieces captured by player 1
  capturedByP2: [],
  winner: null | 1 | 2,
  players: {
    1: { socketId, displayName },
    2: { socketId, displayName }
  }
}
```

## Socket.io Event Contract

### Client → Server

| Event | Payload | Notes |
|-------|---------|-------|
| `create-room` | `{ displayName }` | Returns `{ roomCode, playerSlot: 1 }` |
| `join-room` | `{ roomCode, displayName }` | Returns `room-joined` or `join-error` |
| `move` | `{ roomCode, from: [q,r], to: [q,r] }` | Server validates; rejects with `move-error` if illegal |
| `request-rematch` | `{ roomCode }` | Either player triggers; server resets state |
| `request-rematch` | `{ roomCode }` | Either player can request; server resets state and notifies both |

### Server → Client

| Event | Payload | Notes |
|-------|---------|-------|
| `room-joined` | `{ roomCode, playerSlot, opponentName? }` | Confirms join; includes opponent name if both present |
| `state-update` | Full `GameState` snapshot (serialized) | Sent to both players after every valid move |
| `move-error` | `{ reason }` | Sent only to the sender of the invalid move |
| `opponent-disconnected` | — | Sent when the other player's socket drops |
| `game-over` | `{ winner }` | Included in final `state-update`; also emitted separately |

## Sprint Plan

| Sprint | Goal | Deliverable | Test |
|--------|------|-------------|------|
| S0 | Repo + scaffold | GitHub repo, legacy code committed, Node.js project with Express serving static Canvas page, hex board renders statically | Board visible in browser at localhost |
| S1 | Local game logic | Full hex game logic in JS, local 2-player game fully playable in browser (client-only, no server state) | Play a full game to completion both players on same screen |
| S2 | AI opponent | Random AI runs server-side after each human move; "vs Computer" mode available from lobby | Play vs AI, AI makes valid moves, game ends correctly |
| S3 | Animations | Tile fall-in animation, piece fall-in (P1 then P2), piece slide on move | Animations play on game start and on each move |
| S4 | Captured pieces panel | Left/right panels show captured pieces stacking during game | Capture a piece, confirm it appears in the panel |
| S5 | Multiplayer rooms | Socket.io server, room create/join with 4-char code, two separate browser tabs play a full online game | Two tabs, one creates room, other joins with code, play a complete game |
| S6 | Lobby + polish | Name entry screen, disconnection handling, game-over + rematch flow, dark theme finalized | Full E2E: name entry → room → game → game over → rematch |

## Hex Grid

Flat-top hexagonal grid using axial coordinates `(q, r)`. Board side length N=5 (61 hexes). Pixel conversion uses the same formulas as the Pygame original.

Player 1 starts at positive-r rows (bottom). Player 2 starts at negative-r rows (top). Promotion zones match the existing `logic.py` definitions.

## AI

Port of the existing `AIPlayer` class: random move selection, with jump moves prioritized when mandatory. No minimax in this scope.

## Rendering

HTML5 Canvas, re-rendered each frame via `requestAnimationFrame`. Hex outlines drawn as flat-top polygons. Pieces drawn as filled circles with an inner ring for kings. Dark theme: dark board tiles, red P1 pieces, blue P2 pieces (matching Pygame Dark theme).

## Error Handling

- Invalid moves: rejected server-side with `move-error`; client shows brief flash or ignores
- Disconnection: opponent gets `opponent-disconnected` event; game pauses; no auto-resume in this scope
- Room not found: `join-error` event returned to client
