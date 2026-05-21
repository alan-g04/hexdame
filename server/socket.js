const { PLAYER1, PLAYER2 } = require('./game/hex');
const { RoomManager } = require('./rooms');

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
      if (!room || !slot) return;
      if (room.gs.turn !== slot) { socket.emit('move-error', { reason: 'Not your turn' }); return; }

      const result = rooms.applyMove(roomCode, from[0], from[1], to[0], to[1]);
      if (!result.ok) { socket.emit('move-error', { reason: result.error }); return; }
      io.to(roomCode).emit('state-update', result.state);
    });

    socket.on('request-rematch', ({ roomCode }) => {
      const room = rooms.getRoom(roomCode);
      if (!room || !room.players[PLAYER1] || !room.players[PLAYER2]) return;
      rooms.resetGame(roomCode);
      io.to(roomCode).emit('game-start', {
        p1Name: room.players[PLAYER1].displayName,
        p2Name: room.players[PLAYER2].displayName
      });
    });

    socket.on('disconnect', () => {
      const info = rooms.removePlayer(socket.id);
      if (info) io.to(info.code).emit('opponent-disconnected');
    });
  });
};
