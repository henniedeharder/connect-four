import sys
import math
import time
import random
import pygame

# ==============================
# Connect Four with Beautiful UI
# ==============================
# - 1P vs AI (minimax + alpha-beta, Easy/Medium/Hard)
# - 2P local
# - Smooth piece drop animation, hover preview
# - Win highlighting and polished board with cut-out holes
#
# Requires: pygame
#   pip install pygame
#
# Run:
#   python connect_four.py
#
# Controls:
# - Mouse hover: preview next drop
# - Mouse click: place a piece
# - ESC: back to main menu
# - R: restart match
#

# ------------- Game Constants -------------
ROWS = 6
COLS = 7
CONNECT_N = 4

# UI Dimensions
WINDOW_W = 900
WINDOW_H = 900
TOP_BAR_H = 110
BOARD_MARGIN = 60

FPS = 60

# Colors
COLOR_BG_TOP = (22, 26, 35)     # background gradient top
COLOR_BG_BOTTOM = (12, 15, 22)  # background gradient bottom
COLOR_BOARD = (31, 91, 181)     # main board color
COLOR_BOARD_EDGE = (21, 61, 121)
COLOR_SHADOW = (0, 0, 0, 110)

COLOR_P1 = (237, 64, 64)        # red
COLOR_P2 = (255, 198, 41)       # yellow

COLOR_TEXT = (230, 236, 245)
COLOR_MUTED = (155, 170, 190)
COLOR_ACCENT = (130, 190, 255)

# Simple button theme
BTN_BG = (34, 43, 60)
BTN_BG_HOVER = (44, 53, 75)
BTN_BORDER = (70, 90, 130)

# AI difficulty → depth
DIFFICULTIES = {
    "Easy": 3,
    "Medium": 5,
    "Hard": 6
}


# ------------- Utility Functions -------------
def lerp_color(c1, c2, t):
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t)
    )

def lighten(color, amt):
    r, g, b = color
    return (min(255, int(r + amt)), min(255, int(g + amt)), min(255, int(b + amt)))

def darken(color, amt):
    r, g, b = color
    return (max(0, int(r - amt)), max(0, int(g - amt)), max(0, int(b - amt)))

def draw_vertical_gradient(surface, rect, top_color, bottom_color):
    x, y, w, h = rect
    for i in range(h):
        t = i / max(1, h - 1)
        col = lerp_color(top_color, bottom_color, t)
        pygame.draw.line(surface, col, (x, y + i), (x + w, y + i))


# ------------- Game Board Logic -------------
class Board:
    def __init__(self, rows=ROWS, cols=COLS):
        self.rows = rows
        self.cols = cols
        self.grid = [[0] * cols for _ in range(rows)]
        self.moves = []  # stack of (row, col)

    def reset(self):
        self.grid = [[0] * self.cols for _ in range(self.rows)]
        self.moves = []

    def copy(self):
        b = Board(self.rows, self.cols)
        b.grid = [row[:] for row in self.grid]
        b.moves = self.moves[:]
        return b

    def is_valid_col(self, col):
        return 0 <= col < self.cols and self.grid[0][col] == 0

    def get_valid_cols(self):
        return [c for c in range(self.cols) if self.is_valid_col(c)]

    def get_next_open_row(self, col):
        for r in range(self.rows - 1, -1, -1):
            if self.grid[r][col] == 0:
                return r
        return None

    def drop_piece(self, col, player):
        r = self.get_next_open_row(col)
        if r is not None:
            self.grid[r][col] = player
            self.moves.append((r, col))
            return r
        return None

    def undo(self):
        if not self.moves:
            return None
        r, c = self.moves.pop()
        self.grid[r][c] = 0
        return (r, c)

    def check_win(self, player):
        # Check horizontal
        for r in range(self.rows):
            for c in range(self.cols - 3):
                if all(self.grid[r][c + k] == player for k in range(4)):
                    return [(r, c + k) for k in range(4)]
        # Check vertical
        for c in range(self.cols):
            for r in range(self.rows - 3):
                if all(self.grid[r + k][c] == player for k in range(4)):
                    return [(r + k, c) for k in range(4)]
        # Check diag down-right
        for r in range(self.rows - 3):
            for c in range(self.cols - 3):
                if all(self.grid[r + k][c + k] == player for k in range(4)):
                    return [(r + k, c + k) for k in range(4)]
        # Check diag up-right
        for r in range(3, self.rows):
            for c in range(self.cols - 3):
                if all(self.grid[r - k][c + k] == player for k in range(4)):
                    return [(r - k, c + k) for k in range(4)]
        return None

    def is_draw(self):
        return all(self.grid[0][c] != 0 for c in range(self.cols))

    def terminal_info(self):
        # Returns (is_terminal, winner, winning_positions)
        for p in (1, 2):
            wp = self.check_win(p)
            if wp:
                return (True, p, wp)
        if self.is_draw():
            return (True, 0, None)
        return (False, None, None)


