import pygetwindow as gw
import mss
from PIL import Image
import datetime
import time
import traceback
import pydirectinput
import keyboard

# ========== 設定 ==========
keyword = "Granado Espada M"
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
target_color = (150, 50, 22)  # 血條顏色
tolerance = 10  # 顏色容差，建議用 10 左右避免細微誤差

# 血條終點座標（只看 x2, y）
hp_bar_points = [
    (955, 906),    # 角色1 結尾點
    (1418, 906),   # 角色2
    (1886, 906),   # 角色3
]

def is_color_close(c1, c2, tolerance):
    """判斷兩色是否在容差範圍內"""
    return all(abs(a - b) <= tolerance for a, b in zip(c1, c2))

def send_key_h(win):
    """激活視窗 + 點擊 + 補血動作，加上適當延遲"""
    try:
        # 1. 激活視窗（讓它前景）
        win.activate()
        time.sleep(0.5)  # 等待視窗跳出來

        # 2. 滑鼠移動 + 點擊視窗中心
        center_x = win.left + win.width // 2
        center_y = win.top + win.height // 2
        pydirectinput.moveTo(center_x, center_y) # 移動到中心
        time.sleep(0.2)
        pydirectinput.click()  # ✅ 在中心點擊
        print(f"      ↪ 移動至視窗中心 ({center_x}, {center_y}) 並點擊")
        time.sleep(0.5)

        # 3. 移動並點擊補品或 UI 上某個固定點
        pydirectinput.moveTo(150, 80) # 移動到 (150, 80)
        time.sleep(0.2)
        pydirectinput.click() # 在 (150, 80) 點擊
        print("      ↪ 移動至 (150, 80) 並點擊")
        time.sleep(0.5)

        # 4. 移動並點擊主要位置（如補品鍵）
        pydirectinput.moveTo(1111, 750) # 移動到 (1111, 750)
        time.sleep(0.2)
        pydirectinput.click() # 在 (1111, 750) 點擊
        print("      ↪ 移動至 (1111, 750) 並點擊")
        time.sleep(0.5)

    except Exception as e:
        print(f"      ↪ 發送按鍵失敗: {e}")


if __name__ == "__main__":
    # 設定 pydirectinput 的預設延遲，以避免遊戲偵測為機器人行為
    pydirectinput.PAUSE = 0.05 # 預設延遲，您可以根據需求調整
    pydirectinput.FAILSAFE = True # 啟用故障保護，將滑鼠移動到左上角 (0,0) 會停止程式

    while True:
        windows = [w for w in gw.getWindowsWithTitle(keyword) if w.title and not w.title.isspace()]
        if not windows:
            print(f"[✗] 找不到任何包含「{keyword}」的視窗")
            time.sleep(1)
            continue

        for i, win in enumerate(windows[:3]):  # 最多處理 3 個視窗
            try:
                print(f"\n[→] 處理視窗 {i+1}：{win.title}")

                if win.isMinimized:
                    print("      ↪ 還原最小化視窗...")
                    win.restore()
                    time.sleep(0.5)

                print("      ↪ 等待視窗穩定...")
                time.sleep(1)

                bbox_win = {
                    "top": win.top,
                    "left": win.left,
                    "width": win.width,
                    "height": win.height
                }
                print(f"      ↪ 截圖區域 bbox: {bbox_win}")

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
                            print(f"      [角色{idx+1}] 座標 ({x},{y}) 抓到顏色 {actual_color}")
                            if is_color_close(actual_color, target_color, tolerance):
                                print(f"          ↪ 血條顏色正常")
                            else:
                                print(f"          ↪ 血條顏色異常！")
                                need_press_h = True
                        else:
                            print(f"      [角色{idx+1}] 座標超出視窗範圍")

                    if need_press_h:
                        send_key_h(win)
                    else:
                        print("      ↪ 所有血條顏色正常，無需按鍵")

            except Exception as e:
                print(f"[!] 錯誤發生於視窗 {i+1}：{win.title}")
                print("      → 詳細錯誤堆疊：")
                traceback.print_exc()

        time.sleep(0.5)  # 控制 CPU 使用率
