import pygame
import math
from constants import *
from utils import hex_to_pixel

class Piece:
    def __init__(self, q, r, color, radius):
        self.q = q
        self.r = r
        self.color = color # PLAYER1 or PLAYER2
        self.is_king = False
        self.radius = radius # Piece radius (slightly smaller than hex radius)
        self.pixel_x = 0 # Current drawing position X
        self.pixel_y = 0 # Current drawing position Y
        self.target_x = 0 # Target position X (for animation)
        self.target_y = 0 # Target position Y (for animation)
        self.is_falling = False
        self.is_sliding = False
        self.is_captured = False
        self.capture_target_pos = None

    def make_king(self):
        self.is_king = True

    def move(self, q, r):
        self.q = q
        self.r = r

    def set_pixel_pos(self, x, y):
        self.pixel_x = x
        self.target_x = x
        self.pixel_y = y
        self.target_y = y

    def set_target_pixel_pos(self, target_x, target_y):
        self.target_x = target_x
        self.target_y = target_y
        if not self.is_falling: # Don't slide if just fallen into place
            self.is_sliding = True

    def update_animation(self, dt):
        """Update piece position for animations (falling, sliding)."""
        moved = False
        # Falling animation
        if self.is_falling:
            self.pixel_y += FALL_SPEED_PIECE # * dt # Use dt for frame-rate independence if needed
            if self.pixel_y >= self.target_y:
                self.pixel_y = self.target_y
                self.is_falling = False
            moved = True

        # Sliding animation
        elif self.is_sliding:
            dx = self.target_x - self.pixel_x
            dy = self.target_y - self.pixel_y
            dist = math.sqrt(dx*dx + dy*dy)

            if dist < SLIDE_SPEED: # * dt:
                self.pixel_x = self.target_x
                self.pixel_y = self.target_y
                self.is_sliding = False
            else:
                self.pixel_x += (dx / dist) * SLIDE_SPEED # * dt
                self.pixel_y += (dy / dist) * SLIDE_SPEED # * dt
            moved = True

        # Captured animation
        elif self.is_captured and self.capture_target_pos:
            target_x, target_y = self.capture_target_pos
            dx = target_x - self.pixel_x
            dy = target_y - self.pixel_y
            dist = math.sqrt(dx*dx + dy*dy)

            if dist < SLIDE_SPEED: #*dt
                self.pixel_x = target_x
                self.pixel_y = target_y
                self.capture_target_pos = None # Stop animating once reached target
            else:
                self.pixel_x += (dx / dist) * SLIDE_SPEED #* dt
                self.pixel_y += (dy / dist) * SLIDE_SPEED #* dt
            moved = True

        return moved


    def draw(self, surface, theme, board_center_x, board_center_y):
        """Draws the piece on the surface."""
        # If not animating, ensure pixel coords match logical coords
        # if not self.is_falling and not self.is_sliding and not self.is_captured:
        #     self.pixel_x, self.pixel_y = hex_to_pixel(self.q, self.r, self.radius * 1.2, board_center_x, board_center_y) # Use hex radius here

        color_key = f"player{self.color}_piece"
        piece_color = theme[color_key]
        if self.is_king:
            king_color_key = f"player{self.color}_king"
            piece_color = theme.get(king_color_key, piece_color) # Use king color if defined

        pygame.draw.circle(surface, piece_color, (int(self.pixel_x), int(self.pixel_y)), int(self.radius))

        # Add indication for King (e.g., smaller inner circle or symbol)
        if self.is_king:
            pygame.draw.circle(surface, theme['board_light'], (int(self.pixel_x), int(self.pixel_y)), int(self.radius * 0.5))
            pygame.draw.circle(surface, theme['board_dark'], (int(self.pixel_x), int(self.pixel_y)), int(self.radius * 0.4), 2)