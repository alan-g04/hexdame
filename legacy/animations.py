import pygame
import random
from constants import *

class QuitAnimator:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.stage = 0 # 0: Shrink, 1: Static, 2: Off
        self.start_time = pygame.time.get_ticks()
        self.shrink_duration = 600 # ms
        self.static_duration = 400 # ms
        self.current_width = screen_width
        self.current_height = screen_height
        self.static_surface = pygame.Surface((screen_width, screen_height))

    def update(self):
        """Updates the animation stage. Returns True if animation is ongoing."""
        now = pygame.time.get_ticks()
        elapsed = now - self.start_time

        if self.stage == 0: # Shrinking
            if elapsed < self.shrink_duration:
                progress = elapsed / self.shrink_duration
                # Shrink horizontally first, then vertically to a point
                self.current_width = self.screen_width * (1 - progress)
                self.current_height = self.screen_height # Keep height initially
                if self.current_width < 10: # Once thin, shrink height
                    self.current_width = 1 # Keep a single pixel line
                    height_progress = (elapsed - self.shrink_duration * 0.8) / (self.shrink_duration * 0.2) # Shrink height in last 20%
                    height_progress = max(0, min(1, height_progress)) # Clamp
                    self.current_height = self.screen_height * (1-height_progress)

                return True
            else:
                self.stage = 1 # Move to static
                self.current_width = 1
                self.current_height = 1
                self.start_time = now # Reset timer for next stage
                self._generate_static()
                return True

        elif self.stage == 1: # Static burst
            if elapsed < self.static_duration:
                 if random.randint(0, 2) == 0: # Generate new static occasionally
                    self._generate_static()
                 return True
            else:
                 self.stage = 2 # Turn off
                 return False # Animation finished

        return False # Stage 2 or unknown

    def _generate_static(self):
        """Fills the static surface with random noise."""
        self.static_surface.fill((0, 0, 0))
        for _ in range(int(self.screen_width * self.screen_height * 0.3)): # 30% density noise
            x = random.randint(0, self.screen_width - 1)
            y = random.randint(0, self.screen_height - 1)
            color_val = random.randint(50, 200)
            self.static_surface.set_at((x, y), (color_val, color_val, color_val))


    def draw(self, screen, last_frame_surface):
        """Draws the current animation effect."""
        screen.fill((0, 0, 0)) # Black background

        if self.stage == 0: # Shrinking
            # Scale the last captured frame
            if last_frame_surface and self.current_width > 0 and self.current_height > 0:
                try:
                    shrunk_frame = pygame.transform.scale(last_frame_surface, (int(self.current_width), int(self.current_height)))
                    # Center the shrunk frame
                    x_pos = (self.screen_width - self.current_width) // 2
                    y_pos = (self.screen_height - self.current_height) // 2
                    screen.blit(shrunk_frame, (x_pos, y_pos))
                except (ValueError, pygame.error): # Handle potential errors if width/height become invalid
                     pass # Just draw black screen

        elif self.stage == 1: # Static
            screen.blit(self.static_surface, (0, 0))