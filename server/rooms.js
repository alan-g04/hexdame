const { Board } = require('./game/board');
const { GameLogic } = require('./game/logic');
const { AIPlayer } = require('./game/ai');
const { BOARD_SIDE_LENGTH, PLAYER1, PLAYER2 } = require('./game/hex');

function makeRoomCode() {
  return Math.random().toString(36).substring(2, 6).toUpperCase();
}

function createGameState() {
  const board = new Board(BOARD_SIDE_LENGTH);
  board.initializePieces();
  const logic = new GameLogic(board);
  const { allMoves, mustJump } = logic.getAllPlayerMoves(PLAYER1);
  return { board, logic, turn: PLAYER1, allMoves, mustJump, winner: null,
    capturedByP1: [], capturedByP2: [] };
}

function serializeState(gs) {
  return {
    board: [...gs.board.pieces.entries()].map(([k, p]) => ({ key: k, color: p.color, isKing: p.isKing, q: p.q, r: p.r })),
    turn: gs.turn,
    mustJump: gs.mustJump,
    winner: gs.winner,
    capturedByP1: gs.capturedByP1.map(p => ({ color: p.color, isKing: p.isKing })),
    capturedByP2: gs.capturedByP2.map(p => ({ color: p.color, isKing: p.isKing }))
  };
}

class RoomManager {
  constructor() { this.rooms = new Map(); }

  create(socketId, displayName) {
    let code;
    do { code = makeRoomCode(); } while (this.rooms.has(code));
    this.rooms.set(code, {
      code,
      players: { [PLAYER1]: { socketId, displayName }, [PLAYER2]: null },
      gs: createGameState(),
      mode: 'waiting'
    });
    return code;
  }

  join(code, socketId, displayName) {
    const room = this.rooms.get(code);
    if (!room) return { error: 'Room not found' };
    if (room.players[PLAYER2]) return { error: 'Room is full' };
    room.players[PLAYER2] = { socketId, displayName };
    room.mode = 'playing';
    return { ok: true };
  }

  getRoom(code) { return this.rooms.get(code) || null; }

  getSlot(code, socketId) {
    const r = this.rooms.get(code);
    if (!r) return null;
    if (r.players[PLAYER1]?.socketId === socketId) return PLAYER1;
    if (r.players[PLAYER2]?.socketId === socketId) return PLAYER2;
    return null;
  }

  applyMove(code, fromQ, fromR, toQ, toR) {
    const room = this.rooms.get(code);
    if (!room) return { error: 'Room not found' };
    const { gs } = room;
    const piece = gs.board.getPiece(fromQ, fromR);
    if (!piece) return { error: 'No piece at source' };
    const { valid, jumpedCoord } = gs.logic.isMoveValid(piece, toQ, toR, gs.allMoves, gs.mustJump);
    if (!valid) return { error: 'Invalid move' };

    gs.board.movePiece(fromQ, fromR, toQ, toR);
    if (jumpedCoord) {
      const cap = gs.board.removePiece(jumpedCoord[0], jumpedCoord[1]);
      if (cap) (gs.turn === PLAYER1 ? gs.capturedByP1 : gs.capturedByP2).push(cap);
    }
    gs.logic.checkForPromotion(gs.board.getPiece(toQ, toR));

    const movedPiece = gs.board.getPiece(toQ, toR);
    if (jumpedCoord) {
      const { jumps } = gs.logic.getValidMoves(movedPiece);
      if (jumps.length) {
        gs.allMoves = { [`${toQ},${toR}`]: { moves: [], jumps, q: toQ, r: toR } };
        gs.mustJump = true;
        return { ok: true, state: serializeState(gs), multiJump: true };
      }
    }

    const winner = gs.logic.checkGameOver(gs.turn);
    if (winner) {
      gs.winner = winner;
      return { ok: true, state: serializeState(gs) };
    }

    gs.turn = gs.turn === PLAYER1 ? PLAYER2 : PLAYER1;
    const { allMoves, mustJump } = gs.logic.getAllPlayerMoves(gs.turn);
    gs.allMoves = allMoves;
    gs.mustJump = mustJump;

    if (!Object.keys(allMoves).length) {
      gs.winner = gs.turn === PLAYER1 ? PLAYER2 : PLAYER1;
      return { ok: true, state: serializeState(gs) };
    }

    return { ok: true, state: serializeState(gs) };
  }

  resetGame(code) {
    const room = this.rooms.get(code);
    if (!room) return;
    room.gs = createGameState();
  }

  leaveRoom(code, socketId) {
    const room = this.rooms.get(code);
    if (!room) return null;
    for (const slot of [PLAYER1, PLAYER2]) {
      if (room.players[slot]?.socketId === socketId) {
        const hadActiveGame = !room.gs.winner && room.mode === 'playing';
        room.players[slot] = null;
        if (!room.players[PLAYER1] && !room.players[PLAYER2]) this.rooms.delete(code);
        return { code, slot, hadActiveGame };
      }
    }
    return null;
  }

  removePlayer(socketId) {
    for (const [code, room] of this.rooms) {
      for (const slot of [PLAYER1, PLAYER2]) {
        if (room.players[slot]?.socketId === socketId) {
          const hadActiveGame = !room.gs.winner && room.mode === 'playing';
          room.players[slot] = null;
          if (!room.players[PLAYER1] && !room.players[PLAYER2]) this.rooms.delete(code);
          return { code, slot, hadActiveGame };
        }
      }
    }
    return null;
  }
}

module.exports = { RoomManager, serializeState };
