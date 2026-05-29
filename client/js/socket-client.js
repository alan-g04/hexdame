class SocketClient {
  constructor() {
    this.socket = null;
    this.roomCode = null;
    this.playerSlot = null;
    this.onRoomJoined = null;
    this.onGameStart = null;
    this.onStateUpdate = null;
    this.onOpponentDisconnected = null;
    this.onJoinError = null;
    this.onMoveError = null;
  }

  connect() {
    if (this.socket) return;
    this.socket = io();
    this.socket.on('room-joined', (data) => {
      this.roomCode = data.roomCode;
      this.playerSlot = data.playerSlot;
      if (this.onRoomJoined) this.onRoomJoined(data);
    });
    this.socket.on('game-start',            (d) => { if (this.onGameStart) this.onGameStart(d); });
    this.socket.on('state-update',          (d) => { if (this.onStateUpdate) this.onStateUpdate(d); });
    this.socket.on('opponent-disconnected', ()  => { if (this.onOpponentDisconnected) this.onOpponentDisconnected(); });
    this.socket.on('join-error',            (d) => { if (this.onJoinError) this.onJoinError(d); });
    this.socket.on('move-error',            (d) => { if (this.onMoveError) this.onMoveError(d); });
  }

  createRoom(displayName) { this.socket.emit('create-room', { displayName }); }
  joinRoom(roomCode, displayName) { this.socket.emit('join-room', { roomCode, displayName }); }
  sendMove(from, to) { this.socket.emit('move', { roomCode: this.roomCode, from, to }); }
  sendForfeit() { this.socket.emit('forfeit', { roomCode: this.roomCode }); }

  leaveGame() {
    if (!this.socket || !this.roomCode) return;
    this.socket.emit('leave-game', { roomCode: this.roomCode });
    this.roomCode = null;
    this.playerSlot = null;
  }
  requestRematch() { this.socket.emit('request-rematch', { roomCode: this.roomCode }); }
}
