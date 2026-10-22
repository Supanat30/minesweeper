import flet as ft
import random
from collections import deque

def main(page: ft.Page):
    # ตั้งค่าหน้าตาแอปพลิเคชันมือถือ
    page.title = "Minesweeper"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#1E1E2E" # สีพื้นหลังสไตล์ Catppuccin Macchiato
    page.window_width = 400
    page.window_height = 800
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO

    game = {
        "ROWS": 9, "COLS": 9, "MINES": 10,
        "grid": [], "revealed": [], "flags": [], "buttons": [],
        "is_game_over": False, "first_click": True, "revealed_count": 0
    }

    board = ft.GridView(expand=False, spacing=4, run_spacing=4, child_aspect_ratio=1.0)

    def place_mines(first_r, first_c):
        r, c, m = game["ROWS"], game["COLS"], game["MINES"]
        safe_zone = [(first_r + dr, first_c + dc) for dr in [-1, 0, 1] for dc in [-1, 0, 1]]
        
        placed = 0
        while placed < m:
            rr, cc = random.randint(0, r - 1), random.randint(0, c - 1)
            if game["grid"][rr][cc] != -1 and (rr, cc) not in safe_zone:
                game["grid"][rr][cc] = -1
                placed += 1
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        nr, nc = rr + dr, cc + dc
                        if 0 <= nr < r and 0 <= nc < c and game["grid"][nr][nc] != -1:
                            game["grid"][nr][nc] += 1

    def flood_fill_bfs(start_r, start_c):
        if game["grid"][start_r][start_c] == -1:
            idx = start_r * game["COLS"] + start_c
            btn = game["buttons"][idx]
            btn.content.value = "💣"
            btn.bgcolor = ft.colors.RED_400
            return True 

        queue = deque([(start_r, start_c)])
        while queue:
            curr_r, curr_c = queue.popleft()
            if curr_r < 0 or curr_r >= game["ROWS"] or curr_c < 0 or curr_c >= game["COLS"]: continue
            if game["revealed"][curr_r][curr_c] or game["flags"][curr_r][curr_c]: continue

            game["revealed"][curr_r][curr_c] = True
            game["revealed_count"] += 1
            
            idx = curr_r * game["COLS"] + curr_c
            btn = game["buttons"][idx]
            btn.disabled = True
            btn.bgcolor = "#313244" # สีช่องที่เปิดแล้ว

            val = game["grid"][curr_r][curr_c]
            if val > 0:
                btn.content.value = str(val)
                colors = ["", "#89B4FA", "#A6E3A1", "#F38BA8", "#CBA6F7", "#FAB387", "#94E2D5", "white", "gray"]
                btn.content.color = colors[val] if val < len(colors) else "#F9E2AF"
            elif val == 0:
                btn.content.value = " "
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        queue.append((curr_r + dr, curr_c + dc))
        return False

    def check_win():
        total_safe = (game["ROWS"] * game["COLS"]) - game["MINES"]
        if game["revealed_count"] == total_safe:
            game["is_game_over"] = True
            status_text.value = "🏆 ภารกิจสำเร็จ!"
            status_text.color = "#A6E3A1"

    def show_all_mines():
        for rr in range(game["ROWS"]):
            for cc in range(game["COLS"]):
                if game["grid"][rr][cc] == -1:
                    idx = rr * game["COLS"] + cc
                    game["buttons"][idx].content.value = "💣"
                    game["buttons"][idx].bgcolor = "#F38BA8"
        status_text.value = "💥 ระเบิดทำงาน!"
        status_text.color = "#F38BA8"

    def button_click(e):
        if game["is_game_over"]: return
        rr, cc = e.control.data
        if game["flags"][rr][cc]: return

        if game["first_click"]:
            place_mines(rr, cc)
            game["first_click"] = False

        if flood_fill_bfs(rr, cc):
            game["is_game_over"] = True
            show_all_mines()
        else:
            check_win()
        page.update()

    def button_right_click(e):
        if game["is_game_over"]: return
        rr, cc = e.control.data
        if not game["revealed"][rr][cc]:
            game["flags"][rr][cc] = not game["flags"][rr][cc]
            e.control.content.value = "🚩" if game["flags"][rr][cc] else " "
            e.control.content.color = "#F38BA8"
            page.update()

    def start_game(e=None):
        game["ROWS"], game["COLS"], game["MINES"] = 9, 9, 10
        game["is_game_over"] = False
        game["first_click"] = True
        game["revealed_count"] = 0
        game["grid"] = [[0 for _ in range(game["COLS"])] for _ in range(game["ROWS"])]
        game["revealed"] = [[False for _ in range(game["COLS"])] for _ in range(game["ROWS"])]
        game["flags"] = [[False for _ in range(game["COLS"])] for _ in range(game["ROWS"])]
        game["buttons"] = []

        board.runs_count = game["COLS"]
        board.width = 45 * game["COLS"]
        board.controls.clear()

        for rr in range(game["ROWS"]):
            for cc in range(game["COLS"]):
                # ใช้ Container เพื่อให้ปรับแต่ง UI ได้สวยงามกว่า Button ธรรมดา
                btn = ft.Container(
                    content=ft.Text(" ", size=18, weight="bold"),
                    alignment=ft.alignment.center,
                    width=40, height=40,
                    bgcolor="#45475A", # สีปุ่มที่ยังไม่เปิด
                    border_radius=8,
                    data=(rr, cc),
                    on_click=button_click,
                    on_long_press=button_right_click,
                )
                game["buttons"].append(btn)
                board.controls.append(btn)
        
        status_text.value = f"💣 ระเบิด: {game['MINES']} ลูก"
        status_text.color = "#BAC2DE"
        page.update()

    # สร้าง UI ส่วนบน
    status_text = ft.Text("", size=20, weight="bold")
    btn_restart = ft.ElevatedButton(
        "🔄 เริ่มเกมใหม่", 
        on_click=start_game, 
        bgcolor="#89B4FA", 
        color="#11111B",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )

    # ประกอบหน้าจอ
    page.add(
        ft.Container(height=20), # เว้นขอบจอบน
        ft.Text("MINESWEEPER", size=32, weight="heavy", color="#89B4FA"),
        status_text,
        ft.Container(
            content=board,
            padding=10,
            bgcolor="#11111B",
            border_radius=15,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.BLACK54)
        ),
        ft.Container(height=10),
        btn_restart,
        ft.Text("แตะ: เปิด | กดค้าง: ปักธง 🚩", color="#A6ADC8", size=14)
    )
    start_game()

# รันเป็นหน้าต่างแอปปกติ ไม่ต้องใช้ Web Server
ft.app(target=main)