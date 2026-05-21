const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const path = require('path');
const registerSocketHandlers = require('./socket');

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer);
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname, '../client')));

registerSocketHandlers(io);

httpServer.listen(PORT, () => {
  console.log(`Hexdame server running at http://localhost:${PORT}`);
});
