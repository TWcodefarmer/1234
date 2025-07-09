# 取得滑鼠位置的顏色 迴圈
'''
血的顏色都是 150,50,22
角色1 679,906 955,906 紅色血條 
角色2 1146,906 1418,906 紅色血條
角色3 1611,906 1886,906 紅色血條
'''

def get_mouse_color():
    x, y = pyautogui.position()            # 取得滑鼠目前螢幕座標
    pixel_color = pyautogui.screenshot().getpixel((x, y))  # 取得該點RGB
    return pixel_color

if __name__ == "__main__":
    import time
    print("開始讀取滑鼠顏色，按 Ctrl+C 停止。")
    try:
        while True:
            color = get_mouse_color()
            print(f"滑鼠位置 {pyautogui.position()} 的顏色：{color}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("程式結束")
