# browser_handler.py
"""
브라우저 제어 및 웹 스크래핑 모듈 (최적화 완료 + 영업종료 감지 강화)
"""

import time
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
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
        self.main_window = None
    
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
            
            # 메인 윈도우 핸들 저장
            self.main_window = self.driver.current_window_handle
            
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
        """페이지 접근 가능성 체크"""
        try:
            self.navigate_to_url(url)
            return True, "접근 가능"
        except Exception as e:
            return False, f"접근 오류: {str(e)}"
    
    def check_login_status(self):
        """네이버 로그인 상태 확인"""
        try:
            # 로그인 관련 요소들 확인
            login_indicators = [
                "a[href*='nid.naver.com/nidlogin']",
                "button:contains('로그인')",
                ".login_link"
            ]
            
            for selector in login_indicators:
                if self.driver.find_elements(By.CSS_SELECTOR, selector):
                    return False
            
            return True
            
        except:
            return False
    
    def click_seller_info_button_with_scroll(self):
        """판매자 정보 버튼 클릭 (빠른 포기 로직 추가)"""
        try:
            print("🔍 판매자 정보 버튼 찾는 중...")
            
            # 1차: 스크롤 없이 빠른 확인
            try:
                seller_info_button = self.driver.find_element(By.XPATH, SELLER_INFO_BUTTON_XPATH)
                print("✅ 판매자 정보 버튼 발견 (스크롤 없이)!")
                seller_info_button.click()
                time.sleep(2)
                return True
            except:
                pass
            
            # 2차: 페이지 상태 확인
            try:
                page_text = self.driver.find_element(By.TAG_NAME, 'body').text
                
                # 영업 종료/중단 관련 키워드 확인
                closed_keywords = [
                    '일시적으로 운영이 중지되었습니다',
                    '판매자의 사정에 따라',
                    '영업을 종료',
                    '판매중단',
                    '스토어 운영을 중단',
                    '일시 중단',
                    '영업 중단',
                    '서비스를 종료',
                    '운영하지 않습니다',
                    '더 이상 운영되지 않습니다'
                ]
                
                for keyword in closed_keywords:
                    if keyword in page_text:
                        print(f"❌ 영업 종료 감지: '{keyword}' - 버튼 찾기 중단")
                        return False
                
                # 판매자 정보 버튼이 없는 페이지 패턴 확인
                if '상품이 없습니다' in page_text or '등록된 상품이 없습니다' in page_text:
                    print("❌ 상품 없는 스토어 - 버튼 찾기 중단")
                    return False
                    
            except Exception as e:
                print(f"   - 페이지 상태 확인 실패: {e}")
            
            # 3차: 제한된 스크롤로 버튼 찾기 (최대 2번만)
            print("🔍 제한된 스크롤로 버튼 찾기...")
            max_scrolls = 2  # 5번에서 2번으로 대폭 단축
            
            for i in range(max_scrolls):
                print(f"📜 스크롤 시도 {i+1}/{max_scrolls}")
                
                try:
                    seller_info_button = self.driver.find_element(By.XPATH, SELLER_INFO_BUTTON_XPATH)
                    print("✅ 판매자 정보 버튼 발견!")
                    
                    # 버튼이 보이도록 스크롤
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", seller_info_button)
                    time.sleep(0.5)  # 1초에서 0.5초로 단축
                    
                    # 클릭 시도
                    print("🖱️ 버튼 클릭 시도...")
                    seller_info_button.click()
                    time.sleep(2)  # 3초에서 2초로 단축
                    
                    print("✅ 버튼 클릭 완료!")
                    return True
                    
                except Exception as e:
                    print(f"❌ 스크롤 {i+1}에서 버튼 못찾음")
                    # 빠르게 아래로 스크롤
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                    time.sleep(0.5)  # 1초에서 0.5초로 단축
                    continue
            
            print("❌ 제한된 시도 후에도 버튼을 찾을 수 없음 - 영업 종료로 판단")
            return False
            
        except Exception as e:
            logger.error(f"버튼 클릭 실패: {e}")
            print(f"❌ 버튼 클릭 중 예외 발생: {e}")
            return False
    
    def detect_captcha_by_window_change(self):
        """창 변화로 캡차 감지 (최적화)"""
        try:
            # 현재 모든 창 핸들
            current_windows = self.driver.window_handles
            
            # 메인 창보다 창이 많으면 캡차 팝업으로 간주
            if len(current_windows) > 1:
                print("✅ 새 탭 열림 - 캡차로 판단")
                
                # 새 탭으로 포커스 이동
                for window in current_windows:
                    if window != self.main_window:
                        self.driver.switch_to.window(window)
                        break
                
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ 캡차 감지 오류: {e}")
            return False
    
    def wait_for_captcha_completion(self):
        """캡차 완료 대기"""
        print("\n" + "="*50)
        print("🔍 캡차가 나타났습니다!")
        print("옵션: Enter(완료) / r(캡차 다시로드) / s(건너뛰기)")
        print("="*50)
        
        user_input = input("선택: ").strip().lower()
        
        if user_input == 'r':
            return "reload"
        elif user_input == 's':
            return "skip"
        else:
            time.sleep(2)
            return "success"
    
    def close_captcha_page(self):
        """캡차 페이지/팝업 닫기 (최적화)"""
        try:
            print("🔄 캡차 탭 닫기...")
            
            # 현재 창 정보 확인
            current_windows = self.driver.window_handles
            current_window = self.driver.current_window_handle
            
            # 새 탭이 열린 경우 처리
            if len(current_windows) > 1:
                # 현재 탭이 메인 탭이 아니라면 현재 탭 닫기
                if hasattr(self, 'main_window') and current_window != self.main_window:
                    self.driver.close()
                    self.driver.switch_to.window(self.main_window)
                    print("✅ 캡차 탭 닫기 완료")
                    return True
                
                # 메인 탭이 아닌 다른 탭들 모두 닫기
                for window in current_windows:
                    if window != self.main_window:
                        try:
                            self.driver.switch_to.window(window)
                            self.driver.close()
                        except:
                            continue
                
                # 메인 탭으로 돌아가기
                self.driver.switch_to.window(self.main_window)
                print("✅ 모든 캡차 탭 닫기 완료")
                return True
            
            print("❌ 닫을 캡차 탭이 없음")
            return False
            
        except Exception as e:
            print(f"❌ 캡차 탭 닫기 실패: {e}")
            return False
    
    def extract_store_id_from_url(self, url):
        """URL에서 스토어 ID 추출"""
        try:
            match = re.search(r'smartstore\.naver\.com/([^/?]+)', url)
            return match.group(1) if match else None
        except:
            return None
    
    def _clean_phone_number(self, phone):
        """전화번호 정리"""
        if not phone:
            return None
        
        # 불필요한 텍스트 제거
        cleaned = phone.replace('잘못된 번호 신고', '').replace('인증', '').strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)  # 중복 공백 제거
        cleaned = re.sub(r'[^\d\-\(\)\s]', '', cleaned)  # 숫자, 하이픈, 괄호, 공백만 남기기
        
        return cleaned.strip() if cleaned.strip() else None
    
    def _process_label_value_pair(self, label, value, seller_info):
        """라벨-값 쌍 처리"""
        from config import PHONE_KEYWORDS, EMAIL_KEYWORDS
        
        # 전화번호 정보 처리
        if any(keyword in label for keyword in PHONE_KEYWORDS):
            cleaned_value = self._clean_phone_number(value)
            if cleaned_value:
                seller_info['전화번호'] = cleaned_value
                print(f"   ✅ 전화번호 저장: {cleaned_value}")
        
        # 이메일 정보 처리
        elif any(keyword in label.lower() for keyword in EMAIL_KEYWORDS):
            if '@' in value:  # 간단한 이메일 형식 확인
                seller_info['이메일'] = value
                print(f"   ✅ 이메일 저장: {value}")
    
    def extract_seller_info(self):
        """판매자 정보 추출 (config 설정 활용)"""
        try:
            from config import SELLER_INFO_SELECTORS, PHONE_KEYWORDS, EMAIL_KEYWORDS
            
            seller_info = {}
            
            print("🔍 판매자 정보 추출 시작...")
            
            # DL 컨테이너 찾기
            info_containers = []
            for selector in SELLER_INFO_SELECTORS['DL_CONTAINERS']:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        info_containers.extend(elements)
                        print(f"   - {selector}에서 {len(elements)}개 컨테이너 발견")
                except Exception as e:
                    print(f"   - {selector} 오류: {e}")
                    continue
            
            if not info_containers:
                print("❌ 정보 컨테이너를 찾을 수 없음")
                return {}
            
            # 각 컨테이너에서 정보 추출
            for container in info_containers:
                try:
                    # dt/dd 쌍으로 정보 추출 시도
                    labels = container.find_elements(By.CSS_SELECTOR, ', '.join(SELLER_INFO_SELECTORS['LABELS']))
                    values = container.find_elements(By.CSS_SELECTOR, ', '.join(SELLER_INFO_SELECTORS['VALUES']))
                    
                    # 라벨과 값이 같은 수만큼 있는지 확인
                    if len(labels) == len(values):
                        for label_elem, value_elem in zip(labels, values):
                            try:
                                label = label_elem.text.strip()
                                value = value_elem.text.strip()
                                
                                if label and value:
                                    self._process_label_value_pair(label, value, seller_info)
                            except Exception as e:
                                print(f"   - 라벨/값 쌍 처리 오류: {e}")
                                continue
                    else:
                        # 개별 요소에서 텍스트 추출 시도
                        container_text = container.text.strip()
                        if container_text:
                            self._process_container_text(container_text, seller_info)
                            
                except Exception as e:
                    print(f"   - 컨테이너 처리 오류: {e}")
                    continue
            
            # 전체 페이지에서 추가 정보 검색
            if not seller_info:
                print("🔍 전체 페이지에서 추가 정보 검색...")
                self._extract_from_full_page(seller_info)
            
            print(f"📋 최종 추출된 정보: {seller_info}")
            return seller_info
            
        except Exception as e:
            logger.error(f"정보 추출 실패: {e}")
            print(f"❌ 정보 추출 중 예외: {e}")
            return {}
    
    def _process_container_text(self, text, seller_info):
        """컨테이너 텍스트 처리"""
        lines = text.split('\n')
        for line in lines:
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    label = parts[0].strip()
                    value = parts[1].strip()
                    if label and value:
                        self._process_label_value_pair(label, value, seller_info)
    
    def _extract_from_full_page(self, seller_info):
        """전체 페이지에서 정보 추출"""
        try:
            # 페이지 전체 텍스트에서 패턴 검색
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            
            # 전화번호 패턴 검색
            phone_patterns = [
                r'(\d{2,3}-\d{3,4}-\d{4})',  # 일반적인 전화번호
                r'(\d{3}-\d{4}-\d{4})',      # 휴대폰 번호
                r'(\d{10,11})'               # 연속된 숫자
            ]
            
            for pattern in phone_patterns:
                matches = re.findall(pattern, page_text)
                if matches and '전화번호' not in seller_info:
                    # 가장 그럴듯한 전화번호 선택
                    for match in matches:
                        if len(match) >= 10:
                            seller_info['전화번호'] = match
                            print(f"   ✅ 패턴으로 전화번호 발견: {match}")
                            break
            
            # 이메일 패턴 검색
            email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            email_matches = re.findall(email_pattern, page_text)
            if email_matches and '이메일' not in seller_info:
                seller_info['이메일'] = email_matches[0]
                print(f"   ✅ 패턴으로 이메일 발견: {email_matches[0]}")
                
        except Exception as e:
            print(f"   - 전체 페이지 검색 오류: {e}")