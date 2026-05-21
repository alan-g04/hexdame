const pick = arr => arr[Math.floor(Math.random() * arr.length)];

class AIPlayer {
  constructor(logic) { this.logic = logic; }

  findMove(allPlayerMoves, mustJump) {
    const keys = Object.keys(allPlayerMoves);
    if (!keys.length) return null;

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
    const [jq, jr] = pick(jumps);
    return [piece.q, piece.r, jq, jr];
  }
}

if (typeof module !== 'undefined') module.exports = { AIPlayer };
