import pickle
import heapq
from config import GameConfig

class QuoridorGame:
    def __init__(self):
        self.p1_pos = (4, 8) # (x, y)
        self.p2_pos = (4, 0)
        self.walls = [] 
        self.turn = 1 
        self.p1_walls = 10
        self.p2_walls = 10
        self.winner = None
        self.history = [] 
        self.redo_history = []
        self._path_cache = {}

    def save_state(self):
        """Create a clean snapshot of the board only."""
        state = self.__dict__.copy()
        if 'history' in state: del state['history']
        if 'redo_history' in state: del state['redo_history']
        if '_path_cache' in state: del state['_path_cache']
        return pickle.dumps(state)

    def restore_state(self, snapshot):
        state_data = pickle.loads(snapshot)
        self.__dict__.update(state_data)
        self._path_cache = {} 

    def is_wall_blocking(self, c1, c2, walls=None):
        if walls is None: walls = self.walls
        x1, y1 = c1
        x2, y2 = c2
        
        if x1 == x2: 
            y_gap = min(y1, y2)
            if ((x1, y_gap), 'H') in walls: return True
            if ((x1 - 1, y_gap), 'H') in walls: return True
        elif y1 == y2:
            x_gap = min(x1, x2)
            if ((x_gap, y1), 'V') in walls: return True
            if ((x_gap, y1 - 1), 'V') in walls: return True
        return False

    def get_neighbors(self, pos, walls=None):
        x, y = pos
        moves = []
        candidates = [(x, y-1), (x, y+1), (x-1, y), (x+1, y)]
        for cx, cy in candidates:
            if 0 <= cx < 9 and 0 <= cy < 9:
                if not self.is_wall_blocking(pos, (cx, cy), walls):
                    moves.append((cx, cy))
        return moves

    def get_valid_pawn_moves(self, player_id):
        if self.winner: return []
        curr_pos = self.p1_pos if player_id == 1 else self.p2_pos
        opponent_pos = self.p2_pos if player_id == 1 else self.p1_pos
        valid_moves = []
        neighbors = self.get_neighbors(curr_pos)
        
        for n in neighbors:
            if n == opponent_pos:
                dx, dy = n[0] - curr_pos[0], n[1] - curr_pos[1]
                jump_dest = (n[0] + dx, n[1] + dy)
                can_jump_straight = False
                if 0 <= jump_dest[0] < 9 and 0 <= jump_dest[1] < 9:
                    if not self.is_wall_blocking(n, jump_dest):
                        valid_moves.append(jump_dest)
                        can_jump_straight = True
                if not can_jump_straight:
                    for on in self.get_neighbors(opponent_pos):
                        if on != curr_pos: valid_moves.append(on)
            else:
                valid_moves.append(n)
        return valid_moves

    def shortest_path(self, start_pos, goal_row, walls=None):
        if walls is None: walls = self.walls
        key = (start_pos, goal_row, frozenset(walls))
        if key in self._path_cache: return self._path_cache[key]

        open_heap = []
        heapq.heappush(open_heap, (abs(start_pos[1] - goal_row), 0, start_pos))
        came_from = {start_pos: None}
        gscore = {start_pos: 0}
        visited = set()

        while open_heap:
            _, g, current = heapq.heappop(open_heap)
            if current in visited: continue
            visited.add(current)

            if current[1] == goal_row:
                path = []
                while current:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                self._path_cache[key] = path
                return path

            for n in self.get_neighbors(current, walls):
                tg = g + 1
                if n not in gscore or tg < gscore[n]:
                    gscore[n] = tg
                    came_from[n] = current
                    heapq.heappush(open_heap, (tg + abs(n[1] - goal_row), tg, n))

        self._path_cache[key] = []
        return []

    def shortest_path_len(self, start_pos, goal_row, walls=None):
        path = self.shortest_path(start_pos, goal_row, walls)
        return len(path) - 1 if path else 999

    def get_hashable_state(self):
        walls_key = tuple(sorted(self.walls))
        return (self.p1_pos, self.p2_pos, self.p1_walls, self.p2_walls, walls_key, self.turn)

    def is_valid_wall(self, x, y, orientation):
        if self.winner: return False
        if not (0 <= x < 8 and 0 <= y < 8): return False
        
        for w_pos, w_orient in self.walls:
            wx, wy = w_pos
            if (wx, wy) == (x, y): return False 
            if orientation == 'H' and w_orient == 'H' and wy == y and abs(wx - x) <= 1: return False
            if orientation == 'V' and w_orient == 'V' and wx == x and abs(wy - y) <= 1: return False
            if w_pos == (x, y) and w_orient != orientation: return False

        if self.turn == 1 and self.p1_walls <= 0: return False
        if self.turn == 2 and self.p2_walls <= 0: return False

        self.walls.append(((x, y), orientation))
        p1_len = self.shortest_path_len(self.p1_pos, 0, self.walls)
        p2_len = self.shortest_path_len(self.p2_pos, 8, self.walls)
        self.walls.pop()
        
        return bool(p1_len < 999 and p2_len < 999)

    def apply_move(self, move, record_history=True):
        self._path_cache.clear()
        if len(self.history) > GameConfig.MAX_HISTORY:
            del self.history[0: len(self.history) - GameConfig.MAX_HISTORY]
        
        if record_history:
            self.history.append(self.save_state())
            self.redo_history.clear()

        if move['type'] == 'MOVE':
            if self.turn == 1: self.p1_pos = move['dest']
            else: self.p2_pos = move['dest']
        elif move['type'] == 'WALL':
            self.walls.append((move['pos'], move['orient']))
            if self.turn == 1: self.p1_walls -= 1
            else: self.p2_walls -= 1
            
        self.check_win()
        self.turn = 2 if self.turn == 1 else 1

    def apply_move_fast(self, move):
        self._path_cache.clear()
        undo_data = {'turn': self.turn, 'winner': self.winner}
        if move['type'] == 'MOVE':
            undo_data['type'] = 'MOVE'
            undo_data['prev_pos'] = self.p1_pos if self.turn == 1 else self.p2_pos
            if self.turn == 1: self.p1_pos = move['dest']
            else: self.p2_pos = move['dest']
        else:
            undo_data['type'] = 'WALL'
            self.walls.append((move['pos'], move['orient']))
            if self.turn == 1: self.p1_walls -= 1
            else: self.p2_walls -= 1
        
        self.check_win()
        self.turn = 2 if self.turn == 1 else 1
        return undo_data

    def undo_move_fast(self, undo_data):
        self._path_cache.clear()
        self.turn = undo_data['turn']
        self.winner = undo_data['winner']
        if undo_data['type'] == 'MOVE':
            if self.turn == 1: self.p1_pos = undo_data['prev_pos']
            else: self.p2_pos = undo_data['prev_pos']
        else:
            self.walls.pop()
            if self.turn == 1: self.p1_walls += 1
            else: self.p2_walls += 1

    def undo(self):
        if self.history:
            self.redo_history.append(self.save_state())
            self.restore_state(self.history.pop())
            return True
        return False

    def redo(self):
        if self.redo_history:
            self.history.append(self.save_state())
            self.restore_state(self.redo_history.pop())
            return True
        return False

    def check_win(self):
        if self.p1_pos[1] == 0: self.winner = 1
        elif self.p2_pos[1] == 8: self.winner = 2