import os
import json
import time
import math
import random
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import datetime
import requests
import winsound
import pytz
import statistics
import csv

PHONE_NUMBER = ''
PASSWORD = ''

# PHONE_NUMBER = ''
# PASSWORD = ''

# config 
REFRESH_TIME = 100 # 刷新時間 尖峰時段可調成1 離峰就慢慢刷
range_perctn = 0.1 # 刷新時間隨機範圍百分比
delay_time = 5 # 電腦越快就調越低
refresh_cookie_hour = 2 # 每隔2小時更新一次cookie
mystery_page_1 = "https://ticketplus.com.tw/order/ce65df4ab3ffb4a6baaaef7d3f55d03f/c65e103a9c153ac787d25eef6803022f" # natori 目標購票頁面


# 使用 network 更新票數判斷座位對應位置 mystery_page_1
ticket_info = {
    "1F站席": {"ticketAreaId": "a000004558", "productId": "p000008917"},
    "2F座席A區": {"ticketAreaId": "a000004559", "productId": "p000008918"},
    "2F座席B區": {"ticketAreaId": "a000004560", "productId": "p000008919"},
    "2F站席": {"ticketAreaId": "a000004793", "productId": "p000009264"},
}
target_seat = "2F站席"  # 目標座位區域
target_productId = ticket_info[f'{target_seat}']['productId']
# print(target_productId)
COOKIE_PATH = "ticketplus.json"
REFRESH_TIME = random.uniform(REFRESH_TIME * (1-range_perctn), REFRESH_TIME * (1+range_perctn))
REFRESH_TIME = round(REFRESH_TIME, 2)  # 保留 2 位小數（可選）

# --------------------- 模擬人類操作 ---------------------
def simulate_human_behavior(driver):
    actions = ActionChains(driver)
    for _ in range(random.randint(1, 3)):
        x = random.randint(0, 300)
        y = random.randint(0, 300)
        actions.move_by_offset(x, y).perform()
        time.sleep(random.uniform(0.3, 1.2))

def driver_init():
    chrome_path = os.path.join(os.getcwd(), "bin", "chrome.exe")
    options = uc.ChromeOptions()
    options.binary_location = chrome_path
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1500,1000")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
    driver = uc.Chrome(headless=False, options=options, version_main=137)
    return driver

# --------------------- Cookie 儲存與載入 ---------------------
def save_cookies(driver):
    cookies = driver.get_cookies()
    with open(COOKIE_PATH, "w") as f:
        json.dump(cookies, f)
    print("✅ Cookies 已儲存")

def load_cookies(driver):
    if not os.path.exists(COOKIE_PATH):
        return False
    with open(COOKIE_PATH, "r") as f:
        cookies = json.load(f)
    for cookie in cookies:
        driver.add_cookie(cookie)
    print("✅ Cookies 載入成功")
    return True

def login(driver):

    # 開啟 TicketPlus 首頁
    driver.get("https://ticketplus.com.tw/")

    try:
        # 等待並點擊「會員登入」按鈕
        login_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(), '會員登入')]]"))
        )
        login_button.click()
        print("✅ 成功點擊『會員登入』")

        # 等待手機號碼欄位出現並填入
        phone_input = WebDriverWait(driver, 15).until(EC.presence_of_element_located((
                By.XPATH,
                "//input[(contains(@placeholder, '手機號碼') or @class='input-tel__input') and @type='tel']"
            )))
        phone_input.send_keys(PHONE_NUMBER)
        print("📱 已輸入手機號碼")

        # 等待密碼欄位出現並填入
        password_input = WebDriverWait(driver, 15).until(EC.presence_of_element_located((
                By.XPATH,
                "//label[contains(text(), '密碼')]/following-sibling::input[@type='password'] | //input[@type='password' and @autocomplete='new-password']"
            ))
        )
        password_input.send_keys(PASSWORD)
        print("🔒 已輸入密碼")

        # 模擬按下 Enter 鍵來送出表單
        password_input.send_keys(Keys.ENTER)
        print("⏎ 已按下 Enter 鍵送出登入表單")
        time.sleep(delay_time)
    except Exception as e:
        print("❌ 發生錯誤：", e)

