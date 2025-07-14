# browser_handler.py
"""
브라우저 제어 및 웹 스크래핑 모듈 (영업종료 기준: 버튼 유무, 1회 검색)
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
        """URL로 이동 (URL 형식 검증 추가)"""
        try:
            # URL 형식 검증 및 수정
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            self.driver.get(url)
            time.sleep(1)  # 2초에서 1초로 단축
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
    
    def find_seller_info_button(self):
        """판매자 정보 버튼 찾기 (타임아웃 단축)"""
        try:
            print("🔍 판매자 정보 버튼 찾는 중...")
            
            # 페이지 로드 완료 대기 (단축)
            time.sleep(0.5)
            
            # 짧은 타임아웃으로 버튼 찾기
            try:
                seller_info_button = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, SELLER_INFO_BUTTON_XPATH))
                )
                print("✅ 판매자 정보 버튼 발견!")
                
                # 버튼이 보이도록 스크롤
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", seller_info_button)
                time.sleep(0.3)
                
                # 클릭
                seller_info_button.click()
                time.sleep(1)
                
                print("✅ 판매자 정보 버튼 클릭 완료!")
                return True
                
            except TimeoutException:
                print(f"❌ 판매자 정보 버튼을 찾을 수 없음 - 영업 종료로 판단")
                return False
            
        except Exception as e:
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
    
    def wait_for_captcha_completion(self, timeout=60):
        """캡차 완료 자동 감지 및 사용자 입력 대기 (자동 재시도 포함)"""
        print("\n" + "="*50)
        print("🔍 캡차가 나타났습니다!")
        print("🤖 자동으로 캡차 완료를 감지합니다...")
        print("🔄 캡차 창을 수동으로 닫으면 자동으로 재시도합니다")
        print("또는 수동 옵션: r(캡차 다시로드) / s(건너뛰기)")
        print("="*50)
        
        import threading
        import queue
        
        # 사용자 입력을 위한 큐
        input_queue = queue.Queue()
        
        def get_user_input():
            try:
                user_input = input("선택 (자동 감지 중...): ").strip().lower()
                input_queue.put(user_input)
            except:
                pass
        
        # 사용자 입력 스레드 시작
        input_thread = threading.Thread(target=get_user_input, daemon=True)
        input_thread.start()
        
        # 캡차 완료 자동 감지
        start_time = time.time()
        check_interval = 2  # 2초마다 확인
        last_window_count = len(self.driver.window_handles)
        
        while time.time() - start_time < timeout:
            # 사용자 입력 확인
            try:
                user_input = input_queue.get_nowait()
                if user_input == 'r':
                    return "reload"
                elif user_input == 's':
                    return "skip"
            except queue.Empty:
                pass
            
            current_window_count = len(self.driver.window_handles)
            
            # 🆕 캡차 창이 수동으로 닫혔는지 감지
            if last_window_count > 1 and current_window_count == 1:
                print("🔄 캡차 창이 수동으로 닫힌 것을 감지 - 자동 재시도")
                return "auto_retry"
            
            # 캡차 완료 자동 감지
            if self._check_captcha_completion():
                print("✅ 캡차 자동 완료 감지!")
                return "success"
            
            last_window_count = current_window_count
            time.sleep(check_interval)
        
        print("⏰ 캡차 대기 시간 초과")
        return "timeout"
    
    def _check_captcha_completion(self):
        """캡차 완료 상태 확인"""
        try:
            current_windows = self.driver.window_handles
            
            # 1. 캡차 창이 자동으로 닫혔는지 확인
            if len(current_windows) == 1:
                print("   📋 캡차 창이 닫혔음을 감지")
                return True
            
            # 2. 현재 캡차 창이 열려있다면 페이지 변화 확인
            if len(current_windows) > 1:
                try:
                    # 캡차 창에서 완료 관련 요소 확인
                    current_url = self.driver.current_url
                    page_text = self.driver.find_element(By.TAG_NAME, 'body').text
                    
                    # 완료 관련 키워드 확인
                    completion_keywords = [
                        '완료',
                        '성공',
                        '확인',
                        '판매자 정보',
                        '고객센터',
                        '전화번호',
                        '이메일'
                    ]
                    
                    for keyword in completion_keywords:
                        if keyword in page_text:
                            print(f"   📋 완료 키워드 감지: {keyword}")
                            return True
                            
                    # URL 변화 확인 (캡차에서 정보 페이지로)
                    if 'captcha' not in current_url.lower():
                        print("   📋 URL 변화 감지 (캡차 → 정보페이지)")
                        return True
                        
                except Exception as e:
                    print(f"   ⚠️ 완료 상태 확인 중 오류: {e}")
            
            return False
            
        except Exception as e:
            print(f"   ❌ 캡차 완료 감지 오류: {e}")
            return False
    
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
        """판매자 정보 추출 (중복 제거 및 성능 최적화)"""
        try:
            from config import PHONE_KEYWORDS, EMAIL_KEYWORDS
            
            seller_info = {}
            
            print("🔍 판매자 정보 추출 시작...")
            
            # 빠른 추출을 위해 우선순위 선택자 사용
            priority_selectors = [
                'dl > div',  # 가장 일반적인 패턴
                '.aAVvlAZ43w'  # 네이버 특화 클래스
            ]
            
            # 우선순위 선택자로 먼저 시도
            for selector in priority_selectors:
                try:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if containers:
                        print(f"   ✅ {selector}에서 {len(containers)}개 컨테이너 발견")
                        
                        # 각 컨테이너에서 정보 추출 (최대 3개만)
                        for container in containers[:3]:
                            extracted = self._extract_from_container(container)
                            if extracted:
                                # 중복 방지: 이미 있는 정보는 덮어쓰지 않음
                                for key, value in extracted.items():
                                    if key not in seller_info:
                                        seller_info[key] = value
                        
                        # 전화번호와 이메일 모두 찾았으면 조기 종료
                        if '전화번호' in seller_info and '이메일' in seller_info:
                            break
                            
                except Exception as e:
                    continue
            
            # 우선순위 선택자로 못 찾았을 때만 전체 페이지 검색
            if not seller_info:
                print("🔍 전체 페이지에서 패턴 검색...")
                self._extract_from_full_page(seller_info)
            
            print(f"📋 최종 추출된 정보: {seller_info}")
            return seller_info
            
        except Exception as e:
            logger.error(f"정보 추출 실패: {e}")
            print(f"❌ 정보 추출 중 예외: {e}")
            return {}
    
    def _extract_from_container(self, container):
        """컨테이너에서 정보 추출 (중복 제거)"""
        from config import PHONE_KEYWORDS, EMAIL_KEYWORDS
        
        extracted = {}
        
        try:
            # dt/dd 패턴 시도
            labels = container.find_elements(By.CSS_SELECTOR, 'dt, ._1nqckXI-BW')
            values = container.find_elements(By.CSS_SELECTOR, 'dd, .EdE67hDR6I')
            
            if len(labels) == len(values):
                for label_elem, value_elem in zip(labels, values):
                    try:
                        label = label_elem.text.strip()
                        value = value_elem.text.strip()
                        
                        if not label or not value:
                            continue
                        
                        # 전화번호 확인 (중복 방지)
                        if any(keyword in label for keyword in PHONE_KEYWORDS) and '전화번호' not in extracted:
                            cleaned_phone = self._clean_phone_number(value)
                            if cleaned_phone:
                                extracted['전화번호'] = cleaned_phone
                                print(f"   ✅ 전화번호 발견: {cleaned_phone}")
                        
                        # 이메일 확인 (중복 방지)
                        elif any(keyword in label.lower() for keyword in EMAIL_KEYWORDS) and '이메일' not in extracted:
                            if '@' in value:
                                extracted['이메일'] = value
                                print(f"   ✅ 이메일 발견: {value}")
                        
                        # 둘 다 찾았으면 조기 종료
                        if len(extracted) == 2:
                            break
                            
                    except Exception:
                        continue
            
            # dt/dd 패턴으로 못 찾았고 아직 정보가 없으면 텍스트 파싱
            if not extracted:
                container_text = container.text.strip()
                if container_text:
                    extracted.update(self._parse_text_for_info(container_text))
            
            return extracted
            
        except Exception as e:
            return {}
    
    def _parse_text_for_info(self, text):
        """텍스트에서 정보 파싱 (최적화)"""
        from config import PHONE_KEYWORDS, EMAIL_KEYWORDS
        
        info = {}
        lines = text.split('\n')
        
        for line in lines:
            if ':' not in line:
                continue
                
            parts = line.split(':', 1)
            if len(parts) != 2:
                continue
                
            label = parts[0].strip()
            value = parts[1].strip()
            
            if not label or not value:
                continue
            
            # 전화번호 확인
            if any(keyword in label for keyword in PHONE_KEYWORDS) and '전화번호' not in info:
                cleaned_phone = self._clean_phone_number(value)
                if cleaned_phone:
                    info['전화번호'] = cleaned_phone
            
            # 이메일 확인
            elif any(keyword in label.lower() for keyword in EMAIL_KEYWORDS) and '이메일' not in info:
                if '@' in value:
                    info['이메일'] = value
            
            # 둘 다 찾았으면 조기 종료
            if len(info) == 2:
                break
        
        return info
    
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