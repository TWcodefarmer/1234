import pygetwindow as gw
import mss
from PIL import Image
import datetime
import time
import traceback
import pydirectinput

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

# --- 全域延遲設定 ---
# 這些數值可以根據遊戲反應和您的需求進行調整
DELAY_AFTER_WINDOW_ACTIVATION = 0.5 # 激活視窗後等待時間 (秒)
DELAY_AFTER_MOUSE_MOVE = 0.1       # 滑鼠移動後等待時間 (秒)
DELAY_AFTER_CLICK = 0.2            # 點擊後等待時間 (秒)
DELAY_AFTER_KEY_PRESS = 0.2        # 按鍵後等待時間 (秒)
DELAY_MAIN_LOOP = 0.5              # 主迴圈每次檢查的間隔時間 (秒)
# --------------------

# 用於儲存已經處理過（按過 H 鍵）的視窗句柄 (HWND)
# 使用視窗句柄來確保唯一性，即使視窗標題重複也能正確區分
processed_windows_handles = set()

def is_color_close(c1, c2, tolerance):
    """判斷兩色是否在容差範圍內"""
    return all(abs(a - b) <= tolerance for a, b in zip(c1, c2))

def send_key_h(win):
    """模擬點擊視窗中心並發送 h 鍵，然後點擊指定位置"""
    try:
        # 確保視窗在前台，以便接收輸入
        win.activate()
        time.sleep(DELAY_AFTER_WINDOW_ACTIVATION) # 使用自定義延遲

        # 1. 移動並點擊視窗中心 (聚焦視窗)
        center_x = win.left + win.width // 2
        center_y = win.top + win.height // 2
        pydirectinput.moveTo(center_x, center_y)
        time.sleep(DELAY_AFTER_MOUSE_MOVE)       # 使用自定義延遲
        pydirectinput.click()
        print(f"      ↪ 移動至視窗中心 ({center_x}, {center_y}) 並點擊 (聚焦視窗)")
        time.sleep(DELAY_AFTER_CLICK)            # 使用自定義延遲

        # 2. 發送 'h' 鍵
        pydirectinput.press('h')
        print(f"      ↪ 視窗 '{win.title}' (句柄: {win._hWnd}) 發送按鍵 h")
        time.sleep(DELAY_AFTER_KEY_PRESS)        # 使用自定義延遲

        # 3. 移動並點擊你原本的固定位置 (1111, 750)
        pydirectinput.moveTo(1111, 750)
        time.sleep(DELAY_AFTER_MOUSE_MOVE)       # 使用自定義延遲
        pydirectinput.click()
        print("      ↪ 移動至 (1111, 750) 並點擊")
        time.sleep(DELAY_AFTER_CLICK)            # 使用自定義延遲

    except Exception as e:
        print(f"      ↪ 發送按鍵失敗: {e}")

if __name__ == "__main__":
    # 設定 pydirectinput 的預設延遲和故障保護
    # pydirectinput.PAUSE 會影響所有 pydirectinput 操作間的預設延遲
    # 這裡可以根據需要調整或保持預設
    pydirectinput.PAUSE = 0.05
    pydirectinput.FAILSAFE = True

    print(f"--- 腳本啟動 ---")
    print(f"延遲設定：")
    print(f"  激活視窗後：{DELAY_AFTER_WINDOW_ACTIVATION} 秒")
    print(f"  滑鼠移動後：{DELAY_AFTER_MOUSE_MOVE} 秒")
    print(f"  點擊後：{DELAY_AFTER_CLICK} 秒")
    print(f"  按鍵後：{DELAY_AFTER_KEY_PRESS} 秒")
    print(f"  主迴圈間隔：{DELAY_MAIN_LOOP} 秒")
    print(f"----------------")

    while True:
        windows = [w for w in gw.getWindowsWithTitle(keyword) if w.title and not w.title.isspace()]
        if not windows:
            print(f"[✗] 找不到任何包含「{keyword}」的視窗")
            time.sleep(DELAY_MAIN_LOOP) # 使用自定義延遲
            continue

        for i, win in enumerate(windows[:3]):  # 最多處理 3 個視窗
            # 檢查該視窗是否已經被處理過 (使用視窗句柄)
            if win._hWnd in processed_windows_handles:
                print(f"\n[→] 視窗 {i+1}：{win.title} (句柄: {win._hWnd}) 已處理過，跳過。")
                continue # 跳過此視窗，檢查下一個

            try:
                print(f"\n[→] 處理視窗 {i+1}：{win.title} (句柄: {win._hWnd})")

                if win.isMinimized:
                    print("      ↪ 還原最小化視窗...")
                    win.restore()
                    time.sleep(DELAY_AFTER_WINDOW_ACTIVATION) # 使用自定義延遲

                print("      ↪ 等待視窗穩定...")
                time.sleep(1) # 此處延遲暫時保持固定，確保截圖穩定

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
                        # 將全螢幕座標轉換為視窗內部的相對座標
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
                        # 如果執行了補血操作，將此視窗句柄加入已處理集合
                        processed_windows_handles.add(win._hWnd)
                        print(f"      ↪ 視窗 '{win.title}' (句柄: {win._hWnd}) 已加入已處理列表，將不再監控。")
                    else:
                        print("      ↪ 所有血條顏色正常，無需按鍵")

            except Exception as e:
                print(f"[!] 錯誤發生於視窗 {i+1}：{win.title} (句柄: {win._hWnd})")
                print("      → 詳細錯誤堆疊：")
                traceback.print_exc()

        time.sleep(DELAY_MAIN_LOOP) # 使用自定義延遲
