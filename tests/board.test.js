const { Board } = require('../client/js/board');

describe('Board', () => {
  let board;
  beforeEach(() => { board = new Board(5); });

  test('generates 61 hexes for side length 5', () => {
    expect(board.hexCoordsArray.length).toBe(61);
  });

  test('hasHex returns true for center', () => {
    expect(board.hasHex(0, 0)).toBe(true);
  });

  test('hasHex returns false for out-of-bounds', () => {
    expect(board.hasHex(5, 0)).toBe(false);
    expect(board.hasHex(-5, 0)).toBe(false);
  });

  test('initializePieces places 16 pieces per player', () => {
    board.initializePieces();
    const p1 = board.getPiecesForPlayer(PLAYER1);
    const p2 = board.getPiecesForPlayer(PLAYER2);
    expect(p1.length).toBe(16);
    expect(p2.length).toBe(16);
  });

  test('getPiece returns null for empty hex', () => {
    board.initializePieces();
    expect(board.getPiece(0, 0)).toBeNull();
  });

  test('movePiece updates board state', () => {
    board.initializePieces();
    const before = board.getPiece(0, 1);
    board.movePiece(0, 1, 0, 0);
    expect(board.getPiece(0, 0)).toBe(before);
    expect(board.getPiece(0, 1)).toBeNull();
  });

  test('removePiece returns removed piece', () => {
    board.initializePieces();
    const piece = board.getPiece(0, 1);
    const removed = board.removePiece(0, 1);
    expect(removed).toBe(piece);
    expect(board.getPiece(0, 1)).toBeNull();
  });
});