# ------------- AI (Minimax + Alpha-Beta) -------------
def evaluate_window(window, player):
    opp = 2 if player == 1 else 1
    score = 0
    count_p = window.count(player)
    count_o = window.count(opp)
    count_e = window.count(0)

    if count_p == 4:
        score += 10000
    elif count_p == 3 and count_e == 1:
        score += 80
    elif count_p == 2 and count_e == 2:
        score += 12

    if count_o == 3 and count_e == 1:
        score -= 90
    elif count_o == 2 and count_e == 2:
        score -= 10
    return score

def score_position(board: Board, player):
    score = 0
    center_col = board.cols // 2
    # Center preference
    center_count = sum(1 for r in range(board.rows) if board.grid[r][center_col] == player)
    score += center_count * 8

    # Horizontal
    for r in range(board.rows):
        row_array = board.grid[r]
        for c in range(board.cols - 3):
            window = row_array[c:c + 4]
            score += evaluate_window(window, player)

    # Vertical
    for c in range(board.cols):
        col_array = [board.grid[r][c] for r in range(board.rows)]
        for r in range(board.rows - 3):
            window = col_array[r:r + 4]
            score += evaluate_window(window, player)

    # Positive diagonal
    for r in range(board.rows - 3):
        for c in range(board.cols - 3):
            window = [board.grid[r + k][c + k] for k in range(4)]
            score += evaluate_window(window, player)

    # Negative diagonal
    for r in range(3, board.rows):
        for c in range(board.cols - 3):
            window = [board.grid[r - k][c + k] for k in range(4)]
            score += evaluate_window(window, player)

    return score

