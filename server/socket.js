const { PLAYER1, PLAYER2 } = require('./game/hex');
const { RoomManager, serializeState } = require('./rooms');

const rooms = new RoomManager();

module.exports = function registerSocketHandlers(io) {
  io.on('connection', (socket) => {

    socket.on('create-room', ({ displayName }) => {
      const code = rooms.create(socket.id, displayName);
      socket.join(code);
      socket.emit('room-joined', { roomCode: code, playerSlot: PLAYER1, opponentName: null });
    });

    socket.on('join-room', ({ roomCode, displayName }) => {
      const result = rooms.join(roomCode, socket.id, displayName);
      if (result.error) { socket.emit('join-error', { reason: result.error }); return; }
      const room = rooms.getRoom(roomCode);
      socket.join(roomCode);
      socket.emit('room-joined', {
        roomCode, playerSlot: PLAYER2,
        opponentName: room.players[PLAYER1]?.displayName
      });
      io.to(roomCode).emit('game-start', {
        p1Name: room.players[PLAYER1].displayName,
        p2Name: room.players[PLAYER2].displayName
      });
    });

    socket.on('move', ({ roomCode, from, to }) => {
      const slot = rooms.getSlot(roomCode, socket.id);
      const room = rooms.getRoom(roomCode);
      if (!room || !slot) { socket.emit('move-error', { reason: 'Room or slot not found' }); return; }
      if (room.gs.turn !== slot) { socket.emit('move-error', { reason: 'Not your turn' }); return; }

      const result = rooms.applyMove(roomCode, from[0], from[1], to[0], to[1]);
      if (!result.ok) { socket.emit('move-error', { reason: result.error }); return; }
      io.to(roomCode).emit('state-update', result.state);
    });

    socket.on('leave-game', ({ roomCode }) => {
      socket.leave(roomCode);
      const info = rooms.leaveRoom(roomCode, socket.id);
      if (info) io.to(roomCode).emit('opponent-disconnected');
    });

    socket.on('forfeit', ({ roomCode }) => {
      const slot = rooms.getSlot(roomCode, socket.id);
      const room = rooms.getRoom(roomCode);
      if (!room || !slot || room.gs.winner) return;
      room.gs.winner = slot === PLAYER1 ? PLAYER2 : PLAYER1;
      io.to(roomCode).emit('state-update', serializeState(room.gs));
    });

    socket.on('request-rematch', ({ roomCode }) => {
      const slot = rooms.getSlot(roomCode, socket.id);
      const room = rooms.getRoom(roomCode);
      if (!room || !slot) { socket.emit('rematch-error', { reason: 'Room not found' }); return; }
      const opponentSlot = slot === PLAYER1 ? PLAYER2 : PLAYER1;
      if (!room.players[opponentSlot]) {
        socket.emit('rematch-error', { reason: 'Opponent has left' });
        return;
      }
      io.to(room.players[opponentSlot].socketId).emit('rematch-request');
    });

    socket.on('accept-rematch', ({ roomCode }) => {
      const room = rooms.getRoom(roomCode);
      if (!room || !room.players[PLAYER1] || !room.players[PLAYER2]) {
        socket.emit('rematch-error', { reason: 'Cannot rematch: player(s) disconnected' });
        return;
      }
      rooms.resetGame(roomCode);
      io.to(roomCode).emit('game-start', {
        p1Name: room.players[PLAYER1].displayName,
        p2Name: room.players[PLAYER2].displayName
      });
    });

    socket.on('decline-rematch', ({ roomCode }) => {
      const slot = rooms.getSlot(roomCode, socket.id);
      const room = rooms.getRoom(roomCode);
      if (!room || !slot) return;
      const requesterSlot = slot === PLAYER1 ? PLAYER2 : PLAYER1;
      if (room.players[requesterSlot]) {
        io.to(room.players[requesterSlot].socketId).emit('rematch-declined');
      }
    });

    socket.on('disconnect', () => {
      const info = rooms.removePlayer(socket.id);
      if (info) io.to(info.code).emit('opponent-disconnected');
    });
  });
};
