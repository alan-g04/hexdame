class GameController {
  constructor(canvas) {
    this.hexCanvas = new HexCanvas(canvas);
    this.board = null;
    this.logic = null;
    this.gameMode = null;
    this.currentTurn = PLAYER1;
    this.selectedCoord = null;
    this.possibleMoves = [];
    this.allPlayerMoves = {};
    this.mustJump = false;
    this.capturedByP1 = [];
    this.capturedByP2 = [];
    this.winner = null;
    this.isMultiJumping = false;
    this._aiPending = false;
    this.phase = 'menu';
    this._onGameOver = null;
    this._onTurnChange = null;
    this._onTimerTick = null;
    this._timerInterval = null;
    this._timerSeconds = null;
    this._timerExpiry = null;
    this.aiDepth = 1;
    this._loopRunning = false;
    this._pendingGameOver = null;
    this.anim = new AnimationManager();
    this._loop = this._loop.bind(this);
    window.addEventListener('resize', () => this._recomputeAnimTargets());
  }

  startGame(mode, aiDepth = 1) {
    this.aiDepth = aiDepth;
    this.gameMode = mode;
    this.board = new Board(BOARD_SIDE_LENGTH);
    this.logic = new GameLogic(this.board);
    this.board.initializePieces();
    this.currentTurn = PLAYER1;
    this.selectedCoord = null;
    this.possibleMoves = [];
    this.capturedByP1 = [];
    this.capturedByP2 = [];
    this.winner = null;
    this.isMultiJumping = false;
    this._aiPending = false;
    this._pendingGameOver = null;
    this._clearTimer();
    this.phase = 'setup';
    this.anim.initTileFall(this.board, this.hexCanvas.hexRadius, this.hexCanvas.cx, this.hexCanvas.cy);
    if (!this._loopRunning) {
      this._loopRunning = true;
      requestAnimationFrame(this._loop);
    }
  }

  _loop() {
    if (this.phase === 'setup') {
      const still = this.anim.updateTiles();
      if (!still) {
        this.anim.initPieceFall(this.board, this.hexCanvas.hexRadius, this.hexCanvas.cx, this.hexCanvas.cy);
        this.phase = 'pieces';
      }
    } else if (this.phase === 'pieces') {
      const still = this.anim.updatePieces();
      if (!still) {
        this.phase = 'playing';
        this._calcMoves();
        this._notifyTurn();
      }
    } else if (this.phase === 'playing') {
      this.anim.updatePlay();
      if (this._pendingGameOver && !this.anim.isAnimating()) {
        this._clearTimer();
        this.phase = 'gameover';
        if (this._onGameOver) this._onGameOver(this._pendingGameOver);
      } else if (!this._pendingGameOver && this.gameMode === 'ai' && this.currentTurn === PLAYER2 && !this._aiPending && !this.anim.isAnimating()) {
        this._scheduleAI();
      }
    }
    this.hexCanvas.renderWithAnim(this, this.anim);
    if (this.phase !== 'gameover') {
      requestAnimationFrame(this._loop);
    } else {
      this._loopRunning = false;
    }
  }

  _scheduleAI() {
    this._aiPending = true;
    setTimeout(() => {
      this._doAIMove();
      this._aiPending = false;
    }, AI_DELAY_MS);
  }

  _doAIMove() {
    const ai = new AIPlayer(this.logic, this.aiDepth);
    const move = ai.findMove(this.allPlayerMoves, this.mustJump);
    if (!move) return;
    const [fq, fr, tq, tr] = move;
    const piece = this.board.getPiece(fq, fr);
    const { valid, jumpedCoord } = this.logic.isMoveValid(piece, tq, tr, this.allPlayerMoves, this.mustJump);
    if (valid) this._executeMove(fq, fr, tq, tr, jumpedCoord);
  }

  handleClick(px, py) {
    if (this.phase !== 'playing' || this.anim.isAnimating() || this._pendingGameOver) return;
    const human = this.gameMode === 'local' ||
      (this.gameMode === 'ai' && this.currentTurn === PLAYER1) ||
      this.gameMode === 'online';
    if (!human || this._aiPending) return;
    if (this.gameMode === 'online' && this.currentTurn !== this.playerSlot) {
      this._clearSelection(); return;
    }

    const [q, r] = this.hexCanvas.getHexAt(px, py);
    if (!this.board.hasHex(q, r)) { this._clearSelection(); return; }

    const key = `${q},${r}`;
    const clickedPiece = this.board.getPiece(q, r);

    if (this.selectedCoord) {
      const isDest = this.possibleMoves.some(([mq, mr]) => mq === q && mr === r);
      if (isDest) {
        const selPiece = this.board.getPiece(this.selectedCoord[0], this.selectedCoord[1]);
        const { valid, jumpedCoord } = this.logic.isMoveValid(selPiece, q, r, this.allPlayerMoves, this.mustJump);
        if (valid) {
          if (this.gameMode === 'online' && this.socketClient) {
            this.socketClient.sendMove(this.selectedCoord, [q, r]);
            this._clearSelection();
          } else {
            this._executeMove(this.selectedCoord[0], this.selectedCoord[1], q, r, jumpedCoord);
          }
          return;
        }
      }
    }

    if (clickedPiece && clickedPiece.color === this.currentTurn && this.allPlayerMoves[key]) {
      this.selectedCoord = [q, r];
      const ms = this.allPlayerMoves[key];
      this.possibleMoves = this.mustJump
        ? ms.jumps.map(([jq, jr]) => [jq, jr])
        : [...ms.moves, ...ms.jumps.map(([jq, jr]) => [jq, jr])];
    } else {
      this._clearSelection();
    }
  }

  _executeMove(fq, fr, tq, tr, jumpedCoord) {
    const piece = this.board.movePiece(fq, fr, tq, tr);
    this.anim.onPieceMove(piece, fq, fr, tq, tr, this.hexCanvas.hexRadius, this.hexCanvas.cx, this.hexCanvas.cy);

    if (jumpedCoord) {
      const cap = this.board.removePiece(jumpedCoord[0], jumpedCoord[1]);
      if (cap) {
        const capList = this.currentTurn === PLAYER1 ? this.capturedByP1 : this.capturedByP2;
        capList.push(cap);
        const { tx, ty } = this._captureTarget(capList.length - 1, this.currentTurn);
        this.anim.onPieceCapture(cap, tx, ty);
      }
    }
    this.logic.checkForPromotion(piece);

    if (jumpedCoord) {
      const { jumps } = this.logic.getValidMoves(piece);
      if (jumps.length) {
        this.isMultiJumping = true;
        this.allPlayerMoves = { [`${tq},${tr}`]: { moves: [], jumps, q: tq, r: tr } };
        this.mustJump = true;
        this.selectedCoord = [tq, tr];
        this.possibleMoves = jumps.map(([jq, jr]) => [jq, jr]);
        return;
      }
    }

    this.isMultiJumping = false;
    this._clearSelection();

    const w = this.logic.checkGameOver(this.currentTurn);
    if (w) { this.winner = w; this._pendingGameOver = w; return; }

    this._switchTurn();
  }

  _captureTarget(index, capturingPlayer) {
    const pr = Math.floor(this.hexCanvas.pieceRadius);
    const vSpacing = pr * 2.4;
    const hSpacing = pr * 2.6;
    const margin = pr * 2.5;
    const col = Math.floor(index / 6);
    const row = index % 6;
    const ty = margin + row * vSpacing;
    if (capturingPlayer === PLAYER1) {
      return { tx: margin + col * hSpacing, ty };
    } else {
      return { tx: this.hexCanvas.canvas.width - margin - col * hSpacing, ty };
    }
  }

  _switchTurn() {
    this.currentTurn = this.currentTurn === PLAYER1 ? PLAYER2 : PLAYER1;
    this._calcMoves();
    if (!Object.keys(this.allPlayerMoves).length) {
      this._clearTimer();
      this.winner = this.currentTurn === PLAYER1 ? PLAYER2 : PLAYER1;
      this.phase = 'gameover';
      if (this._onGameOver) this._onGameOver(this.winner);
      return;
    }
    this._notifyTurn();
  }

  _calcMoves() {
    const { allMoves, mustJump } = this.logic.getAllPlayerMoves(this.currentTurn);
    this.allPlayerMoves = allMoves;
    this.mustJump = mustJump;
  }

  _clearSelection() { this.selectedCoord = null; this.possibleMoves = []; }

  _notifyTurn() {
    if (this._onTurnChange) this._onTurnChange(this.currentTurn, this.mustJump, this.gameMode);
    this._clearTimer();
    if (this.gameMode === 'online') {
      this._timerExpiry = this.currentTurn === this.playerSlot ? () => this._doForfeit() : null;
      this._startTimer(30);
    }
  }

  _startTimer(seconds) {
    this._timerSeconds = seconds;
    if (this._onTimerTick) this._onTimerTick(this._timerSeconds);
    this._timerInterval = setInterval(() => {
      this._timerSeconds--;
      if (this._onTimerTick) this._onTimerTick(this._timerSeconds);
      if (this._timerSeconds <= 0) {
        this._clearTimer();
        if (this._timerExpiry) this._timerExpiry();
      }
    }, 1000);
  }

  _clearTimer() {
    if (this._timerInterval) { clearInterval(this._timerInterval); this._timerInterval = null; }
    this._timerSeconds = null;
    if (this._onTimerTick) this._onTimerTick(null);
  }

  _doForfeit() {
    if (this.socketClient) this.socketClient.sendForfeit();
  }

  _doRandomMove() {
    if (this.phase !== 'playing' || this._pendingGameOver || this.anim.isAnimating()) return;
    const rng = new AIPlayer(this.logic, 0);
    if (this.isMultiJumping) {
      const [sq, sr] = this.selectedCoord;
      const piece = this.board.getPiece(sq, sr);
      const move = rng.findNextMultiJump(piece);
      if (!move) return;
      const [fq, fr, tq, tr] = move;
      const { valid, jumpedCoord } = this.logic.isMoveValid(piece, tq, tr, this.allPlayerMoves, this.mustJump);
      if (valid) {
        this._executeMove(fq, fr, tq, tr, jumpedCoord);
        if (this.isMultiJumping) this._startTimer(10);
      }
      return;
    }
    const move = rng.findMove(this.allPlayerMoves, this.mustJump);
    if (!move) return;
    const [fq, fr, tq, tr] = move;
    const piece = this.board.getPiece(fq, fr);
    const { valid, jumpedCoord } = this.logic.isMoveValid(piece, tq, tr, this.allPlayerMoves, this.mustJump);
    if (valid) {
      this._executeMove(fq, fr, tq, tr, jumpedCoord);
      if (this.isMultiJumping) this._startTimer(10);
    }
  }

  _recomputeAnimTargets() {
    if (!this.board || this.anim.phase === 'tiles' || this.anim.phase === 'pieces') return;
    for (const [key, pa] of this.anim.pieceAnims) {
      if (!key.startsWith('cap-') && pa.piece) {
        const [tx, ty] = hexToPixel(pa.piece.q, pa.piece.r, this.hexCanvas.hexRadius, this.hexCanvas.cx, this.hexCanvas.cy);
        if (pa.isSliding) {
          pa.targetX = tx; pa.targetY = ty;
        } else {
          pa.pixelX = tx; pa.pixelY = ty;
          pa.targetX = tx; pa.targetY = ty;
        }
      }
    }
  }
}

