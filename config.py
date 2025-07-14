# config.py
"""
네이버 판매자 정보 수집기 설정 파일 (캡차 처리 강화)
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
CAPTCHA_DETECTION_DELAY = 2

# 캡차 관련 선택자 (HTML 분석 결과 반영)
CAPTCHA_SELECTORS = [
    "img[alt='캡차이미지']",          # 실제 캡차 이미지
    "#captcha",                     # 캡차 입력 필드
    ".captcha_area",                # 캡차 영역
    "[id*='captcha']",              # ID에 captcha가 포함된 모든 요소
    "form.j2FVVB9jV0",             # 캡차 폼 (첫 번째 폼)
    "form._LxSLYFhsC",             # 캡차 폼 (두 번째 폼)
    "._16klV-DjZE",                # 캡차 컨테이너
    ".bill_img",                   # 영수증 이미지
    "#captcha_info",               # 캡차 안내 메시지
    "input[name='captcha']"        # 캡차 입력 필드
]

# 캡차 닫기 버튼 선택자들 (HTML 분석 결과)
CAPTCHA_CLOSE_SELECTORS = [
    "._1fWxIi4neA",                      # 실제 닫기 버튼
    "button._1fWxIi4neA",               # 명시적 버튼 태그
    "._1ktKGzW6bX.FtO9-BHAq-",         # 닫기 버튼 클래스
    ".close_btn",                       # 일반적인 닫기 버튼
    "button[class*='close']",           # 클래스에 close가 포함된 버튼
    "button[title*='닫기']",            # 제목에 닫기가 포함된 버튼
    ".Lqf5Hzlrtz._2cGQIZtUzZ"         # 음성 캡차 닫기 버튼
]

# 판매자 정보 버튼 선택자
SELLER_INFO_BUTTON_XPATH = "//button[contains(text(), '판매자 상세정보') or contains(@data-shp-area-id, 'sellerinfo')]"

# 판매자 정보 추출 선택자들
SELLER_INFO_SELECTORS = {
    'DL_CONTAINERS': [
        'dl > div',
        '.aAVvlAZ43w',
        'dl',
        '.seller_info_area'
    ],
    'LABELS': [
        'dt',
        '._1nqckXI-BW',
        '.info_label',
        '.label'
    ],
    'VALUES': [
        'dd', 
        '.EdE67hDR6I',
        '.info_value',
        '.value'
    ]
}

# 전화번호 관련 키워드
PHONE_KEYWORDS = [
    '고객센터', '전화', 'TEL', 'tel', 'Tel', 
    '연락처', '문의전화', '상담전화', 'PHONE', 'phone'
]

# 이메일 관련 키워드
EMAIL_KEYWORDS = [
    'email', 'e-mail', 'Email', 'E-mail', 'E-Mail',
    '이메일', '메일', '전자메일'
]

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

# 디버깅 설정
DEBUG_MODE = True
VERBOSE_LOGGING = True