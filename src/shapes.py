"""Pixel art shape templates for AI agents to draw."""

from __future__ import annotations

from typing import Optional

# Shape templates using ASCII art
# 'X' represents a filled pixel, '.' represents empty
# Each shape is designed to be ~8-12 pixels wide/tall

SHAPE_TEMPLATES = {
    "heart": [
        ".XX...XX.",
        "XXXXXXXXX",
        "XXXXXXXXX",
        "XXXXXXXXX",
        ".XXXXXXX.",
        "..XXXXX..",
        "...XXX...",
        "....X....",
    ],
    "star": [
        "....X....",
        "....X....",
        "...XXX...",
        "XXXXXXXXX",
        ".XXXXXXX.",
        "..XXXXX..",
        ".XXX.XXX.",
        "XX.....XX",
    ],
    "smiley": [
        "..XXXXX..",
        ".X.....X.",
        "X..X.X..X",
        "X.......X",
        "X.X...X.X",
        "X..XXX..X",
        ".X.....X.",
        "..XXXXX..",
    ],
    "diamond": [
        "....X....",
        "...XXX...",
        "..XXXXX..",
        ".XXXXXXX.",
        "..XXXXX..",
        "...XXX...",
        "....X....",
    ],
    "lightning": [
        "....XXX..",
        "...XXX...",
        "..XXX....",
        ".XXXXXXX.",
        "....XXX..",
        "...XXX...",
        "..XXX....",
        ".XXX.....",
    ],
    "moon": [
        "..XXXX...",
        ".XX..XX..",
        "XX....X..",
        "X.....X..",
        "X.....X..",
        "XX....X..",
        ".XX..XX..",
        "..XXXX...",
    ],
    "house": [
        "....X....",
        "...XXX...",
        "..XXXXX..",
        ".XXXXXXX.",
        ".XX.X.XX.",
        ".XX.X.XX.",
        ".XX...XX.",
        ".XXXXXXX.",
    ],
    "tree": [
        "....X....",
        "...XXX...",
        "..XXXXX..",
        ".XXXXXXX.",
        "..XXXXX..",
        "...XXX...",
        "....X....",
        "....X....",
    ],
}

# List of available shape names
SHAPE_NAMES = list(SHAPE_TEMPLATES.keys())


def get_shape_template(shape_name: str) -> list[str]:
    """Get the ASCII template for a shape."""
    return SHAPE_TEMPLATES.get(shape_name, SHAPE_TEMPLATES["heart"])


def get_shape_dimensions(shape_name: str) -> tuple[int, int]:
    """Get the width and height of a shape."""
    template = get_shape_template(shape_name)
    if not template:
        return (0, 0)
    height = len(template)
    width = max(len(row) for row in template)
    return (width, height)


def get_shape_pixel_count(shape_name: str) -> int:
    """Get the total number of pixels in a shape."""
    template = get_shape_template(shape_name)
    count = 0
    for row in template:
        count += row.count('X')
    return count


def get_shape_pixels(
    shape_name: str,
    color: str,
    offset_x: int = 0,
    offset_y: int = 0,
) -> list[tuple[int, int, str]]:
    """
    Get list of (x, y, color) tuples for a shape at a given position.
    
    Args:
        shape_name: Name of the shape
        color: Color to use for the pixels
        offset_x: X offset for the shape position
        offset_y: Y offset for the shape position
    
    Returns:
        List of (x, y, color) tuples representing each pixel
    """
    template = get_shape_template(shape_name)
    pixels = []
    
    for y, row in enumerate(template):
        for x, char in enumerate(row):
            if char == 'X':
                pixels.append((offset_x + x, offset_y + y, color))
    
    return pixels


def get_shape_pixel_coords(
    shape_name: str,
    offset_x: int = 0,
    offset_y: int = 0,
) -> list[tuple[int, int]]:
    """
    Get list of (x, y) coordinates for a shape at a given position.
    
    Args:
        shape_name: Name of the shape
        offset_x: X offset for the shape position
        offset_y: Y offset for the shape position
    
    Returns:
        List of (x, y) tuples representing each pixel coordinate
    """
    template = get_shape_template(shape_name)
    coords = []
    
    for y, row in enumerate(template):
        for x, char in enumerate(row):
            if char == 'X':
                coords.append((offset_x + x, offset_y + y))
    
    return coords


