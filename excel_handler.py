# excel_handler.py
"""
엑셀 파일 처리 모듈 (영업 종료 표기 개선)
"""

import pandas as pd
import logging
from datetime import datetime
from config import EXCEL_FILE_PATH, COLUMNS

logger = logging.getLogger(__name__)

class ExcelHandler:
    """엑셀 파일 처리 클래스"""
    
    def __init__(self, file_path=None):
        self.file_path = file_path or EXCEL_FILE_PATH
        self.df = None
    
    def load_data(self):
        """엑셀 파일 로드"""
        try:
            self.df = pd.read_excel(self.file_path)
            logger.info(f"엑셀 파일 로드 완료: {len(self.df)}개 행")
            return True
        except Exception as e:
            logger.error(f"엑셀 파일 로드 실패: {e}")
            raise
    
    def filter_naver_stores(self):
        """네이버 스마트스토어만 필터링 (영업종료 및 최신화 완료 제외) - 디버깅 강화"""
        try:
            # 네이버 스마트스토어 URL만 필터링
            naver_stores = self.df[
                self.df[COLUMNS['STORE_URL']].str.contains('smartstore.naver.com', na=False)
            ].copy()
            
            total_naver_stores = len(naver_stores)
            print(f"🔍 디버깅: 전체 네이버 스토어 {total_naver_stores}개 발견")
            
            # 영업종료 항목 디버깅
            phone_col = COLUMNS['UPDATED_PHONE']
            if phone_col in naver_stores.columns:
                # 영업종료로 시작하는 항목들 확인
                closed_mask = naver_stores[phone_col].astype(str).str.startswith('영업종료', na=False)
                closed_stores = naver_stores[closed_mask]
                
                if len(closed_stores) > 0:
                    print(f"🔍 디버깅: 영업종료 표기된 스토어 {len(closed_stores)}개 발견:")
                    for idx, row in closed_stores.head(5).iterrows():  # 최대 5개만 출력
                        store_name = row.get(COLUMNS['COMPANY_NAME'], 'Unknown')
                        phone_value = row.get(phone_col, 'None')
                        print(f"   - {store_name}: {phone_value}")
                else:
                    print("🔍 디버깅: 영업종료 표기된 스토어 없음")
            
            # 1. 영업종료로 표기된 항목 제외
            before_closed_filter = len(naver_stores)
            naver_stores = naver_stores[
                ~(naver_stores[COLUMNS['UPDATED_PHONE']].astype(str).str.startswith('영업종료', na=False))
            ]
            closed_filtered_count = before_closed_filter - len(naver_stores)
            
            # 2. 이미 최신화된 항목 제외
            before_completed_filter = len(naver_stores)
            completed_mask = (
                # 전화번호와 이메일이 모두 있고
                (naver_stores[COLUMNS['UPDATED_PHONE']].notna() & 
                 naver_stores[COLUMNS['UPDATED_EMAIL']].notna()) &
                # 둘 다 빈 문자열이 아니고
                (naver_stores[COLUMNS['UPDATED_PHONE']].astype(str).str.strip() != '') &
                (naver_stores[COLUMNS['UPDATED_EMAIL']].astype(str).str.strip() != '') &
                # ERROR로 시작하지 않는 경우
                (~naver_stores[COLUMNS['UPDATED_PHONE']].astype(str).str.startswith('ERROR', na=False))
            )
            
            completed_stores = naver_stores[completed_mask]
            if len(completed_stores) > 0:
                print(f"🔍 디버깅: 최신화 완료된 스토어 {len(completed_stores)}개 발견:")
                for idx, row in completed_stores.head(3).iterrows():  # 최대 3개만 출력
                    store_name = row.get(COLUMNS['COMPANY_NAME'], 'Unknown')
                    phone_value = row.get(COLUMNS['UPDATED_PHONE'], 'None')
                    email_value = row.get(COLUMNS['UPDATED_EMAIL'], 'None')
                    print(f"   - {store_name}: {phone_value} / {email_value}")
            
            naver_stores = naver_stores[~completed_mask]
            completed_filtered_count = before_completed_filter - len(naver_stores)
            
            # 아래에서 위로 처리하기 위해 역순으로 정렬
            naver_stores = naver_stores.iloc[::-1].reset_index(drop=True)
            
            remaining_count = len(naver_stores)
            
            # 처리할 스토어 미리보기
            if remaining_count > 0:
                print(f"🔍 디버깅: 처리 예정 스토어 미리보기:")
                for idx, row in naver_stores.head(3).iterrows():  # 최대 3개만 출력
                    store_name = row.get(COLUMNS['COMPANY_NAME'], 'Unknown')
                    phone_value = row.get(COLUMNS['UPDATED_PHONE'], 'None')
                    print(f"   - {store_name}: {phone_value}")
            
            # 로그 출력
            logger.info(f"전체 네이버 스토어: {total_naver_stores}개")
            if closed_filtered_count > 0:
                logger.info(f"영업종료 제외: {closed_filtered_count}개")
            if completed_filtered_count > 0:
                logger.info(f"이미 최신화 완료: {completed_filtered_count}개 (건너뜀)")
            logger.info(f"처리할 네이버 스토어: {remaining_count}개 (아래에서 위로)")
            
            return naver_stores, remaining_count
            
        except Exception as e:
            logger.error(f"네이버 스토어 필터링 실패: {e}")
            raise
    
    def mark_as_closed(self, store_info):
        """스토어를 영업 종료로 표기"""
        try:
            # 해당 행 찾기 (상호명으로 매칭)
            store_name = store_info[COLUMNS['COMPANY_NAME']]
            
            # 인덱스 찾기
            mask = self.df[COLUMNS['COMPANY_NAME']] == store_name
            indices = self.df[mask].index
            
            if len(indices) > 0:
                idx = indices[0]
                
                # 현재 날짜
                current_date = datetime.now().strftime('%Y%m%d')
                
                # 영업종료 표기
                closed_mark = f"영업종료_{current_date}"
                
                # 최신화 전화번호 컬럼에 영업종료 표기
                self.df.loc[idx, COLUMNS['UPDATED_PHONE']] = closed_mark
                
                logger.info(f"✅ 영업종료 표기 완료: {store_name}")
                return True
            else:
                logger.warning(f"⚠️ 매칭되는 행을 찾을 수 없음: {store_name}")
                return False
                
        except Exception as e:
            logger.error(f"영업종료 표기 실패: {e}")
            return False
    
    def update_seller_info(self, store_info, seller_info):
        """판매자 정보 업데이트"""
        try:
            # 해당 행 찾기 (상호명으로 매칭)
            store_name = store_info[COLUMNS['COMPANY_NAME']]
            
            # 인덱스 찾기
            mask = self.df[COLUMNS['COMPANY_NAME']] == store_name
            indices = self.df[mask].index
            
            if len(indices) > 0:
                idx = indices[0]
                
                # 최신화 정보 업데이트
                if '전화번호' in seller_info and seller_info['전화번호']:
                    self.df.loc[idx, COLUMNS['UPDATED_PHONE']] = seller_info['전화번호']
                    
                if '이메일' in seller_info and seller_info['이메일']:
                    self.df.loc[idx, COLUMNS['UPDATED_EMAIL']] = seller_info['이메일']
                
                logger.info(f"✅ 엑셀 업데이트 완료: {store_name}")
                return True
            else:
                logger.warning(f"⚠️ 매칭되는 행을 찾을 수 없음: {store_name}")
                return False
                
        except Exception as e:
            logger.error(f"엑셀 업데이트 실패: {e}")
            return False
    
    def log_error(self, store_info, error_msg):
        """에러 정보를 엑셀에 기록"""
        try:
            # 해당 행 찾기
            store_name = store_info[COLUMNS['COMPANY_NAME']]
            mask = self.df[COLUMNS['COMPANY_NAME']] == store_name
            indices = self.df[mask].index
            
            if len(indices) > 0:
                idx = indices[0]
                
                # 에러 정보를 최신화 전화번호 컬럼에 기록
                if COLUMNS['UPDATED_PHONE'] in self.df.columns:
                    self.df.loc[idx, COLUMNS['UPDATED_PHONE']] = f"ERROR: {error_msg}"
                
                logger.info(f"에러 정보 기록: {store_name} - {error_msg}")
                
        except Exception as e:
            logger.error(f"에러 로그 기록 실패: {e}")
    
    def save(self):
        """엑셀 파일 저장"""
        try:
            self.df.to_excel(self.file_path, index=False)
            logger.info(f"📁 엑셀 파일 저장 완료: {self.file_path}")
            return self.file_path
        except Exception as e:
            logger.error(f"파일 저장 실패: {e}")
            return None
    
    def get_dataframe(self):
        """데이터프레임 반환"""
        return self.df