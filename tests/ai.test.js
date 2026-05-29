const { Board } = require('../client/js/board');
const { GameLogic } = require('../client/js/logic');
const { AIPlayer } = require('../client/js/ai');

describe('AIPlayer', () => {
  let board, logic, ai;
  beforeEach(() => {
    board = new Board(5);
    board.initializePieces();
    logic = new GameLogic(board);
    ai = new AIPlayer(logic);
  });

  test('findMove returns a 4-tuple for a normal position', () => {
    const { allMoves, mustJump } = logic.getAllPlayerMoves(PLAYER2);
    const move = ai.findMove(allMoves, mustJump);
    expect(Array.isArray(move)).toBe(true);
    expect(move.length).toBe(4);
  });

  test('findMove returns null when no moves available', () => {
    board.pieces.clear();
    const { allMoves, mustJump } = logic.getAllPlayerMoves(PLAYER2);
    expect(ai.findMove(allMoves, mustJump)).toBeNull();
  });

  test('findMove picks a jump when mustJump is true', () => {
    board.pieces.clear();
    board.pieces.set('0,0', { q:0, r:0, color:PLAYER1, isKing:false });
    board.pieces.set('0,-1', { q:0, r:-1, color:PLAYER2, isKing:false });
    const { allMoves, mustJump } = logic.getAllPlayerMoves(PLAYER2);
    if (mustJump) {
      const move = ai.findMove(allMoves, mustJump);
      const [fq, fr, tq, tr] = move;
      const { valid, jumpedCoord } = logic.isMoveValid(board.getPiece(fq, fr), tq, tr, allMoves, mustJump);
      expect(valid).toBe(true);
      expect(jumpedCoord).not.toBeNull();
    }
  });

  test('generated move is valid according to GameLogic', () => {
    const { allMoves, mustJump } = logic.getAllPlayerMoves(PLAYER2);
    const move = ai.findMove(allMoves, mustJump);
    const [fq, fr, tq, tr] = move;
    const piece = board.getPiece(fq, fr);
    const { valid } = logic.isMoveValid(piece, tq, tr, allMoves, mustJump);
    expect(valid).toBe(true);
  });
});
