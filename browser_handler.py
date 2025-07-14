# browser_handler.py
"""
브라우저 제어 및 웹 스크래핑 모듈 (단순화)
"""

import time
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

from config import (
    BROWSER_WAIT_TIME, PAGE_LOAD_DELAY, BUTTON_CLICK_DELAY,
    CAPTCHA_SELECTORS, SELLER_INFO_BUTTON_XPATH
)

logger = logging.getLogger(__name__)

class BrowserHandler:
    """브라우저 제어 클래스"""
    
    def __init__(self):
        self.driver = None
    
    def setup_driver(self):
        """Undetected Chrome 드라이버 설정"""
        try:
            options = uc.ChromeOptions()
            options.add_argument("--no-first-run")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            
            self.driver = uc.Chrome(options=options, version_main=None)
            self.driver.implicitly_wait(BROWSER_WAIT_TIME)
            
            logger.info("Undetected Chrome 드라이버 초기화 완료")
            
        except Exception as e:
            logger.error(f"드라이버 설정 실패: {e}")
            raise
    
    def close_driver(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            logger.info("드라이버 종료")
    
    def navigate_to_url(self, url):
        """URL로 이동"""
        try:
            self.driver.get(url)
            time.sleep(PAGE_LOAD_DELAY)
            return True
        except Exception as e:
            logger.error(f"URL 이동 실패: {e}")
            return False
    
    def check_page_accessibility(self, url):
        """페이지 접근 가능성 체크 (매우 단순화)"""
        try:
            self.navigate_to_url(url)
            
            # 브라우저가 정상적으로 페이지를 로드했다면 일단 접근 가능한 것으로 판단
            # 판매자 정보 버튼 존재 여부로만 실제 유효성 판단
            return True, "접근 가능"
            
        except Exception as e:
            return False, f"접근 오류: {str(e)}"
    
    def check_login_status(self):
        """네이버 로그인 상태 확인"""
        try:
            # 로그인 관련 요소들 확인
            login_indicators = [
                "a[href*='nid.naver.com/nidlogin']",  # 로그인 링크
                "button:contains('로그인')",
                ".login_link"
            ]
            
            for selector in login_indicators:
                if self.driver.find_elements(By.CSS_SELECTOR, selector):
                    return False  # 로그인 필요
            
            return True  # 이미 로그인됨
            
        except:
            return False
    
    def click_seller_info_button_with_scroll(self):
        """판매자 정보 버튼 클릭 (스크롤 포함) - 디버깅 추가"""
        try:
            print("🔍 스크롤하면서 판매자 정보 버튼 찾는 중...")
            
            # 페이지 끝까지 스크롤하면서 버튼 찾기
            max_scrolls = 5
            for i in range(max_scrolls):
                print(f"📜 스크롤 시도 {i+1}/{max_scrolls}")
                
                try:
                    # 버튼 찾기 시도
                    seller_info_button = self.driver.find_element(By.XPATH, SELLER_INFO_BUTTON_XPATH)
                    print("✅ 판매자 정보 버튼 발견!")
                    
                    # 버튼이 보이도록 스크롤
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", seller_info_button)
                    time.sleep(1)
                    
                    # 클릭 가능할 때까지 대기
                    WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, SELLER_INFO_BUTTON_XPATH))
                    )
                    
                    print("🖱️ 버튼 클릭 시도...")
                    seller_info_button.click()
                    time.sleep(PAGE_LOAD_DELAY + 1)
                    print("✅ 버튼 클릭 완료!")
                    return True
                    
                except Exception as e:
                    print(f"❌ 스크롤 {i+1}에서 버튼 못찾음: {e}")
                    # 버튼을 찾을 수 없으면 아래로 스크롤
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    continue
            
            print("❌ 모든 스크롤 시도 후에도 버튼을 찾을 수 없음")
            return False
            
        except Exception as e:
            logger.error(f"버튼 클릭 실패: {e}")
            print(f"❌ 버튼 클릭 중 예외 발생: {e}")
            return False
    
    def detect_captcha(self):
        """캡차 감지 - 디버깅 추가"""
        try:
            print("🔍 캡차 감지 시작...")
            
            for selector in CAPTCHA_SELECTORS:
                print(f"   - 선택자 확인: {selector}")
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✅ 캡차 요소 발견! 선택자: {selector}, 개수: {len(elements)}")
                    return True
                else:
                    print(f"   - 없음")
            
            print("❌ 캡차 요소를 찾을 수 없음")
            return False
        except Exception as e:
            print(f"❌ 캡차 감지 중 오류: {e}")
            return False
    
    def wait_for_captcha_completion(self):
        """캡차 완료 대기 (수정)"""
        print("\n" + "="*50)
        print("🔍 캡차가 나타났습니다!")
        print("옵션: Enter(완료) / r(캡차 다시로드) / s(건너뛰기)")
        print("="*50)
        
        user_input = input("선택: ").strip().lower()
        
        if user_input == 'r':
            return "reload"  # 캡차 페이지 닫고 다시 버튼 클릭
        elif user_input == 's':
            return "skip"
        else:
            time.sleep(2)
            return "success"
    
    def close_captcha_page(self):
        """캡차 페이지/팝업 닫기"""
        try:
            # 닫기 버튼 찾기
            close_selectors = [
                "._1fWxIi4neA",  # 네이버 캡차 닫기 버튼
                "._1BE8DmNuKn",  # 네이버 팝업 닫기 버튼
                "button[class*='close']",
                ".close_btn",
                "button:contains('닫기')",
                "button[title*='닫기']"
            ]
            
            for selector in close_selectors:
                try:
                    close_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    close_btn.click()
                    time.sleep(1)
                    print("✅ 캡차 페이지 닫기 완료")
                    return True
                except:
                    continue
            
            # ESC 키로도 시도
            from selenium.webdriver.common.keys import Keys
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
            print("✅ ESC로 페이지 닫기 시도")
            return True
            
        except Exception as e:
            logger.error(f"캡차 페이지 닫기 실패: {e}")
            return False
    
    def extract_store_id_from_url(self, url):
        """URL에서 스토어 ID 추출"""
        try:
            match = re.search(r'smartstore\.naver\.com/([^/?]+)', url)
            return match.group(1) if match else None
        except:
            return None
    
    def extract_seller_info(self):
        """판매자 정보 추출 (단순화)"""
        try:
            seller_info = {}
            
            # dl/dt/dd 구조에서 정보 추출
            info_rows = self.driver.find_elements(By.CSS_SELECTOR, 'dl > div, .aAVvlAZ43w')
            
            for row in info_rows:
                try:
                    label = row.find_element(By.CSS_SELECTOR, 'dt, ._1nqckXI-BW').text.strip()
                    value = row.find_element(By.CSS_SELECTOR, 'dd, .EdE67hDR6I').text.strip()
                    
                    if '고객센터' in label or '전화' in label:
                        value = value.replace('잘못된 번호 신고', '').strip()
                        seller_info['전화번호'] = value
                    elif 'e-mail' in label:
                        seller_info['이메일'] = value
                        
                except:
                    continue
            
            return seller_info
            
        except Exception as e:
            logger.error(f"정보 추출 실패: {e}")
            return {}