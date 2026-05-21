import pygame
import random
import time
from constants import *

class AIPlayer:
    def __init__(self, game_logic, player_color):
        self.logic = game_logic
        self.color = player_color
        self.is_thinking = False
        self.think_start_time = 0
        self.move_to_make = None

    def start_thinking(self, current_moves, current_must_jump): # Modified to accept moves
        """Initiates the thinking process (finds move, sets delay timer)."""
        if not self.is_thinking:
             self.is_thinking = True
             self.think_start_time = pygame.time.get_ticks()
             # Use the provided moves directly, don't recalculate here
             self.move_to_make = self._find_best_move(current_moves, current_must_jump)

    def get_move(self):
        """Returns the chosen move after the delay, or None if still thinking."""
        if not self.is_thinking:
             return None

        current_time = pygame.time.get_ticks()
        if current_time - self.think_start_time >= AI_DELAY_MS:
            self.is_thinking = False
            move = self.move_to_make
            self.move_to_make = None # Clear stored move
            return move
        else:
            return None # Still thinking
        
    def find_next_multi_jump(self, jumper_piece):
        """
        Instantly calculates the next available jump for the specific piece
        that is currently in a multi-jump sequence. Returns the move tuple
        (start_q, start_r, end_q, end_r) or None if no further jump found.
        """
        if not jumper_piece:
            return None

        start_coord = (jumper_piece.q, jumper_piece.r)
        # Calculate ONLY jumps for this specific piece
        # Use the GameLogic instance associated with this AI
        jumps_only = self.logic.get_valid_moves(jumper_piece).get('jumps', [])

        if not jumps_only:
            return None # No more jumps found for this piece

        # Simple AI: Choose a random jump from the available ones
        chosen_jump = random.choice(jumps_only)
        # Return format: (start_q, start_r, end_q, end_r)
        return (start_coord[0], start_coord[1], chosen_jump[0], chosen_jump[1])

    def _find_best_move(self, all_moves, must_jump): # Modified to accept moves
        """Finds the best move based on current options (prioritizes jumps)."""
        # Now uses passed-in moves instead of recalculating
        if not all_moves:
            return None # No possible moves

        # --- Logic remains largely the same, but uses the passed `all_moves` ---
        if must_jump:
            jumpable_starts = [start for start, moves in all_moves.items() if moves.get('jumps')]
            if not jumpable_starts: return None
            chosen_start = random.choice(jumpable_starts)
            chosen_jump = random.choice(all_moves[chosen_start]['jumps'])
            return (chosen_start[0], chosen_start[1], chosen_jump[0], chosen_jump[1])
        else:
            # Prefer moves over jumps if not mandatory, or jumps if only option
            movable_starts = [start for start, moves in all_moves.items() if moves.get('moves')]
            if movable_starts:
                 chosen_start = random.choice(movable_starts)
                 chosen_move = random.choice(all_moves[chosen_start]['moves'])
                 return (chosen_start[0], chosen_start[1], chosen_move[0], chosen_move[1])
            else: # No simple moves, must perform a jump if possible (even if not mandatory overall)
                jumpable_starts = [start for start, moves in all_moves.items() if moves.get('jumps')]
                if not jumpable_starts: return None # No moves or jumps
                chosen_start = random.choice(jumpable_starts)
                chosen_jump = random.choice(all_moves[chosen_start]['jumps'])
                return (chosen_start[0], chosen_start[1], chosen_jump[0], chosen_jump[1])