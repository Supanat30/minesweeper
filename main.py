import flet as ft
import random
from collections import deque
import traceback # ใช้ดักจับ Error กรณีแอปจอดำ

def main(page: ft.Page):
    try:
        # -----------------------------------------
        # การตั้งค่าหน้าจอแอปพลิเคชัน (UI/UX)
        # ใช้เรื่อง: GUI (Graphical User Interface)
        # -----------------------------------------
        page.title = "Minesweeper"
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = "#1E1E2E"
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.scroll = ft.ScrollMode.AUTO

        # -----------------------------------------
        # State Management (ตัวแปรเก็บสถานะเกม)
        # ใช้เรื่อง: Dictionary และ Data Structure พื้นฐาน
        # ทำหน้าที่: เก็บข้อมูลสำคัญไว้ตรงกลางเพื่อให้ฟังก์ชันอื่นๆ ดึงไปใช้และแก้ไขได้ง่าย
        # -----------------------------------------
        game = {
            "ROWS": 9, "COLS": 9, "MINES": 10,
            "grid": [], "revealed": [], "flags": [], "buttons": [],
            "is_game_over": False, "first_click": True, "revealed_count": 0
        }

        board = ft.GridView(expand=False, spacing=4, run_spacing=4, child_aspect_ratio=1.0)

        # -----------------------------------------
        # ฟังก์ชันที่ 1: สุ่มวางระเบิดและทำตัวเลขคำใบ้ (First-Click Safe)
        # ใช้เรื่อง: Array 2D (อาร์เรย์ 2 มิติ), Random (สุ่มค่า), Loop
        # ทำหน้าที่: สุ่มวางระเบิดลงในตาราง โดยจะเว้นระยะ 3x3 รอบจุดที่ผู้เล่นคลิกครั้งแรก เพื่อไม่ให้แพ้ตั้งแต่เริ่ม
        # -----------------------------------------
        def place_mines(first_r, first_c):
            r, c, m = game["ROWS"], game["COLS"], game["MINES"]
            safe_zone = [(first_r + dr, first_c + dc) for dr in [-1, 0, 1] for dc in [-1, 0, 1]]
            
            placed = 0
            while placed < m:
                rr, cc = random.randint(0, r - 1), random.randint(0, c - 1)
                # ถ้ายางยังไม่มีระเบิด และไม่อยู่ในเขตปลอดภัย ให้วางระเบิด (-1)
                if game["grid"][rr][cc] != -1 and (rr, cc) not in safe_zone:
                    game["grid"][rr][cc] = -1
                    placed += 1
                    # คำนวณตัวเลขรอบๆ ระเบิด (1-8)
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            nr, nc = rr + dr, cc + dc
                            if 0 <= nr < r and 0 <= nc < c and game["grid"][nr][nc] != -1:
                                game["grid"][nr][nc] += 1

        # -----------------------------------------
        # ฟังก์ชันที่ 2: เปิดพื้นที่ว่างต่อเนื่อง (Flood Fill)
        # ใช้เรื่อง: อัลกอริทึม BFS (Breadth-First Search) และ Queue (คิว)
        # ทำหน้าที่: เมื่อคลิกโดนช่องว่าง (0) ระบบจะใช้คิวลามเปิดช่องว่างและตัวเลขรอบๆ ให้อัตโนมัติ (ป้องกันแอปค้าง)
        # -----------------------------------------
        def flood_fill_bfs(start_r, start_c):
            # ถ้าเหยียบระเบิด คืนค่า True (แพ้)
            if game["grid"][start_r][start_c] == -1:
                idx = start_r * game["COLS"] + start_c
                btn = game["buttons"][idx]
                btn.content.value = "💣"
                btn.bgcolor = "#F38BA8"
                return True 

            # เริ่มต้นคิว นำช่องที่คลิกเข้าคิว
            queue = deque([(start_r, start_c)])
            
            while queue:
                curr_r, curr_c = queue.popleft() # ดึงช่องหัวคิวออกมา
                
                # เช็กกันหลุดขอบกระดาน และเช็กว่าเคยเปิด/ปักธงไปแล้วหรือยัง
                if curr_r < 0 or curr_r >= game["ROWS"] or curr_c < 0 or curr_c >= game["COLS"]: continue
                if game["revealed"][curr_r][curr_c] or game["flags"][curr_r][curr_c]: continue

                # บันทึกว่าเปิดแล้ว
                game["revealed"][curr_r][curr_c] = True
                game["revealed_count"] += 1
                
                idx = curr_r * game["COLS"] + curr_c
                btn = game["buttons"][idx]
                btn.disabled = True
                btn.bgcolor = "#313244"

                val = game["grid"][curr_r][curr_c]
                if val > 0:
                    btn.content.value = str(val)
                    colors = ["", "#89B4FA", "#A6E3A1", "#F38BA8", "#CBA6F7", "#FAB387", "#94E2D5", "white", "gray"]
                    btn.content.color = colors[val] if val < len(colors) else "#F9E2AF"
                elif val == 0:
                    btn.content.value = " "
                    # ถ้าเป็นช่องว่างเปล่า นำช่องรอบทิศต่อท้ายคิว
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            queue.append((curr_r + dr, curr_c + dc))
            return False

        # -----------------------------------------
        # ฟังก์ชันที่ 3: ตรวจสอบชัยชนะ
        # ใช้เรื่อง: เงื่อนไข (Condition) และคณิตศาสตร์พื้นฐาน
        # ทำหน้าที่: เช็กว่าจำนวนช่องที่เปิดได้ เท่ากับ จำนวนช่องปลอดภัยทั้งหมดหรือยัง
        # -----------------------------------------
        def check_win():
            total_safe = (game["ROWS"] * game["COLS"]) - game["MINES"]
            if game["revealed_count"] == total_safe:
                game["is_game_over"] = True
                status_text.value = "🏆 ภารกิจสำเร็จ!"
                status_text.color = "#A6E3A1"

        # -----------------------------------------
        # ฟังก์ชันที่ 4: แสดงระเบิดทั้งหมด
        # ใช้เรื่อง: Nested Loop (ลูปซ้อนลูป)
        # ทำหน้าที่: วนลูปหากดโดนระเบิด จะสั่งเปิดช่องที่มีระเบิดทุกช่องในกระดาน
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
        # ฟังก์ชันที่ 5: เหตุการณ์เมื่อ "แตะ/คลิก" ปุ่ม
        # ใช้เรื่อง: Event-Driven Programming (การเขียนโปรแกรมตอบสนองเหตุการณ์)
        # ทำหน้าที่: สั่งให้เกิดการทำงานต่างๆ เมื่อผู้เล่นกดปุ่มบนตาราง
        # -----------------------------------------
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

        # -----------------------------------------
        # ฟังก์ชันที่ 6: เหตุการณ์เมื่อ "กดค้าง" ปุ่ม
        # ใช้เรื่อง: Event-Driven Programming และ Boolean Logic
        # ทำหน้าที่: สลับสถานะปักธง (True/False) เมื่อกดค้างที่ปุ่ม
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
        # ฟังก์ชันที่ 7: เตรียมระบบและเริ่มเกมใหม่
        # ใช้เรื่อง: List Comprehension และ UI Dynamic Generation
        # ทำหน้าที่: ล้างกระดานเก่า สร้างกระดานใหม่ตามระดับความยาก และรีเซ็ตตัวแปรทั้งหมด
        # -----------------------------------------
        def start_game(e=None):
            diff = dropdown_diff.value
            if diff is not None:
                if "ง่าย" in diff: game.update({"ROWS": 9, "COLS": 9, "MINES": 10})
                elif "ปานกลาง" in diff: game.update({"ROWS": 16, "COLS": 16, "MINES": 40})
                elif "ยาก" in diff: game.update({"ROWS": 24, "COLS": 16, "MINES": 99}) # ระดับยาก!
            
            game["is_game_over"] = False
            game["first_click"] = True
            game["revealed_count"] = 0
            
            # สร้าง Array 2D ใหม่
            game["grid"] = [[0 for _ in range(game["COLS"])] for _ in range(game["ROWS"])]
            game["revealed"] = [[False for _ in range(game["COLS"])] for _ in range(game["ROWS"])]
            game["flags"] = [[False for _ in range(game["COLS"])] for _ in range(game["ROWS"])]
            game["buttons"] = []

            board.runs_count = game["COLS"]
            board.width = 45 * game["COLS"]
            board.controls.clear()

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
                ft.dropdown.Option("ยาก (24x16, 99 💣)"),
            ],
            value="ง่าย (9x9, 10 💣)", width=220, bgcolor="#313244", color="white"
        )
        status_text = ft.Text("", size=20, weight="bold")
        btn_restart = ft.ElevatedButton("🔄 เริ่มเกมใหม่", on_click=start_game, bgcolor="#89B4FA", color="#11111B")

        # นำชิ้นส่วน UI มาเรียงต่อกัน
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

    except Exception as e:
        # ระบบดักจับ Error
        error_msg = f"🚨 โค้ดมีปัญหา:\n{traceback.format_exc()}"
        page.add(
            ft.Container(
                content=ft.Text(error_msg, color="red", size=12, selectable=True),
                padding=20, bgcolor="black", border_radius=10, expand=True
            )
        )
        page.update()

# คำสั่งรันแอปพลิเคชัน
ft.app(main)