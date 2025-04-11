from constants import *
from utils import hex_distance

class GameLogic:
    def __init__(self, board):
        self.board = board

    def get_valid_moves(self, piece):
        """
        Gets all valid moves (simple moves and jumps) for a single piece.
        Returns a dictionary: {'moves': [(q, r)], 'jumps': [(q, r, jumped_q, jumped_r)]}
        """
        valid_moves = {'moves': [], 'jumps': []}
        q, r = piece.q, piece.r
        player = piece.color

        directions = KING_DIRECTIONS if piece.is_king else MOVE_DIRECTIONS[player]

        for dq, dr in directions:
            target_q, target_r = q + dq, r + dr
            jump_q, jump_r = q + 2*dq, r + 2*dr # Potential jump destination

            target_hex = self.board.get_piece(target_q, target_r)

            # Check if target coordinates are on the board
            if (target_q, target_r) not in self.board.hex_coords:
                 continue # Skip moves off the board edge for the first step

            # Simple Move: Target is empty
            if target_hex is None:
                valid_moves['moves'].append((target_q, target_r))

            # Jump Move: Target contains opponent, and space beyond is empty and on board
            elif target_hex.color != player:
                if (jump_q, jump_r) in self.board.hex_coords and self.board.get_piece(jump_q, jump_r) is None:
                     valid_moves['jumps'].append((jump_q, jump_r, target_q, target_r)) # Store jumped piece coord

        return valid_moves

    def get_all_player_moves(self, player_color):
        """
        Gets all possible moves for a given player.
        Checks if any jumps are available.
        Returns: (dict_of_moves, must_jump)
        dict_of_moves: { (start_q, start_r): {'moves': [...], 'jumps': [...]}, ... }
        must_jump: Boolean indicating if at least one jump is possible for the player.
        """
        all_moves = {}
        must_jump = False
        player_pieces = [p for p in self.board.pieces.values() if p.color == player_color]

        for piece in player_pieces:
            moves = self.get_valid_moves(piece)
            if moves['moves'] or moves['jumps']:
                all_moves[(piece.q, piece.r)] = moves
            if moves['jumps']:
                must_jump = True

        # If a jump is mandatory, filter out simple moves
        if must_jump:
            filtered_moves = {}
            for start_coord, moves_dict in all_moves.items():
                if moves_dict['jumps']:
                     # Only keep pieces that can jump, and only list their jumps
                     filtered_moves[start_coord] = {'moves': [], 'jumps': moves_dict['jumps']}
            return filtered_moves, True
        else:
            return all_moves, False # No jumps available, return all moves

    def is_move_valid(self, piece, end_q, end_r, all_player_moves, must_jump):
        """Checks if a specific move is valid according to the rules."""
        start_coord = (piece.q, piece.r)
        if start_coord not in all_player_moves:
            return False, None # This piece has no valid moves

        possible_piece_moves = all_player_moves[start_coord]

        # Check jumps first
        for jump_dest_q, jump_dest_r, jumped_q, jumped_r in possible_piece_moves.get('jumps', []):
            if (end_q, end_r) == (jump_dest_q, jump_dest_r):
                return True, (jumped_q, jumped_r) # Valid jump, return jumped piece coord

        # If jumps are mandatory, but this wasn't a jump, it's invalid
        if must_jump:
            return False, None

        # Check simple moves (only if not must_jump)
        if (end_q, end_r) in possible_piece_moves.get('moves', []):
            return True, None # Valid simple move, no piece jumped

        return False, None # Move not found

    def check_for_promotion(self, piece):
        """Check if a piece reaches the promotion row."""
        # Define promotion rows (opposite end of the board)
        # Example: If P1 starts at negative r, promotion is at the max positive r edge
        # Example: If P2 starts at positive r, promotion is at the max negative r edge
        max_r = self.board.side_length - 1
        min_r = -(self.board.side_length - 1)

        # Find the min/max r values actually present on the board for edge cases
        all_r = [r for q,r in self.board.hex_coords]
        actual_max_r = max(all_r)
        actual_min_r = min(all_r)


        if piece.color == PLAYER1 and not piece.is_king:
             # Player 1 promotes if it reaches any hex where r == actual_max_r
             # This condition might need refinement depending on exact board shape/goal rows
             if piece.r == actual_max_r:
                 piece.make_king()
                 print(f"Player 1 piece at ({piece.q},{piece.r}) promoted!") # Debug
                 return True

        elif piece.color == PLAYER2 and not piece.is_king:
             # Player 2 promotes if it reaches any hex where r == actual_min_r
             if piece.r == actual_min_r:
                  piece.make_king()
                  print(f"Player 2 piece at ({piece.q},{piece.r}) promoted!") # Debug
                  return True

        return False

    def check_game_over(self, current_player):
        """
        Checks if the game has ended.
        Returns winner (PLAYER1, PLAYER2) or None if game continues.
        """
        opponent = PLAYER2 if current_player == PLAYER1 else PLAYER1

        # Check if opponent has any pieces left
        opponent_pieces = [p for p in self.board.pieces.values() if p.color == opponent]
        if not opponent_pieces:
            print(f"Game Over! Player {current_player} wins (opponent has no pieces).")
            return current_player # Current player wins

        # Check if opponent has any valid moves
        opponent_moves, _ = self.get_all_player_moves(opponent)
        if not opponent_moves:
            print(f"Game Over! Player {current_player} wins (opponent has no moves).")
            return current_player # Current player wins

        return None # Game continues