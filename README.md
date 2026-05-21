# Hexdame

Hexagonal checkers (Hexdame) playable in the browser. Supports local 2-player, vs AI, and online multiplayer via room codes.

## Play modes

- **Local 2-player** — two players on the same screen
- **vs Computer** — play against a random-move AI
- **Online** — create a room, share the 4-letter code with a friend

## Rules

- Pieces move one step in their forward direction (P1 moves up, P2 moves down)
- Jumps over opponent pieces are mandatory
- Multi-jump chains are allowed in a single turn
- Reach the opponent's back edge to become a king (moves in all 6 directions)
- Win by capturing all opponent pieces or leaving them with no moves

## Run locally

```
npm install
npm start
```

Open http://localhost:3000

## Development

```
npm run dev   # auto-restart on file changes
npm test      # Jest unit tests for game logic
```

## Original desktop version

The original Python/Pygame version is archived in `legacy/`.
