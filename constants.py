import pygame

# Screen dimensions (set dynamically to fullscreen initially)
SCREEN_WIDTH = 0
SCREEN_HEIGHT = 0

# Board parameters
HEX_RADIUS = 30 # Initial radius, will be adjusted based on screen size
BOARD_SIDE_LENGTH = 5 # Number of hexes along each edge from the center (total diameter 2*N-1)

# Colors (Themes) - Define more themes as needed
# Ensure text contrasts with button backgrounds, pieces contrast with board tiles
THEMES = {
    "Light": {
        "board_light": (230, 210, 180), # Light wood/beige
        "board_dark": (180, 130, 100), # Darker wood/brown
        "player1_piece": (240, 240, 240), # White
        "player1_king": (255, 255, 200), # Pale Yellow
        "player2_piece": (30, 30, 30), # Black
        "player2_king": (80, 80, 80), # Dark Grey
        "highlight_valid": (100, 200, 100, 180), # Semi-transparent Green
        "highlight_selected": (255, 255, 0, 150), # Semi-transparent Yellow
        "capture_bg": (200, 200, 200),
        "text": (10, 10, 10),
        "button_bg": (200, 180, 160),
        "button_hover_bg": (220, 200, 180),
        "button_text": (10, 10, 10),
        "menu_bg": (210, 190, 170),
        "info_popup_bg": (240, 220, 200),
        "info_popup_text": (10, 10, 10),
    },
    "Dark": {
        "board_light": (80, 80, 80), # Dark Grey
        "board_dark": (40, 40, 40), # Very Dark Grey
        "player1_piece": (200, 50, 50), # Red
        "player1_king": (255, 100, 100), # Lighter Red
        "player2_piece": (50, 50, 200), # Blue
        "player2_king": (100, 100, 255), # Lighter Blue
        "highlight_valid": (100, 200, 100, 180), # Semi-transparent Green
        "highlight_selected": (200, 200, 50, 150), # Semi-transparent Yellow
        "capture_bg": (60, 60, 60),
        "text": (240, 240, 240),
        "button_bg": (70, 70, 70),
        "button_hover_bg": (90, 90, 90),
        "button_text": (240, 240, 240),
        "menu_bg": (50, 50, 50),
        "info_popup_bg": (60, 60, 60),
        "info_popup_text": (240, 240, 240),
    },
    # Add "Light Wood", "Dark Wood" themes here...
}
DEFAULT_THEME = "Light"

# Player Identifiers
PLAYER1 = 1
PLAYER2 = 2
COMPUTER = 2 # Computer plays as Player 2

# Game States
STATE_MENU = "MENU"
STATE_PLAYING = "PLAYING"
STATE_OPTIONS = "OPTIONS"
STATE_INFO = "INFO"
STATE_QUIT_ANIMATION = "QUIT_ANIMATION"
STATE_GAME_OVER = "GAME_OVER"
STATE_BOARD_SETUP_ANIM = "BOARD_SETUP_ANIM"
STATE_PIECE_SETUP_ANIM = "PIECE_SETUP_ANIM"

# AI Difficulty / Delay
AI_DELAY_MS = 750 # Milliseconds delay for AI move

try: # loading a specific font if directory exists
    UI_FONT_PATH = './fonts/PressStart2P-Regular.ttf'
    pygame.font.init() # Initialize font module explicitly
    # Test if font can be loaded
    _ = pygame.font.Font(UI_FONT_PATH, 10)
except (pygame.error, FileNotFoundError):
    print(f"Warning: Font '{UI_FONT_PATH}' not found or invalid. Falling back to monospace.")
    UI_FONT_PATH = pygame.font.match_font('monospace') # Fallback using a common monospace font as a placeholder

# Animation Speeds
FALL_SPEED_TILE = 50 # Pixels per frame (adjust for desired speed)
FALL_SPEED_PIECE = 40 # Pixels per frame
SLIDE_SPEED = 15 # Pixels per frame

# --- Axial Coordinates Directions ---
# Flat-top hex grid directions
#       (+0,-1) (-1,-1)
# (+1, 0) (0,0) (-1, 0)
#       (+1,+1) (+0,+1)
# Axial directions (q, r) corresponding to potential moves
DIRECTIONS = [
    (1, 0), (1, -1), (0, -1), # Player 1 Forward Right, Forward Up-Right, Forward Up-Left
    (-1, 0), (-1, 1), (0, 1)  # Player 1 Backward Left, Backward Down-Left, Backward Down-Right
]
# Directions for standard pieces (relative to player)
# P1 moves towards negative r, P2 moves towards positive r typically
# Let's define directions more explicitly for moves/jumps
# (dq, dr)
MOVE_DIRECTIONS = {
    PLAYER1: [(0, -1), (1, -1), (-1, 0)], # Up-Left, Up-Right, Left (adjust based on your desired 'forward')
    PLAYER2: [(0, 1), (-1, 1), (1, 0)]   # Down-Right, Down-Left, Right (adjust based on desired 'forward')
}
# Directions for King moves (all 6)
KING_DIRECTIONS = DIRECTIONS