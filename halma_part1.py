#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import sys
import argparse
import math
import time
import tkinter as tk
from tkinter import ttk, messagebox


# In[ ]:


"""
Halma Part 1 – Two-Player Manual Game (Tkinter)

Usage examples:
    python halma_part1.py
    python halma_part1.py --size 10 --limit 5 --human GREEN
    python halma_part1.py -s 16 -t 8 -c RED
"""



# ------------------------ Constants ------------------------

CELL_PAD = 6
GRID_COLOR = "#bbbbbb"
SEL_OUTLINE = "#ff7043"
MOVE_HILITE_ADJ = "#66bb6a"
MOVE_HILITE_JUMP = "#42a5f5"
LAST_MOVE_GREEN = "#c8e6c9"
LAST_MOVE_RED = "#ffcdd2"
BOARD_MARGIN = 40  # margin for labels

EMPTY = 0
GREEN = 1
RED = 2

COLOR_TO_NAME = {
    GREEN: "GREEN",
    RED: "RED",
}


# ------------------------ Utility functions ------------------------

def col_to_letter(c: int) -> str:
    return chr(ord('a') + c)


def letter_to_col(ch: str) -> int:
    return ord(ch.lower()) - ord('a')


def euclidean_distance(a, b) -> float:
    (r1, c1), (r2, c2) = a, b
    return math.hypot(r1 - r2, c1 - c2)


# ------------------------ Halma Game Class ------------------------

