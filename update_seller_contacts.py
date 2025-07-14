"""
SmartStore 연락처 자동 수집기
- 엑셀 '온라인 쇼핑몰 URL' 컬럼에 smartstore/shopping.naver 주소가 있을 때만 작업
- 사용자는 캡차만 풀고 엔터(또는 아무 키) → 나머지 단계는 자동
"""

import time, sys, argparse, pathlib
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

BTN_SEL = 'button[data-shp-area="fot.sellerinfo"]'
CAPTCHA_IMG = 'img#captchaimg'
SELLER_DLG = 'dl._3BlyWp6LJv'          # 판매자 정보 팝업

def scrape_seller_info(driver):
    """판매자 팝업이 열린 상태에서 전화·메일 추출"""
    root = driver.find_element(By.CSS_SELECTOR, SELLER_DLG)
    field_elems = root.find_elements(By.CSS_SELECTOR, 'div.aAVvlAZ43w')
    info = {}
    for d in field_elems:
        key = d.find_element(By.TAG_NAME, 'dt').text.strip()
        val = d.find_element(By.TAG_NAME, 'dd').text.strip()
        info[key] = val
    # SmartStore가 주로 쓰는 라벨만 리턴
    return {
        '최신화 전화번호': info.get('고객센터') or '',
        '최신화 이메일':   info.get('e-mail') or '',
    }

def process_url(driver, url):
    driver.get(url)
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, BTN_SEL))).click()

    # 1) 캡차가 뜨면 사용자가 풀게 둔다
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, CAPTCHA_IMG)))
        print(f'⚠️  {url} – 캡차 풀고 엔터를 눌러 주세요…', flush=True)
        input()                 # 사용자가 풀면 엔터
    except Exception:
        pass                    # 캡차가 안 뜨는 경우도 있음

    # 2) 팝업의 판매자 정보를 파싱
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, SELLER_DLG)))
    return scrape_seller_info(driver)

def main(xlsx_path):
    df = pd.read_excel(xlsx_path)
    mask = df['온라인 쇼핑몰 URL'].str.contains('smartstore|shopping.naver', na=False)
    targets = df[mask]

    driver = uc.Chrome(headless=False)          # 로그인 세션이 유지되도록 쿠키 프로필 써도 OK
    wait = WebDriverWait(driver, 30)

    for idx, row in targets.iterrows():
        url = row['온라인 쇼핑몰 URL']
        try:
            result = process_url(driver, url)
            for k, v in result.items():
                df.at[idx, k] = v
            print(f'✅ {row["입점사명"]} – {result}')
        except Exception as e:
            print(f'❌ {url} – {e}')

    driver.quit()
    backup = pathlib.Path(xlsx_path).with_suffix('.bak.xlsx')
    pathlib.Path(xlsx_path).rename(backup)
    df.to_excel(xlsx_path, index=False)
    print(f'🔄 저장 완료 ({xlsx_path}), 백업: {backup}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('xlsx', help='업데이트할 엑셀 파일 경로')
    main(parser.parse_args().xlsx)
