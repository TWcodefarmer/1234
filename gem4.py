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
    """激活視窗 + 點擊 + 補血動作，加上適當延遲"""
    try:
        # 1. 激活視窗（讓它前景）
        win.activate()
        time.sleep(0.5)  # 等待視窗跳出來

        # 2. 滑鼠移動 + 點擊視窗中心
        center_x = win.left + win.width // 2
        center_y = win.top + win.height // 2
        pyautogui.moveTo(center_x, center_y)
        time.sleep(0.2)
        pyautogui.click()  # 點擊視窗讓它真的聚焦
        print(f"    ↪ 點擊視窗中心 ({center_x}, {center_y})")
        time.sleep(0.5)

        # 3. 點擊補品或 UI 上某個固定點
        pyautogui.click(150, 80)
        print("    ↪ 點擊 (150, 80)")
        time.sleep(0.5)

        # 4. 點擊主要位置（如補品鍵）
        pyautogui.click(1111, 750)
        print("    ↪ 點擊 (1111, 750)")
        time.sleep(0.5)
        return True # 表示已執行 'H' 動作
    except Exception as e:
        print(f"    ↪ 發送按鍵失敗: {e}")
        return False # 表示執行失敗

if __name__ == "__main__":
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
                                break # 只要發現一個血條異常，就立即準備補血，無需檢查其他角色
                        else:
                            print(f"    [角色{idx+1}] 座標超出視窗範圍")

                    if need_press_h:
                        print(f"    ↪ 視窗 '{win.title}' 偵測到血條異常，準備執行補血動作...")
                        if send_key_h(win):
                            print(f"    ↪ 視窗 '{win.title}' 已執行補血動作，跳過此視窗，檢查下一個。")
                            continue # **關鍵修改：執行補血後立即跳到下一個視窗**
                    else:
                        print("    ↪ 所有血條顏色正常，無需按鍵")

            except Exception as e:
                print(f"[!] 錯誤發生於視窗 {i+1}：{win.title}")
                print("    → 詳細錯誤堆疊：")
                traceback.print_exc()

        time.sleep(0.5)  # 控制 CPU 使用率
