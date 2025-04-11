import pygame
import math
from constants import *

# --- Hex Grid Math (Axial Coordinates, Flat-Top) ---

def hex_to_pixel(q, r, radius, center_x, center_y):
    """Converts axial hex coordinates to pixel coordinates."""
    x = radius * (3./2 * q)
    y = radius * (math.sqrt(3)/2 * q + math.sqrt(3) * r)
    return int(center_x + x), int(center_y + y)

def pixel_to_hex(x, y, radius, center_x, center_y):
    """Converts pixel coordinates to approximate axial hex coordinates."""
    px = (x - center_x)
    py = (y - center_y)
    q = (2./3 * px) / radius
    r = (-1./3 * px + math.sqrt(3)/3 * py) / radius
    return _hex_round(q, r)

def _hex_round(q, r):
    """Rounds fractional hex coordinates to the nearest integer hex coordinates. SUPPLEMENTARY FUNCTION."""
    s = -q - r
    rq = round(q)
    rr = round(r)
    rs = round(s)

    q_diff = abs(rq - q)
    r_diff = abs(rr - r)
    s_diff = abs(rs - s)

    if q_diff > r_diff and q_diff > s_diff:
        rq = -rr - rs
    elif r_diff > s_diff:
        rr = -rq - rs
    # else: rs = -rq - rr # This line isn't needed as s is derived

    return int(rq), int(rr)

def get_hex_corners(q, r, radius, center_x, center_y):
    """Gets the pixel coordinates of the 6 corners of a hex."""
    center = hex_to_pixel(q, r, radius, center_x, center_y)
    corners = []
    for i in range(6):
        angle_deg = 60 * i
        angle_rad = math.pi / 180 * angle_deg
        corners.append(
            (center[0] + radius * math.cos(angle_rad),
             center[1] + radius * math.sin(angle_rad))
        )
    return corners

def hex_distance(q1, r1, q2, r2):
    """Calculates the distance between two hexes in grid units."""
    return (abs(q1 - q2) + abs(q1 + r1 - q2 - r2) + abs(r1 - r2)) // 2

# --- Text Rendering ---
def draw_text(surface, text, size, x, y, color, font_path=UI_FONT_PATH, center=False, screen_width=None):
    """Draws text on the surface."""
    try:
        font = pygame.font.Font(font_path, size)
    except pygame.error: # Fallback if specific font fails during rendering
        font = pygame.font.Font(pygame.font.match_font('monospace'), size)

    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center:
        if screen_width: # Center horizontally on screen
             text_rect.centerx = screen_width // 2
             text_rect.top = y
        else: # Center at given x, y
             text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_surface, text_rect)
    return text_rect

# --- Contrast Check (Basic Implementation) ---
def check_contrast(color1, color2, threshold=128):
    """Basic contrast check based on luminance difference."""
    def luminance(r, g, b):
        return 0.299 * r + 0.587 * g + 0.114 * b

    lum1 = luminance(*color1[:3]) # Ignore alpha if present
    lum2 = luminance(*color2[:3])
    return abs(lum1 - lum2) >= threshold