class PieceAnim {
  constructor(piece, x, y) {
    this.piece = piece;
    this.pixelX = x; this.pixelY = y;
    this.targetX = x; this.targetY = y;
    this.isFalling = false;
    this.isSliding = false;
    this.isCaptured = false;
    this.captureTargetX = 0; this.captureTargetY = 0;
  }

  update() {
    if (this.isFalling) {
      this.pixelY += FALL_SPEED_PIECE;
      if (this.pixelY >= this.targetY) { this.pixelY = this.targetY; this.isFalling = false; }
      return true;
    }
    if (this.isSliding) {
      const dx = this.targetX - this.pixelX, dy = this.targetY - this.pixelY;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < SLIDE_SPEED) {
        this.pixelX = this.targetX; this.pixelY = this.targetY; this.isSliding = false;
      } else {
        this.pixelX += dx / dist * SLIDE_SPEED;
        this.pixelY += dy / dist * SLIDE_SPEED;
      }
      return true;
    }
    if (this.isCaptured) {
      const dx = this.captureTargetX - this.pixelX, dy = this.captureTargetY - this.pixelY;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < SLIDE_SPEED) {
        this.pixelX = this.captureTargetX; this.pixelY = this.captureTargetY; this.isCaptured = false;
      } else {
        this.pixelX += dx / dist * SLIDE_SPEED; this.pixelY += dy / dist * SLIDE_SPEED;
      }
      return true;
    }
    return false;
  }

  isActive() { return this.isFalling || this.isSliding || this.isCaptured; }
}

class TileAnim {
  constructor(q, r, targetX, targetY) {
    this.q = q; this.r = r;
    this.currentY = targetY - window.innerHeight * 0.9;
    this.targetY = targetY;
    this.x = targetX;
    this.done = false;
    this.active = false;
  }

  update() {
    if (this.done || !this.active) return !this.done;
    this.currentY += FALL_SPEED_TILE;
    if (this.currentY >= this.targetY) { this.currentY = this.targetY; this.done = true; }
    return !this.done;
  }
}

class AnimationManager {
  constructor() {
    this.pieceAnims = new Map();
    this.tileAnims = [];
    this.phase = 'idle';
    this._tileIndex = 0;
    this._p1Done = false;
  }

  initTileFall(board, hexRadius, cx, cy) {
    this.phase = 'tiles';
    this._tileIndex = 0;
    const sorted = [...board.hexCoordsArray].sort((a, b) => a[1] - b[1] || a[0] - b[0]);
    this.tileAnims = sorted.map(([q, r]) => {
      const [tx, ty] = hexToPixel(q, r, hexRadius, cx, cy);
      return new TileAnim(q, r, tx, ty);
    });
    if (this.tileAnims.length) this.tileAnims[0].active = true;
  }

  initPieceFall(board, hexRadius, cx, cy) {
    this.phase = 'pieces';
    this._p1Done = false;
    this.pieceAnims.clear();
    for (const p of board.pieces.values()) {
      const [tx, ty] = hexToPixel(p.q, p.r, hexRadius, cx, cy);
      const anim = new PieceAnim(p, tx, ty - window.innerHeight);
      anim.targetX = tx; anim.targetY = ty;
      anim.isFalling = p.color === PLAYER1;
      this.pieceAnims.set(`${p.q},${p.r}`, anim);
    }
  }

  updateTiles() {
    const MAX_ACTIVE = 7;
    let activeFalling = 0;
    for (const t of this.tileAnims) { if (t.active && !t.done) activeFalling++; }
    while (this._tileIndex < this.tileAnims.length && activeFalling < MAX_ACTIVE) {
      this.tileAnims[this._tileIndex].active = true;
      activeFalling++;
      this._tileIndex++;
    }
    let anyActive = false;
    for (const t of this.tileAnims) { if (!t.done) { t.update(); anyActive = true; } }
    if (!anyActive) { this.phase = 'idle'; return false; }
    return true;
  }

  updatePieces() {
    if (!this._p1Done) {
      let p1Falling = false;
      for (const anim of this.pieceAnims.values()) {
        if (anim.piece.color === PLAYER1 && anim.isFalling) { anim.update(); p1Falling = true; }
      }
      if (!p1Falling) {
        this._p1Done = true;
        for (const anim of this.pieceAnims.values()) {
          if (anim.piece.color === PLAYER2) anim.isFalling = true;
        }
      }
      return true;
    }
    let p2Falling = false;
    for (const anim of this.pieceAnims.values()) {
      if (anim.piece.color === PLAYER2 && anim.isFalling) { anim.update(); p2Falling = true; }
    }
    if (!p2Falling) { this.phase = 'idle'; return false; }
    return true;
  }

  updatePlay() {
    let any = false;
    for (const anim of this.pieceAnims.values()) { if (anim.update()) any = true; }
    return any;
  }

  isAnimating() {
    if (this.phase === 'tiles' || this.phase === 'pieces') return true;
    for (const anim of this.pieceAnims.values()) { if (anim.isActive()) return true; }
    return false;
  }

  onPieceMove(piece, fromQ, fromR, toQ, toR, hexRadius, cx, cy) {
    const oldAnim = this.pieceAnims.get(`${fromQ},${fromR}`);
    if (!oldAnim) return;
    this.pieceAnims.delete(`${fromQ},${fromR}`);
    const [tx, ty] = hexToPixel(toQ, toR, hexRadius, cx, cy);
    oldAnim.targetX = tx; oldAnim.targetY = ty;
    oldAnim.isSliding = true;
    this.pieceAnims.set(`${toQ},${toR}`, oldAnim);
  }

  syncBoard(board, hexRadius, cx, cy) {
    const keysToRemove = [];
    for (const key of this.pieceAnims.keys()) {
      if (!key.startsWith('cap-')) keysToRemove.push(key);
    }
    for (const key of keysToRemove) this.pieceAnims.delete(key);
    for (const p of board.pieces.values()) {
      const [tx, ty] = hexToPixel(p.q, p.r, hexRadius, cx, cy);
      const anim = new PieceAnim(p, tx, ty);
      this.pieceAnims.set(`${p.q},${p.r}`, anim);
    }
  }

  onPieceCapture(capturedPiece, targetX, targetY) {
    const key = `${capturedPiece.q},${capturedPiece.r}`;
    const anim = this.pieceAnims.get(key);
    if (!anim) return;
    this.pieceAnims.delete(key);
    anim.captureTargetX = targetX;
    anim.captureTargetY = targetY;
    anim.isCaptured = true;
    anim.isSliding = false;
    this.pieceAnims.set(`cap-${key}-${Date.now()}`, anim);
  }
}
