# excel_handler.py
"""
엑셀 파일 처리 모듈
"""

import pandas as pd
import logging
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
        """네이버 스마트스토어만 필터링"""
        try:
            # 네이버 스마트스토어 URL만 필터링
            naver_stores = self.df[
                self.df[COLUMNS['STORE_URL']].str.contains('smartstore.naver.com', na=False)
            ].copy()
            
            # 이미 최신화된 항목 제외 (전화번호와 이메일이 모두 있는 경우)
            before_filter = len(naver_stores)
            naver_stores = naver_stores[
                (naver_stores[COLUMNS['UPDATED_PHONE']].isna() | (naver_stores[COLUMNS['UPDATED_PHONE']] == '')) |
                (naver_stores[COLUMNS['UPDATED_EMAIL']].isna() | (naver_stores[COLUMNS['UPDATED_EMAIL']] == ''))
            ]
            
            # 아래에서 위로 처리하기 위해 역순으로 정렬
            naver_stores = naver_stores.iloc[::-1].reset_index(drop=True)
            
            filtered_count = before_filter - len(naver_stores)
            total_count = len(naver_stores)
            
            logger.info(f"전체 네이버 스토어: {before_filter}개")
            logger.info(f"이미 최신화 완료: {filtered_count}개 (건너뜀)")
            logger.info(f"처리할 네이버 스토어: {total_count}개 (아래에서 위로)")
            
            return naver_stores, total_count
            
        except Exception as e:
            logger.error(f"네이버 스토어 필터링 실패: {e}")
            raise
    
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