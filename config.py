# Visual Theme (Classic Wood)
class Theme:
    # Warm, earthy tones
    BACKGROUND = (61, 43, 31)    # Deep Walnut Brown
    BOARD_BG = (139, 107, 78)    # Medium Oak
    CELL_BG = (194, 178, 128)    # Light Sand/Beige wood
    CELL_HOVER = (235, 213, 179) # Very light wood
    GRID_LINES = (89, 60, 41)    # Dark Chocolate
    
    # Fallback colors if PNGs fail to load
    PLAYER_1 = (166, 43, 43)     # Mahogany Red
    PLAYER_2 = (60, 100, 60)     # Forest Green
    
    # Walls
    WALL_PREVIEW_VALID = (100, 150, 100, 180) # Moss Green Transparent
    WALL_PREVIEW_INVALID = (150, 50, 50, 180) # Red Transparent
    WALL_PLACED = (80, 50, 20)   # Dark polished wood
    
    VALID_MOVE_DOT = (110, 90, 70, 150) # Subtle Brown
    
    # UI Elements
    BUTTON_BG = (101, 67, 33)    # Dark Brown
    BUTTON_HOVER = (120, 85, 50) # Lighter Brown
    BUTTON_TEXT = (255, 248, 220) # Cornsilk (Off-white)

# Dynamic Layout
class Layout:
    SCREEN_WIDTH = 900
    SCREEN_HEIGHT = 850 
    CELL_SIZE = 50
    GAP_SIZE = 12
    MARGIN_X = 0
    MARGIN_Y = 0
    
    @classmethod
    def update(cls, width, height):
        cls.SCREEN_WIDTH = width
        cls.SCREEN_HEIGHT = height
        min_dim = min(width, height - 100)
        board_pixel_size = min_dim * 0.85
        unit = board_pixel_size / 10.6
        cls.CELL_SIZE = int(unit)
        cls.GAP_SIZE = int(unit * 0.2)
        total_board_w = (9 * cls.CELL_SIZE) + (8 * cls.GAP_SIZE)
        cls.MARGIN_X = (width - total_board_w) // 2
        cls.MARGIN_Y = (height - total_board_w) // 2 + 20

# Game & AI Configuration
class GameConfig:
    MAX_HISTORY = 200
    AI_DEPTH_EASY = 1
    AI_DEPTH_HARD = 3
    WIN_SCORE = 10000
    WALL_SEARCH_RADIUS = 1