def minimax(board: Board, depth, alpha, beta, maximizing_player, ai_player):
    terminal, winner, _ = board.terminal_info()
    if depth == 0 or terminal:
        if terminal:
            if winner == ai_player:
                return (None, 1_000_000)
            elif winner == 0:
                return (None, 0)
            else:
                return (None, -1_000_000)
        else:
            return (None, score_position(board, ai_player))

    valid_cols = board.get_valid_cols()
    if not valid_cols:
        return (None, 0)

    if maximizing_player:
        value = -math.inf
        best_col = random.choice(valid_cols)
        # Move ordering: prioritize center columns
        ordered = sorted(valid_cols, key=lambda c: abs(c - board.cols // 2))
        for col in ordered:
            row = board.get_next_open_row(col)
            board.grid[row][col] = ai_player
            board.moves.append((row, col))

            _, new_score = minimax(board, depth - 1, alpha, beta, False, ai_player)

            board.grid[row][col] = 0
            board.moves.pop()

            if new_score > value:
                value = new_score
                best_col = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return best_col, value
    else:
        value = math.inf
        best_col = random.choice(valid_cols)
        opp = 2 if ai_player == 1 else 1
        ordered = sorted(valid_cols, key=lambda c: abs(c - board.cols // 2))
        for col in ordered:
            row = board.get_next_open_row(col)
            board.grid[row][col] = opp
            board.moves.append((row, col))

            _, new_score = minimax(board, depth - 1, alpha, beta, True, ai_player)

            board.grid[row][col] = 0
            board.moves.pop()

            if new_score < value:
                value = new_score
                best_col = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return best_col, value


# ------------- UI Components -------------
class Button:
    def __init__(self, rect, text, font, on_click, small=False):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.on_click = on_click
        self.small = small

    def draw(self, surface, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)
        bg = BTN_BG_HOVER if hovered else BTN_BG
        pygame.draw.rect(surface, bg, self.rect, border_radius=10)
        pygame.draw.rect(surface, BTN_BORDER, self.rect, width=1, border_radius=10)
        txt = self.font.render(self.text, True, COLOR_TEXT)
        surface.blit(txt, txt.get_rect(center=self.rect.center))

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(mouse_pos):
                if self.on_click:
                    self.on_click()


# ------------- Game UI & Drawing -------------
class GameUI:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_lg = pygame.font.SysFont("arialrounded", 48, bold=True)
        self.font_md = pygame.font.SysFont("arialrounded", 30, bold=True)
        self.font_sm = pygame.font.SysFont("arialrounded", 22)

        # Board positioning computed later
        self.board_rect = None
        self.cell_size = None
        self.hole_radius = None
        self.hover_col = None

        # Menu buttons
        self.buttons = []

        # Game state
        self.state = "MENU"  # MENU | PLAYING | GAME_OVER
        self.board = Board()
        self.turn = 1  # 1 or 2
        self.mode = None  # "PVP" or "AI"
        self.ai_depth = DIFFICULTIES["Medium"]
        self.winning_positions = None
        self.ai_thinking = False
        self.last_ai_time = 0

        self._compute_layout()

    def _compute_layout(self):
        # Compute board rectangle that fits nicely in the window
        w, h = self.screen.get_size()
        usable_h = h - TOP_BAR_H - BOARD_MARGIN
        usable_w = w - BOARD_MARGIN * 2

        # Maintain aspect ratio based on grid (COLS x ROWS)
        cell_w = usable_w // COLS
        cell_h = usable_h // ROWS
        self.cell_size = min(cell_w, cell_h)
        board_w = self.cell_size * COLS
        board_h = self.cell_size * ROWS

        x = (w - board_w) // 2
        y = TOP_BAR_H + (usable_h - board_h) // 2
        self.board_rect = pygame.Rect(x, y, board_w, board_h)
        self.hole_radius = int(self.cell_size * 0.42)

    def draw_background(self):
        draw_vertical_gradient(self.screen, (0, 0, *self.screen.get_size()), COLOR_BG_TOP, COLOR_BG_BOTTOM)

    def draw_top_bar(self):
        # Subtle overlay on top
        top_rect = pygame.Rect(0, 0, self.screen.get_width(), TOP_BAR_H)
        overlay = pygame.Surface(top_rect.size, pygame.SRCALPHA)
        draw_vertical_gradient(overlay, overlay.get_rect(), (255, 255, 255, 16), (255, 255, 255, 8))
        self.screen.blit(overlay, top_rect)

        # Title
        title = self.font_lg.render("Connect Four", True, COLOR_TEXT)
        self.screen.blit(title, (20, (TOP_BAR_H - title.get_height()) // 2))

        # Mode/Turn info
        mode_text = f"Mode: {'2 Players' if self.mode == 'PVP' else f'1 Player ({self.depth_label()})' if self.mode == 'AI' else '—'}"
        state_text = f"Turn: {'Red' if self.turn == 1 else 'Yellow'}" if self.state == "PLAYING" else ""
        rt = self.font_sm.render(mode_text, True, COLOR_MUTED)
        st = self.font_sm.render(state_text, True, COLOR_MUTED)
        self.screen.blit(rt, (self.screen.get_width() - rt.get_width() - 20, 16))
        self.screen.blit(st, (self.screen.get_width() - st.get_width() - 20, 16 + rt.get_height() + 6))

    def depth_label(self):
        for k, v in DIFFICULTIES.items():
            if v == self.ai_depth:
                return k
        return f"Depth {self.ai_depth}"

    def draw_board_layers(self):
        # Board shadow
        shadow = pygame.Surface((self.board_rect.w + 24, self.board_rect.h + 24), pygame.SRCALPHA)
        pygame.draw.rect(shadow, COLOR_SHADOW, shadow.get_rect(), border_radius=24)
        self.screen.blit(shadow, (self.board_rect.x - 12, self.board_rect.y - 6))

        # Tokens first (so they appear under the board overlay holes)
        self.draw_tokens()

        # Board overlay with cut-out holes
        board_surf = pygame.Surface(self.board_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(board_surf, COLOR_BOARD, board_surf.get_rect(), border_radius=22)
        pygame.draw.rect(board_surf, COLOR_BOARD_EDGE, board_surf.get_rect(), width=4, border_radius=22)

        # Cut holes (transparent)
        for r in range(ROWS):
            for c in range(COLS):
                cx = int(c * self.cell_size + self.cell_size / 2)
                cy = int(r * self.cell_size + self.cell_size / 2)
                pygame.draw.circle(board_surf, (0, 0, 0, 0), (cx, cy), self.hole_radius)

        self.screen.blit(board_surf, self.board_rect.topleft)

        # Hover preview on top
        self.draw_hover_preview()

        # Win highlight if any
        if self.winning_positions:
            self.draw_win_highlight(self.winning_positions)

    def draw_tokens(self):
        # Draw each placed token with a simple radial highlight
        for r in range(ROWS):
            for c in range(COLS):
                p = self.board.grid[r][c]
                if p != 0:
                    color = COLOR_P1 if p == 1 else COLOR_P2
                    cx = self.board_rect.x + int(c * self.cell_size + self.cell_size / 2)
                    cy = self.board_rect.y + int(r * self.cell_size + self.cell_size / 2)
                    self.draw_token(cx, cy, self.hole_radius - 2, color)

    def draw_token(self, x, y, radius, color):
        # Draw radial gradient token
        surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        center = (radius + 2, radius + 2)

        layers = max(6, radius // 3)
        for i in range(layers, 0, -1):
            t = i / layers
            col = lerp_color(darken(color, 30), lighten(color, 80), 1 - t)
            pygame.draw.circle(surf, col, center, int(radius * (0.3 + 0.7 * t)))
        # Highlight gloss
        gloss = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        pygame.draw.circle(gloss, (255, 255, 255, 40), (center[0] - radius // 3, center[1] - radius // 3), radius // 2)
        surf.blit(gloss, (0, 0), special_flags=pygame.BLEND_PREMULTIPLIED)

        self.screen.blit(surf, (x - center[0], y - center[1]))

    def draw_hover_preview(self):
        if self.state != "PLAYING" or self.hover_col is None:
            return
        if not self.board.is_valid_col(self.hover_col):
            return
        r = self.board.get_next_open_row(self.hover_col)
        if r is None:
            return
        p = self.turn
        color = COLOR_P1 if p == 1 else COLOR_P2
        cx = self.board_rect.x + int(self.hover_col * self.cell_size + self.cell_size / 2)
        top_y = self.board_rect.y - self.cell_size // 2
        # Draw semi-transparent preview
        surf = pygame.Surface((self.hole_radius * 2 + 6, self.hole_radius * 2 + 6), pygame.SRCALPHA)
        self.draw_token(self.hole_radius + 3, self.hole_radius + 3, self.hole_radius - 2, color)
        # Apply alpha
        temp = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        temp.blit(self.screen, (- (cx - self.hole_radius - 3), - (top_y - self.hole_radius - 3)))
        surf.set_alpha(150)
        # Instead of compositing, just draw a dim token
        self.draw_token(cx, top_y, self.hole_radius - 2, lighten(color, 30))

    def draw_win_highlight(self, positions):
        # Draw a glowing line through the center of the 4 winning slots
        pts = []
        for (r, c) in positions:
            cx = self.board_rect.x + int(c * self.cell_size + self.cell_size / 2)
            cy = self.board_rect.y + int(r * self.cell_size + self.cell_size / 2)
            pts.append((cx, cy))

        if len(pts) >= 2:
            # Draw multiple wide translucent lines for glow
            for w, alpha in [(18, 40), (12, 90), (6, 200)]:
                col = (*COLOR_ACCENT, alpha)
                surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
                pygame.draw.lines(surf, col, False, pts, w)
                self.screen.blit(surf, (0, 0))

    def animate_drop(self, col, row, player):
        # Animate piece falling from above the board into (row, col)
        color = COLOR_P1 if player == 1 else COLOR_P2
        cx = self.board_rect.x + int(col * self.cell_size + self.cell_size / 2)
        target_y = self.board_rect.y + int(row * self.cell_size + self.cell_size / 2)
        y = self.board_rect.y - self.cell_size  # start above
        velocity = 0
        gravity = max(1.8, self.cell_size / 20)

        while y < target_y:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

            velocity += gravity
            y += velocity
            if y > target_y:
                y = target_y

            self.draw_frame(preview=False)
            self.draw_token(cx, int(y), self.hole_radius - 2, color)
            pygame.display.flip()

    def draw_menu(self):
        self.draw_background()
        self.draw_top_bar()

        # Title in center-ish
        title = self.font_lg.render("Classic Connect Four", True, COLOR_TEXT)
        subtitle = self.font_md.render("Choose a mode", True, COLOR_MUTED)

        self.screen.blit(title, title.get_rect(center=(self.screen.get_width() // 2, TOP_BAR_H + 120)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(self.screen.get_width() // 2, TOP_BAR_H + 170)))

        # Buttons (compute once)
        if not self.buttons:
            cx = self.screen.get_width() // 2
            start_y = TOP_BAR_H + 240
            bw, bh, gap = 260, 58, 18

            def set_pvp():
                self.start_game("PVP", None)

            def set_ai_easy():
                self.start_game("AI", DIFFICULTIES["Easy"])

            def set_ai_med():
                self.start_game("AI", DIFFICULTIES["Medium"])

            def set_ai_hard():
                self.start_game("AI", DIFFICULTIES["Hard"])

            self.buttons = [
                Button((cx - bw // 2, start_y, bw, bh), "2 Players (Local)", self.font_md, set_pvp),
                Button((cx - bw // 2, start_y + (bh + gap), bw, bh), "1 Player - Easy", self.font_md, set_ai_easy),
                Button((cx - bw // 2, start_y + 2 * (bh + gap), bw, bh), "1 Player - Medium", self.font_md, set_ai_med),
                Button((cx - bw // 2, start_y + 3 * (bh + gap), bw, bh), "1 Player - Hard", self.font_md, set_ai_hard),
            ]

        mouse_pos = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(self.screen, mouse_pos)

        # Footer
        footer = self.font_sm.render("Tip: Hover over a column to preview your move. ESC to return here.", True, COLOR_MUTED)
        self.screen.blit(footer, footer.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 40)))

    def start_game(self, mode, ai_depth):
        self.mode = mode
        if ai_depth is not None:
            self.ai_depth = ai_depth
        self.board.reset()
        self.turn = 1
        self.winning_positions = None
        self.state = "PLAYING"
        self.ai_thinking = False
        self.last_ai_time = 0

    def draw_game_over_overlay(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))
        self.screen.blit(overlay, (0, 0))

        if self.winning_positions:
            winner = 1 if self.board.grid[self.winning_positions[0][0]][self.winning_positions[0][1]] == 1 else 2
            msg = "Red wins!" if winner == 1 else "Yellow wins!"
        else:
            msg = "It's a draw!"

        msg_surf = self.font_lg.render(msg, True, COLOR_TEXT)
        self.screen.blit(msg_surf, msg_surf.get_rect(center=(self.screen.get_width() // 2, TOP_BAR_H + 80)))

        # Buttons
        bw, bh = 200, 54
        cx = self.screen.get_width() // 2
        base_y = TOP_BAR_H + 160

        def restart():
            self.start_game(self.mode, self.ai_depth if self.mode == "AI" else None)

        def back_menu():
            self.state = "MENU"
            self.buttons = []  # reset menu buttons

        btn_restart = Button((cx - bw - 14, base_y, bw, bh), "Play Again (R)", self.font_md, restart)
        btn_menu = Button((cx + 14, base_y, bw, bh), "Main Menu (ESC)", self.font_md, back_menu)
        for b in [btn_restart, btn_menu]:
            b.draw(self.screen, pygame.mouse.get_pos())

    def draw_frame(self, preview=True):
        self.draw_background()
        self.draw_top_bar()
        self.draw_board_layers()
        if self.state == "GAME_OVER":
            self.draw_game_over_overlay()

        # Helper labels during AI thinking
        if self.state == "PLAYING" and self.mode == "AI" and self.turn == 2 and self.ai_thinking:
            msg = self.font_md.render("Computer is thinking...", True, COLOR_MUTED)
            self.screen.blit(msg, msg.get_rect(center=(self.screen.get_width() // 2, TOP_BAR_H + 40)))

    def handle_game_click(self, pos):
        if self.state != "PLAYING":
            return
        if self.mode == "AI" and self.turn == 2:
            return  # ignore clicks during AI turn

        if self.board_rect.collidepoint(pos):
            col = (pos[0] - self.board_rect.x) // self.cell_size
            col = int(col)
            if self.board.is_valid_col(col):
                row = self.board.drop_piece(col, self.turn)
                if row is not None:
                    self.animate_drop(col, row, self.turn)
                    self.check_post_move()

    def check_post_move(self):
        terminal, winner, winpos = self.board.terminal_info()
        if terminal:
            self.winning_positions = winpos
            self.state = "GAME_OVER"
            return

        # Switch turn
        self.turn = 2 if self.turn == 1 else 1

        # If AI turn, trigger AI move
        if self.state == "PLAYING" and self.mode == "AI" and self.turn == 2:
            self.ai_move()

    def ai_move(self):
        self.ai_thinking = True
        self.draw_frame()
        pygame.display.flip()

        # Compute AI decision
        start = time.time()
        tmp_board = self.board.copy()
        col, _ = minimax(tmp_board, self.ai_depth, -math.inf, math.inf, True, ai_player=2)
        if col is None or not self.board.is_valid_col(col):
            # Fallback: random valid move
            valid_cols = self.board.get_valid_cols()
            col = random.choice(valid_cols) if valid_cols else None

        if col is not None:
            row = self.board.drop_piece(col, 2)
            if row is not None:
                self.animate_drop(col, row, 2)
        self.ai_thinking = False
        self.last_ai_time = time.time() - start

        self.check_post_move()

    def run_menu_loop(self):
        self.state = "MENU"
        self.buttons = []
        while self.state == "MENU":
            self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif event.type == pygame.VIDEORESIZE:
                    pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self._compute_layout()
                    self.buttons = []
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for b in self.buttons:
                        b.handle_event(event, mouse_pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()

            self.draw_menu()
            pygame.display.flip()

    def run_game_loop(self):
        while self.state == "PLAYING" or self.state == "GAME_OVER":
            self.clock.tick(FPS)
            self.hover_col = None
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif event.type == pygame.VIDEORESIZE:
                    pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self._compute_layout()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.state = "MENU"
                        self.buttons = []
                        return
                    if event.key == pygame.K_r:
                        # restart match
                        self.start_game(self.mode, self.ai_depth if self.mode == "AI" else None)
                        continue
                elif event.type == pygame.MOUSEMOTION:
                    if self.board_rect.collidepoint(event.pos):
                        col = (event.pos[0] - self.board_rect.x) // self.cell_size
                        if 0 <= col < COLS:
                            self.hover_col = int(col)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_game_click(event.pos)

            self.draw_frame()
            pygame.display.flip()


# ------------- Entry Point -------------
def main():
    pygame.init()
    pygame.display.set_caption("Connect Four - Beautiful Edition")
    flags = pygame.RESIZABLE
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), flags)
    ui = GameUI(screen)

    while True:
        ui.run_menu_loop()
        ui.run_game_loop()


if __name__ == "__main__":
    main()
