import pygame
from constants import *
from utils import draw_text

class Button:
    def __init__(self, x, y, width, height, text, text_size, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.text_size = text_size
        self.action = action # Function to call when clicked
        self.is_hovered = False

    def draw(self, surface, theme):
        bg_color = theme["button_hover_bg"] if self.is_hovered else theme["button_bg"]
        text_color = theme["button_text"]
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=5)
        pygame.draw.rect(surface, text_color, self.rect, width=2, border_radius=5) # Outline

        draw_text(surface, self.text, self.text_size, self.rect.centerx, self.rect.centery, text_color, center=True)

    def handle_event(self, event):
        """Checks for hover and click events."""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered and event.button == 1: # Left click
                if self.action:
                    self.action() # Execute the button's action
                return True # Indicate button was clicked
        return False

# --- Basic Dropdown --- (More complex UI elements need more code)
class Dropdown:
     def __init__(self, x, y, width, height, options, text_size):
         self.rect = pygame.Rect(x, y, width, height)
         self.options = options
         self.text_size = text_size
         self.is_open = False
         self.selected_option = options[0] if options else None
         self.option_rects = []

     def draw(self, surface, theme):
         # Draw main box
         bg_color = theme["button_bg"]
         text_color = theme["button_text"]
         pygame.draw.rect(surface, bg_color, self.rect, border_radius=3)
         pygame.draw.rect(surface, text_color, self.rect, width=1, border_radius=3)
         draw_text(surface, self.selected_option, self.text_size, self.rect.centerx, self.rect.centery, text_color, center=True)
         # Draw arrow indicator
         pygame.draw.polygon(surface, text_color, [(self.rect.right - 15, self.rect.centery - 3),
                                                   (self.rect.right - 5, self.rect.centery - 3),
                                                   (self.rect.right - 10, self.rect.centery + 5)])

         # Draw options if open
         if self.is_open:
             self.option_rects = []
             opt_y = self.rect.bottom + 2
             for i, option in enumerate(self.options):
                 opt_rect = pygame.Rect(self.rect.x, opt_y + i * self.rect.height, self.rect.width, self.rect.height)
                 self.option_rects.append((option, opt_rect))
                 pygame.draw.rect(surface, theme["button_hover_bg"], opt_rect, border_radius=3) # Highlight background
                 pygame.draw.rect(surface, text_color, opt_rect, width=1, border_radius=3)
                 draw_text(surface, option, self.text_size, opt_rect.centerx, opt_rect.centery, text_color, center=True)


     def handle_event(self, event):
        """Handles opening, closing, and selecting options."""
        clicked_handled = False
        option_selected = None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                clicked_handled = True # Handled the click to toggle
            elif self.is_open:
                handled_option_click = False
                for option, opt_rect in self.option_rects:
                    if opt_rect.collidepoint(event.pos):
                        self.selected_option = option
                        self.is_open = False
                        option_selected = option # Store selected option
                        handled_option_click = True
                        clicked_handled = True # Handled the click on an option
                        break # Exit loop once option is found
                if not handled_option_click:
                    # Clicked outside the dropdown while it was open, so close it
                    self.is_open = False
                    # Important: DO NOT set clicked_handled = True here
                    # Let the main event loop potentially handle this click elsewhere (e.g., deselecting things)
            # else: click was outside closed dropdown, do nothing here

        # Return True if the dropdown *processed* the click (toggle, select, close by outside click)
        # Return selected option if one was clicked this frame
        return clicked_handled, option_selected

# --- Basic Radio Button Group ---
class RadioButtonGroup:
    def __init__(self, x, y, options, text_size, initial_selection=None):
        self.x = x
        self.y = y
        self.options = options # List of strings
        self.text_size = text_size
        self.selected_option = initial_selection if initial_selection in options else options[0]
        self.radio_rects = {} # option_text -> rect

    def draw(self, surface, theme):
        text_color = theme["text"]
        radio_outer_color = theme["button_text"]
        radio_inner_color = theme["highlight_selected"][:3] # Use highlight color without alpha
        radius = self.text_size // 2
        spacing = self.text_size * 2.5 # Vertical spacing

        current_y = self.y
        self.radio_rects.clear()

        for option in self.options:
            # Draw radio circle
            radio_center_y = current_y + radius
            pygame.draw.circle(surface, radio_outer_color, (self.x + radius, radio_center_y), radius, 1)

            # Draw selected indicator
            if option == self.selected_option:
                pygame.draw.circle(surface, radio_inner_color, (self.x + radius, radio_center_y), radius - 3)

            # Draw text label
            text_rect = draw_text(surface, option, self.text_size, self.x + radius * 2 + 5, current_y, text_color)

            # Store clickable area (circle + text)
            clickable_rect = pygame.Rect(self.x, current_y, text_rect.right - self.x, self.text_size * 1.5)
            self.radio_rects[option] = clickable_rect

            current_y += spacing

    def handle_event(self, event):
        """Handles selecting an option."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for option, rect in self.radio_rects.items():
                if rect.collidepoint(event.pos):
                    if self.selected_option != option:
                         self.selected_option = option
                         return True # Selection changed
        return False # No change