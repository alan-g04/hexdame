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
        self.is_multi_jumping = False

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
        start_game_button = Button(self.screen_width // 2 - button_width // 2, start_y, button_width, button_height, "START GAME", text_size, action=self._toggle_start_dropdown)
        self.menu_buttons.append(start_game_button)

        # Dropdown for game mode (initially hidden)
        # Position it based on the start_game_button's rect
        # FIX: Ensure correct options are passed and position is dynamic
        self.start_game_dropdown = Dropdown(
            start_game_button.rect.left, # Align with button's left
            start_game_button.rect.bottom + 5, # Position below the button
            button_width,
            button_height,
            ["LOCAL", "VS COMPUTER"], # Corrected options
            text_size
        )
        self.start_game_dropdown.is_open = False # Hide initially

        self.menu_buttons.append(Button(self.screen_width // 2 - button_width // 2, start_y + spacing, button_width, button_height, "OPTIONS", text_size, action=lambda: self.change_state(STATE_OPTIONS)))
        self.menu_buttons.append(Button(self.screen_width // 2 - button_width // 2, start_y + 2*spacing, button_width, button_height, "INFO", text_size, action=lambda: self.change_state(STATE_INFO)))
        self.menu_buttons.append(Button(self.screen_width // 2 - button_width // 2, start_y + 3*spacing, button_width, button_height, "QUIT", text_size, action=self.initiate_quit))

    def _toggle_start_dropdown(self):
         # This function's sole purpose is now just to toggle visibility
         # The positioning is handled during creation in _setup_menu
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
        # Handle dropdown first if open or if the click is on the main dropdown rect
        dropdown_handled_click, selected_option = self.start_game_dropdown.handle_event(event)

        if dropdown_handled_click:
             if selected_option: # An option was actually chosen
                 print(f"Dropdown option selected: {selected_option}")
                 if selected_option == "LOCAL":
                     self.start_game('LOCAL')
                 elif selected_option == "VS COMPUTER":
                     self.start_game('VS_COMPUTER')
                 # If dropdown handled the click (even just opening/closing),
                 # we might want to prevent other buttons below from processing the SAME click event.
                 return # Prevent processing other buttons

        # If dropdown didn't handle the click, process regular buttons
        if not dropdown_handled_click:
            for button in self.menu_buttons:
                # Ensure START GAME button doesn't re-trigger dropdown if it was just closed
                if button.text == "START GAME" and event.type == pygame.MOUSEBUTTONDOWN and button.rect.collidepoint(event.pos):
                    # The button's own action handles the toggle now, so we might just need to pass
                    # or ensure the button.handle_event call happens correctly below.
                    pass # Let the button handle its action

                if button.handle_event(event):
                     # If a button handled the event (and wasn't the dropdown interaction), break.
                     break


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
            clicked_coord = (clicked_q, clicked_r) # Store coordinate tuple

            # Check if the click is on a valid hex on the board
            if clicked_coord not in self.board.hex_coords:
                self.selected_piece = None # Clicked outside board
                self.selected_piece_coord = None
                self.possible_moves = []
                return

            clicked_piece = self.board.get_piece(clicked_q, clicked_r)

            # --- Selecting a piece ---
            if clicked_piece and clicked_piece.color == self.current_turn:
                # *** FIX START ***
                # Check if this piece has any moves listed (it might not if it's blocked)
                # Also check if this piece is allowed to be selected (due to forced jumps)
                if clicked_coord not in self.all_player_moves:
                    if self.must_jump:
                         print("Must move a piece that can jump!") # User feedback
                    else:
                         print("This piece has no valid moves.") # User feedback
                    self.selected_piece = None # Cannot select this piece
                    self.selected_piece_coord = None
                    self.possible_moves = []
                else:
                    # Piece clicked has moves listed, proceed with selection
                    self.selected_piece = clicked_piece
                    self.selected_piece_coord = clicked_coord
                    current_piece_moves = self.all_player_moves[clicked_coord] # Safe to access now

                    # Show only jumps if must_jump, otherwise show all moves for this piece
                    if self.must_jump:
                         # If must_jump is True, all_player_moves only contains jumping pieces/moves
                         self.possible_moves = [jump[:2] for jump in current_piece_moves.get('jumps', [])]
                    else:
                         # If not must_jump, combine moves and jumps
                         moves = current_piece_moves.get('moves', [])
                         jumps = [jump[:2] for jump in current_piece_moves.get('jumps', [])]
                         self.possible_moves = moves + jumps
                    # print(f"Selected piece at {self.selected_piece_coord}. Possible moves: {self.possible_moves}") # Debug
                # *** FIX END ***

            # --- Making a move ---
            elif self.selected_piece and clicked_coord in self.possible_moves:
                 # Check validity (should be intrinsically valid if in possible_moves)
                 is_valid, jumped_coord = self.logic.is_move_valid(self.selected_piece, clicked_q, clicked_r, self.all_player_moves, self.must_jump)

                 if is_valid:
                      self.execute_move(self.selected_piece_coord, clicked_coord, jumped_coord)
                 else:
                      # This case suggests an internal logic inconsistency if reached
                      print("Error: Move selected from possible_moves was deemed invalid.")
                      self.selected_piece = None
                      self.selected_piece_coord = None
                      self.possible_moves = []

            # --- Clicking elsewhere (empty square or opponent piece) ---
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
        if self.winner: # If game already ended (checked previously)
             self.change_state(STATE_GAME_OVER)
             return

        was_animating = self.is_animating_move # Store previous state
        board_animating = False
        capture_animating = False
        just_finished_animating = False
        self.is_animating_move = board_animating or capture_animating
        just_finished_animating = was_animating and not self.is_animating_move

        # Update animations (sliding, captured)
        if self.board:
            board_animating = self.board.update_piece_animations(dt)
            capture_animating = False
            for player_list in self.captured_pieces.values():
                 for piece in player_list:
                     if piece.is_captured and piece.capture_target_pos: # Only update if target exists
                         if piece.update_animation(dt):
                              capture_animating = True
            self.is_animating_move = board_animating or capture_animating
            # FIX: Check if animation JUST finished
            just_finished_animating = was_animating and not self.is_animating_move

        # If an animation is playing, wait for it to finish
        if self.is_animating_move:
            return

        # FIX: If animation just finished, NOW check for game over and switch turn
        if just_finished_animating:
             # FIX: Check the multi-jump flag
             if not self.is_multi_jumping:
                 print("Animation finished (NOT multi-jump), checking game over and switching turn...") # Debug
                 winner = self.logic.check_game_over(self.current_turn)
                 if winner:
                     self.winner = winner
                     self.change_state(STATE_GAME_OVER)
                 else:
                     self.switch_turn()
                 # Since turn logic might switch, return to process next frame cleanly
                 return
             else:
                 # Animation finished, but we are mid-multi-jump.
                 # If it's the AI's turn, it needs to act NOW.
                 # If it's the Human's turn, just wait for input.
                 if self.current_turn == COMPUTER:
                     # AI needs to calculate next jump immediately
                     print("AI Mid-Multi-Jump: Calculating next jump...") # Debug
                     next_jump = self.ai_player.find_next_multi_jump(self.selected_piece) # <-- Need new AI method
                     if next_jump:
                         start_q, start_r, end_q, end_r = next_jump
                         # Find the jumped coord for this specific jump segment
                         _, jumped_coord = self.logic.is_move_valid(self.selected_piece, end_q, end_r, self.all_player_moves, self.must_jump)
                         self.execute_move((start_q, start_r), (end_q, end_r), jumped_coord)
                         # execute_move will handle setting is_multi_jumping if further jumps exist
                     else:
                         # AI couldn't find another jump? This shouldn't happen if logic is right.
                         # End the multi-jump sequence and switch turn.
                         print("AI Multi-Jump Error: No next jump found. Ending turn.")
                         self.is_multi_jumping = False
                         self.switch_turn()
                     return # Prevent normal AI turn logic below

        # --- Normal AI Turn Logic (Only run if not animating, not just finished anim, AND not AI multi-jump) ---
        if self.game_mode == 'VS_COMPUTER' and self.current_turn == COMPUTER and not self.winner and not self.is_multi_jumping:
            if not self.ai_player.is_thinking:
                print("AI Starting Turn Thinking...") # Debug
                # Pass the *current* potential moves to the AI when it starts thinking
                current_moves, current_must_jump = self.logic.get_all_player_moves(self.current_turn)
                self.ai_player.start_thinking(current_moves, current_must_jump) # Pass available moves

            ai_move = self.ai_player.get_move()
            if ai_move:
                print(f"AI executing move: {ai_move}") # Debug
                start_q, start_r, end_q, end_r = ai_move
                ai_piece = self.board.get_piece(start_q, start_r)
                if ai_piece:
                    # Need to recalculate the specific valid moves *for the AI's chosen piece* right before the move
                    # This is because all_player_moves might be stale if the board changed during AI thinking? Unlikely here.
                    # Re-check validity just in case
                    is_valid, jumped_coord = self.logic.is_move_valid(ai_piece, end_q, end_r, self.all_player_moves, self.must_jump)
                    if is_valid:
                         self.execute_move((start_q, start_r), (end_q, end_r), jumped_coord)
                         # NOTE: execute_move now sets is_multi_jumping flag if applicable
                         # If it became true here, the next frame's update_playing will handle it above.
                    else:
                         print(f"AI Error: AI generated invalid move! {ai_move} from {self.all_player_moves}") # Debug invalid move
                         # Attempt to recover: recalculate moves and let AI try again next frame? Or just switch?
                         self.switch_turn() # Simple error handling: skip turn
                else:
                     print("AI Error: AI chose non-existent piece!")
                     self.switch_turn() # Skip turn

        # No updates needed for local player's turn other than animation & event handling


    # --- Core Game Actions ---

    def execute_move(self, start_coord, end_coord, jumped_coord):
        """Executes the move, handles captures, checks promotion & game over AFTER animations."""
        print(f"Executing move: {start_coord} -> {end_coord}") # Debug
        moved_piece = self.board.move_piece(start_coord[0], start_coord[1], end_coord[0], end_coord[1])

        if not moved_piece:
            print("Error: Failed to move piece logically.")
            return # Should not happen

        self.is_animating_move = True # Start animation flag immediately

        captured_piece = None
        if jumped_coord:
            captured_piece = self.board.remove_piece(jumped_coord[0], jumped_coord[1])
            if captured_piece:
                print(f"Captured piece at {jumped_coord}")
                self.add_captured_piece(captured_piece) # This triggers capture animation

        # --- Promotion and Multi-Jump Checks (These don't depend on animation visually) ---
        promoted = self.logic.check_for_promotion(moved_piece)

        self.is_multi_jumping = False

        can_multi_jump = False
        if jumped_coord and not promoted:
             piece_jumps = self.logic.get_valid_moves(moved_piece)['jumps']
             if piece_jumps:
                  can_multi_jump = True
                  self.is_multi_jumping = True
                  print("Multi-jump available!")
                  self.all_player_moves = {end_coord: {'moves': [], 'jumps': piece_jumps}}
                  self.must_jump = True
                  self.selected_piece = moved_piece
                  self.selected_piece_coord = end_coord
                  self.possible_moves = [jump[:2] for jump in piece_jumps]
                  # Do NOT switch turn or check game over yet
                  # The animation flag (is_animating_move) is already set,
                  # the game loop will handle waiting.
                  return

        # --- Defer Game Over Check and Turn Switch ---
        # If no multi-jump, clear selection, but DO NOT check game over or switch turn yet.
        # This will happen in update_playing AFTER animations complete.
        self.selected_piece = None
        self.selected_piece_coord = None
        self.possible_moves = []

        # The actual check_game_over and switch_turn will now happen in update_playing


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
        """Adds captured piece to list and sets target pos, stacking in 3 columns of 6."""
        MAX_PER_COLUMN = 6
        NUM_COLUMNS = 3

        # Determine Margins and Spacing
        piece_diameter = int(piece.radius * 2)
        vertical_spacing = int(piece_diameter * 1.2)  # Space between stacked pieces vertically
        horizontal_spacing = int(piece_diameter * 1.3) # Space between columns horizontally
        side_margin = int(piece.radius * 3)            # Distance from screen edge for first column

        target_x = 0
        target_y = 0

        capturing_player = PLAYER2 if piece.color == PLAYER1 else PLAYER1

        if capturing_player == PLAYER1:
            # P1 captured a P2 piece -> Display on LEFT side
            num_captured = len(self.captured_pieces[PLAYER1])
            column_index = num_captured // MAX_PER_COLUMN  # 0, 1, or 2
            position_in_column = num_captured % MAX_PER_COLUMN # 0 to 5

            # Ensure we don't exceed NUM_COLUMNS (though 16 captures max means index 2 is highest)
            if column_index >= NUM_COLUMNS:
                column_index = NUM_COLUMNS - 1
                # Optional: stack further pieces in the last column beyond MAX_PER_COLUMN
                # position_in_column = MAX_PER_COLUMN + (num_captured - NUM_COLUMNS * MAX_PER_COLUMN) -1 ?
                # Simpler: Just stack in the last column beyond 6 if needed.
                position_in_column = num_captured - (column_index * MAX_PER_COLUMN)


            # Calculate X: Starts at margin, adds spacing for subsequent columns
            target_x = side_margin + (column_index * horizontal_spacing)
            # Calculate Y: Starts at margin, adds spacing for position in column
            target_y = side_margin + (position_in_column * vertical_spacing)

            piece.capture_target_pos = (target_x, target_y)
            self.captured_pieces[PLAYER1].append(piece)

        else: # Captured by P2 or Computer
            # P2 captured a P1 piece -> Display on RIGHT side
            num_captured = len(self.captured_pieces[PLAYER2])
            column_index = num_captured // MAX_PER_COLUMN # 0, 1, or 2
            position_in_column = num_captured % MAX_PER_COLUMN # 0 to 5

            if column_index >= NUM_COLUMNS:
                 column_index = NUM_COLUMNS - 1
                 position_in_column = num_captured - (column_index * MAX_PER_COLUMN)


            # Calculate X: Starts from right edge margin, subtracts spacing for subsequent columns
            # Make sure columns move inwards (closer to board)
            target_x = (self.screen_width - side_margin) - (column_index * horizontal_spacing)
            # Calculate Y: Starts at margin, adds spacing for position in column
            target_y = side_margin + (position_in_column * vertical_spacing)

            piece.capture_target_pos = (target_x, target_y)
            self.captured_pieces[PLAYER2].append(piece)

        piece.is_captured = True
        self.is_animating_move = True


    # --- State-Specific Drawing ---

    def draw_menu(self):
        # Title
        draw_text(self.screen, "HEXDAME", 64, self.screen_width // 2, 100, self.theme["text"], center=True)

        # Buttons
        for button in self.menu_buttons:
            button.draw(self.screen, self.theme)

        # Dropdown (drawn on top ONLY if open)
        # FIX: Add explicit check for is_open before drawing
        if self.start_game_dropdown.is_open:
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