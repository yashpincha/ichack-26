"""Grid system for AI r/place simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Any
from collections import defaultdict
import copy


# Color palette for the grid
COLORS = ["red", "blue", "green", "yellow", "purple", "orange", "cyan", "pink"]

# ASCII representation of colors (first letter, uppercase for visibility)
COLOR_ASCII = {
    "red": "R",
    "blue": "B",
    "green": "G",
    "yellow": "Y",
    "purple": "P",
    "orange": "O",
    "cyan": "C",
    "pink": "K",
    "empty": ".",
}

# ANSI color codes for terminal display
COLOR_ANSI = {
    "red": "\033[91m",
    "blue": "\033[94m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "purple": "\033[95m",
    "orange": "\033[33m",
    "cyan": "\033[96m",
    "pink": "\033[95m",
    "empty": "\033[90m",
    "reset": "\033[0m",
}


@dataclass
class Pixel:
    """A single pixel on the grid."""
    color: str = "empty"
    owner_id: Optional[str] = None
    placed_at_turn: int = 0
    
    def to_dict(self) -> dict:
        return {
            "color": self.color,
            "owner_id": self.owner_id,
            "placed_at_turn": self.placed_at_turn,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Pixel":
        return cls(
            color=data.get("color", "empty"),
            owner_id=data.get("owner_id"),
            placed_at_turn=data.get("placed_at_turn", 0),
        )


@dataclass
class PlacementRecord:
    """Record of a pixel placement."""
    turn: int
    x: int
    y: int
    color: str
    agent_id: str
    previous_color: str
    previous_owner: Optional[str]
    
    def to_dict(self) -> dict:
        return {
            "turn": self.turn,
            "x": self.x,
            "y": self.y,
            "color": self.color,
            "agent_id": self.agent_id,
            "previous_color": self.previous_color,
            "previous_owner": self.previous_owner,
        }


@dataclass
class Grid:
    """The shared canvas where agents place pixels."""
    
    width: int = 16
    height: int = 16
    pixels: list[list[Pixel]] = field(default_factory=list)
    history: list[PlacementRecord] = field(default_factory=list)
    current_turn: int = 0
    
    def __post_init__(self):
        """Initialize the pixel grid if empty."""
        if not self.pixels:
            self.pixels = [
                [Pixel() for _ in range(self.width)]
                for _ in range(self.height)
            ]
    
    def reset(self) -> None:
        """Reset the grid to empty state."""
        self.pixels = [
            [Pixel() for _ in range(self.width)]
            for _ in range(self.height)
        ]
        self.history = []
        self.current_turn = 0
    
    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if coordinates are within grid bounds."""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def get_pixel(self, x: int, y: int) -> Optional[Pixel]:
        """Get pixel at position, or None if out of bounds."""
        if not self.is_valid_position(x, y):
            return None
        return self.pixels[y][x]
    
    def place_pixel(
        self,
        x: int,
        y: int,
        color: str,
        agent_id: str,
        turn: Optional[int] = None,
    ) -> bool:
        """
        Place a pixel on the grid.
        
        Returns True if placement was successful, False otherwise.
        """
        if not self.is_valid_position(x, y):
            return False
        
        if color not in COLORS:
            return False
        
        current_turn = turn if turn is not None else self.current_turn
        
        # Record the previous state
        old_pixel = self.pixels[y][x]
        record = PlacementRecord(
            turn=current_turn,
            x=x,
            y=y,
            color=color,
            agent_id=agent_id,
            previous_color=old_pixel.color,
            previous_owner=old_pixel.owner_id,
        )
        self.history.append(record)
        
        # Update the pixel
        self.pixels[y][x] = Pixel(
            color=color,
            owner_id=agent_id,
            placed_at_turn=current_turn,
        )
        
        return True
    
    def get_territory_count(self, agent_id: str) -> int:
        """Count how many pixels an agent currently owns."""
        count = 0
        for row in self.pixels:
            for pixel in row:
                if pixel.owner_id == agent_id:
                    count += 1
        return count
    
    def get_territory_by_agent(self) -> dict[str, int]:
        """Get territory count for all agents."""
        territory = defaultdict(int)
        for row in self.pixels:
            for pixel in row:
                if pixel.owner_id:
                    territory[pixel.owner_id] += 1
        return dict(territory)
    
    def get_color_count(self, color: str) -> int:
        """Count pixels of a specific color."""
        count = 0
        for row in self.pixels:
            for pixel in row:
                if pixel.color == color:
                    count += 1
        return count
    
    def get_empty_count(self) -> int:
        """Count empty pixels."""
        count = 0
        for row in self.pixels:
            for pixel in row:
                if pixel.color == "empty":
                    count += 1
        return count
    
    def get_neighbors(self, x: int, y: int) -> list[Pixel]:
        """Get adjacent pixels (4-directional)."""
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            pixel = self.get_pixel(nx, ny)
            if pixel:
                neighbors.append(pixel)
        return neighbors
    
    def get_neighbor_coords(self, x: int, y: int) -> list[tuple[int, int]]:
        """Get coordinates of adjacent pixels (4-directional)."""
        coords = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if self.is_valid_position(nx, ny):
                coords.append((nx, ny))
        return coords
    
    def get_agent_pixels(self, agent_id: str) -> list[tuple[int, int]]:
        """Get all pixel coordinates owned by an agent."""
        coords = []
        for y, row in enumerate(self.pixels):
            for x, pixel in enumerate(row):
                if pixel.owner_id == agent_id:
                    coords.append((x, y))
        return coords
    
    def get_empty_positions(self) -> list[tuple[int, int]]:
        """Get all empty pixel coordinates."""
        coords = []
        for y, row in enumerate(self.pixels):
            for x, pixel in enumerate(row):
                if pixel.color == "empty":
                    coords.append((x, y))
        return coords
    
    def get_average_pixel_lifespan(self, agent_id: str) -> float:
        """
        Calculate average lifespan of pixels placed by an agent.
        
        Lifespan = how many turns a pixel survived before being overwritten.
        """
        # Track when each of the agent's pixels was overwritten
        agent_placements = {}  # (x, y) -> turn placed
        pixel_lifespans = []
        
        for record in self.history:
            if record.agent_id == agent_id:
                # Agent placed a pixel
                agent_placements[(record.x, record.y)] = record.turn
            elif record.previous_owner == agent_id:
                # Agent's pixel was overwritten
                if (record.x, record.y) in agent_placements:
                    placed_turn = agent_placements[(record.x, record.y)]
                    lifespan = record.turn - placed_turn
                    pixel_lifespans.append(lifespan)
                    del agent_placements[(record.x, record.y)]
        
        # Add lifespans for pixels that survived until end
        for (x, y), placed_turn in agent_placements.items():
            pixel = self.get_pixel(x, y)
            if pixel and pixel.owner_id == agent_id:
                lifespan = self.current_turn - placed_turn
                pixel_lifespans.append(lifespan)
        
        if not pixel_lifespans:
            return 0.0
        
        return sum(pixel_lifespans) / len(pixel_lifespans)
    
    def get_overwrites_by_agent(self, agent_id: str) -> int:
        """Count how many times an agent overwrote others' pixels."""
        count = 0
        for record in self.history:
            if record.agent_id == agent_id and record.previous_owner and record.previous_owner != agent_id:
                count += 1
        return count
    
    def get_times_overwritten(self, agent_id: str) -> int:
        """Count how many times an agent's pixels were overwritten."""
        count = 0
        for record in self.history:
            if record.previous_owner == agent_id and record.agent_id != agent_id:
                count += 1
        return count
    
    def to_ascii(self, use_color: bool = False) -> str:
        """
        Convert grid to ASCII representation for LLM context.
        
        Format:
          0123456789...
        0 .R.B..G.....
        1 ..RR.BB.....
        ...
        """
        lines = []
        
        # Header with column numbers
        col_header = "  " + "".join(str(i % 10) for i in range(self.width))
        lines.append(col_header)
        
        for y, row in enumerate(self.pixels):
            row_str = f"{y % 10} "
            for pixel in row:
                char = COLOR_ASCII.get(pixel.color, "?")
                if use_color and pixel.color != "empty":
                    ansi = COLOR_ANSI.get(pixel.color, "")
                    reset = COLOR_ANSI["reset"]
                    row_str += f"{ansi}{char}{reset}"
                else:
                    row_str += char
            lines.append(row_str)
        
        return "\n".join(lines)
    
    def to_compact_ascii(self) -> str:
        """Compact ASCII without row/column numbers."""
        lines = []
        for row in self.pixels:
            line = "".join(COLOR_ASCII.get(p.color, "?") for p in row)
            lines.append(line)
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """Serialize grid to dictionary."""
        return {
            "width": self.width,
            "height": self.height,
            "current_turn": self.current_turn,
            "pixels": [
                [pixel.to_dict() for pixel in row]
                for row in self.pixels
            ],
            "history": [record.to_dict() for record in self.history],
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Grid":
        """Deserialize grid from dictionary."""
        grid = cls(
            width=data["width"],
            height=data["height"],
            current_turn=data.get("current_turn", 0),
        )
        grid.pixels = [
            [Pixel.from_dict(p) for p in row]
            for row in data["pixels"]
        ]
        grid.history = [
            PlacementRecord(**record) for record in data.get("history", [])
        ]
        return grid
    
    def get_recent_history(self, n: int = 10) -> list[PlacementRecord]:
        """Get the N most recent placement records."""
        return self.history[-n:] if self.history else []
    
    def get_state_summary(self) -> dict:
        """Get a summary of the current grid state."""
        territory = self.get_territory_by_agent()
        color_counts = {color: self.get_color_count(color) for color in COLORS}
        
        return {
            "turn": self.current_turn,
            "total_pixels": self.width * self.height,
            "empty_pixels": self.get_empty_count(),
            "filled_pixels": self.width * self.height - self.get_empty_count(),
            "territory_by_agent": territory,
            "color_counts": color_counts,
            "total_placements": len(self.history),
        }
    
    def clone(self) -> "Grid":
        """Create a deep copy of the grid."""
        return Grid.from_dict(self.to_dict())
    
    def __repr__(self) -> str:
        filled = self.width * self.height - self.get_empty_count()
        return f"Grid({self.width}x{self.height}, {filled} filled, turn {self.current_turn})"


def create_grid(width: int = 16, height: int = 16) -> Grid:
    """Create a new empty grid."""
    return Grid(width=width, height=height)
