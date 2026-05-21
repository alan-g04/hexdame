const { BOARD_SIDE_LENGTH, PLAYER1, PLAYER2, generateGrid } = require('./hex');

class Board {
  constructor(sideLength) {
    this.sideLength = sideLength;
    this.hexCoordsSet = new Set();
    this.hexCoordsArray = [];
    this.pieces = new Map();
    this._generateGrid();
  }

  _generateGrid() {
    this.hexCoordsArray = generateGrid(this.sideLength);
    this.hexCoordsSet = new Set(this.hexCoordsArray.map(([q, r]) => `${q},${r}`));
  }

  hasHex(q, r) { return this.hexCoordsSet.has(`${q},${r}`); }

  getPiece(q, r) { return this.pieces.get(`${q},${r}`) || null; }

  setPiece(q, r, piece) { this.pieces.set(`${q},${r}`, piece); }

  removePiece(q, r) {
    const piece = this.pieces.get(`${q},${r}`) || null;
    this.pieces.delete(`${q},${r}`);
    return piece;
  }

  movePiece(fromQ, fromR, toQ, toR) {
    const piece = this.pieces.get(`${fromQ},${fromR}`);
    if (!piece) return null;
    this.pieces.delete(`${fromQ},${fromR}`);
    piece.q = toQ; piece.r = toR;
    this.pieces.set(`${toQ},${toR}`, piece);
    return piece;
  }

  initializePieces() {
    this.pieces.clear();
    const posP1 = [
      [-1,4],[-2,4],[-3,4],[0,4],
      [-2,3],[-1,3],[0,3],[1,3],
      [-1,2],[0,2],[1,2],[2,2],
      [0,1],[1,1],[2,1],[3,1]
    ];
    const posP2 = [
      [0,-4],[1,-4],[2,-4],[3,-4],
      [-1,-3],[0,-3],[1,-3],[2,-3],
      [-2,-2],[-1,-2],[0,-2],[1,-2],
      [-3,-1],[-2,-1],[-1,-1],[0,-1]
    ];
    for (const [q, r] of posP1) {
      if (this.hasHex(q, r))
        this.pieces.set(`${q},${r}`, { q, r, color: PLAYER1, isKing: false });
    }
    for (const [q, r] of posP2) {
      if (this.hasHex(q, r))
        this.pieces.set(`${q},${r}`, { q, r, color: PLAYER2, isKing: false });
    }
  }

  getPiecesForPlayer(color) {
    return [...this.pieces.values()].filter(p => p.color === color);
  }
}

if (typeof module !== 'undefined') module.exports = { Board };
