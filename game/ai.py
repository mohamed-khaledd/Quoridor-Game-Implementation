import pygame
import random
from config import GameConfig

class AI:
    def __init__(self, difficulty):
        self.difficulty = difficulty # 1=Easy, 3=Hard
        if difficulty == 1:
            self.max_depth = GameConfig.AI_DEPTH_EASY
        else:
            self.max_depth = GameConfig.AI_DEPTH_HARD
        
        self.transposition = {}

    def evaluate(self, game):
        if game.winner == 2: return GameConfig.WIN_SCORE
        if game.winner == 1: return -GameConfig.WIN_SCORE
        
        p2_dist = game.shortest_path_len(game.p2_pos, 8)
        p1_dist = game.shortest_path_len(game.p1_pos, 0)
        
        score = (20 - p2_dist) * 10 - (20 - p1_dist) * 10
        score += (game.p2_walls - game.p1_walls) * 5
        return score

    def get_all_moves(self, game, player_id):
        moves = []
        # Pawn Moves
        for dest in game.get_valid_pawn_moves(player_id):
            moves.append({'type': 'MOVE', 'dest': dest})

        # Wall Moves
        has_walls = (player_id == 2 and game.p2_walls > 0) or (player_id == 1 and game.p1_walls > 0)
        if has_walls:
            target_pos = game.p1_pos if player_id == 2 else game.p2_pos
            goal_row = 0 if player_id == 2 else 8
            path = game.shortest_path(target_pos, goal_row)
            candidates = set()
            radius = GameConfig.WALL_SEARCH_RADIUS
            
            for cell in path:
                cx, cy = cell
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        wx, wy = cx + dx, cy + dy
                        if 0 <= wx < 8 and 0 <= wy < 8:
                            for orient in ('H', 'V'):
                                if game.is_valid_wall(wx, wy, orient):
                                    candidates.add((wx, wy, orient))
            for (wx, wy, orient) in candidates:
                moves.append({'type': 'WALL', 'pos': (wx, wy), 'orient': orient})

        random.shuffle(moves)
        return moves

    def minimax(self, game, depth, alpha, beta, maximizing_player):
        if depth == self.max_depth:
            pygame.event.pump()

        state_key = game.get_hashable_state()
        tt_entry = self.transposition.get((state_key, depth, maximizing_player))
        if tt_entry is not None:
            return tt_entry[0], tt_entry[1]

        if depth == 0 or game.winner:
            val = self.evaluate(game)
            self.transposition[(state_key, depth, maximizing_player)] = (val, None)
            return val, None

        best_move = None
        
        player_id = 2 if maximizing_player else 1
        moves = self.get_all_moves(game, player_id)
        moves.sort(key=lambda m: 0 if m['type'] == 'MOVE' else 1)

        if maximizing_player:
            max_eval = -float('inf')
            for move in moves:
                undo_data = game.apply_move_fast(move)
                eval_val, _ = self.minimax(game, depth - 1, alpha, beta, False)
                game.undo_move_fast(undo_data)

                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = move
                alpha = max(alpha, eval_val)
                if beta <= alpha: break
            
            self.transposition[(state_key, depth, maximizing_player)] = (max_eval, best_move)
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in moves:
                undo_data = game.apply_move_fast(move)
                eval_val, _ = self.minimax(game, depth - 1, alpha, beta, True)
                game.undo_move_fast(undo_data)

                if eval_val < min_eval:
                    min_eval = eval_val
                    best_move = move
                beta = min(beta, eval_val)
                if beta <= alpha: break

            self.transposition[(state_key, depth, maximizing_player)] = (min_eval, best_move)
            return min_eval, best_move

    def get_move(self, game):
        _, move = self.minimax(game, self.max_depth, -float('inf'), float('inf'), True)
        return move
