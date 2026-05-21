import pygame
import math
from constants import *
from utils import hex_to_pixel, get_hex_corners, pixel_to_hex
from piece import Piece

class Board:
    def __init__(self, side_length, hex_radius, screen_width, screen_height):
        self.side_length = side_length
        self.hex_radius = hex_radius
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.center_x = screen_width // 2
        self.center_y = screen_height // 2
        self.pieces = {}  # (q, r) -> Piece object
        self.hex_coords = [] # List of all valid (q, r) coordinates on the board
        self._generate_grid()

        # Used in starting animation
        self.tile_fall_data = [] # Stores [(q, r, start_y, target_y), ...]
        self.tiles_drawn = set() # Tracks which tiles have finished falling

    def _generate_grid(self):
        """Generate the coordinates for hexagonal grid."""
        self.hex_coords = []
        for q in range(-(self.side_length - 1), self.side_length):
            r1 = max(-(self.side_length - 1), -q - (self.side_length - 1))
            r2 = min(self.side_length - 1, -q + (self.side_length - 1))
            for r in range(r1, r2 + 1):
                self.hex_coords.append((q, r))

    def initialize_pieces(self):
        """Place exactly 16 pieces per player, filling the 4 rows closest to each edge symmetrically."""
        self.pieces.clear()
        piece_radius = int(self.hex_radius * 0.7)
        N = self.side_length # Assumed to be 5

        if N != 5:
             print(f"Warning: This layout is explicitly designed for N=5. Results may vary for N={N}.")

        # Define explicit coordinates for the 16 pieces per player for N=5 board
        # Player 1 (White/Bottom - positive r)
        positions_p1 = [
            # Row r=4 (4 pieces)
            (-1, 4), (-2, 4), (-3, 4), (0, 4),
            # Row r=3 (4 pieces)
            (-2, 3), (-1, 3), (0, 3), (1, 3),
            # Row r=2 (4 pieces)
            (-1, 2), (0, 2), (1, 2), (2, 2),
            # Row r=1 (4 pieces)
            (0, 1), (1, 1), (2, 1), (3, 1)
        ]

        # Player 2 (Black/Top - negative r)
        positions_p2 = [
            # Row r=-4 (4 pieces)
            (0, -4), (1, -4), (2, -4), (3, -4),
            # Row r=-3 (4 pieces)
            (-1, -3), (0, -3), (1, -3), (2, -3),
            # Row r=-2 (4 pieces)
            (-2, -2), (-1, -2), (0, -2), (1, -2),
            # Row r=-1 (4 pieces)
            (-3, -1), (-2, -1), (-1, -1), (0, -1)
        ]

        # Place Player 1 pieces, checking if the hex exists on the board
        placed_p1 = 0
        for q, r in positions_p1:
            if (q,r) in self.hex_coords: # Check if the coordinate is valid for the generated board
                self.pieces[(q, r)] = Piece(q, r, PLAYER1, piece_radius)
                placed_p1 += 1
            else:
                 # This indicates an issue with board generation or coordinate definition if N=5
                 print(f"Error: P1 coord ({q},{r}) defined for 16-piece layout not found in generated hex_coords!")

        # Place Player 2 pieces
        placed_p2 = 0
        for q, r in positions_p2:
             if (q,r) in self.hex_coords:
                self.pieces[(q, r)] = Piece(q, r, PLAYER2, piece_radius)
                placed_p2 += 1
             else:
                 print(f"Error: P2 coord ({q},{r}) defined for 16-piece layout not found in generated hex_coords!")

        print(f"Initialized pieces: P1={placed_p1}, P2={placed_p2}. Total={len(self.pieces)}.")
        # Ensure we actually placed 16 per player if N=5
        if N == 5 and (placed_p1 != 16 or placed_p2 != 16):
             print("Error: Did not place the expected 16 pieces per player for N=5 layout!")

        self.initialize_piece_fall_animation()


    def initialize_tile_fall_animation(self):
        self.tile_fall_data = []
        self.tiles_drawn.clear()
        # FIX: Make tiles start further off-screen
        start_y_offset = -self.screen_height * 0.75 # Start well above the screen

        # Sort tiles for a more natural top-to-bottom or center-out fall pattern
        # Example: Sort by r, then by q for a somewhat row-by-row fall
        sorted_coords = sorted(self.hex_coords, key=lambda coord: (coord[1], coord[0]))

        stagger_delay_ms = 25 # Milliseconds between each tile starting its fall
        current_start_time = pygame.time.get_ticks()

        for q, r in sorted_coords:
            target_x, target_y = hex_to_pixel(q, r, self.hex_radius, self.center_x, self.center_y)
            # Initial y position is now target_y + offset (so it starts above and falls down to target_y)
            initial_y = target_y + start_y_offset
            self.tile_fall_data.append({
                'q': q, 'r': r,
                'current_y': initial_y,
                'target_y': target_y,
                'start_fall_time': current_start_time # Time when this tile should begin falling
            })
            current_start_time += stagger_delay_ms


    def update_tile_fall_animation(self):
        """Update falling tile positions. Animates multiple tiles simultaneously."""
        animating_overall = False
        current_time = pygame.time.get_ticks()
        active_falling_tiles = 0
        MAX_SIMULTANEOUS_FALLING = 7 # Adjust for desired effect

        # Iterate through all tiles that could be falling
        # We need to be careful modifying the list while iterating, so collect finished ones
        finished_indices = []

        for i, tile_data in enumerate(self.tile_fall_data):
            if (tile_data['q'], tile_data['r']) in self.tiles_drawn: # Already drawn
                continue

            # Check if it's time for this tile to start falling
            if current_time >= tile_data['start_fall_time'] and active_falling_tiles < MAX_SIMULTANEOUS_FALLING:
                if tile_data.get('is_actively_falling', False) is False:
                    tile_data['is_actively_falling'] = True # Mark as actively falling

                if tile_data['is_actively_falling']:
                    active_falling_tiles += 1
                    tile_data['current_y'] += FALL_SPEED_TILE
                    if tile_data['current_y'] >= tile_data['target_y']:
                        tile_data['current_y'] = tile_data['target_y']
                        self.tiles_drawn.add((tile_data['q'], tile_data['r']))
                        # Don't remove from list yet, mark for removal
                        # This tile is done falling
                        tile_data['is_actively_falling'] = False
                    else:
                        animating_overall = True # This specific tile is still moving
            elif not tile_data.get('is_actively_falling', False):
                # This tile hasn't started or isn't active, but is still pending
                animating_overall = True


        # A tile is considered "finished" if it's in tiles_drawn
        # The animation is truly over when all tile_fall_data coords are in tiles_drawn
        if len(self.tiles_drawn) == len(self.hex_coords):
            self.tile_fall_data.clear() # All tiles have reached destination
            return False # No more tiles to process or animate

        return animating_overall # True if any tile is still to start or is actively falling
    
    def initialize_piece_fall_animation(self):
         start_y_offset = -self.screen_height # Start above the screen

         # Player 1 pieces fall first
         p1_pieces = [p for p in self.pieces.values() if p.color == PLAYER1]
         p1_pieces.sort(key=lambda p: p.r) # Sort by row
         for piece in p1_pieces:
             target_x, target_y = hex_to_pixel(piece.q, piece.r, self.hex_radius, self.center_x, self.center_y)
             piece.target_x = target_x
             piece.target_y = target_y
             piece.pixel_x = target_x
             piece.pixel_y = target_y + start_y_offset
             piece.is_falling = True
             piece.is_sliding = False # Ensure not sliding during fall

         # Player 2 pieces fall next (will be triggered after P1 finishes)
         p2_pieces = [p for p in self.pieces.values() if p.color == PLAYER2]
         p2_pieces.sort(key=lambda p: p.r) # Sort by row
         for piece in p2_pieces:
             target_x, target_y = hex_to_pixel(piece.q, piece.r, self.hex_radius, self.center_x, self.center_y)
             piece.target_x = target_x
             piece.target_y = target_y
             piece.pixel_x = target_x
             # Set initial position, but don't start falling yet
             piece.pixel_y = target_y + start_y_offset
             piece.is_falling = False # Will be set to True later
             piece.is_sliding = False


    def update_tile_fall_animation(self):
        """Update falling tile positions. Animates multiple tiles simultaneously."""
        animating_overall = False
        current_time = pygame.time.get_ticks()
        active_falling_tiles = 0
        MAX_SIMULTANEOUS_FALLING = 7 # Adjust for desired effect

        for i, tile_data in enumerate(self.tile_fall_data):
            if (tile_data['q'], tile_data['r']) in self.tiles_drawn: # Already drawn
                continue

            if current_time >= tile_data['start_fall_time']: # Check if it's time for this tile to consider falling
                if not tile_data.get('is_actively_falling', False) and active_falling_tiles < MAX_SIMULTANEOUS_FALLING:
                    # If not already actively falling AND we have capacity, start it
                    tile_data['is_actively_falling'] = True
                    active_falling_tiles += 1

                if tile_data.get('is_actively_falling', False):
                    # tile_data['y'] += FALL_SPEED_TILE # OLD - CAUSES ERROR
                    tile_data['current_y'] += FALL_SPEED_TILE # CORRECTED
                    if tile_data['current_y'] >= tile_data['target_y']:
                        tile_data['current_y'] = tile_data['target_y']
                        self.tiles_drawn.add((tile_data['q'], tile_data['r']))
                        tile_data['is_actively_falling'] = False # Done falling, no longer active
                        # No need to remove from tile_fall_data here, as we iterate over it.
                        # The check len(self.tiles_drawn) == len(self.hex_coords) handles completion.
                    else:
                        animating_overall = True # This specific tile is still moving
            else: # Tile hasn't reached its start_fall_time yet
                animating_overall = True # Still pending, so animation is ongoing

        if not self.tile_fall_data: # Should only happen if hex_coords was empty
            return False

        if len(self.tiles_drawn) == len(self.hex_coords):
            self.tile_fall_data.clear() # All tiles have reached destination
            return False # No more tiles to process or animate

        return animating_overall


    def draw_board(self, surface, theme):
        """Draws the hexagonal board tiles, including those currently falling."""
        # Draw tiles that have finished falling and are static
        for q, r in self.tiles_drawn:
            center_x, center_y = hex_to_pixel(q, r, self.hex_radius, self.center_x, self.center_y)
            corners = get_hex_corners(q, r, self.hex_radius, self.center_x, self.center_y)
            color = theme["board_light"] if (q + r) % 2 == 0 else theme["board_dark"]
            pygame.draw.polygon(surface, color, corners)
            pygame.draw.polygon(surface, theme["text"], corners, 1) # Outline

        # Draw currently falling tiles
        for tile_data in self.tile_fall_data:
            if (tile_data['q'], tile_data['r']) not in self.tiles_drawn and tile_data.get('is_actively_falling', False):
                q, r = tile_data['q'], tile_data['r']
                # Calculate temporary center based on current falling y
                temp_center_x, _ = hex_to_pixel(q, r, self.hex_radius, self.center_x, self.center_y)
                current_y_pos = tile_data['current_y']

                # Create corners based on this temp center_x and current_y_pos
                temp_corners = []
                for i in range(6):
                    angle_deg = 60 * i
                    angle_rad = math.pi / 180 * angle_deg
                    temp_corners.append(
                        (temp_center_x + self.hex_radius * math.cos(angle_rad),
                         current_y_pos + self.hex_radius * math.sin(angle_rad))
                    )

                color = theme["board_light"] if (q + r) % 2 == 0 else theme["board_dark"]
                pygame.draw.polygon(surface, color, temp_corners)
                pygame.draw.polygon(surface, theme["text"], temp_corners, 1)


    def draw_pieces(self, surface, theme):
        """Draws all pieces currently on the board."""
        for piece in self.pieces.values():
            # Use piece's internal pixel coords which handle animation
             piece.draw(surface, theme, self.center_x, self.center_y)

    def draw_highlights(self, surface, theme, selected_piece_coord, valid_moves):
        """Highlights the selected piece and its valid moves."""
        highlight_radius = self.hex_radius * 0.9 # Slightly smaller than hex

        # Highlight selected piece
        if selected_piece_coord:
            q, r = selected_piece_coord
            center_x, center_y = hex_to_pixel(q, r, self.hex_radius, self.center_x, self.center_y)
            # Use a surface for transparency
            highlight_surface = pygame.Surface((self.hex_radius*2, self.hex_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(highlight_surface, theme["highlight_selected"], (self.hex_radius, self.hex_radius), int(highlight_radius))
            surface.blit(highlight_surface, (center_x - self.hex_radius, center_y - self.hex_radius))


        # Highlight valid moves
        for q, r in valid_moves:
            center_x, center_y = hex_to_pixel(q, r, self.hex_radius, self.center_x, self.center_y)
            # Use a surface for transparency
            highlight_surface = pygame.Surface((self.hex_radius*2, self.hex_radius*2), pygame.SRCALPHA)
            # Draw a smaller circle or dot for valid moves
            pygame.draw.circle(highlight_surface, theme["highlight_valid"], (self.hex_radius, self.hex_radius), int(highlight_radius * 0.5))
            surface.blit(highlight_surface, (center_x - self.hex_radius, center_y - self.hex_radius))


    def get_piece(self, q, r):
        """Returns the piece at (q, r) or None."""
        return self.pieces.get((q, r))

    def get_hex_under_mouse(self, mouse_pos):
        """Converts mouse pixel coordinates to hex coordinates."""
        return pixel_to_hex(mouse_pos[0], mouse_pos[1], self.hex_radius, self.center_x, self.center_y)

    def remove_piece(self, q, r):
        """Removes a piece from the board."""
        if (q, r) in self.pieces:
            removed_piece = self.pieces[(q, r)]
            del self.pieces[(q, r)]
            return removed_piece
        return None

    def move_piece(self, start_q, start_r, end_q, end_r):
        """Moves a piece logically and updates its target pixel position for animation."""
        if (start_q, start_r) in self.pieces:
            piece = self.pieces.pop((start_q, start_r))
            piece.move(end_q, end_r)
            self.pieces[(end_q, end_r)] = piece

            # Set target for sliding animation
            target_x, target_y = hex_to_pixel(end_q, end_r, self.hex_radius, self.center_x, self.center_y)
            piece.set_target_pixel_pos(target_x, target_y)
            return piece # Return the moved piece
        return None

    def update_piece_animations(self, dt):
        """Update all piece animations. Returns True if any piece is still animating."""
        is_animating = False
        for piece in self.pieces.values():
            if piece.update_animation(dt):
                 is_animating = True
        return is_animating

    def resize(self, new_width, new_height):
        """Adjusts board parameters based on new screen size."""
        self.screen_width = new_width
        self.screen_height = new_height
        self.center_x = new_width // 2
        self.center_y = new_height // 2

        # Adjust hex radius based on the smaller screen dimension and board size
        # Fit the board width (diameter = 2*side_length-1 hexes, width = (2*side_length-1)*1.5*radius)
        # Fit the board height (diameter = 2*side_length-1 hexes, height = (2*side_length-1)*sqrt(3)*radius)
        # Add some padding
        padding = 0.9
        max_board_width = (2 * self.side_length - 1) * 1.5
        max_board_height = (2 * self.side_length - 1) * math.sqrt(3)

        radius_w = (new_width * padding) / max_board_width if max_board_width > 0 else 30
        radius_h = (new_height * padding) / max_board_height if max_board_height > 0 else 30

        self.hex_radius = int(min(radius_w, radius_h))

        # Update piece radii and positions
        piece_radius = int(self.hex_radius * 0.7)
        for piece in self.pieces.values():
            piece.radius = piece_radius
            # Recalculate and set both current and target pixel positions immediately
            # (unless an animation is currently running, which resize might interrupt)
            # For simplicity during resize, we snap positions. More complex handling is possible.
            target_x, target_y = hex_to_pixel(piece.q, piece.r, self.hex_radius, self.center_x, self.center_y)
            piece.set_pixel_pos(target_x, target_y)
            piece.is_sliding = False # Stop any slide animation