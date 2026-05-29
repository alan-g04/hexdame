const pick = arr => arr[Math.floor(Math.random() * arr.length)];

function _cloneBoard(original) {
  return {
    sideLength: original.sideLength,
    hexCoordsSet: original.hexCoordsSet,
    hexCoordsArray: original.hexCoordsArray,
    pieces: new Map([...original.pieces].map(([k, p]) => [k, { ...p }])),
    hasHex(q, r) { return this.hexCoordsSet.has(`${q},${r}`); },
    getPiece(q, r) { return this.pieces.get(`${q},${r}`) || null; },
    removePiece(q, r) { const p = this.pieces.get(`${q},${r}`) || null; this.pieces.delete(`${q},${r}`); return p; },
    movePiece(fq, fr, tq, tr) {
      const piece = this.pieces.get(`${fq},${fr}`);
      this.pieces.delete(`${fq},${fr}`);
      piece.q = tq; piece.r = tr;
      this.pieces.set(`${tq},${tr}`, piece);
      return piece;
    },
    getPiecesForPlayer(color) { return [...this.pieces.values()].filter(p => p.color === color); }
  };
}

function _makeLogic(board) {
  if (typeof GameLogic !== 'undefined') return new GameLogic(board);
  return new (require('./logic').GameLogic)(board);
}

function _evaluate(board) {
  let score = 0;
  for (const p of board.pieces.values()) {
    const val = p.isKing ? 3 : 1;
    score += p.color === PLAYER2 ? val : -val;
  }
  return score;
}

function _applyStep(board, fq, fr, tq, tr, jumped) {
  const nb = _cloneBoard(board);
  const piece = nb.movePiece(fq, fr, tq, tr);
  if (jumped) nb.removePiece(jumped[0], jumped[1]);
  _makeLogic(nb).checkForPromotion(piece);
  return { board: nb, piece };
}

function _expandJumps(board, piece) {
  const logic = _makeLogic(board);
  const { jumps } = logic.getValidMoves(piece);
  if (!jumps.length) return [board];
  const finals = [];
  for (const [jq, jr, cq, cr] of jumps) {
    const { board: nb, piece: np } = _applyStep(board, piece.q, piece.r, jq, jr, [cq, cr]);
    finals.push(..._expandJumps(nb, np));
  }
  return finals;
}

function _getMoveOptions(board, player) {
  const logic = _makeLogic(board);
  const { allMoves } = logic.getAllPlayerMoves(player);
  const result = [];
  for (const [key, ms] of Object.entries(allMoves)) {
    const [fq, fr] = key.split(',').map(Number);
    for (const [tq, tr] of ms.moves) {
      const { board: nb } = _applyStep(board, fq, fr, tq, tr, null);
      result.push({ firstMove: [fq, fr, tq, tr], finalBoard: nb });
    }
    for (const [jq, jr, cq, cr] of ms.jumps) {
      const { board: nb, piece: np } = _applyStep(board, fq, fr, jq, jr, [cq, cr]);
      for (const fb of _expandJumps(nb, np)) {
        result.push({ firstMove: [fq, fr, jq, jr], finalBoard: fb });
      }
    }
  }
  return result;
}

function _minimax(board, depth, alpha, beta, player) {
  if (depth === 0) return _evaluate(board);
  const options = _getMoveOptions(board, player);
  if (!options.length) return player === PLAYER2 ? -10000 : 10000;
  const opponent = player === PLAYER1 ? PLAYER2 : PLAYER1;
  if (player === PLAYER2) {
    let best = -Infinity;
    for (const { finalBoard } of options) {
      const score = _minimax(finalBoard, depth - 1, alpha, beta, opponent);
      if (score > best) best = score;
      if (best > alpha) alpha = best;
      if (beta <= alpha) break;
    }
    return best;
  } else {
    let best = Infinity;
    for (const { finalBoard } of options) {
      const score = _minimax(finalBoard, depth - 1, alpha, beta, opponent);
      if (score < best) best = score;
      if (best < beta) beta = best;
      if (beta <= alpha) break;
    }
    return best;
  }
}

class AIPlayer {
  constructor(logic, depth = 1) {
    this.logic = logic;
    this.depth = depth;
  }

  findMove(allPlayerMoves, mustJump) {
    if (!Object.keys(allPlayerMoves).length) return null;
    if (this.depth === 0) return this._randomMove(allPlayerMoves, mustJump);

    const options = _getMoveOptions(this.logic.board, PLAYER2);
    if (!options.length) return null;
    let bestScore = -Infinity;
    let bestMove = options[0].firstMove;
    for (const { firstMove, finalBoard } of options) {
      const score = _minimax(finalBoard, this.depth - 1, -Infinity, Infinity, PLAYER1);
      if (score > bestScore) { bestScore = score; bestMove = firstMove; }
    }
    return bestMove;
  }

  _randomMove(allPlayerMoves, mustJump) {
    const keys = Object.keys(allPlayerMoves);
    if (mustJump) {
      const jumpable = keys.filter(k => allPlayerMoves[k].jumps.length);
      if (!jumpable.length) return null;
      const k = pick(jumpable);
      const [jq, jr] = pick(allPlayerMoves[k].jumps);
      const [q, r] = k.split(',').map(Number);
      return [q, r, jq, jr];
    }
    const movable = keys.filter(k => allPlayerMoves[k].moves.length);
    if (!movable.length) return null;
    const k = pick(movable);
    const [mq, mr] = pick(allPlayerMoves[k].moves);
    const [q, r] = k.split(',').map(Number);
    return [q, r, mq, mr];
  }

  findNextMultiJump(piece) {
    const { jumps } = this.logic.getValidMoves(piece);
    if (!jumps.length) return null;
    const [jq, jr] = jumps[0];
    return [piece.q, piece.r, jq, jr];
  }
}

if (typeof module !== 'undefined') module.exports = { AIPlayer };