# --------------------- 搶票相關功能 ---------------------
def click_random_ticket(driver, timeout, start_pct, end_pct):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    ticket_divs = soup.find_all('div', class_='ticket-unit')
    data = []
    for idx, ticket in enumerate(ticket_divs):
        ticket_ID = soup.find_all('div', id=lambda x: x and 'ticket' in x)[idx]['id']
        ticket_price = ticket.find('span', class_='ticket-price').get_text(strip=True)
        ticket_name = ticket.find('span', class_='ticket-name').get_text(strip=True)
        try:
            available_seats = ticket.find('input', class_='ng-pristine ng-untouched ng-valid ng-not-empty').get('value')
        except:
            available_seats = ticket.find('span', class_='ticket-quantity ng-binding ng-scope').get_text(strip=True)
        data.append({'ID': ticket_ID, '票區': ticket_name, '票價': ticket_price, '空位': available_seats})

    filtered = [item for item in data if item['空位'] == '0']
    filtered = [item for item in filtered if not any(keyword in item['票區'] for keyword in ['身障', '愛心', '輪椅'])]
    if not filtered:
        print("❌ 沒有可用票種")
        return False

    selected = filtered[int(len(filtered)*start_pct):math.ceil(len(filtered)*end_pct)]
    target = random.choice(selected)['ID']
    try:
        ticket_div = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, target)))
        input_element = ticket_div.find_element(By.XPATH, ".//input[@ng-model='ticketModel.quantity']")
        input_element.clear()
        input_element.send_keys("1")
        print("✅ 票種已選擇")
        return True
    except:
        print("❌ 票種選擇失敗")
        return False

def click_element(driver, xpath, label, timeout=2):
    try:
        element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        element.click()
        print(f"✅ {label} 點擊成功")
        return True
    except:
        print(f"❌ {label} 點擊失敗")
        return False

def keyin_answer(driver, answer):
    try:
        input_box = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='請填入答案']")))
        input_box.clear()
        input_box.send_keys(answer)
        print("✅ 填寫答案成功")
        return True
    except:
        print("❌ 填寫答案失敗")
        return False

def check_page_changed(driver, timeout, original_url):
    try:
        WebDriverWait(driver, timeout).until(EC.url_changes(original_url))
        print("✅ 頁面已跳轉")
        return True
    except:
        return False

def check_alert(driver, timeout=1):
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        print("⚠️ 警告視窗：", alert.text)
        alert.accept()
        return True
    except:
        return False

def click_vip2_button(driver, timeout=5):
    try:
        # 等待按鈕出現
        buttons = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'button.v-expansion-panel-header')))
        for btn in buttons:
            if "VIP2區" in btn.text:
                btn.click()
                print("✅ 成功點擊 VIP2區 按鈕")
                return True
        print("❌ 找不到 VIP2區 按鈕")
        return False
    except Exception as e:
        print("❌ 點擊 VIP2區 按鈕失敗:", e)
        return False

def click_plus_one_button(driver, timeout=5):
    try:
        # 用包含 mdi-plus 的 i 元素的父按鈕來定位
        xpath = "//button[contains(@class, 'v-btn') and .//i[contains(@class, 'mdi-plus')]]"
        plus_button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        plus_button.click()
        print("✅ 成功點擊 +1 按鈕")
        return True
    except Exception as e:
        print("❌ 點擊 +1 按鈕失敗:", e)
        return False

def click_1F_section_button(driver, timeout=5):
    try:
        xpath = "//button[contains(@class, 'v-expansion-panel-header') and contains(., '1F站席')]"
        btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        btn.click()
        print("✅ 成功點擊 1F站席 按鈕")
        return True
    except Exception as e:
        print("❌ 點擊 1F站席 按鈕失敗:", e)
        return False

