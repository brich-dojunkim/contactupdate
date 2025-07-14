# collector.py
"""
네이버 판매자 정보 수집기 메인 클래스 (최적화 완료 + 영업종료 표기)
"""

import logging
import time
import pandas as pd

from config import EXCEL_FILE_PATH, COLUMNS, INTER_STORE_DELAY, SELLER_INFO_BUTTON_XPATH
from excel_handler import ExcelHandler
from browser_handler import BrowserHandler

logger = logging.getLogger(__name__)

class NaverSellerInfoCollector:
    """네이버 판매자 정보 수집기"""
    
    def __init__(self, excel_file_path=None):
        self.excel_file_path = excel_file_path or EXCEL_FILE_PATH
        self.excel_handler = ExcelHandler(self.excel_file_path)
        self.browser_handler = BrowserHandler()
        self.processed_count = 0
        self.total_count = 0
    
    def setup(self):
        """초기 설정"""
        try:
            # 엑셀 데이터 로드
            self.excel_handler.load_data()
            
            # 브라우저 설정
            self.browser_handler.setup_driver()
            
            logger.info("초기 설정 완료")
            return True
            
        except Exception as e:
            logger.error(f"초기 설정 실패: {e}")
            return False
    
    def cleanup(self):
        """정리 작업"""
        self.browser_handler.close_driver()
    
    def process_single_store(self, store_info):
        """단일 스토어 처리 (개선된 캡차 처리)"""
        try:
            store_name = store_info[COLUMNS['COMPANY_NAME']]
            store_url = store_info[COLUMNS['STORE_URL']]
            
            # 실제 엑셀 행 번호 찾기
            original_df = self.excel_handler.get_dataframe()
            actual_row = None
            for idx, row in original_df.iterrows():
                if row[COLUMNS['COMPANY_NAME']] == store_name:
                    actual_row = idx + 2
                    break
            
            if actual_row is None:
                actual_row = "알 수 없음"
            
            self.processed_count += 1
            
            print(f"\n📍 스토어 처리 중: {store_name} ({self.processed_count}/{self.total_count})")
            print(f"📊 엑셀 행 번호: {actual_row}")
            print(f"🔗 URL: {store_url}")
            
            # 현재 최신화 상태 확인
            current_phone = store_info.get(COLUMNS['UPDATED_PHONE'], '')
            current_email = store_info.get(COLUMNS['UPDATED_EMAIL'], '')
            
            # 이미 영업 종료로 표기된 경우 건너뛰기
            if (pd.notna(current_phone) and str(current_phone).strip().startswith('영업종료')):
                print(f"⏭️ 이미 영업종료로 표기됨 - 건너뜀")
                return True
            
            # 둘 다 이미 있으면 건너뛰기
            if (pd.notna(current_phone) and pd.notna(current_email) and 
                str(current_phone).strip() != '' and str(current_email).strip() != '' and
                not str(current_phone).strip().startswith('ERROR')):
                print(f"⏭️ 이미 최신화 완료됨 - 건너뜀")
                return True
            
            # 스토어 페이지 접속
            accessible, access_msg = self.browser_handler.check_page_accessibility(store_url)
            if not accessible:
                print(f"❌ {access_msg}")
                self.excel_handler.log_error(store_info, access_msg)
                return False
            
            # 판매자 정보 버튼 클릭
            print("🔍 판매자 정보 버튼을 찾는 중...")
            if not self.browser_handler.click_seller_info_button_with_scroll():
                print(f"❌ 영업 종료로 판단됨")
                # 영업 종료 표기 및 즉시 저장
                self.excel_handler.mark_as_closed(store_info)
                self.excel_handler.save()
                print(f"💾 영업종료 표기 저장 완료")
                return True  # 정상적인 건너뛰기로 처리
            
            print("✅ 판매자 정보 버튼 클릭 완료")
            
            # 캡차 처리 개선된 로직
            return self._handle_captcha_and_extract_info(store_info)
            
        except Exception as e:
            logger.error(f"스토어 처리 실패: {e}")
            self.excel_handler.log_error(store_info, f"처리 실패: {str(e)}")
            return False
    
    def _handle_captcha_and_extract_info(self, store_info, max_retries=3):
        """캡차 처리 및 정보 추출 (최적화)"""
        for attempt in range(max_retries):
            try:
                print(f"\n🔄 캡차 처리 시도 {attempt + 1}/{max_retries}")
                
                # 잠시 대기 후 창 변화로 캡차 감지
                time.sleep(1)  # 3초에서 1초로 단축
                
                # 창 변화로 캡차 확인
                has_captcha = self.browser_handler.detect_captcha_by_window_change()
                
                if not has_captcha:
                    print("✅ 캡차 없음 - 바로 정보 추출")
                    return self._extract_and_save_info(store_info)
                
                print("🔍 캡차 감지됨")
                
                # 사용자 입력 대기
                result = self.browser_handler.wait_for_captcha_completion()
                
                if result == "skip":
                    print("⏭️ 사용자 요청으로 건너뜀")
                    return False
                    
                elif result == "reload":
                    print("🔄 캡차 탭 닫고 다시 시도")
                    
                    # 캡차 페이지 닫기 (페이지 재로딩 없이)
                    if self.browser_handler.close_captcha_page():
                        print("✅ 캡차 탭 닫기 완료")
                        time.sleep(0.5)  # 2초에서 0.5초로 단축
                        
                        # 페이지 재로딩 없이 바로 다시 버튼 클릭
                        print("🔄 판매자 정보 버튼 다시 클릭...")
                        if self.browser_handler.click_seller_info_button_with_scroll():
                            print("✅ 버튼 재클릭 완료")
                            continue  # 다음 시도로
                        else:
                            print("❌ 재시도 버튼 클릭 실패")
                            return False
                    else:
                        print("❌ 캡차 탭 닫기 실패")
                        return False
                        
                elif result == "success":
                    print("✅ 캡차 완료 - 정보 추출 시도")
                    time.sleep(1)  # 2초에서 1초로 단축
                    
                    # 정보 추출 시도
                    return self._extract_and_save_info(store_info)
                
            except Exception as e:
                print(f"❌ 캡차 처리 시도 {attempt + 1} 실패: {e}")
                if attempt < max_retries - 1:
                    print("🔄 다음 시도 준비...")
                    time.sleep(1)  # 2초에서 1초로 단축
                    continue
                else:
                    print("❌ 모든 캡차 처리 시도 실패")
                    return False
        
        print("❌ 최대 재시도 횟수 초과")
        return False
    
    def _extract_and_save_info(self, store_info):
        """정보 추출 및 저장 (최적화)"""
        try:
            print("📋 판매자 정보 추출 중...")
            
            # 페이지 로드 대기 단축
            time.sleep(1)  # 3초에서 1초로 단축
            
            # 판매자 정보 추출
            seller_info = self.browser_handler.extract_seller_info()
            
            if seller_info:
                print(f"✅ 정보 추출 완료:")
                for key, value in seller_info.items():
                    print(f"   {key}: {value}")
                
                # 엑셀 업데이트 및 즉시 저장
                if self.excel_handler.update_seller_info(store_info, seller_info):
                    saved_file = self.excel_handler.save()
                    if saved_file:
                        print(f"💾 엑셀 저장 완료")
                    else:
                        print(f"💾 엑셀 업데이트 완료")
                    return True
                else:
                    print(f"⚠️ 엑셀 업데이트 실패")
                    return False
            else:
                print(f"❌ 정보 추출 실패")
                self.excel_handler.log_error(store_info, "정보 추출 실패")
                return False
                
        except Exception as e:
            logger.error(f"정보 추출 및 저장 실패: {e}")
            print(f"❌ 정보 추출 및 저장 중 오류: {e}")
            return False
    
    def run(self):
        """메인 실행 함수"""
        try:
            print("🚀 네이버 판매자 정보 수집 시작")
            print("📋 처리 방식: 아래에서 위로 (역순)")
            print("⏭️ 이미 최신화된 항목은 자동 건너뜀")
            print("🚫 영업종료 표기된 항목은 자동 제외")
            print("🔑 네이버 로그인이 필요합니다!")
            print("🎯 최적화된 캡차 처리 시스템 적용")
            print("="*60)
            
            # 1. 초기 설정
            if not self.setup():
                print("❌ 초기 설정 실패")
                return
            
            # 2. 네이버 스토어 필터링
            naver_stores, self.total_count = self.excel_handler.filter_naver_stores()
            
            if self.total_count == 0:
                print("❌ 처리할 네이버 스토어가 없습니다.")
                return
            
            # 3. 네이버 로그인 페이지로 이동
            print("🔑 네이버 로그인 페이지로 이동합니다...")
            self.browser_handler.navigate_to_url("https://nid.naver.com/nidlogin.login")
            print("브라우저에서 네이버에 로그인해주세요.")
            input("로그인 완료 후 Enter를 눌러주세요...")
            
            # 4. 각 스토어 처리
            success_count = 0
            
            for _, store_info in naver_stores.iterrows():
                try:
                    if self.process_single_store(store_info):
                        success_count += 1
                    
                    # 잠시 대기 (서버 부하 방지)
                    time.sleep(INTER_STORE_DELAY)
                    
                except KeyboardInterrupt:
                    print("\n⏹️ 사용자에 의해 중단됨")
                    break
                except Exception as e:
                    logger.error(f"스토어 처리 중 오류: {e}")
                    continue
            
            # 5. 최종 결과 요약
            failed_count = self.processed_count - success_count
            print("\n" + "="*60)
            print("📊 작업 완료 요약")
            print(f"총 스토어 수: {self.total_count}")
            print(f"처리 완료: {self.processed_count}")
            print(f"성공: {success_count}")
            print(f"실패: {failed_count}")
            if failed_count > 0:
                print(f"⚠️ 실패한 스토어들은 엑셀에 에러 메시지가 기록되었습니다.")
            print(f"📝 영업종료된 스토어들은 '영업종료_날짜' 형태로 표기되어 다음 실행시 제외됩니다.")
            print(f"최종 파일: {self.excel_file_path}")
            print("="*60)
            
        except Exception as e:
            logger.error(f"실행 중 오류: {e}")
        finally:
            self.cleanup()