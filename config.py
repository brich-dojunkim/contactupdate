# config.py
"""
네이버 판매자 정보 수집기 설정 파일
"""

# 파일 경로 설정
EXCEL_FILE_PATH = "sellers_250711.xlsx"

# 브라우저 설정
BROWSER_WAIT_TIME = 10
PAGE_LOAD_DELAY = 2
BUTTON_CLICK_DELAY = 1
INTER_STORE_DELAY = 2

# 캡차 관련 설정
CAPTCHA_MAX_RETRIES = 3

# 캡차 관련 선택자
CAPTCHA_SELECTORS = [
    "img[alt='캡차이미지']",
    ".captcha_img",
    "#captcha",
    "[class*='captcha']"
]

# 판매자 정보 버튼 선택자
SELLER_INFO_BUTTON_XPATH = "//button[contains(text(), '판매자 상세정보') or contains(@data-shp-area-id, 'sellerinfo')]"

# 로깅 설정
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'

# 엑셀 컬럼명
COLUMNS = {
    'COMPANY_NAME': '입점사명',
    'STORE_URL': '온라인 쇼핑몰 URL',
    'UPDATED_PHONE': '최신화 전화번호',
    'UPDATED_EMAIL': '최신화 이메일'
}