def click_2FA_section_button(driver, timeout=5):
    try:
        xpath = "//button[contains(@class, 'v-expansion-panel-header') and contains(., '2F座席A區')]"
        btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        btn.click()
        print("✅ 成功點擊 2F座席A區 按鈕")
        return True
    except Exception as e:
        print("❌ 點擊 2F座席A區 按鈕失敗:", e)
        return False
    
def click_2FB_section_button(driver, timeout=5):
    try:
        xpath = "//button[contains(@class, 'v-expansion-panel-header') and contains(., '2F座席B區')]"
        btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        btn.click()
        print("✅ 成功點擊 2F座席B區 按鈕")
        return True
    except Exception as e:
        print("❌ 點擊 2F座席B區 按鈕失敗:", e)
        return False
    
def click_2FS_section_button(driver, timeout=5):
    try:
        xpath = "//button[contains(@class, 'v-expansion-panel-header') and contains(., '2F站席')]"
        btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        btn.click()
        print("✅ 成功點擊 2F站席 按鈕")
        return True
    except Exception as e:
        print("❌ 點擊 2F站席 按鈕失敗:", e)
        return False
    
def refresh_cookie():
    driver = driver_init()
    login(driver)
    save_cookies(driver)
    driver.quit()

def validate_cookies_expiry(cookies):
    now = int(time.time())  # 現在時間（UNIX timestamp）
    print(f"🕒 現在時間: {now} ({datetime.datetime.utcfromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')} UTC)\n")

    for cookie in cookies:
        name = cookie.get("name", "(無名)")
        expiry = cookie.get("expiry")

        if expiry:
            expiry_str = datetime.datetime.utcfromtimestamp(expiry).strftime('%Y-%m-%d %H:%M:%S')
            print(f"🍪 Cookie: {name}，到期時間: {expiry} ({expiry_str} UTC)")

            if expiry < now:
                raise ValueError(f"\n❌ Cookie '{name}' 已過期！到期時間: {expiry_str} UTC < 現在時間。")
        else:
            print(f"🍪 Cookie: {name} 沒有 expiry，可能是 session cookie。")
    
    print("\n✅ 所有 cookies 都還有效。")

def check_clck_cookie_expiry(cookies, target_cookie_name = "_clck"):
    now = int(time.time())
    
    for cookie in cookies:
        if cookie.get("name") == target_cookie_name:
            expiry = cookie.get("expiry")
            if not expiry:
                print("⚠️ _clck 沒有 expiry（可能是 session cookie）")
                return None
            
            expiry_dt = datetime.datetime.utcfromtimestamp(expiry)
            now_dt = datetime.datetime.utcfromtimestamp(now)
            delta = expiry_dt - now_dt  # datetime.timedelta

            print(f"🕒 _clck 到期時間: {expiry_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")

            return delta

    print("⚠️ 沒有找到 _clck cookie。")
    return None

def should_refresh_cookie(remaining_time, refresh_cookie_hour = 2):
    threshold = datetime.timedelta(days=364, hours=24-refresh_cookie_hour)
    if remaining_time < threshold:
        print(f"✅ 剩餘時間超過 {threshold}，需要 refresh。")
        return True
    else:
        # print(f"❌ 剩餘時間未超過 {threshold}。")
        return False

def mantal_says_telegram(message):
    TOKEN = '6063267049:AAEV9VzwClNp-grUWzdCZh2XttUPJmi0S8I'
    chat_id = '-4167513159'
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
    requests.get(url)

def notify_user():
    for i in range(40):
        time.sleep(1)
        mantal_says_telegram("搶到票了快結帳！")
        time.sleep(1)
        winsound.Beep(3500, 3000)  # 播放 1000Hz，持續 0.5 秒
        time.sleep(10)
        
