const P1_PROMOTION_ZONE = new Set([
  '-4,0','-3,-1','-2,-2','-1,-3','0,-4','1,-4','2,-4','3,-4','4,-4'
]);
const P2_PROMOTION_ZONE = new Set([
  '-4,4','-3,4','-2,4','-1,4','0,4','1,3','2,2','3,1','4,0'
]);

class GameLogic {
  constructor(board) { this.board = board; }

  getValidMoves(piece) {
    const { q, r, color, isKing } = piece;
    const moves = [], jumps = [];
    const dirs = isKing ? KING_DIRECTIONS : MOVE_DIRECTIONS[color];

    for (const [dq, dr] of dirs) {
      const tq = q + dq, tr = r + dr;
      const jq = q + 2 * dq, jr = r + 2 * dr;
      if (!this.board.hasHex(tq, tr)) continue;
      const target = this.board.getPiece(tq, tr);
      if (!target) {
        moves.push([tq, tr]);
      } else if (target.color !== color) {
        if (this.board.hasHex(jq, jr) && !this.board.getPiece(jq, jr))
          jumps.push([jq, jr, tq, tr]);
      }
    }
    return { moves, jumps };
  }

  getAllPlayerMoves(playerColor) {
    const allMoves = {};
    let mustJump = false;

    for (const piece of this.board.getPiecesForPlayer(playerColor)) {
      const { moves, jumps } = this.getValidMoves(piece);
      if (moves.length || jumps.length)
        allMoves[`${piece.q},${piece.r}`] = { moves, jumps, q: piece.q, r: piece.r };
      if (jumps.length) mustJump = true;
    }

    if (mustJump) {
      const filtered = {};
      for (const [k, v] of Object.entries(allMoves)) {
        if (v.jumps.length) filtered[k] = { moves: [], jumps: v.jumps, q: v.q, r: v.r };
      }
      return { allMoves: filtered, mustJump: true };
    }
    return { allMoves, mustJump: false };
  }

  isMoveValid(piece, endQ, endR, allPlayerMoves, mustJump) {
    const key = `${piece.q},${piece.r}`;
    const moveset = allPlayerMoves[key];
    if (!moveset) return { valid: false, jumpedCoord: null };

    for (const [jq, jr, cq, cr] of moveset.jumps) {
      if (jq === endQ && jr === endR) return { valid: true, jumpedCoord: [cq, cr] };
    }
    if (mustJump) return { valid: false, jumpedCoord: null };
    for (const [mq, mr] of moveset.moves) {
      if (mq === endQ && mr === endR) return { valid: true, jumpedCoord: null };
    }
    return { valid: false, jumpedCoord: null };
  }

  checkForPromotion(piece) {
    if (piece.isKing) return false;
    const key = `${piece.q},${piece.r}`;
    if (piece.color === PLAYER1 && P1_PROMOTION_ZONE.has(key)) {
      piece.isKing = true; return true;
    }
    if (piece.color === PLAYER2 && P2_PROMOTION_ZONE.has(key)) {
      piece.isKing = true; return true;
    }
    return false;
  }

  checkGameOver(currentPlayer) {
    const opponent = currentPlayer === PLAYER1 ? PLAYER2 : PLAYER1;
    if (!this.board.getPiecesForPlayer(opponent).length) return currentPlayer;
    const { allMoves } = this.getAllPlayerMoves(opponent);
    if (!Object.keys(allMoves).length) return currentPlayer;
    return null;
  }
}

if (typeof module !== 'undefined') module.exports = { GameLogic };
