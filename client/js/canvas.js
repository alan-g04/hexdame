class HexCanvas {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.hexRadius = 0;
    this.pieceRadius = 0;
    this.cx = 0;
    this.cy = 0;
    this._computeLayout();
    window.addEventListener('resize', () => this._computeLayout());
  }

  _computeLayout() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
    const n = BOARD_SIDE_LENGTH;
    const pad = 0.82;
    this.hexRadius = Math.floor(Math.min(
      this.canvas.width  * pad / ((2 * n - 1) * 1.5),
      this.canvas.height * pad / ((2 * n - 1) * Math.sqrt(3))
    ));
    this.pieceRadius = Math.floor(this.hexRadius * 0.7);
    this.cx = Math.floor(this.canvas.width  / 2);
    this.cy = Math.floor(this.canvas.height / 2);
  }

  render(gs) {
    const ctx = this.ctx;
    ctx.fillStyle = '#0f0f1a';
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    this._drawBoard(gs.board);
    this._drawHighlights(gs.selectedCoord, gs.possibleMoves);
    this._drawPieces(gs.board);
  }

  _drawBoard(board) {
    for (const [q, r] of board.hexCoordsArray) {
      const fill = (q + r) % 2 === 0 ? '#4a4a6a' : '#2d2d4a';
      this._drawHex(q, r, fill, '#7a7a9a');
    }
  }

  _drawHex(q, r, fill, stroke) {
    const ctx = this.ctx;
    const corners = getHexCorners(q, r, this.hexRadius, this.cx, this.cy);
    ctx.beginPath();
    ctx.moveTo(corners[0][0], corners[0][1]);
    for (let i = 1; i < 6; i++) ctx.lineTo(corners[i][0], corners[i][1]);
    ctx.closePath();
    ctx.fillStyle = fill;
    ctx.fill();
    ctx.strokeStyle = stroke;
    ctx.lineWidth = 1;
    ctx.stroke();
  }

  _drawHighlights(sel, moves) {
    if (!sel) return;
    const ctx = this.ctx;
    const [sx, sy] = hexToPixel(sel[0], sel[1], this.hexRadius, this.cx, this.cy);
    ctx.beginPath();
    ctx.arc(sx, sy, this.hexRadius * 0.85, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,255,0,0.22)';
    ctx.fill();

    for (const [q, r] of moves) {
      const [mx, my] = hexToPixel(q, r, this.hexRadius, this.cx, this.cy);
      ctx.beginPath();
      ctx.arc(mx, my, this.hexRadius * 0.32, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(80,255,120,0.55)';
      ctx.fill();
    }
  }

  _drawPieces(board) {
    for (const p of board.pieces.values()) {
      const [x, y] = hexToPixel(p.q, p.r, this.hexRadius, this.cx, this.cy);
      this._drawPieceAt(x, y, p.color, p.isKing);
    }
  }

  _drawPieceAt(x, y, color, isKing) {
    const ctx = this.ctx;
    const r = this.pieceRadius;
    const baseColor  = color === PLAYER1 ? '#bb2222' : '#2244bb';
    const kingColor  = color === PLAYER1 ? '#ee5555' : '#5577ee';
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fillStyle = isKing ? kingColor : baseColor;
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.18)';
    ctx.lineWidth = 2;
    ctx.stroke();
    if (isKing) {
      ctx.beginPath();
      ctx.arc(x, y, r * 0.42, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255,255,255,0.35)';
      ctx.fill();
    }
  }

  getHexAt(px, py) {
    return pixelToHex(px, py, this.hexRadius, this.cx, this.cy);
  }
}

HexCanvas.prototype.renderWithAnim = function(gs, anim) {
  const ctx = this.ctx;
  ctx.fillStyle = '#0f0f1a';
  ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

  if (anim.phase === 'tiles') {
    this._drawTilesAnim(anim);
  } else {
    if (gs.board) this._drawBoard(gs.board);
    this._drawHighlights(gs.selectedCoord, gs.possibleMoves);
    this._drawPiecesAnim(anim);
  }
};

HexCanvas.prototype._drawTilesAnim = function(anim) {
  for (const t of anim.tileAnims) {
    const fill = (t.q + t.r) % 2 === 0 ? '#4a4a6a' : '#2d2d4a';
    const corners = [];
    for (let i = 0; i < 6; i++) {
      const angle = Math.PI / 180 * 60 * i;
      corners.push([t.x + this.hexRadius * Math.cos(angle), t.currentY + this.hexRadius * Math.sin(angle)]);
    }
    this.ctx.beginPath();
    this.ctx.moveTo(corners[0][0], corners[0][1]);
    for (let i = 1; i < 6; i++) this.ctx.lineTo(corners[i][0], corners[i][1]);
    this.ctx.closePath();
    this.ctx.fillStyle = fill; this.ctx.fill();
    this.ctx.strokeStyle = '#7a7a9a'; this.ctx.lineWidth = 1; this.ctx.stroke();
  }
};

HexCanvas.prototype._drawPiecesAnim = function(anim) {
  for (const pa of anim.pieceAnims.values()) {
    this._drawPieceAt(pa.pixelX, pa.pixelY, pa.piece.color, pa.piece.isKing);
  }
};