def refresh_for_ticket_v1(driver):
    status = False
    while not status:
        with open(COOKIE_PATH, "r") as f:
            cookies = json.load(f)
        remaining_time = check_clck_cookie_expiry(cookies, target_cookie_name = "_clck")
        if not should_refresh_cookie(remaining_time, refresh_cookie_hour=refresh_cookie_hour):
            click_2FS_section_button(driver, timeout=1)
            if not click_plus_one_button(driver, timeout=0.3):
                click_1F_section_button(driver, timeout=1)
                if not click_plus_one_button(driver, timeout=0.3):
                    click_2FA_section_button(driver, timeout=1)
                    if not click_plus_one_button(driver, timeout=0.3):
                        click_2FB_section_button(driver, timeout=1)
                        if not click_plus_one_button(driver, timeout=0.3):
                            time.sleep(REFRESH_TIME)
                            driver.get(mystery_page_1)
                            continue
            if click_element(driver, "//span[text()='下一步']/..", "下一步") or click_element(driver, "//span[text()='電腦配位']/..", "電腦配位"):
                for _ in range(150):
                    if check_page_changed(driver, 1, mystery_page_1):
                        print("🎉 成功進入下一頁")
                        status = True
                        break
                    check_alert(driver)
                    time.sleep(1)
            else:
                print("⚠️ 流程異常，重新整理")
                driver.get(mystery_page_1)
                time.sleep(REFRESH_TIME)
        else:
            refresh_cookie()

def refresh_for_ticket_click_all_available_sections_and_one_ticket_next_step(driver, timeout=5):
    try:
        sections = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//button[contains(@class, 'v-expansion-panel-header')]")
            )
        )
        available_count = 0
        for idx, section in enumerate(sections):
            try:
                text = section.text
                if "剩餘" in text:
                    # 抓出剩餘數量
                    import re
                    match = re.search(r"剩餘\s*(\d+)", text)
                    if match and int(match.group(1)) > 0:
                        section.click()
                        click_plus_one_button(driver, timeout=2)
                        if click_element(driver, "//span[text()='下一步']/..", "下一步") or click_element(driver, "//span[text()='電腦配位']/..", "電腦配位"):
                            for _ in range(150):
                                if check_page_changed(driver, 1, mystery_page_1):
                                    print("🎉 成功進入下一頁")
                                    return True
                                check_alert(driver)
                                time.sleep(1)
                        else:
                            print("⚠️ 流程異常，重新整理")
                            driver.get(mystery_page_1)
                            time.sleep(REFRESH_TIME)
                        available_count += 1
                        print(f"✅ 點擊第 {idx+1} 區：「{text.strip()}」")
                        time.sleep(0.5)  # 防止太快點擊
                    else:
                        print(f"🕳️ 無票略過：第 {idx+1} 區：「{text.strip()}」")
                else:
                    print(f"❓ 未找到剩餘資訊：第 {idx+1} 區：「{text.strip()}」")
            except Exception as inner_e:
                print(f"⚠️ 點擊失敗：第 {idx+1} 區 - {inner_e}")

        if available_count == 0:
            print("🚫 所有區域都沒有票")
        else:
            print(f"🎉 完成，共點擊 {available_count} 個有票區塊")

    except Exception as e:
        print("❌ 無法載入區塊列表:", e)
        return False

def click_refresh_button(driver, timeout=5):
    try:
        btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[.//span[contains(text(), '更新票數')]]"
            ))
        )
        btn.click()
        print("🔄 成功點擊 更新票數")
        return True
    except Exception as e:
        print("❌ 點擊 更新票數 失敗:", e)
        return False

