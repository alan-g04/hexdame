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
    this._loop = this._loop.bind(this);
  }

  startGame(mode) {
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
    this.phase = 'playing';
    this._calcMoves();
    this._notifyTurn();
    requestAnimationFrame(this._loop);
  }

  _loop() {
    if (this.phase === 'playing' && this.gameMode === 'ai' && this.currentTurn === PLAYER2 && !this._aiPending) {
      this._scheduleAI();
    }
    this.hexCanvas.render(this);
    if (this.phase !== 'gameover') requestAnimationFrame(this._loop);
  }

  _scheduleAI() {
    this._aiPending = true;
    setTimeout(() => {
      this._doAIMove();
      this._aiPending = false;
    }, AI_DELAY_MS);
  }

  _doAIMove() {
    const ai = new AIPlayer(this.logic);
    const move = ai.findMove(this.allPlayerMoves, this.mustJump);
    if (!move) return;
    const [fq, fr, tq, tr] = move;
    const piece = this.board.getPiece(fq, fr);
    const { valid, jumpedCoord } = this.logic.isMoveValid(piece, tq, tr, this.allPlayerMoves, this.mustJump);
    if (valid) this._executeMove(fq, fr, tq, tr, jumpedCoord);
  }

  handleClick(px, py) {
    if (this.phase !== 'playing') return;
    const human = this.gameMode === 'local' || (this.gameMode === 'ai' && this.currentTurn === PLAYER1);
    if (!human || this._aiPending) return;

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
          this._executeMove(this.selectedCoord[0], this.selectedCoord[1], q, r, jumpedCoord);
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
    if (jumpedCoord) {
      const cap = this.board.removePiece(jumpedCoord[0], jumpedCoord[1]);
      if (cap) (this.currentTurn === PLAYER1 ? this.capturedByP1 : this.capturedByP2).push(cap);
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
    if (w) { this.winner = w; this.phase = 'gameover'; if (this._onGameOver) this._onGameOver(w); return; }

    this._switchTurn();
  }

  _switchTurn() {
    this.currentTurn = this.currentTurn === PLAYER1 ? PLAYER2 : PLAYER1;
    this._calcMoves();
    if (!Object.keys(this.allPlayerMoves).length) {
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
  _notifyTurn() { if (this._onTurnChange) this._onTurnChange(this.currentTurn, this.mustJump, this.gameMode); }
}
