import pygame
import random

title = "winter.wav"

print(f"Song Title: {title}")

# Define keyword-to-color mapping
color_mapping = {
    'blue': [(0, 0, 128), (0, 0, 255)], # Navy to Blue
    'sad': [(0, 0, 128), (0, 0, 255)],  # Similar to "blue"
    'winter': [(0, 0, 128), (0, 0, 255)],  # Similar to "blue"
    'happy': [(255, 223, 0), (255, 255, 0)], # Gold to Yellow
    'love': [(255, 20, 147), (255, 105, 180)], # DeepPink to HotPink
    'red': [(128, 0, 0), (255, 0, 0)], # Maroon to Red
    'green': [(0, 128, 0), (0, 255, 0)], # Green to Lime
    'daydreams': [(255, 0, 255), (75, 0, 130)], # Magenta to Indigo
    # Add more mappings as needed
}

def get_color_scheme(title, color_mapping):
    # Convert title to lowercase to match case-insensitively
    title_lower = title.lower()

    # Find the first matching keyword
    for keyword, colors in color_mapping.items():
        if keyword in title_lower:
            return colors
    
    # Default color scheme if no keywords match
    return [(255, 255, 255), (192, 192, 192)]  # White to Light Gray

# Example title
title = "winter.wav"

# Get the color scheme based on the title
colors = get_color_scheme(title, color_mapping)
print(f"Color Scheme for '{title}': {colors}")

# Initialize Pygame
pygame.init()

# Set up the display
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Music Visualizer")

# Get color scheme for the song title
title = "winter"
colors = get_color_scheme(title, color_mapping)

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Fill the screen with the background color (interpolated)
    color_index = random.randint(0, len(colors) - 1)
    screen.fill(colors[color_index])

    # Example visualization: random circles
    for _ in range(50):
        color = random.choice(colors)
        radius = random.randint(5, 30)
        position = (random.randint(0, 800), random.randint(0, 600))
        pygame.draw.circle(screen, color, position, radius)

    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()
