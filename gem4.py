import pygetwindow as gw
import mss
from PIL import Image
import datetime
import time
import traceback
import pyautogui
import keyboard

# ========== 設定 ==========
keyword = "Granado Espada M"
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
target_color = (150, 50, 22)  # 血條顏色
tolerance = 10  # 顏色容差，建議用 10 左右避免細微誤差

# 血條終點座標（只看 x2, y）
hp_bar_points = [
    (955, 906),   # 角色1 結尾點
    (1418, 906),  # 角色2
    (1886, 906),  # 角色3
]

def is_color_close(c1, c2, tolerance):
    """判斷兩色是否在容差範圍內"""
    return all(abs(a - b) <= tolerance for a, b in zip(c1, c2))

def send_key_h(win):
    """模擬點擊視窗中心並發送 h 鍵"""
    try:
        time.sleep(0.3)
        center_x = win.left + win.width // 2
        center_y = win.top + win.height // 2
        pyautogui.click(center_x, center_y)  # 聚焦視窗
        time.sleep(0.3)
        keyboard.send('h')                   # 發送 h 鍵
        print(f"    ↪ 視窗 '{win.title}' 發送按鍵 h")
        time.sleep(0.3)
        pyautogui.click(1111, 750)          # 你原本點擊的固定位置
    except Exception as e:
        print(f"    ↪ 發送按鍵失敗: {e}")

if __name__ == "__main__":
    running = True
    while running:
        windows = [w for w in gw.getWindowsWithTitle(keyword) if w.title and not w.title.isspace()]
        if not windows:
            print(f"[✗] 找不到任何包含「{keyword}」的視窗")
            time.sleep(1)
            continue

        for i, win in enumerate(windows[:3]):  # 最多處理 3 個視窗
            try:
                print(f"\n[→] 處理視窗 {i+1}：{win.title}")

                if win.isMinimized:
                    print("    ↪ 還原最小化視窗...")
                    win.restore()
                    time.sleep(0.5)

                print("    ↪ 等待視窗穩定...")
                time.sleep(1)

                bbox_win = {
                    "top": win.top,
                    "left": win.left,
                    "width": win.width,
                    "height": win.height
                }
                print(f"    ↪ 截圖區域 bbox: {bbox_win}")

                with mss.mss() as sct:
                    screenshot = sct.grab(bbox_win)
                    img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                    pixels = img.load()

                    need_press_h = False
                    for idx, (x, y) in enumerate(hp_bar_points):
                        rel_x = x - win.left
                        rel_y = y - win.top

                        if 0 <= rel_x < img.width and 0 <= rel_y < img.height:
                            r, g, b = pixels[rel_x, rel_y]
                            actual_color = (r, g, b)
                            print(f"    [角色{idx+1}] 座標 ({x},{y}) 抓到顏色 {actual_color}")
                            if is_color_close(actual_color, target_color, tolerance):
                                print(f"        ↪ 血條顏色正常")
                            else:
                                print(f"        ↪ 血條顏色異常！")
                                need_press_h = True
                        else:
                            print(f"    [角色{idx+1}] 座標超出視窗範圍")

                    if need_press_h:
                        send_key_h(win)
                        running = False  # 停止外層 while 迴圈
                        break  # 跳出 for 迴圈
                    else:
                        print("    ↪ 所有血條顏色正常，無需按鍵")

            except Exception as e:
                print(f"[!] 錯誤發生於視窗 {i+1}：{win.title}")
                print("    → 詳細錯誤堆疊：")
                traceback.print_exc()

        time.sleep(0.5)  # 控制 CPU 使用率