# 時間同步相關功能
def get_time_offset_once(url):
    try:
        headers = {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        local_before = datetime.datetime.now(datetime.timezone.utc)
        response = requests.get(url, headers=headers, timeout=5)
        local_after = datetime.datetime.now(datetime.timezone.utc)

        server_date_str = response.headers.get('Date')
        if not server_date_str:
            print("錯誤：找不到 Date 標頭")
            return None

        age_str = response.headers.get('age')
        age = float(age_str) if age_str and age_str.isdigit() else 0

        server_time = datetime.datetime.strptime(
            server_date_str, '%a, %d %b %Y %H:%M:%S GMT'
        ).replace(tzinfo=datetime.timezone.utc)

        rtt = local_after - local_before
        if rtt.total_seconds() > 0.3:
            print(f"⚠️ RTT 太高: {rtt.total_seconds():.3f}秒，放棄此測量")
            return None

        if age > 1:
            print(f"⚠️ 回應快取時間過長: {age} 秒，放棄此測量")
            return None

        one_way = rtt / 2
        est_server_time = server_time + one_way
        offset = est_server_time - local_after
        return offset

    except requests.RequestException as e:
        print(f"網路請求失敗: {e}")
        return None

def get_stable_offset(url, retries=5, total_duration=60):
    offsets = []
    interval = total_duration / retries

    for i in range(retries):
        offset = get_time_offset_once(url)
        if offset is not None:
            print(f"測量 {i+1}: 偏移量 {offset.total_seconds():.4f} 秒")
            offsets.append(offset.total_seconds())
        else:
            print(f"測量 {i+1}: 無效測量，跳過")
        if i < retries - 1:
            print(f"等待 {interval:.1f} 秒後進行下一次測量...")
            time.sleep(interval)

    if not offsets:
        print("無有效測量資料，無法計算偏移量")
        return None

    median_offset = statistics.median(offsets)
    return datetime.timedelta(seconds=median_offset)

def save_result_to_csv(filename, measure_time, offset_seconds, local_cst, server_cst):
    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # 如果檔案不存在，寫入標題列
        if not file_exists:
            writer.writerow(['測量時間 (本地)', '偏移量(秒)', '本地時間 (CST)', '預測伺服器時間 (CST)'])
        writer.writerow([
            measure_time.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
            f"{offset_seconds:.4f}",
            local_cst.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
            server_cst.strftime('%Y-%m-%d %H:%M:%S.%f %z')
        ])

def get_offset_and_save_results(retries=10, total_duration=18000):
    url = 'https://apis.ticketplus.com.tw/config/api/v1/getS3?path=main/mainEvents.json'
    print("開始同步 TicketPlus 伺服器時間（多次測量）...")
    offset = get_stable_offset(url, retries=retries, total_duration=total_duration)
    if offset:
        cst_tz = pytz.timezone('Asia/Taipei')
        local_cst = datetime.datetime.now(cst_tz)
        predicted_server_cst = (datetime.datetime.now(datetime.timezone.utc) + offset).astimezone(cst_tz)
        measure_time = local_cst  # 以本地時間作為測量時間

        print("\n--- 最終同步結果 ---")
        print(f"偏移量 (秒): {offset.total_seconds():.4f}")
        print(f"本地時間 (CST): {local_cst.strftime('%Y-%m-%d %H:%M:%S.%f %z')}")
        print(f"預測伺服器時間 (CST): {predicted_server_cst.strftime('%Y-%m-%d %H:%M:%S.%f %z')}")

        if offset.total_seconds() > 0:
            print("分析：本地時鐘比伺服器慢")
        else:
            print("分析：本地時鐘比伺服器快")

        # 儲存結果
        csv_filename = 'time_sync_results.csv'
        save_result_to_csv(csv_filename, measure_time, offset.total_seconds(), local_cst, predicted_server_cst)
        print(f"結果已儲存至 {csv_filename}")
        return offset.total_seconds()
    else:
        print("同步失敗，無法取得有效偏移量")

try:
    with open(COOKIE_PATH, "r") as f:
        cookies = json.load(f)
except:
    refresh_cookie()
    time.sleep(delay_time)
    with open(COOKIE_PATH, "r") as f:
        cookies = json.load(f)
remaining_time = check_clck_cookie_expiry(cookies, target_cookie_name = "_clck")
if should_refresh_cookie(remaining_time, refresh_cookie_hour=refresh_cookie_hour):
    refresh_cookie()

driver = driver_init()
driver.get("https://ticketplus.com.tw/")
time.sleep(delay_time)
load_cookies(driver)
driver.get(mystery_page_1)
while True:
    if refresh_for_ticket_click_all_available_sections_and_one_ticket_next_step(driver) == True:
        break
    click_refresh_button(driver, timeout=5)
    time.sleep(REFRESH_TIME)
notify_user()
