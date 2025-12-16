import pygame
import pygame.gfxdraw
import pickle
import os
import sys
import random
import ctypes
from config import Theme, Layout, GameConfig
from ui.components import Button
from game.logic import QuoridorGame
from game.ai import AI

# High-DPI Fix
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def draw_aa_circle(surface, x, y, r, color):
    pygame.gfxdraw.aacircle(surface, x, y, r, color)
    pygame.gfxdraw.filled_circle(surface, x, y, r, color)

class QuoridorGUI:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        # Audio
        self.wood_sounds = []
        for i in range(1, 5):
            filename = f"wood{i}.mp3"
            try:
                path = resource_path(os.path.join('assets', 'audio', filename))
                sound = pygame.mixer.Sound(path)
                self.wood_sounds.append(sound)
            except Exception:
                pass

        # Pawn Images
        self.pawn_imgs = {1: None, 2: None}
        self.pawn_imgs_scaled = {1: None, 2: None}
        for pid in [1, 2]:
            fname = f"pawn{pid}.png"
            try:
                path = resource_path(os.path.join('assets', 'images', fname))
                self.pawn_imgs[pid] = pygame.image.load(path)
            except Exception:
                pass

        # Logo Image
        self.logo_img = None
        self.logo_scaled = None
        try:
            path = resource_path(os.path.join('assets', 'images', 'logo.png'))
            self.logo_img = pygame.image.load(path)
            pygame.display.set_icon(self.logo_img) 
        except Exception:
            print("Warning: logo.png not found in assets/images/")

        # Initialize Layout
        Layout.update(Layout.SCREEN_WIDTH, Layout.SCREEN_HEIGHT)
        
        self.screen = pygame.display.set_mode(
            (Layout.SCREEN_WIDTH, Layout.SCREEN_HEIGHT), 
            pygame.RESIZABLE
        )
        pygame.display.set_caption("Quoridor Ultimate")
        self.clock = pygame.time.Clock()
        
        self.init_fonts()
        
        self.state = "MENU"
        self.game_mode = "PVP"
        self.current_difficulty = 1
        self.ai = None
        self.game = None
        self.wall_orientation = 'H' 
        self.running = True
        
        self.setup_menu()
        self.setup_game_ui()

    def init_fonts(self):
        self.font_lg = pygame.font.SysFont("Segoe UI", 40, bold=True)
        self.font_md = pygame.font.SysFont("Segoe UI", 28, bold=True)
        self.font_sm = pygame.font.SysFont("Segoe UI", 20, bold=True)
        self.font_hint = pygame.font.SysFont("Segoe UI", 16, bold=False)

    def setup_menu(self):
        self.menu_buttons_data = [
            ("Player vs Player", lambda: self.start_game("PVP")),
            ("Player vs AI (Easy)", lambda: self.start_game("PVE", 1)),
            ("Player vs AI (Hard)", lambda: self.start_game("PVE", 3)),
            ("Load Game", self.load_game),
            ("Exit", sys.exit)
        ]
        self.menu_buttons = [] 

    def setup_game_ui(self):
        self.game_buttons_data = [
            ("Menu", self.return_to_menu),
            ("Save", self.save_game),
            ("Undo", self.do_undo),
            ("Redo", self.do_redo),
            ("Exit", sys.exit)
        ]
        self.game_buttons = []
        self.rematch_btn = None
        self.menu_overlay_btn = None

    def recalculate_ui(self):
        w, h = Layout.SCREEN_WIDTH, Layout.SCREEN_HEIGHT
        cx, cy = w // 2, h // 2
        
        # Scale Images (Pawns)
        target_size = int(Layout.CELL_SIZE * 0.8)
        for pid in [1, 2]:
            if self.pawn_imgs[pid]:
                self.pawn_imgs_scaled[pid] = pygame.transform.smoothscale(
                    self.pawn_imgs[pid], (target_size, target_size)
                )

        # Scale Logo
        logo_h = 0
        if self.logo_img:
            # Scale logo to 50% of screen width, maintaining aspect ratio
            target_w = int(w * 0.5)
            ratio = target_w / self.logo_img.get_width()
            target_h = int(self.logo_img.get_height() * ratio)
            
            # Cap height if it gets too tall (max 25% of screen height)
            if target_h > h * 0.25:
                target_h = int(h * 0.25)
                ratio = target_h / self.logo_img.get_height()
                target_w = int(self.logo_img.get_width() * ratio)
                
            self.logo_scaled = pygame.transform.smoothscale(self.logo_img, (target_w, target_h))
            logo_h = target_h

        # Menu Buttons Layout
        self.menu_buttons = []
        btn_w, btn_h = 300, 70
        
        # Calculate vertical positioning
        # If logo exists, start buttons below logo. Else center them.
        total_btn_h = len(self.menu_buttons_data) * 85
        
        if self.logo_scaled:
            start_y = 50 + logo_h + 40 # 50px margin + logo + gap
        else:
            start_y = (h - total_btn_h) // 2 + 50
        
        for i, (text, cb) in enumerate(self.menu_buttons_data):
            self.menu_buttons.append(Button(text, cx - btn_w//2, start_y + (i * 85), btn_w, btn_h, cb))

        # Game Buttons Layout
        self.game_buttons = []
        board_real_w = (9 * Layout.CELL_SIZE) + (8 * Layout.GAP_SIZE)
        Layout.MARGIN_X = (w - board_real_w) // 2
        is_wide_layout = w > (h + 200) 

        if is_wide_layout:
            # Side Layout
            btn_w, btn_h = 140, 50
            board_right_edge = Layout.MARGIN_X + board_real_w
            remaining_space = w - board_right_edge
            center_x = board_right_edge + (remaining_space // 2)
            total_btn_h = len(self.game_buttons_data) * 70
            start_y = (h - total_btn_h) // 2
            
            for i, (text, cb) in enumerate(self.game_buttons_data):
                self.game_buttons.append(Button(text, center_x - btn_w//2, start_y + (i * 70), btn_w, btn_h, cb))
        else:
            # Bottom Layout
            btn_w, btn_h = 120, 50
            y_pos = h - 70
            spacing = 20
            total_width = (len(self.game_buttons_data) * btn_w) + ((len(self.game_buttons_data) - 1) * spacing)
            start_x = (w - total_width) // 2
            
            for i, (text, cb) in enumerate(self.game_buttons_data):
                x_pos = start_x + i * (btn_w + spacing)
                self.game_buttons.append(Button(text, x_pos, y_pos, btn_w, btn_h, cb))

        # Overlay Buttons
        rm_w, rm_h = 200, 60
        self.rematch_btn = Button("Rematch", cx - rm_w//2, cy + 50, rm_w, rm_h, self.restart_game)
        self.menu_overlay_btn = Button("Menu", cx - rm_w//2, cy + 120, rm_w, rm_h, self.return_to_menu)

    def play_sound(self):
        if self.wood_sounds:
            random.choice(self.wood_sounds).play()

    def start_game(self, mode, difficulty=1):
        self.game = QuoridorGame()
        self.game_mode = mode
        self.current_difficulty = difficulty
        if mode == "PVE":
            self.ai = AI(difficulty)
        else:
            self.ai = None
        self.state = "GAME"
        self.recalculate_ui()

    def restart_game(self):
        self.start_game(self.game_mode, self.current_difficulty)

    def return_to_menu(self):
        self.state = "MENU"
        self.recalculate_ui()

    def save_game(self):
        if self.game:
            with open("quoridor_save.pkl", "wb") as f:
                data = {
                    'game_state': self.game.__dict__,
                    'mode': self.game_mode,
                    'ai_diff': self.ai.difficulty if self.ai else None
                }
                pickle.dump(data, f)
            print("Game Saved")

    def load_game(self):
        if os.path.exists("quoridor_save.pkl"):
            with open("quoridor_save.pkl", "rb") as f:
                data = pickle.load(f)
                self.game = QuoridorGame()
                self.game.__dict__ = data['game_state']
                self.game_mode = data['mode']
                if self.game_mode == "PVE":
                    self.ai = AI(data['ai_diff'])
                    self.current_difficulty = data['ai_diff']
                self.state = "GAME"
                self.recalculate_ui()

    def do_undo(self):
        if self.game_mode == "PVP":
            self.game.undo()
        else:
            self.game.undo()

    def do_redo(self):
        if self.game_mode == "PVP":
            self.game.redo()
        else:
            self.game.redo()

    def to_screen_coords(self, grid_x, grid_y):
        px = Layout.MARGIN_X + grid_x * (Layout.CELL_SIZE + Layout.GAP_SIZE)
        py = Layout.MARGIN_Y + grid_y * (Layout.CELL_SIZE + Layout.GAP_SIZE)
        return px, py

    def get_interaction_target(self, screen_x, screen_y):
        board_w = (9 * Layout.CELL_SIZE) + (8 * Layout.GAP_SIZE)
        if not (Layout.MARGIN_X <= screen_x <= Layout.MARGIN_X + board_w and
                Layout.MARGIN_Y <= screen_y <= Layout.MARGIN_Y + board_w):
            return {'type': 'NONE'}

        rx = screen_x - Layout.MARGIN_X
        ry = screen_y - Layout.MARGIN_Y
        unit = Layout.CELL_SIZE + Layout.GAP_SIZE
        
        fx = rx / unit
        fy = ry / unit
        gx, gy = int(fx), int(fy)
        
        if gx < 0 or gx > 8 or gy < 0 or gy > 8: return {'type': 'NONE'}

        frac_x = fx - gx
        frac_y = fy - gy
        
        is_gap_x = frac_x > (Layout.CELL_SIZE / unit)
        is_gap_y = frac_y > (Layout.CELL_SIZE / unit)
        
        if is_gap_x and is_gap_y:
             return {'type': 'WALL', 'grid': (gx, gy), 'orient': self.wall_orientation}
        elif is_gap_x:
             return {'type': 'WALL', 'grid': (gx, gy), 'orient': 'V'}
        elif is_gap_y:
             return {'type': 'WALL', 'grid': (gx, gy), 'orient': 'H'}
        
        dist_right = 1.0 - frac_x
        dist_bottom = 1.0 - frac_y
        if dist_right < 0.25: return {'type': 'WALL', 'grid': (gx, gy), 'orient': 'V'}
        if dist_bottom < 0.25: return {'type': 'WALL', 'grid': (gx, gy), 'orient': 'H'}
             
        return {'type': 'MOVE', 'grid': (gx, gy)}

    def draw_menu(self):
        self.screen.fill(Theme.BACKGROUND)
        
        # Draw Logo if available
        if self.logo_scaled:
            lx = (Layout.SCREEN_WIDTH - self.logo_scaled.get_width()) // 2
            ly = 50 # 50px margin top
            self.screen.blit(self.logo_scaled, (lx, ly))
        else:
            # Fallback Text
            title = self.font_lg.render("QUORIDOR", True, Theme.BUTTON_TEXT)
            self.screen.blit(title, (Layout.SCREEN_WIDTH//2 - title.get_width()//2, Layout.SCREEN_HEIGHT//5))
            
        for btn in self.menu_buttons:
            btn.draw(self.screen, self.font_md)

    def draw_game(self):
        self.screen.fill(Theme.BACKGROUND)
        
        turn_col = Theme.BUTTON_TEXT
        status_text = f"Player {self.game.turn}'s Turn"
        if self.game_mode == "PVE" and self.game.turn == 2:
            status_text = "AI Thinking..."
            
        txt = self.font_lg.render(status_text, True, turn_col)
        self.screen.blit(txt, (Layout.SCREEN_WIDTH//2 - txt.get_width()//2, 20))

        # Stats
        p1_lbl = self.font_sm.render("P1 Walls: ", True, Theme.BUTTON_TEXT)
        p1_val = self.font_sm.render(str(self.game.p1_walls), True, Theme.PLAYER_1)
        p2_lbl = self.font_sm.render("P2 Walls: ", True, Theme.BUTTON_TEXT)
        p2_val = self.font_sm.render(str(self.game.p2_walls), True, Theme.PLAYER_2)
        
        y_stats = 30
        self.screen.blit(p1_lbl, (50, y_stats))
        self.screen.blit(p1_val, (50 + p1_lbl.get_width(), y_stats))
        
        total_p2_w = p2_lbl.get_width() + p2_val.get_width()
        start_p2 = Layout.SCREEN_WIDTH - 50 - total_p2_w
        self.screen.blit(p2_lbl, (start_p2, y_stats))
        self.screen.blit(p2_val, (start_p2 + p2_lbl.get_width(), y_stats))

        # Board BG
        board_rect = (Layout.MARGIN_X - 10, Layout.MARGIN_Y - 10, 
                      (9*Layout.CELL_SIZE + 8*Layout.GAP_SIZE) + 20, 
                      (9*Layout.CELL_SIZE + 8*Layout.GAP_SIZE) + 20)
        pygame.draw.rect(self.screen, Theme.BOARD_BG, board_rect, border_radius=8)

        mouse_x, mouse_y = pygame.mouse.get_pos()
        target = self.get_interaction_target(mouse_x, mouse_y)
        valid_moves = self.game.get_valid_pawn_moves(self.game.turn) if not self.game.winner and (self.game_mode == "PVP" or self.game.turn == 1) else []

        for y in range(9):
            for x in range(9):
                px, py = self.to_screen_coords(x, y)
                pygame.draw.rect(self.screen, Theme.CELL_BG, (px, py, Layout.CELL_SIZE, Layout.CELL_SIZE), border_radius=4)
                
                if (x, y) in valid_moves:
                    cx, cy = px + Layout.CELL_SIZE//2, py + Layout.CELL_SIZE//2
                    if target['type'] == 'MOVE' and target['grid'] == (x, y):
                         draw_aa_circle(self.screen, cx, cy, int(Layout.CELL_SIZE * 0.2), Theme.CELL_HOVER)
                    else:
                         draw_aa_circle(self.screen, cx, cy, int(Layout.CELL_SIZE * 0.12), Theme.VALID_MOVE_DOT)

        for wall in self.game.walls:
            self.draw_wall_rect(wall[0][0], wall[0][1], wall[1], Theme.WALL_PLACED)

        self.draw_player(self.game.p1_pos, 1)
        self.draw_player(self.game.p2_pos, 2)
        
        human_turn = (self.game_mode == "PVP") or (self.game_mode == "PVE" and self.game.turn == 1)
        if not self.game.winner and human_turn and target['type'] == 'WALL':
            self.draw_wall_preview(target['grid'], target['orient'])

        # Buttons
        for btn in self.game_buttons:
            btn.draw(self.screen, self.font_sm)

        # Winner Overlay
        if self.game.winner:
            self.draw_winner()
            if self.rematch_btn:
                self.rematch_btn.draw(self.screen, self.font_md)
            if self.menu_overlay_btn:
                self.menu_overlay_btn.draw(self.screen, self.font_md)
        else:
            hint_txt = self.font_hint.render("Right-Click to Rotate Wall", True, Theme.VALID_MOVE_DOT)
            self.screen.blit(hint_txt, (Layout.SCREEN_WIDTH//2 - hint_txt.get_width()//2, Layout.SCREEN_HEIGHT - 35))

    def draw_player(self, pos, pid):
        px, py = self.to_screen_coords(pos[0], pos[1])
        cx, cy = px + Layout.CELL_SIZE // 2, py + Layout.CELL_SIZE // 2
        
        if self.pawn_imgs_scaled[pid]:
            img = self.pawn_imgs_scaled[pid]
            self.screen.blit(img, (cx - img.get_width() // 2, cy - img.get_height() // 2))
        else:
            col = Theme.PLAYER_1 if pid == 1 else Theme.PLAYER_2
            r = int(Layout.CELL_SIZE * 0.35)
            draw_aa_circle(self.screen, cx, cy, r, col)
            pygame.gfxdraw.aacircle(self.screen, cx, cy, r, (0,0,0))

    def draw_wall_rect(self, x, y, orientation, color):
        px, py = self.to_screen_coords(x, y)
        if orientation == 'H':
            pygame.draw.rect(self.screen, color, (px, py + Layout.CELL_SIZE, (Layout.CELL_SIZE * 2) + Layout.GAP_SIZE, Layout.GAP_SIZE), border_radius=2)
        else:
            pygame.draw.rect(self.screen, color, (px + Layout.CELL_SIZE, py, Layout.GAP_SIZE, (Layout.CELL_SIZE * 2) + Layout.GAP_SIZE), border_radius=2)

    def draw_wall_preview(self, grid_pos, orientation):
        gx, gy = grid_pos
        if gx >= 8 or gy >= 8: return 
        is_valid = self.game.is_valid_wall(gx, gy, orientation)
        color = Theme.WALL_PREVIEW_VALID if is_valid else Theme.WALL_PREVIEW_INVALID
        s = pygame.Surface((Layout.SCREEN_WIDTH, Layout.SCREEN_HEIGHT), pygame.SRCALPHA)
        px, py = self.to_screen_coords(gx, gy)
        
        rect = (0,0,0,0)
        if orientation == 'H':
            rect = (px, py + Layout.CELL_SIZE, (Layout.CELL_SIZE * 2) + Layout.GAP_SIZE, Layout.GAP_SIZE)
        else:
            rect = (px + Layout.CELL_SIZE, py, Layout.GAP_SIZE, (Layout.CELL_SIZE * 2) + Layout.GAP_SIZE)
            
        pygame.draw.rect(s, color, rect, border_radius=2)
        self.screen.blit(s, (0,0))

    def draw_winner(self):
        s = pygame.Surface((Layout.SCREEN_WIDTH, Layout.SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (0,0))
        txt = self.font_lg.render(f"PLAYER {self.game.winner} WINS!", True, Theme.BUTTON_TEXT)
        self.screen.blit(txt, (Layout.SCREEN_WIDTH//2 - txt.get_width()//2, Layout.SCREEN_HEIGHT//2 - 50))

    def run(self):
        self.recalculate_ui()
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    sys.exit()
                
                if event.type == pygame.VIDEORESIZE:
                    Layout.update(event.w, event.h)
                    self.recalculate_ui()
                    self.draw_menu() if self.state == "MENU" else self.draw_game()
                    pygame.display.flip()
                    
                if self.state == "MENU":
                    for btn in self.menu_buttons: btn.handle_event(event)
                elif self.state == "GAME":
                    if self.game.winner:
                        if self.rematch_btn: self.rematch_btn.handle_event(event)
                        if self.menu_overlay_btn: self.menu_overlay_btn.handle_event(event)
                        for btn in self.game_buttons: btn.handle_event(event)
                    else:
                        for btn in self.game_buttons: btn.handle_event(event)
                        
                        human_turn = (self.game_mode == "PVP") or (self.game_mode == "PVE" and self.game.turn == 1)
                        if human_turn and event.type == pygame.MOUSEBUTTONDOWN:
                            if event.button == 3:
                                self.wall_orientation = 'V' if self.wall_orientation == 'H' else 'H'
                            elif event.button == 1:
                                target = self.get_interaction_target(event.pos[0], event.pos[1])
                                btn_clicked = any(b.rect.collidepoint(event.pos) for b in self.game_buttons)
                                if not btn_clicked:
                                    if target['type'] == 'MOVE':
                                        if target['grid'] in self.game.get_valid_pawn_moves(self.game.turn):
                                            self.game.apply_move({'type': 'MOVE', 'dest': target['grid']})
                                            self.play_sound()
                                    elif target['type'] == 'WALL':
                                        if self.game.is_valid_wall(target['grid'][0], target['grid'][1], target['orient']):
                                            self.game.apply_move({'type': 'WALL', 'pos': target['grid'], 'orient': target['orient']})
                                            self.play_sound()

            if self.state == "GAME":
                if not self.game.winner and self.game_mode == "PVE" and self.game.turn == 2:
                    self.draw_game()
                    pygame.display.flip()
                    move = self.ai.get_move(self.game)
                    if move:
                        self.game.apply_move(move, record_history=False)
                        self.play_sound()
                    else:
                        print("AI Resigns")
                self.draw_game()
            else:
                self.draw_menu()
            pygame.display.flip()
            self.clock.tick(60)
