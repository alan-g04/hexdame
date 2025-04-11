import pygame
import sys
import math
import random
import time # If not using pygame.time.wait

import constants # Updated in __init__.py thus import... rather than from constants import *
from utils import *
from board import Board
from piece import Piece
from logic import GameLogic
from ui import Button, Dropdown, RadioButtonGroup
from ai import AIPlayer
from animations import QuitAnimator

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        # Get initial screen dimensions for fullscreen
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        constants.SCREEN_WIDTH = self.screen_width # Update constants if needed elsewhere
        constants.SCREEN_HEIGHT = self.screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("Hexdame")
        self.clock = pygame.time.Clock()

        self.current_theme_name = DEFAULT_THEME
        self.theme = THEMES[self.current_theme_name]

        self.game_state = STATE_MENU
        self.game_mode = None # 'LOCAL' or 'VS_COMPUTER'

        # --- Menu UI ---
        self.menu_buttons = []
        self.options_ui = {}
        self.info_popup_visible = False
        self.quit_animator = None
        self.last_screen_capture = None # For quit animation

        # --- Game Variables ---
        self.board = None # Initialized in start_game
        self.logic = None # Initialized in start_game
        self.ai_player = None # Initialized in start_game if needed
        self.current_turn = PLAYER1
        self.selected_piece = None # The Piece object selected
        self.selected_piece_coord = None # (q, r) of selected piece
        self.possible_moves = [] # List of valid (q, r) destinations for selected piece
        self.all_player_moves = {} # All moves for the current player {(q,r): {'moves':[], 'jumps':[]}}
        self.must_jump = False # Flag indicating if a jump is mandatory
        self.captured_pieces = {PLAYER1: [], PLAYER2: []} # Store captured Piece objects
        self.winner = None
        self.is_animating_move = False # Flag to prevent input during move slide/capture
        self.is_animating_setup = False # Flag for board/piece falling animations
        self.p1_fall_complete = False
        self.p2_fall_initiated = False

        self._setup_menu()
        self._setup_options()


    def _setup_menu(self):
        self.menu_buttons = []
        button_width = 300
        button_height = 60
        text_size = 24
        start_y = self.screen_height // 2 - 150
        spacing = 80

        # Start Game Button (placeholder action, real action shows dropdown)
        self.menu_buttons.append(Button(self.screen_width // 2 - button_width // 2, start_y, button_width, button_height, "START GAME", text_size, action=self._toggle_start_dropdown))
        # Dropdown for game mode (initially hidden)
        self.start_game_dropdown = Dropdown(self.screen_width // 2 - button_width // 2, start_y + button_height + 5, button_width, button_height, ["LOCAL", "VS COMPUTER"], text_size)
        self.start_game_dropdown.is_open = False # Hide initially

        self.menu_buttons.append(Button(self.screen_width // 2 - button_width // 2, start_y + spacing, button_width, button_height, "OPTIONS", text_size, action=lambda: self.change_state(STATE_OPTIONS)))
        self.menu_buttons.append(Button(self.screen_width // 2 - button_width // 2, start_y + 2*spacing, button_width, button_height, "INFO", text_size, action=lambda: self.change_state(STATE_INFO)))
        self.menu_buttons.append(Button(self.screen_width // 2 - button_width // 2, start_y + 3*spacing, button_width, button_height, "QUIT", text_size, action=self.initiate_quit))

    def _toggle_start_dropdown(self):
         # Find the start button to position dropdown correctly
         start_button_rect = None
         for btn in self.menu_buttons:
             if btn.text == "START GAME":
                 start_button_rect = btn.rect
                 break
         if start_button_rect:
             self.start_game_dropdown.rect.topleft = (start_button_rect.left, start_button_rect.bottom + 5)
             self.start_game_dropdown.is_open = not self.start_game_dropdown.is_open


    def _setup_options(self):
         self.options_ui = {}
         # Theme Selection Radio Buttons
         theme_options = list(THEMES.keys())
         radio_x = 100
         radio_y = 150
         radio_text_size = 20
         self.options_ui['theme_selector'] = RadioButtonGroup(radio_x, radio_y, theme_options, radio_text_size, initial_selection=self.current_theme_name)

         # Back Button
         back_button = Button(self.screen_width - 170, self.screen_height - 80, 150, 50, "BACK", 20, action=lambda: self.change_state(STATE_MENU))
         self.options_ui['back_button'] = back_button

    def change_state(self, new_state):
        print(f"Changing state from {self.game_state} to {new_state}") # Debug
        # Reset things when leaving a state if necessary
        if self.game_state == STATE_INFO:
            self.info_popup_visible = False
        if self.game_state == STATE_MENU:
             self.start_game_dropdown.is_open = False # Close dropdown when leaving menu

        self.game_state = new_state

        # Setup things when entering a new state
        if new_state == STATE_INFO:
            self.info_popup_visible = True
        if new_state == STATE_MENU:
             # Refresh menu button positions if screen size changed? (Add later if needed)
             pass
        if new_state == STATE_BOARD_SETUP_ANIM:
            self.start_board_setup_animation()


    def start_game(self, mode):
        self.game_mode = mode
        print(f"Starting game: {self.game_mode}")

        # Calculate initial hex radius based on screen size
        padding = 0.85 # Leave some space around the board
        max_board_width = (2 * BOARD_SIDE_LENGTH - 1) * 1.5
        max_board_height = (2 * BOARD_SIDE_LENGTH - 1) * math.sqrt(3)
        radius_w = (self.screen_width * padding) / max_board_width if max_board_width > 0 else 30
        radius_h = (self.screen_height * padding) / max_board_height if max_board_height > 0 else 30
        initial_hex_radius = int(min(radius_w, radius_h))
        constants.HEX_RADIUS = initial_hex_radius # Store globally if needed

        self.board = Board(BOARD_SIDE_LENGTH, initial_hex_radius, self.screen_width, self.screen_height)
        self.logic = GameLogic(self.board)
        self.board.initialize_pieces() # Creates pieces but doesn't position them yet
        self.current_turn = PLAYER1
        self.selected_piece = None
        self.selected_piece_coord = None
        self.possible_moves = []
        self.all_player_moves = {}
        self.must_jump = False
        self.captured_pieces = {PLAYER1: [], PLAYER2: []}
        self.winner = None
        self.is_animating_move = False
        self.is_animating_setup = True # Start setup animations
        self.p1_fall_complete = False
        self.p2_fall_initiated = False


        if self.game_mode == 'VS_COMPUTER':
            self.ai_player = AIPlayer(self.logic, COMPUTER)
        else:
            self.ai_player = None

        self.change_state(STATE_BOARD_SETUP_ANIM) # Go to tile falling animation first


    def start_board_setup_animation(self):
        self.board.initialize_tile_fall_animation()
        self.is_animating_setup = True

    def start_piece_setup_animation(self):
        self.board.initialize_piece_fall_animation() # Sets pieces above board, P1 ready to fall
        self.change_state(STATE_PIECE_SETUP_ANIM)
        self.is_animating_setup = True


    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0 # Delta time in seconds

            # --- Event Handling ---
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.initiate_quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                         if self.game_state == STATE_PLAYING:
                              self.change_state(STATE_MENU) # Option to go back to menu
                         elif self.game_state == STATE_OPTIONS or self.game_state == STATE_INFO or self.game_state == STATE_GAME_OVER:
                              self.change_state(STATE_MENU)
                         elif self.game_state == STATE_MENU:
                              self.initiate_quit() # Escape quits from main menu

                if event.type == pygame.VIDEORESIZE:
                    # Handle window resizing if not fullscreen or if allowed
                    # self.screen_width, self.screen_height = event.w, event.h
                    # self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE | ...)
                    # self.resize_elements() # Need a function to resize/reposition everything
                    pass # Fullscreen initially, so ignore this for now

                # Pass events to current state handler
                if self.game_state == STATE_MENU:
                    self.handle_menu_events(event)
                elif self.game_state == STATE_OPTIONS:
                    self.handle_options_events(event)
                elif self.game_state == STATE_INFO:
                    self.handle_info_events(event)
                elif self.game_state == STATE_PLAYING and not self.is_animating_move and not self.is_animating_setup:
                    self.handle_playing_events(event)
                elif self.game_state == STATE_GAME_OVER:
                    self.handle_game_over_events(event)


            # --- Game Logic / Updates ---
            if self.game_state == STATE_QUIT_ANIMATION:
                if self.quit_animator:
                    if not self.quit_animator.update():
                        running = False # Quit animation finished
                else:
                    running = False # Should not happen, but exit anyway

            elif self.game_state == STATE_BOARD_SETUP_ANIM:
                if self.board:
                    if not self.board.update_tile_fall_animation():
                        # Tiles finished falling, start piece animation
                        self.start_piece_setup_animation()

            elif self.game_state == STATE_PIECE_SETUP_ANIM:
                 if self.board:
                    # Animate P1 pieces first
                    p1_still_falling = False
                    if not self.p1_fall_complete:
                        for piece in self.board.pieces.values():
                            if piece.color == PLAYER1 and piece.is_falling:
                                piece.update_animation(dt)
                                if piece.is_falling: # Check again after update
                                    p1_still_falling = True
                        if not p1_still_falling:
                            self.p1_fall_complete = True
                            self.p2_fall_initiated = False # Ensure ready to start P2

                     # Animate P2 pieces after P1 finishes
                    if self.p1_fall_complete:
                        if not self.p2_fall_initiated:
                            # Start P2 falling
                            for piece in self.board.pieces.values():
                                if piece.color == PLAYER2:
                                    piece.is_falling = True
                            self.p2_fall_initiated = True

                        p2_still_falling = False
                        if self.p2_fall_initiated:
                            for piece in self.board.pieces.values():
                                if piece.color == PLAYER2 and piece.is_falling:
                                    piece.update_animation(dt)
                                    if piece.is_falling:
                                        p2_still_falling = True

                          # If P2 also finished, transition to playing state
                        if self.p2_fall_initiated and not p2_still_falling:
                            self.is_animating_setup = False
                            self.change_state(STATE_PLAYING)
                            self._calculate_initial_moves() # Calculate moves for the first turn


            elif self.game_state == STATE_PLAYING:
                 self.update_playing(dt)


            # --- Drawing ---
            # Background
            self.screen.fill(self.theme.get("menu_bg", (150, 150, 150)))

            if self.game_state == STATE_MENU:
                self.draw_menu()
            elif self.game_state == STATE_OPTIONS:
                self.draw_options()
            elif self.game_state == STATE_INFO:
                self.draw_info_popup()
            elif self.game_state in [STATE_BOARD_SETUP_ANIM, STATE_PIECE_SETUP_ANIM, STATE_PLAYING, STATE_GAME_OVER]:
                 self.draw_game_screen()
                 if self.game_state == STATE_GAME_OVER:
                     self.draw_game_over_message()

            elif self.game_state == STATE_QUIT_ANIMATION:
                if self.quit_animator and self.last_screen_capture:
                    self.quit_animator.draw(self.screen, self.last_screen_capture)


            pygame.display.flip() # Update the full screen

        pygame.quit()
        sys.exit()


    # --- State-Specific Event Handlers ---

    def handle_menu_events(self, event):
        # Handle dropdown first if open
        if self.start_game_dropdown.is_open:
            if self.start_game_dropdown.handle_event(event):
                 # Check if an option was selected
                 selected = self.start_game_dropdown.selected_option
                 if selected == "LOCAL":
                     self.start_game('LOCAL')
                 elif selected == "VS COMPUTER":
                     self.start_game('VS_COMPUTER')
                 # Don't process other buttons if dropdown handled the click
                 return

        # Handle regular buttons
        for button in self.menu_buttons:
            if button.handle_event(event):
                 break # Stop processing buttons if one was clicked


    def handle_options_events(self, event):
        if self.options_ui['theme_selector'].handle_event(event):
            new_theme_name = self.options_ui['theme_selector'].selected_option
            if new_theme_name != self.current_theme_name:
                 self.current_theme_name = new_theme_name
                 self.theme = THEMES[self.current_theme_name]
                 # Add contrast check validation here if needed
                 print(f"Theme changed to: {self.current_theme_name}")

        if self.options_ui['back_button'].handle_event(event):
            pass # Action is handled by the button itself


    def handle_info_events(self, event):
         # Allow closing info by clicking anywhere or pressing Esc (handled in main loop)
         if event.type == pygame.MOUSEBUTTONDOWN:
              self.change_state(STATE_MENU)


    def handle_playing_events(self, event):
        # Only handle clicks if it's human's turn or local play
        is_human_turn = (self.game_mode == 'LOCAL' or
                         (self.game_mode == 'VS_COMPUTER' and self.current_turn == PLAYER1))

        if is_human_turn and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Left click
            mouse_pos = event.pos
            clicked_q, clicked_r = self.board.get_hex_under_mouse(mouse_pos)

            # Check if the click is on a valid hex on the board
            if (clicked_q, clicked_r) not in self.board.hex_coords:
                self.selected_piece = None # Clicked outside board
                self.selected_piece_coord = None
                self.possible_moves = []
                return

            clicked_piece = self.board.get_piece(clicked_q, clicked_r)

            # --- Selecting a piece ---
            if clicked_piece and clicked_piece.color == self.current_turn:
                # Check if this piece is allowed to be selected (due to forced jumps)
                if self.must_jump and (clicked_q, clicked_r) not in self.all_player_moves:
                     print("Must move a piece that can jump!") # User feedback
                     self.selected_piece = None # Cannot select this piece
                     self.selected_piece_coord = None
                     self.possible_moves = []
                else:
                     self.selected_piece = clicked_piece
                     self.selected_piece_coord = (clicked_q, clicked_r)
                     # Show only jumps if must_jump, otherwise show all moves for this piece
                     if self.must_jump:
                          self.possible_moves = [jump[:2] for jump in self.all_player_moves[(clicked_q, clicked_r)].get('jumps', [])]
                     else:
                          moves = self.all_player_moves[(clicked_q, clicked_r)].get('moves', [])
                          jumps = [jump[:2] for jump in self.all_player_moves[(clicked_q, clicked_r)].get('jumps', [])]
                          self.possible_moves = moves + jumps
                     # print(f"Selected piece at {self.selected_piece_coord}. Possible moves: {self.possible_moves}") # Debug


            # --- Making a move ---
            elif self.selected_piece and (clicked_q, clicked_r) in self.possible_moves:
                 # Double check validity (redundant but safe)
                 is_valid, jumped_coord = self.logic.is_move_valid(self.selected_piece, clicked_q, clicked_r, self.all_player_moves, self.must_jump)

                 if is_valid:
                      self.execute_move(self.selected_piece_coord, (clicked_q, clicked_r), jumped_coord)
                 else:
                      # This shouldn't happen if possible_moves is correct
                      print("Error: Move deemed invalid unexpectedly.")
                      self.selected_piece = None
                      self.selected_piece_coord = None
                      self.possible_moves = []

            # --- Clicking elsewhere ---
            else:
                 self.selected_piece = None
                 self.selected_piece_coord = None
                 self.possible_moves = []


    def handle_game_over_events(self, event):
         # Click or Keypress to return to menu
         if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
              self.change_state(STATE_MENU)


    # --- State-Specific Update Logic ---

    def update_playing(self, dt):
        if self.winner: # If game already ended this turn
             self.change_state(STATE_GAME_OVER)
             return

        # Update piece animations (sliding, captured)
        if self.board:
            self.is_animating_move = self.board.update_piece_animations(dt)
            # Update captured piece animations
            for player_list in self.captured_pieces.values():
                 for piece in player_list:
                     if piece.is_captured:
                         if piece.update_animation(dt):
                              self.is_animating_move = True


        # If an animation is playing, wait for it to finish
        if self.is_animating_move:
            return

        # --- AI Turn Logic ---
        if self.game_mode == 'VS_COMPUTER' and self.current_turn == COMPUTER and not self.winner:
            if not self.ai_player.is_thinking:
                self.ai_player.start_thinking()

            ai_move = self.ai_player.get_move() # Returns move after delay, or None
            if ai_move:
                start_q, start_r, end_q, end_r = ai_move
                ai_piece = self.board.get_piece(start_q, start_r)
                if ai_piece:
                    is_valid, jumped_coord = self.logic.is_move_valid(ai_piece, end_q, end_r, self.all_player_moves, self.must_jump)
                    if is_valid:
                         self.execute_move((start_q, start_r), (end_q, end_r), jumped_coord)
                    else:
                         print("AI Error: AI generated invalid move!")
                         # Handle error: maybe force AI to recalculate or skip turn?
                         self.switch_turn() # Simple error handling: skip turn
                else:
                     print("AI Error: AI chose non-existent piece!")
                     self.switch_turn() # Skip turn

        # No updates needed for local player's turn other than animation & event handling


    # --- Core Game Actions ---

    def execute_move(self, start_coord, end_coord, jumped_coord):
        """Executes the move, handles captures, checks promotion & game over."""
        print(f"Executing move: {start_coord} -> {end_coord}") # Debug
        moved_piece = self.board.move_piece(start_coord[0], start_coord[1], end_coord[0], end_coord[1])

        if not moved_piece:
            print("Error: Failed to move piece logically.")
            return # Should not happen

        captured_piece = None
        if jumped_coord:
            captured_piece = self.board.remove_piece(jumped_coord[0], jumped_coord[1])
            if captured_piece:
                print(f"Captured piece at {jumped_coord}")
                self.add_captured_piece(captured_piece)
                captured_piece.is_captured = True # Trigger capture animation
                self.is_animating_move = True # Ensure animations run

        # Check for promotion *after* the move is complete
        promoted = self.logic.check_for_promotion(moved_piece)

        # --- Check for multi-jump ---
        # If a jump was made and the piece can jump AGAIN from the new position
        can_multi_jump = False
        if jumped_coord and not promoted: # Kings usually stop multi-jumps in checkers, but depends on ruleset. Assume they do for now.
             # Temporarily calculate jumps only for the piece that just moved
             piece_jumps = self.logic.get_valid_moves(moved_piece)['jumps']
             if piece_jumps:
                  can_multi_jump = True
                  print("Multi-jump available!")
                  # Force the current player to continue jumping with this piece
                  self.all_player_moves = {end_coord: {'moves': [], 'jumps': piece_jumps}}
                  self.must_jump = True
                  # Re-select the piece at its new location
                  self.selected_piece = moved_piece
                  self.selected_piece_coord = end_coord
                  self.possible_moves = [jump[:2] for jump in piece_jumps]
                  # Do NOT switch turn yet
                  return # Exit execute_move, wait for next player input/AI move


        # If no multi-jump, proceed to end the turn
        self.selected_piece = None
        self.selected_piece_coord = None
        self.possible_moves = []

        # Check for game over BEFORE switching turns
        winner = self.logic.check_game_over(self.current_turn)
        if winner:
            self.winner = winner
            self.change_state(STATE_GAME_OVER)
        else:
            self.switch_turn()


    def switch_turn(self):
        self.current_turn = PLAYER2 if self.current_turn == PLAYER1 else PLAYER1
        print(f"--- Switching Turn: Player {self.current_turn}'s Turn ---")
        # Recalculate valid moves for the new player
        self.all_player_moves, self.must_jump = self.logic.get_all_player_moves(self.current_turn)
        # print(f"Player {self.current_turn} moves calculated. Must jump: {self.must_jump}")
        # print(f"All moves: {self.all_player_moves}") # Debug

        # Check if the new player has any moves. If not, game over.
        if not self.all_player_moves and not self.is_animating_move: # Don't end game during animation
             opponent = PLAYER2 if self.current_turn == PLAYER1 else PLAYER1
             self.winner = opponent # Previous player wins because current player has no moves
             print(f"No moves available for Player {self.current_turn}. Player {opponent} wins.")
             self.change_state(STATE_GAME_OVER)


    def _calculate_initial_moves(self):
         """Calculates moves for the starting player (P1)."""
         self.all_player_moves, self.must_jump = self.logic.get_all_player_moves(self.current_turn)
         # print(f"Initial moves calculated for Player {self.current_turn}. Must jump: {self.must_jump}")
         # print(f"All moves: {self.all_player_moves}") # Debug

    def add_captured_piece(self, piece):
        """Adds a captured piece to the correct list and sets its target animation pos."""
        capture_area_y = 50
        capture_spacing = int(piece.radius * 2.5)
        capture_x = 0

        capturing_player = PLAYER2 if piece.color == PLAYER1 else PLAYER1 # The player who DID the capture

        if capturing_player == PLAYER1:
             # Captured by P1 -> display on left side (adjust x based on screen width)
             capture_x = 50 + len(self.captured_pieces[PLAYER1]) * capture_spacing
             piece.capture_target_pos = (capture_x, capture_area_y)
             self.captured_pieces[PLAYER1].append(piece)
        else: # Captured by P2 or Computer
             # Captured by P2 -> display on right side (adjust x based on screen width)
             capture_x = self.screen_width - 50 - len(self.captured_pieces[PLAYER2]) * capture_spacing
             piece.capture_target_pos = (capture_x, capture_area_y)
             self.captured_pieces[PLAYER2].append(piece)

        piece.is_captured = True # Ensure animation starts


    # --- State-Specific Drawing ---

    def draw_menu(self):
        # Title
        draw_text(self.screen, "HEXDAME", 64, self.screen_width // 2, 100, self.theme["text"], center=True)

        # Buttons
        for button in self.menu_buttons:
            button.draw(self.screen, self.theme)

        # Dropdown (drawn on top if open)
        self.start_game_dropdown.draw(self.screen, self.theme)


    def draw_options(self):
         draw_text(self.screen, "OPTIONS", 48, self.screen_width // 2, 50, self.theme["text"], center=True)
         draw_text(self.screen, "Theme:", 24, 100, 110, self.theme["text"])

         # Draw UI elements
         self.options_ui['theme_selector'].draw(self.screen, self.theme)
         self.options_ui['back_button'].draw(self.screen, self.theme)


    def draw_info_popup(self):
         # Semi-transparent overlay
         overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
         overlay.fill((0, 0, 0, 180)) # Dark semi-transparent
         self.screen.blit(overlay, (0,0))

         # Popup Box
         popup_width = self.screen_width * 0.7
         popup_height = self.screen_height * 0.7
         popup_x = (self.screen_width - popup_width) // 2
         popup_y = (self.screen_height - popup_height) // 2
         popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
         pygame.draw.rect(self.screen, self.theme["info_popup_bg"], popup_rect, border_radius=10)
         pygame.draw.rect(self.screen, self.theme["info_popup_text"], popup_rect, width=2, border_radius=10)


         # Info Text (Add your detailed instructions here)
         info_lines = [
             ("HEXDAME INSTRUCTIONS", 32, True),
             ("", 10, False), # Spacer
             ("Goal: Capture all opponent pieces or leave them with no valid moves.", 18, False),
             ("Movement:", 20, False),
             ("- Normal pieces move 'forward' one step diagonally or sideways to an empty hex.", 16, False),
             ("- Kings (pieces reaching the opponent's far edge) can move one step in any direction.", 16, False),
             ("Capturing:", 20, False),
             ("- Jump over an adjacent opponent piece to an empty hex directly beyond it.", 16, False),
             ("- Jumps are MANDATORY. If a jump is available, you MUST take it.", 16, False),
             ("- Multiple jumps in a single turn are possible if available.", 16, False),
             ("- Captured pieces are removed from the board.", 16, False),
             ("", 10, False),
             ("Starting a Game:", 20, False),
             ("- Click START GAME, then select LOCAL (2 players) or VS COMPUTER.", 16, False),
             ("", 10, False),
             ("Options:", 20, False),
             ("- Click OPTIONS to change the board/piece theme using the radio buttons.", 16, False),
             ("", 10, False),
             ("Controls:", 20, False),
             ("- Click your piece to select it.", 16, False),
             ("- Click a highlighted hex to move.", 16, False),
             ("- Press ESC to return to the menu from game/options/info.", 16, False),
             ("- Press ESC in the menu to quit.", 16, False),
             ("", 15, False),
             ("Click anywhere or press ESC to close this.", 18, True),
         ]

         current_y = popup_y + 30
         line_height_multiplier = 1.3
         for text, size, centered in info_lines:
             text_x = popup_x + popup_width // 2 if centered else popup_x + 30
             text_rect = draw_text(self.screen, text, size, text_x, current_y, self.theme["info_popup_text"], center=centered)
             current_y += int(size * line_height_multiplier)


    def draw_game_screen(self):
        if not self.board: return

        # Draw board tiles (handles falling animation internally)
        self.board.draw_board(self.screen, self.theme)

        # Draw highlights below pieces
        if not self.is_animating_setup: # Don't draw highlights during setup
            self.board.draw_highlights(self.screen, self.theme, self.selected_piece_coord, self.possible_moves)

        # Draw pieces (handles falling/sliding animation internally)
        self.board.draw_pieces(self.screen, self.theme)

        # Draw captured pieces (handles sliding animation internally)
        self.draw_captured_pieces()

        # Draw Turn Indicator (only when not animating setup)
        if not self.is_animating_setup:
             indicator_text = ""
             if self.current_turn == PLAYER1:
                 indicator_text = "PLAYER 1's TURN" if self.game_mode == 'LOCAL' else "PLAYER'S TURN"
             else: # Player 2 / Computer
                 indicator_text = "PLAYER 2's TURN" if self.game_mode == 'LOCAL' else "COMPUTER'S TURN"

             if self.must_jump:
                 indicator_text += " (MUST JUMP)"

             draw_text(self.screen, indicator_text, 24, self.screen_width // 2, 15, self.theme["text"], center=True)


    def draw_captured_pieces(self):
        """Draws the piles of captured pieces."""
        # Draw background areas for captured pieces (optional)
        cap_bg_height = int(self.board.hex_radius * 2.5)
        cap_bg_width = self.screen_width * 0.3 # Adjust width as needed
        cap_area_p1 = pygame.Rect(10, 10, cap_bg_width, cap_bg_height)
        cap_area_p2 = pygame.Rect(self.screen_width - cap_bg_width - 10, 10, cap_bg_width, cap_bg_height)
        # pygame.draw.rect(self.screen, self.theme["capture_bg"], cap_area_p1, border_radius=5)
        # pygame.draw.rect(self.screen, self.theme["capture_bg"], cap_area_p2, border_radius=5)

        # Draw Player 1's captures (pieces belonging to P2, captured by P1)
        for piece in self.captured_pieces[PLAYER1]:
             piece.draw(self.screen, self.theme, 0, 0) # Use piece's own pixel coords

        # Draw Player 2's captures (pieces belonging to P1, captured by P2)
        for piece in self.captured_pieces[PLAYER2]:
             piece.draw(self.screen, self.theme, 0, 0) # Use piece's own pixel coords


    def draw_game_over_message(self):
        # Semi-transparent overlay
         overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
         overlay.fill((0, 0, 0, 150)) # Dark semi-transparent
         self.screen.blit(overlay, (0,0))

         winner_text = ""
         if self.winner == PLAYER1:
             winner_text = "PLAYER 1 WINS!" if self.game_mode == 'LOCAL' else "PLAYER WINS!"
         elif self.winner == PLAYER2:
             winner_text = "PLAYER 2 WINS!" if self.game_mode == 'LOCAL' else "COMPUTER WINS!"
         else:
              winner_text = "IT'S A DRAW!" # Should not happen in checkers normally

         draw_text(self.screen, "GAME OVER", 72, self.screen_width // 2, self.screen_height // 2 - 50, self.theme.get("player1_king", (255,255,0)), center=True)
         draw_text(self.screen, winner_text, 48, self.screen_width // 2, self.screen_height // 2 + 20, self.theme.get("player2_king", (255,255,255)), center=True)
         draw_text(self.screen, "Click or Press ESC to return to Menu", 20, self.screen_width // 2, self.screen_height // 2 + 80, self.theme.get("text", (200,200,200)), center=True)

    def initiate_quit(self):
         print("Initiating Quit")
         # Capture the current screen for the animation
         self.last_screen_capture = self.screen.copy()
         self.quit_animator = QuitAnimator(self.screen_width, self.screen_height)
         self.change_state(STATE_QUIT_ANIMATION)


    def resize_elements(self):
         # --- Important for Resizable Window (Not used in initial fullscreen setup) ---
         # Recalculate button positions, font sizes, board size etc. based on new
         # self.screen_width and self.screen_height
         print("Resizing elements...") # Placeholder
         # Example: Recalculate board size and piece positions
         if self.board:
              self.board.resize(self.screen_width, self.screen_height)
         # Remake UI elements like buttons with new coordinates/sizes
         self._setup_menu()
         self._setup_options()
         # Recalculate captured piece positions etc.


# --- Main Execution ---
if __name__ == '__main__':
    # Before starting the game, ensure the 'fonts' directory exists
    # if not os.path.exists('fonts'):
    #     os.makedirs('fonts')
    #     print("Created 'fonts' directory. Please place your font file (e.g., PressStart2P-Regular.ttf or your .woff2) inside.")

    game = Game()
    game.run()