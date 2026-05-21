const { Board } = require('../client/js/board');
const { GameLogic } = require('../client/js/logic');

describe('GameLogic', () => {
  let board, logic;
  beforeEach(() => {
    board = new Board(5);
    board.initializePieces();
    logic = new GameLogic(board);
  });

  test('P1 has valid moves at game start', () => {
    const { allMoves } = logic.getAllPlayerMoves(PLAYER1);
    expect(Object.keys(allMoves).length).toBeGreaterThan(0);
  });

  test('no forced jump at game start', () => {
    const { mustJump } = logic.getAllPlayerMoves(PLAYER1);
    expect(mustJump).toBe(false);
  });

  test('getValidMoves returns moves for a P1 piece in row 1', () => {
    const piece = board.getPiece(0, 1);
    const { moves, jumps } = logic.getValidMoves(piece);
    expect(moves.length).toBeGreaterThan(0);
    expect(jumps.length).toBe(0);
  });

  test('isMoveValid returns valid for a legal simple move', () => {
    const { allMoves, mustJump } = logic.getAllPlayerMoves(PLAYER1);
    const key = Object.keys(allMoves)[0];
    const { q, r, moves } = allMoves[key];
    const piece = board.getPiece(q, r);
    const [toQ, toR] = moves[0];
    const { valid } = logic.isMoveValid(piece, toQ, toR, allMoves, mustJump);
    expect(valid).toBe(true);
  });

  test('isMoveValid returns invalid for wrong destination', () => {
    const { allMoves, mustJump } = logic.getAllPlayerMoves(PLAYER1);
    const key = Object.keys(allMoves)[0];
    const { q, r } = allMoves[key];
    const piece = board.getPiece(q, r);
    const { valid } = logic.isMoveValid(piece, 0, 0, allMoves, mustJump);
    expect(valid).toBe(false);
  });

  test('checkForPromotion promotes P1 piece at top edge', () => {
    board.pieces.clear();
    const piece = { q: 0, r: -4, color: PLAYER1, isKing: false };
    board.pieces.set('0,-4', piece);
    logic.checkForPromotion(piece);
    expect(piece.isKing).toBe(true);
  });

  test('checkForPromotion promotes P2 piece at bottom edge', () => {
    board.pieces.clear();
    const piece = { q: 0, r: 4, color: PLAYER2, isKing: false };
    board.pieces.set('0,4', piece);
    logic.checkForPromotion(piece);
    expect(piece.isKing).toBe(true);
  });

  test('checkForPromotion does not promote king again', () => {
    board.pieces.clear();
    const piece = { q: 0, r: -4, color: PLAYER1, isKing: true };
    board.pieces.set('0,-4', piece);
    const result = logic.checkForPromotion(piece);
    expect(result).toBe(false);
  });

  test('checkGameOver returns null when game is ongoing', () => {
    expect(logic.checkGameOver(PLAYER1)).toBeNull();
  });

  test('checkGameOver returns winner when opponent has no pieces', () => {
    board.getPiecesForPlayer(PLAYER2).forEach(p => board.removePiece(p.q, p.r));
    expect(logic.checkGameOver(PLAYER1)).toBe(PLAYER1);
  });
});
