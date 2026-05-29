const BOARD_SIDE_LENGTH = 5;
const PLAYER1 = 1;
const PLAYER2 = 2;
const FALL_SPEED_TILE = 8;
const FALL_SPEED_PIECE = 7;
const SLIDE_SPEED = 12;
const AI_DELAY_MS = 750;

const DIRECTIONS = [[1,0],[1,-1],[0,-1],[-1,0],[-1,1],[0,1]];
const MOVE_DIRECTIONS = {
  [PLAYER1]: [[0,-1],[1,-1],[-1,0]],
  [PLAYER2]: [[0,1],[-1,1],[1,0]]
};
const KING_DIRECTIONS = DIRECTIONS;

function generateGrid(sideLength) {
  const coords = [];
  for (let q = -(sideLength - 1); q < sideLength; q++) {
    const r1 = Math.max(-(sideLength - 1), -q - (sideLength - 1));
    const r2 = Math.min(sideLength - 1, -q + (sideLength - 1));
    for (let r = r1; r <= r2; r++) coords.push([q, r]);
  }
  return coords;
}

function hexToPixel(q, r, radius, cx, cy) {
  return [
    cx + radius * 1.5 * q,
    cy + radius * (Math.sqrt(3) / 2 * q + Math.sqrt(3) * r)
  ];
}

function pixelToHex(px, py, radius, cx, cy) {
  const x = px - cx, y = py - cy;
  const q = (2 / 3 * x) / radius;
  const r = (-1 / 3 * x + Math.sqrt(3) / 3 * y) / radius;
  return hexRound(q, r);
}

function hexRound(q, r) {
  const s = -q - r;
  let rq = Math.round(q), rr = Math.round(r), rs = Math.round(s);
  const dq = Math.abs(rq - q), dr = Math.abs(rr - r), ds = Math.abs(rs - s);
  if (dq > dr && dq > ds) rq = -rr - rs;
  else if (dr > ds) rr = -rq - rs;
  return [rq, rr];
}

function getHexCorners(q, r, radius, cx, cy) {
  const [hx, hy] = hexToPixel(q, r, radius, cx, cy);
  const corners = [];
  for (let i = 0; i < 6; i++) {
    const a = Math.PI / 180 * 60 * i;
    corners.push([hx + radius * Math.cos(a), hy + radius * Math.sin(a)]);
  }
  return corners;
}

if (typeof module !== 'undefined') {
  module.exports = {
    BOARD_SIDE_LENGTH, PLAYER1, PLAYER2, FALL_SPEED_TILE, FALL_SPEED_PIECE,
    SLIDE_SPEED, AI_DELAY_MS, DIRECTIONS, MOVE_DIRECTIONS, KING_DIRECTIONS,
    generateGrid, hexToPixel, pixelToHex, hexRound, getHexCorners
  };
}