GameController.prototype.startOnlineGame = function(slot, socketClient) {
  this.gameMode = 'online';
  this.aiDepth = 0;
  this.playerSlot = slot;
  this.socketClient = socketClient;
  this.board = new Board(BOARD_SIDE_LENGTH);
  this.logic = new GameLogic(this.board);
  this.board.initializePieces();
  this.currentTurn = PLAYER1;
  this.selectedCoord = null;
  this.possibleMoves = [];
  this.capturedByP1 = [];
  this.capturedByP2 = [];
  this.winner = null;
  this.isMultiJumping = false;
  this._aiPending = false;
  this._pendingGameOver = null;
  this._clearTimer();
  this.phase = 'setup';
  this.anim.initTileFall(this.board, this.hexCanvas.hexRadius, this.hexCanvas.cx, this.hexCanvas.cy);
  if (!this._loopRunning) {
    this._loopRunning = true;
    requestAnimationFrame(this._loop);
  }
};

GameController.prototype.handleServerState = function(state) {
  if (!this.board || this.phase === 'setup' || this.phase === 'pieces') return;
  this.board.pieces.clear();
  for (const { key, color, isKing, q, r } of state.board) {
    this.board.pieces.set(key, { q, r, color, isKing });
  }
  this.anim.syncBoard(this.board, this.hexCanvas.hexRadius, this.hexCanvas.cx, this.hexCanvas.cy);
  this.currentTurn = state.turn;
  this.mustJump = state.mustJump;
  this.capturedByP1 = state.capturedByP1;
  this.capturedByP2 = state.capturedByP2;
  if (state.winner) {
    this.winner = state.winner;
    this.phase = 'gameover';
    if (this._onGameOver) this._onGameOver(state.winner);
    return;
  }
  const { allMoves } = this.logic.getAllPlayerMoves(this.currentTurn);
  this.allPlayerMoves = allMoves;
  this.mustJump = state.mustJump;
  this._notifyTurn();
};
