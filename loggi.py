import serial
import serial.tools.list_ports
import time
import sys
import os

# ----------------------------------------------------------------------
# 鍵盤與滑鼠代碼對應表
# ----------------------------------------------------------------------
# 這張表將按鍵名稱對應到數值，這些數值是 Arduino Keyboard.h 庫所使用的。
# 這些數值需要手動從你的 Arduino IDE 庫文件中查找或從網路上參考。
# 如果找不到某些按鍵，可以參考 Keyboard.h 文件的路徑：
# C:\Users\[你的使用者名稱]\AppData\Local\Arduino15\libraries\Keyboard\src\Keyboard.h
# ----------------------------------------------------------------------
KEY_MAP = {
    'a': 97, 'b': 98, 'c': 99, 'd': 100, 'e': 101, 'f': 102, 'g': 103,
    'h': 104, 'i': 105, 'j': 106, 'k': 107, 'l': 108, 'm': 109, 'n': 110,
    'o': 111, 'p': 112, 'q': 113, 'r': 114, 's': 115, 't': 116, 'u': 117,
    'v': 118, 'w': 119, 'x': 120, 'y': 121, 'z': 122,
    
    '1': 49, '2': 50, '3': 51, '4': 52, '5': 53,
    '6': 54, '7': 55, '8': 56, '9': 57, '0': 48,

    'comma': 44, 'period': 46, 'semicolon': 59, 'equals': 61,
    'minus': 45, 'slash': 47, 'backtick': 96, 'left_bracket': 91,
    'right_bracket': 93, 'backslash': 92, 'quote': 39, 'space': 32,
    
    'enter': 176, 'esc': 177, 'tab': 179, 'backspace': 178,
    'capslock': 193, 'delete': 212, 'home': 210, 'end': 213,
    'pageup': 211, 'pagedown': 214, 'insert': 209,
    
    'up': 218, 'down': 217, 'left': 216, 'right': 215,
    
    'alt': 226, 'ctrl': 224, 'shift': 225, 'gui': 227,

    'f1': 194, 'f2': 195, 'f3': 196, 'f4': 197, 'f5': 198,
    'f6': 199, 'f7': 200, 'f8': 201, 'f9': 202, 'f10': 203,
    'f11': 204, 'f12': 205
}


# 預設的序列埠設定
# 這些變數現在會被自動偵測函式設定
SERIAL_PORT = None 
BAUD_RATE = 9600
ser = None


def _find_arduino_port():
    """
    自動尋找 Arduino Leonardo 的序列埠。
    """
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # 根據裝置描述來尋找
        # 你的輸出顯示描述為 'Arduino Leonardo (COM20)'
        if "Arduino Leonardo" in port.description:
            print(f"自動偵測到 Arduino 裝置在：{port.device}")
            return port.device
    print("錯誤：沒有偵測到任何 Arduino 裝置。")
    return None

def _connect_to_arduino():
    """
    自動尋找 COM port 並建立與 Arduino 的序列連線。
    """
    global ser, SERIAL_PORT
    
    # 如果已經連線，則直接返回
    if ser is not None and ser.is_open:
        return
    
    # 自動尋找序列埠
    SERIAL_PORT = _find_arduino_port()
    if SERIAL_PORT is None:
        sys.exit(1)

    try:
        print(f"嘗試連線到 {SERIAL_PORT}...")
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # 等待 Arduino 重置完成
        print("成功連線到 Arduino。")
    except serial.SerialException as e:
        print(f"錯誤：無法連線到 {SERIAL_PORT}。請檢查板子是否正確連接。{e}")
        sys.exit(1)
def _send_command(command_prefix, value):
    """發送格式化指令到 Arduino。"""
    _connect_to_arduino()
    command = f"{command_prefix}:{value}\n".encode('utf-8')
    ser.write(command)

# ----------------------------------------------------------------------
# pyautogui 替代函數
# ----------------------------------------------------------------------

# 鍵盤函數
def press(key):
    """模擬單次按鍵。"""
    key_code = KEY_MAP.get(str(key).lower())
    if key_code is not None:
        _send_command("KEYPRESS", key_code)
    else:
        print(f"警告：找不到按鍵'{key}'的對應代碼。")

def keyDown(key):
    """模擬按鍵按下。"""
    key_code = KEY_MAP.get(str(key).lower())
    if key_code is not None:
        _send_command("KEYDOWN", key_code)
    else:
        print(f"警告：找不到按鍵'{key}'的對應代碼。")

def keyUp(key):
    """模擬按鍵放開。"""
    key_code = KEY_MAP.get(str(key).lower())
    if key_code is not None:
        _send_command("KEYUP", key_code)
    else:
        print(f"警告：找不到按鍵'{key}'的對應代碼。")

def hotkey(*keys):
    """模擬熱鍵組合。"""
    key_codes = [KEY_MAP.get(str(k).lower()) for k in keys if KEY_MAP.get(str(k).lower()) is not None]
    if len(key_codes) == len(keys):
        for code in key_codes:
            _send_command("KEYDOWN", code)
        time.sleep(0.1)
        for code in reversed(key_codes):
            _send_command("KEYUP", code)
    else:
        print(f"警告：熱鍵組合中存在無效按鍵：{keys}")


# 滑鼠函數
def moveTo(x, y, duration=0, tween=None):
    """
    將滑鼠從當前位置移動到 (x, y)。
    由於 Arduino 只能進行相對移動，這個函數會模擬一步步移動。
    (注意：這比真正的 pyautogui 慢，可能需要調整)
    """
    _send_command("MOUSE_MOVE", f"{x},{y}")
    # 這裡的實現很簡化，你可能需要根據你的需求來改進
    # 例如，你可以計算相對移動量並分步發送指令
    pass 

def click(x=None, y=None, button='left'):
    """模擬滑鼠點擊。"""
    if x is not None and y is not None:
        # 如果提供了坐標，先移動再點擊
        # 由於我們沒有讀取當前滑鼠位置的功能，這裡需要假設
        # 如果需要精確位置，你可能需要手動計算相對位移
        # 例如: Mouse.move(x - current_x, y - current_y)
        pass 
    _send_command("MOUSE_CLICK", button)

def mouseDown(button='left'):
    """模擬滑鼠按鍵按下。"""
    _send_command("MOUSE_DOWN", button)

def mouseUp(button='left'):
    """模擬滑鼠按鍵放開。"""
    _send_command("MOUSE_UP", button)
    
def write(message, interval=0.1):
    """模擬打字。"""
    for char in message:
        key_code = KEY_MAP.get(char.lower())
        if key_code:
            # 處理大小寫
            if char.isupper():
                hotkey('shift', char.lower())
            else:
                press(char)
        else:
            print(f"警告：無法輸入字元 '{char}'")
        time.sleep(interval)
        
def screenshot(region=None):
    """
    這個函數無法直接由 Arduino 實現。
    如果需要螢幕截圖，你仍然需要使用一個原生的 Python 函式庫，例如 Pillow。
    所以這裡仍使用原本的 pyautogui.screenshot。
    """
    print("警告：截圖功能由原生 pyautogui 執行。")
    return pyautogui.screenshot(region)

# ----------------------------------------------------------------------
# 在模組載入時嘗試連線
# ----------------------------------------------------------------------
try:
    import serial
    _connect_to_arduino()
except ImportError:
    print("錯誤：pyserial 函式庫未安裝。請執行 'pip install pyserial'")
    sys.exit(1)
