import flet as ft
import random
from collections import deque

def main(page: ft.Page):
    # ตั้งค่าหน้าตาแอปพลิเคชัน (UI/UX)
    page.title = "Minesweeper"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#1E1E2E" # สีพื้นหลัง
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO

    # [State Management]: เก็บสถานะเกมทั้งหมดไว้ตรงกลาง เพื่อให้จัดการง่าย
    game = {
        "ROWS": 9, "COLS": 9, "MINES": 10,
        "grid": [], "revealed": [], "flags": [], "buttons": [],
        "is_game_over": False, "first_click": True, "revealed_count": 0
    }

    board = ft.GridView(expand=False, spacing=4, run_spacing=4, child_aspect_ratio=1.0)

    # -----------------------------------------
    # 1. ฟังก์ชันวางระเบิด (First-Click Safe)
    # -----------------------------------------
    def place_mines(first_r, first_c):
        # สร้างพื้นที่ปลอดภัย 3x3 รอบจุดที่คลิกครั้งแรก เพื่อไม่ให้ผู้เล่นตายตั้งแต่เริ่ม
        r, c, m = game["ROWS"], game["COLS"], game["MINES"]
        safe_zone = [(first_r + dr, first_c + dc) for dr in [-1, 0, 1] for dc in [-1, 0, 1]]
        
        placed = 0
        while placed < m:
            rr, cc = random.randint(0, r - 1), random.randint(0, c - 1)
            # สุ่มวางระเบิด (-1) ในช่องที่ยังไม่มีระเบิด และไม่อยู่ในพื้นที่ปลอดภัย
            if game["grid"][rr][cc] != -1 and (rr, cc) not in safe_zone:
                game["grid"][rr][cc] = -1
                placed += 1
                # บวกตัวเลขใบ้ (1-8) ให้กับช่องรอบๆ ระเบิด
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        nr, nc = rr + dr, cc + dc
                        if 0 <= nr < r and 0 <= nc < c and game["grid"][nr][nc] != -1:
                            game["grid"][nr][nc] += 1

    # -----------------------------------------
    # 2. ฟังก์ชันเปิดพื้นที่ว่างต่อเนื่อง (BFS Queue)
    # -----------------------------------------
    def flood_fill_bfs(start_r, start_c):
        # ถ้าคลิกโดนระเบิด
        if game["grid"][start_r][start_c] == -1:
            idx = start_r * game["COLS"] + start_c
            btn = game["buttons"][idx]
            btn.content.value = "💣"
            btn.bgcolor = "#F38BA8" # สีแดง
            return True 

        # เริ่มต้นคิว (Queue) นำช่องแรกเข้าคิว
        queue = deque([(start_r, start_c)])
        
        while queue:
            curr_r, curr_c = queue.popleft() # ดึงช่องหัวคิวออกมาประมวลผล
            
            # เช็กว่าทะลุขอบกระดาน หรือช่องนั้นเคยเปิด/ปักธงไปหรือยัง
            if curr_r < 0 or curr_r >= game["ROWS"] or curr_c < 0 or curr_c >= game["COLS"]: continue
            if game["revealed"][curr_r][curr_c] or game["flags"][curr_r][curr_c]: continue

            # อัปเดตสถานะว่าเปิดแล้ว และเพิ่มคะแนน
            game["revealed"][curr_r][curr_c] = True
            game["revealed_count"] += 1
            
            idx = curr_r * game["COLS"] + curr_c
            btn = game["buttons"][idx]
            btn.disabled = True
            btn.bgcolor = "#313244" # เปลี่ยนสีเป็นช่องที่ถูกเปิดแล้ว

            val = game["grid"][curr_r][curr_c]
            if val > 0:
                # ถ้าเป็นตัวเลข ให้แสดงเลขและใส่สีตามตัวเลข
                btn.content.value = str(val)
                colors = ["", "#89B4FA", "#A6E3A1", "#F38BA8", "#CBA6F7", "#FAB387", "#94E2D5", "white", "gray"]
                btn.content.color = colors[val] if val < len(colors) else "#F9E2AF"
            elif val == 0:
                # ถ้าเป็นช่องว่างเปล่า (0) ให้นำช่องรอบๆ ทั้ง 8 ทิศ ต่อท้ายคิวเพื่อรอเปิดขยายต่อไป
                btn.content.value = " "
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        queue.append((curr_r + dr, curr_c + dc))
        return False

    # -----------------------------------------
    # 3. ฟังก์ชันตรวจสอบชัยชนะ (Win Condition)
    # -----------------------------------------
    def check_win():
        # ถ้าจำนวนช่องที่เปิดได้ เท่ากับ (ช่องทั้งหมด ลบ จำนวนระเบิด) แปลว่าชนะ
        total_safe = (game["ROWS"] * game["COLS"]) - game["MINES"]
        if game["revealed_count"] == total_safe:
            game["is_game_over"] = True
            status_text.value = "🏆 ภารกิจสำเร็จ!"
            status_text.color = "#A6E3A1"

    # -----------------------------------------
    # 4. ฟังก์ชันแสดงระเบิดทั้งหมดเมื่อแพ้ (Game Over)
    # -----------------------------------------
    def show_all_mines():
        for rr in range(game["ROWS"]):
            for cc in range(game["COLS"]):
                if game["grid"][rr][cc] == -1:
                    idx = rr * game["COLS"] + cc
                    game["buttons"][idx].content.value = "💣"
                    game["buttons"][idx].bgcolor = "#F38BA8"
        status_text.value = "💥 ระเบิดทำงาน!"
        status_text.color = "#F38BA8"

    # -----------------------------------------
    # 5. ฟังก์ชันจัดการการคลิก (เปิดช่อง)
    # -----------------------------------------
    def button_click(e):
        if game["is_game_over"]: return
        rr, cc = e.control.data
        if game["flags"][rr][cc]: return # ถ้าปักธงอยู่ห้ามกดโดน

        # ถ้าเป็นการคลิกครั้งแรกของเกม ค่อยเรียกฟังก์ชันวางระเบิด
        if game["first_click"]:
            place_mines(rr, cc)
            game["first_click"] = False

        # เรียกใช้ BFS เพื่อเปิดช่อง
        if flood_fill_bfs(rr, cc):
            game["is_game_over"] = True
            show_all_mines()
        else:
            check_win()
        page.update()

    # -----------------------------------------
    # 6. ฟังก์ชันจัดการการกดค้าง (ปักธง)
    # -----------------------------------------
    def button_right_click(e):
        if game["is_game_over"]: return
        rr, cc = e.control.data
        if not game["revealed"][rr][cc]:
            game["flags"][rr][cc] = not game["flags"][rr][cc] # สลับสถานะธง
            e.control.content.value = "🚩" if game["flags"][rr][cc] else " "
            e.control.content.color = "#F38BA8"
            page.update()

    # -----------------------------------------
    # 7. ฟังก์ชันเริ่มเกมใหม่และสร้างกระดาน
    # -----------------------------------------
    def start_game(e=None):
        # เลือกระดับความยากจาก Dropdown
        diff = dropdown_diff.value
        if "ง่าย" in diff: game.update({"ROWS": 9, "COLS": 9, "MINES": 10})
        elif "ปานกลาง" in diff: game.update({"ROWS": 16, "COLS": 16, "MINES": 40})
        
        # รีเซ็ตตัวแปรสถานะ
        game["is_game_over"] = False
        game["first_click"] = True
        game["revealed_count"] = 0
        
        # สร้าง Array 2D ว่างๆ
        game["grid"] = [[0 for _ in range(game["COLS"])] for _ in range(game["ROWS"])]
        game["revealed"] = [[False for _ in range(game["COLS"])] for _ in range(game["ROWS"])]
        game["flags"] = [[False for _ in range(game["COLS"])] for _ in range(game["ROWS"])]
        game["buttons"] = []

        board.runs_count = game["COLS"]
        board.width = 45 * game["COLS"]
        board.controls.clear()

        # สร้างปุ่ม UI ลงในกระดาน
        for rr in range(game["ROWS"]):
            for cc in range(game["COLS"]):
                btn = ft.Container(
                    content=ft.Text(" ", size=18, weight="bold"),
                    alignment=ft.alignment.center,
                    width=40, height=40,
                    bgcolor="#45475A",
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

    # --- ส่วนประกอบ UI ด้านบน ---
    dropdown_diff = ft.Dropdown(
        options=[
            ft.dropdown.Option("ง่าย (9x9, 10 💣)"),
            ft.dropdown.Option("ปานกลาง (16x16, 40 💣)"),
        ],
        value="ง่าย (9x9, 10 💣)", width=220, bgcolor="#313244", color="white"
    )
    
    status_text = ft.Text("", size=20, weight="bold")
    btn_restart = ft.ElevatedButton("🔄 เริ่มเกมใหม่", on_click=start_game, bgcolor="#89B4FA", color="#11111B")

    page.add(
        ft.Container(height=10),
        ft.Text("MINESWEEPER", size=32, weight="heavy", color="#89B4FA"),
        ft.Row([dropdown_diff, btn_restart], alignment=ft.MainAxisAlignment.CENTER),
        status_text,
        ft.Container(
            content=board, padding=10, bgcolor="#11111B", border_radius=15,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.BLACK54)
        ),
        ft.Text("แตะ: เปิด | กดค้าง: ปักธง 🚩", color="#A6ADC8", size=14)
    )
    start_game()

ft.app(target=main)