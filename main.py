import flet as ft
import random
from collections import deque
import traceback # เพิ่มโมดูลนี้เข้ามาเพื่อดักจับและอ่านข้อความ Error

def main(page: ft.Page):
    # --- เริ่มต้นบล็อกดักจับ Error (ถ้ามีอะไรพังในนี้ จะข้ามไปที่ except ด้านล่างสุด) ---
    try:
        # 1. ตั้งค่าหน้าตาแอปพลิเคชัน (UI/UX)
        page.title = "Minesweeper"
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = "#1E1E2E" # สีพื้นหลังธีม Dark
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.scroll = ft.ScrollMode.AUTO

        # 2. State Management: เก็บสถานะเกมทั้งหมดไว้ใน Dictionary เพื่อให้จัดการง่าย
        game = {
            "ROWS": 9, "COLS": 9, "MINES": 10,
            "grid": [], "revealed": [], "flags": [], "buttons": [],
            "is_game_over": False, "first_click": True, "revealed_count": 0
        }

        # สร้างกระดานเปล่าๆ รอก่อน
        board = ft.GridView(expand=False, spacing=4, run_spacing=4, child_aspect_ratio=1.0)

        # -----------------------------------------
        # ฟังก์ชัน 1: วางระเบิด (First-Click Safe)
        # -----------------------------------------
        def place_mines(first_r, first_c):
            # สร้างพื้นที่ปลอดภัย 3x3 รอบจุดที่คลิกครั้งแรก เพื่อไม่ให้ผู้เล่นแพ้ตั้งแต่เริ่ม
            r, c, m = game["ROWS"], game["COLS"], game["MINES"]
            safe_zone = [(first_r + dr, first_c + dc) for dr in [-1, 0, 1] for dc in [-1, 0, 1]]
            
            placed = 0
            while placed < m:
                # สุ่มตำแหน่งแถวและคอลัมน์
                rr, cc = random.randint(0, r - 1), random.randint(0, c - 1)
                # วางระเบิด (-1) ในช่องที่ยังไม่มีระเบิด และไม่อยู่ในเขตปลอดภัย
                if game["grid"][rr][cc] != -1 and (rr, cc) not in safe_zone:
                    game["grid"][rr][cc] = -1
                    placed += 1
                    # บวกตัวเลขคำใบ้ (1-8) ให้กับช่องที่อยู่รอบๆ ระเบิดลูกนี้
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            nr, nc = rr + dr, cc + dc
                            if 0 <= nr < r and 0 <= nc < c and game["grid"][nr][nc] != -1:
                                game["grid"][nr][nc] += 1

        # -----------------------------------------
        # ฟังก์ชัน 2: เปิดพื้นที่ว่างต่อเนื่องด้วย BFS Queue
        # -----------------------------------------
        def flood_fill_bfs(start_r, start_c):
            # ถ้าคลิกโดนระเบิด (ค่าเป็น -1) ส่งค่า True กลับไปเพื่อบอกว่าแพ้
            if game["grid"][start_r][start_c] == -1:
                idx = start_r * game["COLS"] + start_c
                btn = game["buttons"][idx]
                btn.content.value = "💣"
                btn.bgcolor = "#F38BA8"
                return True 

            # นำจุดที่คลิกเข้าคิวเพื่อเตรียมตรวจสอบ
            queue = deque([(start_r, start_c)])
            
            while queue:
                curr_r, curr_c = queue.popleft() # ดึงช่องหัวคิวออกมา
                
                # ข้ามช่องที่อยู่นอกกระดาน, ช่องที่เปิดไปแล้ว, หรือช่องที่ปักธงอยู่
                if curr_r < 0 or curr_r >= game["ROWS"] or curr_c < 0 or curr_c >= game["COLS"]: continue
                if game["revealed"][curr_r][curr_c] or game["flags"][curr_r][curr_c]: continue

                # อัปเดตสถานะว่าเปิดแล้ว
                game["revealed"][curr_r][curr_c] = True
                game["revealed_count"] += 1
                
                idx = curr_r * game["COLS"] + curr_c
                btn = game["buttons"][idx]
                btn.disabled = True
                btn.bgcolor = "#313244" # สีช่องที่ถูกเปิด

                val = game["grid"][curr_r][curr_c]
                if val > 0:
                    # ถ้าเป็นตัวเลข ให้แสดงเลขและใส่สีตามตัวเลขนั้นๆ
                    btn.content.value = str(val)
                    colors = ["", "#89B4FA", "#A6E3A1", "#F38BA8", "#CBA6F7", "#FAB387", "#94E2D5", "white", "gray"]
                    btn.content.color = colors[val] if val < len(colors) else "#F9E2AF"
                elif val == 0:
                    # ถ้าเป็นช่องว่าง (0) ให้นำช่องรอบๆ ทั้ง 8 ทิศ ต่อท้ายคิวเพื่อเปิดขยายต่อ
                    btn.content.value = " "
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            queue.append((curr_r + dr, curr_c + dc))
            return False

        # -----------------------------------------
        # ฟังก์ชัน 3: ตรวจสอบชัยชนะ (Win Condition)
        # -----------------------------------------
        def check_win():
            # ถ้าจำนวนช่องที่เปิด เท่ากับ ช่องที่ปลอดภัยทั้งหมด แปลว่าชนะ
            total_safe = (game["ROWS"] * game["COLS"]) - game["MINES"]
            if game["revealed_count"] == total_safe:
                game["is_game_over"] = True
                status_text.value = "🏆 ภารกิจสำเร็จ!"
                status_text.color = "#A6E3A1"

        # -----------------------------------------
        # ฟังก์ชัน 4: แสดงระเบิดทั้งหมดเมื่อแพ้
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
        # ฟังก์ชัน 5: จัดการเมื่อผู้เล่น "แตะ" เพื่อเปิดช่อง
        # -----------------------------------------
        def button_click(e):
            if game["is_game_over"]: return
            rr, cc = e.control.data
            if game["flags"][rr][cc]: return # ถ้าปักธงอยู่ห้ามกดโดน

            # แตะครั้งแรกของเกม ค่อยสุ่มวางระเบิด
            if game["first_click"]:
                place_mines(rr, cc)
                game["first_click"] = False

            # สั่งเปิดช่อง ถ้าคืนค่า True แปลว่าเหยียบระเบิด
            if flood_fill_bfs(rr, cc):
                game["is_game_over"] = True
                show_all_mines()
            else:
                check_win()
            page.update()

        # -----------------------------------------
        # ฟังก์ชัน 6: จัดการเมื่อผู้เล่น "กดค้าง" เพื่อปักธง
        # -----------------------------------------
        def button_right_click(e):
            if game["is_game_over"]: return
            rr, cc = e.control.data
            if not game["revealed"][rr][cc]:
                game["flags"][rr][cc] = not game["flags"][rr][cc]
                e.control.content.value = "🚩" if game["flags"][rr][cc] else " "
                e.control.content.color = "#F38BA8"
                page.update()

        # -----------------------------------------
        # ฟังก์ชัน 7: เริ่มเกมใหม่และสร้างกระดาน
        # -----------------------------------------
        def start_game(e=None):
            # อ่านค่าความยากจาก Dropdown
            diff = dropdown_diff.value
            if diff is not None:
                if "ง่าย" in diff: game.update({"ROWS": 9, "COLS": 9, "MINES": 10})
                elif "ปานกลาง" in diff: game.update({"ROWS": 16, "COLS": 16, "MINES": 40})
            
            game["is_game_over"] = False
            game["first_click"] = True
            game["revealed_count"] = 0
            
            # รีเซ็ตอาร์เรย์ 2 มิติทั้งหมด
            game["grid"] = [[0 for _ in range(game["COLS"])] for _ in range(game["ROWS"])]
            game["revealed"] = [[False for _ in range(game["COLS"])] for _ in range(game["ROWS"])]
            game["flags"] = [[False for _ in range(game["COLS"])] for _ in range(game["ROWS"])]
            game["buttons"] = []

            board.runs_count = game["COLS"]
            board.width = 45 * game["COLS"]
            board.controls.clear()

            # สร้างปุ่มลงใน Grid
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

        # --- ส่วนประกอบ UI เมนูด้านบน ---
        dropdown_diff = ft.Dropdown(
            options=[
                ft.dropdown.Option("ง่าย (9x9, 10 💣)"),
                ft.dropdown.Option("ปานกลาง (16x16, 40 💣)"),
            ],
            value="ง่าย (9x9, 10 💣)", width=220, bgcolor="#313244", color="white"
        )
        status_text = ft.Text("", size=20, weight="bold")
        btn_restart = ft.ElevatedButton("🔄 เริ่มเกมใหม่", on_click=start_game, bgcolor="#89B4FA", color="#11111B")

        # นำชิ้นส่วน UI ทั้งหมดมาต่อกันลงบนหน้าจอ
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
        
        # เรียกเริ่มเกมครั้งแรก
        start_game()

    # --- จบบล็อกตรวจสอบ Error ---
    except Exception as e:
        # หากโค้ดด้านบนมีปัญหาตอนรันบนมือถือ ให้พ่นข้อความ Error สีแดงออกมาแสดงแทนจอดำ
        error_msg = f"🚨 โค้ดมีปัญหา:\n{traceback.format_exc()}"
        page.add(
            ft.Container(
                content=ft.Text(error_msg, color="red", size=12, selectable=True),
                padding=20, bgcolor="black", border_radius=10, expand=True
            )
        )
        page.update()

# คำสั่งรันแอปพลิเคชัน (ใช้ main เพียวๆ เพื่อป้องกัน Error บนมือถือ)
ft.app(target=main)