def shape_to_ascii(shape_name: str, fill_char: str = "X", empty_char: str = ".") -> str:
    """
    Convert a shape template to ASCII art string.
    
    Args:
        shape_name: Name of the shape
        fill_char: Character to use for filled pixels
        empty_char: Character to use for empty pixels
    
    Returns:
        ASCII art string representation
    """
    template = get_shape_template(shape_name)
    lines = []
    for row in template:
        line = row.replace("X", fill_char).replace(".", empty_char)
        lines.append(line)
    return "\n".join(lines)


def get_shape_bounds(
    shape_name: str,
    offset_x: int = 0,
    offset_y: int = 0,
) -> tuple[int, int, int, int]:
    """
    Get bounding box for a shape at a given position.
    
    Returns:
        (min_x, min_y, max_x, max_y)
    """
    width, height = get_shape_dimensions(shape_name)
    return (offset_x, offset_y, offset_x + width - 1, offset_y + height - 1)


def calculate_shape_positions(
    num_agents: int,
    grid_width: int,
    grid_height: int,
    shapes: list[str],
) -> list[tuple[int, int]]:
    """
    Calculate spread-out positions for multiple shapes on a grid.
    
    Tries to place shapes in different quadrants/areas to avoid
    immediate overlap at the start.
    
    Args:
        num_agents: Number of agents/shapes
        grid_width: Width of the grid
        grid_height: Height of the grid
        shapes: List of shape names
    
    Returns:
        List of (x, y) starting positions for each shape
    """
    positions = []
    
    if num_agents == 1:
        # Center the single shape
        shape_w, shape_h = get_shape_dimensions(shapes[0])
        x = (grid_width - shape_w) // 2
        y = (grid_height - shape_h) // 2
        positions.append((x, y))
    
    elif num_agents == 2:
        # Left and right halves
        for i, shape in enumerate(shapes[:2]):
            shape_w, shape_h = get_shape_dimensions(shape)
            if i == 0:
                x = grid_width // 4 - shape_w // 2
            else:
                x = 3 * grid_width // 4 - shape_w // 2
            y = (grid_height - shape_h) // 2
            positions.append((x, y))
    
    elif num_agents <= 4:
        # Quadrants
        quadrants = [
            (grid_width // 4, grid_height // 4),           # Top-left
            (3 * grid_width // 4, grid_height // 4),       # Top-right
            (grid_width // 4, 3 * grid_height // 4),       # Bottom-left
            (3 * grid_width // 4, 3 * grid_height // 4),   # Bottom-right
        ]
        for i, shape in enumerate(shapes[:4]):
            shape_w, shape_h = get_shape_dimensions(shape)
            center_x, center_y = quadrants[i]
            x = center_x - shape_w // 2
            y = center_y - shape_h // 2
            positions.append((x, y))
    
    else:
        # Grid layout for more agents
        cols = int(num_agents ** 0.5) + 1
        rows = (num_agents + cols - 1) // cols
        cell_w = grid_width // cols
        cell_h = grid_height // rows
        
        for i, shape in enumerate(shapes):
            shape_w, shape_h = get_shape_dimensions(shape)
            col = i % cols
            row = i // cols
            center_x = col * cell_w + cell_w // 2
            center_y = row * cell_h + cell_h // 2
            x = center_x - shape_w // 2
            y = center_y - shape_h // 2
            positions.append((x, y))
    
    return positions


def get_random_shape() -> str:
    """Get a random shape name."""
    import random
    return random.choice(SHAPE_NAMES)


def get_shapes_for_agents(num_agents: int) -> list[str]:
    """
    Get a list of shape names for a given number of agents.
    
    Ensures each agent gets a different shape (if possible).
    """
    if num_agents <= len(SHAPE_NAMES):
        return SHAPE_NAMES[:num_agents]
    else:
        # Repeat shapes if we have more agents than shapes
        shapes = []
        for i in range(num_agents):
            shapes.append(SHAPE_NAMES[i % len(SHAPE_NAMES)])
        return shapes
