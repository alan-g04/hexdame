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

    def start_thinking(self):
        """Initiates the thinking process (finds move, sets delay timer)."""
        if not self.is_thinking:
             self.is_thinking = True
             self.think_start_time = pygame.time.get_ticks()
             self.move_to_make = self._find_best_move()
             # print(f"AI decided on move: {self.move_to_make}") # Debug

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

    def _find_best_move(self):
        """Simple AI: Prioritize jumps, then random valid move."""
        all_moves, must_jump = self.logic.get_all_player_moves(self.color)

        if not all_moves:
            return None # No possible moves

        possible_starts = list(all_moves.keys())
        chosen_start = random.choice(possible_starts)
        piece_moves = all_moves[chosen_start]

        if must_jump:
            # Must choose a jump if available for the selected piece
            if piece_moves['jumps']:
                 chosen_jump = random.choice(piece_moves['jumps'])
                 # Return format: (start_q, start_r, end_q, end_r)
                 return (chosen_start[0], chosen_start[1], chosen_jump[0], chosen_jump[1])
            else:
                 # This case shouldn't happen if must_jump is true and logic is correct,
                 # but handle defensively: pick another piece that CAN jump
                 jumpable_starts = [start for start, moves in all_moves.items() if moves['jumps']]
                 if not jumpable_starts: return None # Should not happen
                 chosen_start = random.choice(jumpable_starts)
                 piece_moves = all_moves[chosen_start]
                 chosen_jump = random.choice(piece_moves['jumps'])
                 return (chosen_start[0], chosen_start[1], chosen_jump[0], chosen_jump[1])

        else:
            # Choose a random simple move
            if piece_moves['moves']:
                 chosen_move = random.choice(piece_moves['moves'])
                 return (chosen_start[0], chosen_start[1], chosen_move[0], chosen_move[1])
            else:
                 # Should only happen if piece has no moves, pick another piece
                 movable_starts = [start for start, moves in all_moves.items() if moves['moves']]
                 if not movable_starts: return None # No moves possible at all
                 chosen_start = random.choice(movable_starts)
                 piece_moves = all_moves[chosen_start]
                 chosen_move = random.choice(piece_moves['moves'])
                 return (chosen_start[0], chosen_start[1], chosen_move[0], chosen_move[1])

        return None # Should not be reached