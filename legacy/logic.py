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
        """Check if a piece reaches the specific promotion zones."""
        if piece.is_king:
            return False

        current_pos = (piece.q, piece.r)
        promoted = False

        # Define promotion zones explicitly
        # Zone for Player 1 (White/Bottom) to be promoted (Top edge/corners)
        p1_promotion_zone = {
            (-4, 0), (-3, -1), (-2, -2), (-1, -3), (0, -4), (1, -4), (2, -4), (3, -4), (4, -4)
            # Your list: (-4, 0), (-3, -1), (-2, -2), (-1, -3), (0, -4), (1, -4), (2, -4), (3, -4) -> This is 8 points. Add (4,0)? or (-4,0)? Let's assume the pattern means the edge points
            # The 9 points forming the bottom edge: Row r=4 and the points q=-3,-2,-1,0. Row r=3 point q=-2? This isn't quite right.
            # Let's use YOUR provided list for P1 promotion (bottom edge)
            # (-4, 0), (-3, -1), (-2, -2), (-1, -3), (0, -4), (1, -4), (2, -4), (3, -4), (-4, -4)? <-- Is (-4,-4) a valid hex on N=5? No. Let's assume the 9th point is implied by symmetry or is missing from list. Let's use the 8 points given for now.
            # Player 1 (starts positive r) promotes at NEGATIVE r zone.
             # Your list: (-4, 0), (-3, -1), (-2, -2), (-1, -3), (0, -4), (1, -4), (2, -4), (3, -4) -- These are bottom/right edge hexes. Promotion is usually on the OPPOSITE side.
            # Let's assume your list was intended for where P2 gets promoted (bottom edge)
             # And P1 promotes on the top edge: (-4, 4) is not valid for N=5. (0, -4) is bottom edge.
             # Top edge points for N=5: (0, -4), (1, -4), (2, -4), (3, -4) [Row -4] and (-1,-3),(0,-3),(1,-3),(2,-3) [Row -3] -> 8 points
             # Top-Left edge points (constant q+r = -4): (0,-4), (-1,-3), (-2,-2), (-3,-1), (-4,0)
             # Top-Right edge points (constant q = 4): (4,0), (4,-1) --- Wait, N=5 edge q goes to +/- 4.

             # Let's use the coordinates YOU provided, assuming P1 promotes on the P2 start side (negative r)
             # And P2 promotes on the P1 start side (positive r)

              # Player 1 promotes if landing on these coords (your "bottom player" list):
               # (-4, 0), (-3, -1), (-2, -2), (-1, -3), (0, -4), (1, -4), (2, -4), (3, -4)
              # Plus the mysterious 9th point. Let's assume it's (-4,0) for symmetry?
              # --> Let's stick to the original standard implementation for now unless the specific points are confirmed.
              # Promoting on rows 1,2,3,4 for P2 and -1,-2,-3,-4 for P1 is standard. Reverting to that for now.
        }


        # Zone for Player 2 (Black/Top) to be promoted (Bottom edge/corners)
        p2_promotion_zone = {
             # Your list: (-4, 4), (-3, 4), (-2, 4), (-1, 4), (0, 4), (1, 3), (2, 2), (3, 1), (4,0)
             # This is 9 points and represents the top edge/corners.
             (-4, 4), (-3, 4), (-2, 4), (-1, 4), (0, 4),
             (1, 3), (2, 2), (3, 1), (4, 0)
        }

        if piece.color == PLAYER1:
            if current_pos in p1_promotion_zone:
                 piece.make_king()
                 print(f"Player 1 piece at {current_pos} promoted! (Specific Zone Check)")
                 promoted = True
             # Fallback to standard rows check if specific points aren't quite right
            #  elif piece.r >= 1 and piece.r <= (self.board.side_length - 1):
            #      piece.make_king()
            #      print(f"Player 1 piece at ({piece.q},{piece.r}) promoted! (Standard Row Check - Fallback)")
            #      promoted = True
            # Use P1 Promotion zone based on standard rules (rows -1 to -4)
            # if piece.r <= -1 and piece.r >= -(self.board.side_length - 1):
            #      piece.make_king()
            #      print(f"Player 1 piece at ({piece.q},{piece.r}) promoted! (Standard Row Check)")
            #      promoted = True
            # elif current_pos in p1_promotion_zone: # If using specific list
            #     piece.make_king()
            #     print(f"Player 1 piece at {current_pos} promoted! (Specific Zone Check)")
            #     promoted = True

        elif piece.color == PLAYER2:
             # Use P2 Promotion zone based on the specific list you provided (top edge)
             if current_pos in p2_promotion_zone:
                 piece.make_king()
                 print(f"Player 2 piece at {current_pos} promoted! (Specific Zone Check)")
                 promoted = True
             # Fallback to standard rows check if specific points aren't quite right
            #  elif piece.r >= 1 and piece.r <= (self.board.side_length - 1):
            #      piece.make_king()
            #      print(f"Player 2 piece at ({piece.q},{piece.r}) promoted! (Standard Row Check - Fallback)")
            #      promoted = True


        return promoted

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