class HalmaBoard:
    def __init__(self, root, board_size=8, move_time_limit=10, human_color="GREEN"):
        self.root = root
        self.N = board_size
        self.move_time_limit = float(move_time_limit)
        self.human_color_label = human_color.upper()  # just for status label

                # Scores
        self.score_green = 0.0
        self.score_red = 0.0

        # Timer
        self.time_left = self.move_time_limit
        self.timer_id = None
        self.turn_start_time = time.time()

        # Status / message tracking
        self.last_msg = ""
        self.last_msg_time = 0.0

        self.root.title("Halma Part 1 – Two-Player Manual Game")

        # ---- Top: Status bar ----
        top_frame = ttk.Frame(root)
        top_frame.pack(side="top", fill="x")

        self.status_label = ttk.Label(
            top_frame, text="", anchor="w", font=("Arial", 10, "bold")
        )
        self.status_label.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        # ---- Center: Canvas ----
        self.canvas = tk.Canvas(root, bg="white", highlightthickness=0)
        self.canvas.pack(side="top", fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # ---- Bottom: Text move input (optional) ----
        bottom = ttk.Frame(root)
        bottom.pack(side="bottom", fill="x", pady=4)

        ttk.Label(bottom, text="Text move (e.g., a3->b4):").pack(side="left", padx=(5, 2))
        self.move_entry = ttk.Entry(bottom, width=15)
        self.move_entry.pack(side="left")
        ttk.Button(bottom, text="Enter Move", command=self.on_text_move).pack(side="left", padx=4)

        self.msg_var = tk.StringVar(value="")

# Big, obvious message banner at the bottom
        self.msg_label = tk.Label(
            bottom,
            textvariable=self.msg_var,
            fg="red",           # text color
            bg="yellow",        # background highlight
            font=("Arial", 11, "bold"),
            anchor="w",
            padx=8,
            pady=2
        )
        self.msg_label.pack(side="left", fill="x", expand=True, padx=10)


        # ---- Game state ----
        self.board = [[EMPTY] * self.N for _ in range(self.N)]
        self.cell_size = 50

        self.green_camp = set()
        self.red_camp = set()

        self.current_player = GREEN  # GREEN starts
        self.selected = None          # (r, c) or None
        self.jump_origin = None       # starting square for chain
        self.has_jumped_this_turn = False
        self.game_over = False

        # Highlights and drawing bookkeeping
        self.piece_ids = {}           # (r,c) -> oval id
        self.highlight_ids = []       # move highlight rectangles
        self.sel_id = None            # selected piece outline
        self.last_move_ids = []       # rectangles showing last move per color
        self.last_move_by_color = {GREEN: None, RED: None}  # ((r0,c0),(r1,c1))

        # Scores
        self.score_green = 0.0
        self.score_red = 0.0

        # Timer
        self.time_left = self.move_time_limit
        self.timer_id = None
        self.turn_start_time = time.time()

        # Setup board & camps
        self._init_camps_and_pieces()
        self._compute_cell_size()
        self._redraw_board()
        self._update_scores()
        self._update_status("Game started. GREEN to move.")
        self._start_timer()

    # ------------------------ Board / Camps Setup ------------------------

    def _camp_size_for(self, N):
        return {8: 4, 10: 5, 16: 6}.get(N, 4)

    def _init_camps_and_pieces(self):
        """Initialize green and red camps and starting pieces."""
        self.board = [[EMPTY] * self.N for _ in range(self.N)]
        self.green_camp.clear()
        self.red_camp.clear()

        camp = self._camp_size_for(self.N)

        # Green camp: top-left triangle
        for r in range(camp):
            for c in range(camp - r):
                self.green_camp.add((r, c))

        # Red camp: bottom-right triangle (mirror)
        for (r, c) in list(self.green_camp):
            rr = self.N - 1 - r
            cc = self.N - 1 - c
            self.red_camp.add((rr, cc))

        # Place pieces: GREEN at top-left camp, RED at bottom-right camp
        for (r, c) in self.green_camp:
            self.board[r][c] = GREEN
        for (r, c) in self.red_camp:
            self.board[r][c] = RED

    # ------------------------ Drawing ------------------------

    def _compute_cell_size(self):
        w = max(1, self.canvas.winfo_width() - 2 * BOARD_MARGIN)
        h = max(1, self.canvas.winfo_height() - 2 * BOARD_MARGIN)
        self.cell_size = int(min(w, h) / max(1, self.N))

    def _on_resize(self, _evt):
        self._compute_cell_size()
        self._redraw_board()

    def _redraw_board(self):
        self.canvas.delete("all")
        self.piece_ids.clear()
        self.highlight_ids.clear()
        self.sel_id = None
        self.last_move_ids.clear()

        self._draw_grid_and_labels()
        self._draw_all_pieces()
        self._draw_last_moves()
        if self.selected is not None:
            self._draw_selection_outline(*self.selected)
            self._show_highlights_for_selected()

    def _board_to_pixel_rect(self, r, c):
        cs = self.cell_size
        x0 = BOARD_MARGIN + c * cs
        y0 = BOARD_MARGIN + r * cs
        x1 = x0 + cs
        y1 = y0 + cs
        return x0, y0, x1, y1

    def _draw_grid_and_labels(self):
        cs = self.cell_size
        N = self.N

        # Grid
        for r in range(N):
            for c in range(N):
                x0, y0, x1, y1 = self._board_to_pixel_rect(r, c)
                self.canvas.create_rectangle(x0, y0, x1, y1, outline=GRID_COLOR, fill="")

        # Row numbers (1..N) on left
        for r in range(N):
            x = BOARD_MARGIN - 15
            y = BOARD_MARGIN + r * cs + cs / 2
            self.canvas.create_text(x, y, text=str(r + 1), anchor="e", font=("Arial", 9))

        # Column letters on top
        for c in range(N):
            x = BOARD_MARGIN + c * cs + cs / 2
            y = BOARD_MARGIN - 15
            self.canvas.create_text(x, y, text=col_to_letter(c), anchor="s", font=("Arial", 9))

    def _draw_piece(self, r, c):
        val = self.board[r][c]
        if val == EMPTY:
            return
        x0, y0, x1, y1 = self._board_to_pixel_rect(r, c)
        if val == GREEN:
            fill = "green"
        else:
            fill = "red"
        oval_id = self.canvas.create_oval(
            x0 + CELL_PAD, y0 + CELL_PAD,
            x1 - CELL_PAD, y1 - CELL_PAD,
            fill=fill, outline="black", width=1
        )
        self.piece_ids[(r, c)] = oval_id

    def _draw_all_pieces(self):
        for r in range(self.N):
            for c in range(self.N):
                if self.board[r][c] != EMPTY:
                    self._draw_piece(r, c)

    def _clear_highlights(self):
        for hid in self.highlight_ids:
            self.canvas.delete(hid)
        self.highlight_ids.clear()

    def _draw_highlight(self, r, c, color, width=3):
        x0, y0, x1, y1 = self._board_to_pixel_rect(r, c)
        rid = self.canvas.create_rectangle(
            x0 + 3, y0 + 3, x1 - 3, y1 - 3,
            outline=color, width=width
        )
        self.highlight_ids.append(rid)

    def _draw_selection_outline(self, r, c):
        if self.sel_id is not None:
            self.canvas.delete(self.sel_id)
            self.sel_id = None
        x0, y0, x1, y1 = self._board_to_pixel_rect(r, c)
        pad = 4
        self.sel_id = self.canvas.create_rectangle(
            x0 + pad, y0 + pad, x1 - pad, y1 - pad,
            outline=SEL_OUTLINE, width=3
        )

    def _draw_last_moves(self):
        """Draw subtle backgrounds for last moves of each color."""
        for mid in self.last_move_ids:
            self.canvas.delete(mid)
        self.last_move_ids.clear()

        for color, mv in self.last_move_by_color.items():
            if mv is None:
                continue
            (r0, c0), (r1, c1) = mv
            shade = LAST_MOVE_GREEN if color == GREEN else LAST_MOVE_RED
            for (rr, cc) in [(r0, c0), (r1, c1)]:
                x0, y0, x1, y1 = self._board_to_pixel_rect(rr, cc)
                mid = self.canvas.create_rectangle(
                    x0, y0, x1, y1,
                    outline="", fill=shade
                )
                self.last_move_ids.append(mid)
        # Redraw pieces on top
        self._draw_all_pieces()

    # ------------------------ Status & Timer ------------------------

    def _update_scores(self):
        self.score_green = self._compute_score_for_color(GREEN)
        self.score_red = self._compute_score_for_color(RED)

    def _compute_score_for_color(self, color):
        """Pieces in opponent camp: 1 point each.
           Others: 1 / (1 + distance_to_nearest_goal_square)."""
        if color == GREEN:
            goal_camp = self.red_camp
        else:
            goal_camp = self.green_camp

        camp_list = list(goal_camp)
        score = 0.0
        for r in range(self.N):
            for c in range(self.N):
                if self.board[r][c] != color:
                    continue
                if (r, c) in goal_camp:
                    score += 1.0
                else:
                    # distance to nearest goal camp square
                    if not camp_list:
                        continue
                    d = min(euclidean_distance((r, c), g) for g in camp_list)
                    score += 1.0 / (1.0 + d)
        return score

    # def _update_status(self, msg=""):
    #     self._update_scores()
    #     player_name = COLOR_TO_NAME[self.current_player]
    #     time_left_str = f"{self.time_left:4.1f}s"
    #     status = (
    #         f"Player: {player_name}  |  "
    #         f"Time left: {time_left_str}  |  "
    #         f"Scores - GREEN: {self.score_green:.2f}, RED: {self.score_red:.2f}"
    #     )
    #     if self.human_color_label in ("GREEN", "RED"):
    #         status += f"  |  You are: {self.human_color_label}"
    #     if msg:
    #         status += f"  |  {msg}"
    #     self.status_label.config(text=status)
    #     self.msg_var.set(msg)

    # def _update_status(self, msg=None):
    #     """
    #     Update top status bar and bottom message label.

    #     - If msg is not None: set and timestamp the message.
    #     - If msg is None: keep showing the last message until it has
    #       been visible for ~3 seconds, then clear it automatically.
    #     """
    #     now = time.time()

    #     # Update stored message if a new one is provided
    #     if msg is not None:
    #         self.last_msg = msg
    #         self.last_msg_time = now
    #     else:
    #         # Auto-clear message after 3 seconds
    #         if self.last_msg and (now - self.last_msg_time > 3.0):
    #             self.last_msg = ""

    #     # Build status text
    #     self._update_scores()
    #     player_name = COLOR_TO_NAME[self.current_player]
    #     time_left_str = f"{self.time_left:4.1f}s"
    #     status = (
    #         f"Player: {player_name}  |  "
    #         f"Time left: {time_left_str}  |  "
    #         f"Scores - GREEN: {self.score_green:.2f}, RED: {self.score_red:.2f}"
    #     )
    #     if self.human_color_label in ("GREEN", "RED"):
    #         status += f"  |  You are: {self.human_color_label}"
    #     if self.last_msg:
    #         status += f"  |  {self.last_msg}"

    #     self.status_label.config(text=status)
    #     self.msg_var.set(self.last_msg)

    def _update_status(self, msg=None):
        """
        Update top status bar and bottom message label.

        - If msg is not None: set and timestamp the message.
        - If msg is None: keep showing the last message until it has
          been visible for ~3 seconds, then clear it automatically.
        """
        now = time.time()

        # Update stored message if a new one is provided
        if msg is not None:
            self.last_msg = msg
            self.last_msg_time = now
        else:
            # Auto-clear message after 3 seconds
            if self.last_msg and (now - self.last_msg_time > 3.0):
                self.last_msg = ""

        # Build status text (NO message here)
        self._update_scores()
        player_name = COLOR_TO_NAME[self.current_player]
        time_left_str = f"{self.time_left:4.1f}s"
        status = (
            f"Player: {player_name}  |  "
            f"Time left: {time_left_str}  |  "
            f"Scores - GREEN: {self.score_green:.2f}, RED: {self.score_red:.2f}"
        )
        if self.human_color_label in ("GREEN", "RED"):
            status += f"  |  You are: {self.human_color_label}"

        # Apply to widgets
        self.status_label.config(text=status)
        self.msg_var.set(self.last_msg)

    def _start_timer(self):
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
        self.time_left = self.move_time_limit
        self.turn_start_time = time.time()
        self._tick_timer()

    def _tick_timer(self):
        if self.game_over:
            return
        elapsed = time.time() - self.turn_start_time
        self.time_left = max(0.0, self.move_time_limit - elapsed)
        self._update_status()
        if self.time_left <= 0.0:
            self._handle_timeout()
            return
        self.timer_id = self.root.after(100, self._tick_timer)

    # def _handle_timeout(self):
    #     if self.game_over:
    #         return
    #     # Current player loses on timeout
    #     loser = self.current_player
    #     winner = GREEN if loser == RED else RED
    #     self.game_over = True
    #     self._update_scores()
    #     self._update_status(f"Time out! {COLOR_TO_NAME[loser]} forfeits.")
    #     msg = (
    #         f"{COLOR_TO_NAME[loser]} ran out of time.\n"
    #         f"{COLOR_TO_NAME[winner]} wins by forfeit.\n\n"
    #         f"Final scores:\n"
    #         f"  GREEN: {self.score_green:.2f}\n"
    #         f"  RED:   {self.score_red:.2f}"
    #     )
    #     messagebox.showinfo("Time Out", msg)

    def restart_game(self):
        """Reset the entire game state to the initial setup."""
        # Stop any running timer first
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

        # Reset flags
        self.game_over = False
        self.current_player = GREEN  # GREEN always starts
        self.selected = None
        self.jump_origin = None
        self.has_jumped_this_turn = False

        # Clear last moves
        self.last_move_by_color = {GREEN: None, RED: None}
        self.last_move_ids.clear()

        # Clear text move entry (if it exists)
        if hasattr(self, "move_entry"):
            self.move_entry.delete(0, tk.END)

        # Reset message state
        self.last_msg = ""
        self.last_msg_time = 0.0

        # Reinitialize board
        self._init_camps_and_pieces()
        self._compute_cell_size()
        self._redraw_board()
        self._update_scores()

        # Start again
        self._update_status("Game restarted. GREEN to move.")
        self._start_timer()


    def _handle_timeout(self):
        if self.game_over:
            return
        # Current player loses on timeout
        loser = self.current_player
        winner = GREEN if loser == RED else RED
        self.game_over = True

        # Stop timer completely
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

        self._update_scores()
        self._update_status(f"Time out! {COLOR_TO_NAME[loser]} forfeits.")

        msg = (
            f"{COLOR_TO_NAME[loser]} ran out of time.\n"
            f"{COLOR_TO_NAME[winner]} wins by forfeit.\n\n"
            f"Final scores:\n"
            f"  GREEN: {self.score_green:.2f}\n"
            f"  RED:   {self.score_red:.2f}\n\n"
            "Would you like to restart the game?"
        )

        restart = messagebox.askyesno("Time Out", msg)
        if restart:
            self.restart_game()


    # ------------------------ Event Handling ------------------------

    def _pixel_to_board(self, x, y):
        cs = self.cell_size
        if x < BOARD_MARGIN or y < BOARD_MARGIN:
            return None
        c = (x - BOARD_MARGIN) // cs
        r = (y - BOARD_MARGIN) // cs
        if 0 <= r < self.N and 0 <= c < self.N:
            return int(r), int(c)
        return None

    def on_canvas_click(self, event):
        if self.game_over:
            return
        pos = self._pixel_to_board(event.x, event.y)
        if pos is None:
            return
        r, c = pos

        # If we are mid-jump and user clicks the selected piece again -> end turn
        if self.selected is not None and (r, c) == self.selected and self.has_jumped_this_turn:
            self._finish_turn()
            return

        # Normal click handling
        if self.selected is None:
            # Select a piece
            if self.board[r][c] == self.current_player:
                self._select_piece((r, c))
            else:
                self._update_status("Click one of your own pieces.")
        else:
            # We have a selected piece; attempt to move
            if (r, c) == self.selected:
                # Deselect if no jumps have been made
                self._clear_selection()
                return

            adj, jump = self._legal_moves_for_current_player(self.selected)
            if (r, c) in adj or (r, c) in jump:
                is_jump = (r, c) in jump
                self._perform_move(self.selected, (r, c), is_jump=is_jump)
            else:
                # Clicking another of your own pieces while not in jump chain
                if self.board[r][c] == self.current_player and not self.has_jumped_this_turn:
                    self._select_piece((r, c))
                else:
                    if self.has_jumped_this_turn:
                        self._update_status("Finish your jump chain or click the piece again to end your move.")
                    else:
                        reason = self._explain_illegal_move(self.current_player, self.selected, (r, c))
                        self._update_status(reason)

    def on_text_move(self):
        """Handle text input like 'a3->b4'. Supports single-step or single jump."""
        if self.game_over:
            return
        raw = self.move_entry.get().strip()
        if not raw:
            return
        try:
            parts = raw.split("->")
            if len(parts) != 2:
                raise ValueError
            src_str, dst_str = parts[0].strip(), parts[1].strip()
            c1 = letter_to_col(src_str[0])
            r1 = int(src_str[1:]) - 1
            c2 = letter_to_col(dst_str[0])
            r2 = int(dst_str[1:]) - 1
        except Exception:
            self._update_status("Invalid text move format. Use like 'a3->b4'.")
            return

        if not (0 <= r1 < self.N and 0 <= c1 < self.N and 0 <= r2 < self.N and 0 <= c2 < self.N):
            self._update_status("Move coordinates out of bounds.")
            return

        if self.board[r1][c1] != self.current_player:
            self._update_status("You must move your own piece.")
            return

        # Text moves: allow only single-step or single-jump (for simplicity)
        adj, jump = self._legal_moves_for_current_player((r1, c1), for_chain=False)
        dst = (r2, c2)
        if dst not in adj and dst not in jump:
            self._update_status("Illegal move for this piece (text moves support single-step or single-jump only).")
            return

        is_jump = dst in jump
        self.selected = (r1, c1)
        self.jump_origin = (r1, c1)
        self.has_jumped_this_turn = is_jump
        self._perform_move((r1, c1), dst, is_jump=is_jump, from_text=True)

    # ------------------------ Selection & Move Execution ------------------------

    def _select_piece(self, rc):
        self.selected = rc
        self.jump_origin = rc
        self.has_jumped_this_turn = False
        self._clear_highlights()
        self._draw_selection_outline(*rc)
        self._show_highlights_for_selected()
        self._update_status(f"Selected piece at {self._coord_to_label(rc)}.")

    def _clear_selection(self):
        self.selected = None
        self.jump_origin = None
        self.has_jumped_this_turn = False
        if self.sel_id is not None:
            self.canvas.delete(self.sel_id)
            self.sel_id = None
        self._clear_highlights()
        self._update_status("")

    def _show_highlights_for_selected(self):
        if self.selected is None:
            return
        adj, jump = self._legal_moves_for_current_player(self.selected)
        for rc in adj:
            self._draw_highlight(*rc, MOVE_HILITE_ADJ)
        for rc in jump:
            self._draw_highlight(*rc, MOVE_HILITE_JUMP)

    def _perform_move(self, src, dst, is_jump=False, from_text=False):
        """Actually move a piece after verifying legality."""
        if self.game_over:
            return

        sr, sc = src
        dr, dc = dst

        # Model update
        color = self.board[sr][sc]
        self.board[sr][sc] = EMPTY
        self.board[dr][dc] = color

        # Update last move info BEFORE redraw
        self.last_move_by_color[color] = (src, dst)

        # Redraw pieces + last-move highlights
        self._redraw_board()

        if is_jump:
            self.has_jumped_this_turn = True
        else:
            self.has_jumped_this_turn = False

        # After a jump, player may continue jumping or stop.
        if is_jump and not from_text:
            self.selected = (dr, dc)
            # Keep same jump_origin
            self._clear_highlights()
            self._draw_selection_outline(dr, dc)
            adj, jump = self._legal_moves_for_current_player((dr, dc), in_jump_chain=True)
            # Only allow further jumps in mid-chain
            for rc in jump:
                self._draw_highlight(*rc, MOVE_HILITE_JUMP)
            if not jump:
                # No further jumps; turn ends
                self._finish_turn()
            else:
                self._update_status("Jump made. You may continue jumping, or click the piece again to end your move.")
        else:
            # Single-step or text-initiated move
            self._finish_turn()

    

    def _finish_turn(self):
        """Called when a player's move is done (after jumps or step)."""
        self._clear_selection()
        self._update_scores()
        winner = self._check_for_win()
        if winner is not None:
            self._handle_win(winner)
            return
        # Switch player
        self.current_player = GREEN if self.current_player == RED else RED
        self._update_status(f"{COLOR_TO_NAME[self.current_player]} to move.")
        self._start_timer()

    # ------------------------ Move Generation & Rules ------------------------

    def _neighbors8(self, r, c):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = r + dr, c + dc
                if 0 <= rr < self.N and 0 <= cc < self.N:
                    yield rr, cc

    def _adjacent_moves(self, r, c):
        moves = set()
        for (rr, cc) in self._neighbors8(r, c):
            if self.board[rr][cc] == EMPTY:
                moves.add((rr, cc))
        return moves

    def _jump_moves(self, r, c, origin):
        """Return all landing squares reachable via jumps, excluding origin (no-return rule)."""
        N = self.N
        visited_landings = set()

        def dfs(pr, pc, seen):
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    mid_r, mid_c = pr + dr, pc + dc
                    land_r, land_c = pr + 2 * dr, pc + 2 * dc
                    if not (0 <= mid_r < N and 0 <= mid_c < N):
                        continue
                    if not (0 <= land_r < N and 0 <= land_c < N):
                        continue
                    if self.board[mid_r][mid_c] != EMPTY and self.board[land_r][land_c] == EMPTY:
                        landing = (land_r, land_c)
                        if landing == origin:
                            # no-return rule
                            continue
                        if landing not in seen:
                            visited_landings.add(landing)
                            dfs(land_r, land_c, seen | {landing})

        dfs(r, c, set())
        return visited_landings

    def _dist_to_goal(self, rc, color):
        if color == GREEN:
            goal_camp = self.red_camp
        else:
            goal_camp = self.green_camp
        if not goal_camp:
            return 0.0
        return min(euclidean_distance(rc, g) for g in goal_camp)

    def _in_home_camp(self, rc, color):
        if color == GREEN:
            return rc in self.green_camp
        else:
            return rc in self.red_camp

    def _in_opponent_camp(self, rc, color):
        if color == GREEN:
            return rc in self.red_camp
        else:
            return rc in self.green_camp

    def _move_respects_rules(self, color, src, dst):
        """Apply blocking rule, progress rule, and no-leaving-opponent-camp rule."""
        # Can't move into an occupied square (already ensured earlier)
        if self.board[dst[0]][dst[1]] != EMPTY:
            return False

        # Can't leave opponent camp once inside
        if self._in_opponent_camp(src, color) and not self._in_opponent_camp(dst, color):
            return False

        d0 = self._dist_to_goal(src, color)
        d1 = self._dist_to_goal(dst, color)

        # In own camp: must strictly reduce distance (blocking rule)
        if self._in_home_camp(src, color):
            if d1 >= d0:
                return False

        # Outside own camp: cannot move away (allow equal or closer)
        if not self._in_home_camp(src, color):
            if d1 > d0:
                return False

        return True

    def _explain_illegal_move(self, color, src, dst):
        """Return a human-readable reason why a move is illegal, if we can infer it."""
        r2, c2 = dst

        # 1) Outside board
        if not (0 <= r2 < self.N and 0 <= c2 < self.N):
            return "That square is outside the board."

        # 2) Destination occupied
        if self.board[r2][c2] != EMPTY:
            return "You cannot move onto an occupied square."

        # 3) Can't leave opponent camp once inside
        if self._in_opponent_camp(src, color) and not self._in_opponent_camp(dst, color):
            return "Once a piece enters the opponent's camp, it cannot leave."

        # 4) Distance / progress rules
        d0 = self._dist_to_goal(src, color)
        d1 = self._dist_to_goal(dst, color)

        # Blocking rule: inside home camp must strictly reduce distance
        if self._in_home_camp(src, color) and d1 >= d0:
            return "Blocking rule: in your home camp you must move closer to the opponent's camp."

        # Outside home camp: cannot move farther away
        if (not self._in_home_camp(src, color)) and d1 > d0:
            return "You cannot move farther away from the opponent's camp."

        # 5) Fallback: probably not a valid step/jump pattern
        return "That move does not follow the step/jump rules for Halma."


    def _legal_moves_for_current_player(self, rc, in_jump_chain=False, for_chain=True):
        """Return (adjacent_moves, jump_moves) for currently selected piece.

        - in_jump_chain=True: only jumps allowed; starting point is current rc but
          origin of chain is self.jump_origin.
        - for_chain=False used for text moves basic check.
        """
        r, c = rc
        color = self.board[r][c]
        if color != self.current_player:
            return set(), set()

        origin = self.jump_origin if self.jump_origin is not None else rc

        adj_raw = self._adjacent_moves(r, c)
        jump_raw = self._jump_moves(r, c, origin)

        adj = set()
        jump = set()

        # Filter by game rules
        for dst in adj_raw:
            if self._move_respects_rules(color, rc, dst):
                adj.add(dst)
        for dst in jump_raw:
            if self._move_respects_rules(color, rc, dst):
                jump.add(dst)

        # If we are in a jump chain, no adjacent moves allowed
        if in_jump_chain:
            adj.clear()

        # for text-move legality check, we don't care about chain state
        if not for_chain:
            return adj, jump

        return adj, jump

    # ------------------------ Win Detection ------------------------

    def _check_for_win(self):
        """Return GREEN, RED, or None for no winner yet."""
        # Win: a player occupies every square in the opponent’s camp
        # Green wins if every red camp square is occupied by GREEN
        green_win = all(self.board[r][c] == GREEN for (r, c) in self.red_camp)
        red_win = all(self.board[r][c] == RED for (r, c) in self.green_camp)
        if green_win and not red_win:
            return GREEN
        if red_win and not green_win:
            return RED
        # If both somehow true, treat as draw (not expected)
        return None

    def _handle_win(self, winner):
        self.game_over = True
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        self._update_scores()
        self._update_status(f"{COLOR_TO_NAME[winner]} wins!")

        # msg = (
        #     f"{COLOR_TO_NAME[winner]} has occupied the opponent's camp.\n\n"
        #     f"Final scores:\n"
        #     f"  GREEN: {self.score_green:.2f}\n"
        #     f"  RED:   {self.score_red:.2f}"
        # )
        # messagebox.showinfo("Game Over", msg)
        msg = (
            f"{COLOR_TO_NAME[winner]} has occupied the opponent's camp.\n\n"
            f"Final scores:\n"
            f"  GREEN: {self.score_green:.2f}\n"
            f"  RED:   {self.score_red:.2f}\n\n"
            "Would you like to restart the game?"
        )

        restart = messagebox.askyesno("Game Over", msg)

        if restart:
            self.restart_game()


    # ------------------------ Helper ------------------------

    def _coord_to_label(self, rc):
        r, c = rc
        return f"{col_to_letter(c)}{r + 1}"


# ------------------------ App Wrapper ------------------------

class HalmaApp:
    def __init__(self, board_size=8, move_time_limit=10, human_color="GREEN"):
        self.root = tk.Tk()
        self.board = HalmaBoard(
            self.root,
            board_size=board_size,
            move_time_limit=move_time_limit,
            human_color=human_color,
        )

    def run(self):
        self.root.minsize(600, 600)
        self.root.mainloop()


# ------------------------ Main ------------------------

def parse_args(argv):
    parser = argparse.ArgumentParser(description="Halma Part 1 – Two-Player Tkinter Game")
    parser.add_argument(
        "-s", "--size", type=int, default=8,
        help="Board size: 8, 10, or 16 (default 8)"
    )
    parser.add_argument(
        "-t", "--limit", type=float, default=10.0,
        help="Move time limit in seconds (default 10)"
    )
    parser.add_argument(
        "-c", "--human", type=str, default="GREEN",
        help="Human player color label for status bar: GREEN or RED (default GREEN)"
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    # args = parse_args(sys.argv[1:])
    args = parse_args(sys.argv[1:])
    if args.size not in (8, 10, 16):
        print("Board size must be 8, 10, or 16. Using default 8.")
        args.size = 8
    human_color = args.human.upper()
    if human_color not in ("GREEN", "RED"):
        print("Human color must be GREEN or RED. Using GREEN.")
        human_color = "GREEN"

    app = HalmaApp(board_size=args.size, move_time_limit=args.limit, human_color=human_color)
    app.run()

