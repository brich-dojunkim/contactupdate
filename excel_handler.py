# excel_handler.py
"""
CSV 파일 처리 모듈 (엑셀 → CSV 변경)
"""

import pandas as pd
import logging
from datetime import datetime
from config import EXCEL_FILE_PATH, COLUMNS

logger = logging.getLogger(__name__)

class ExcelHandler:
    """CSV 파일 처리 클래스 (이름은 유지, 실제로는 CSV 처리)"""
    
    def __init__(self, file_path=None):
        self.file_path = file_path or EXCEL_FILE_PATH
        # 확장자를 CSV로 변경
        if self.file_path.endswith('.xlsx'):
            self.file_path = self.file_path.replace('.xlsx', '.csv')
        self.df = None
    
    def load_data(self):
        """CSV 파일 직접 로드"""
        try:
            # CSV 파일만 읽기
            self.df = pd.read_csv(self.file_path, encoding='utf-8')
            logger.info(f"CSV 파일 로드 완료: {len(self.df)}개 행")
            print(f"📁 CSV 파일 로드: {self.file_path} ({len(self.df)}개 행)")
            return True
        except FileNotFoundError:
            logger.error(f"CSV 파일을 찾을 수 없음: {self.file_path}")
            print(f"❌ CSV 파일을 찾을 수 없습니다: {self.file_path}")
            print(f"   현재 경로에 {self.file_path} 파일이 있는지 확인해주세요.")
            raise
        except Exception as e:
            logger.error(f"CSV 파일 로드 실패: {e}")
            print(f"❌ CSV 파일 로드 실패: {e}")
            raise
    
    def filter_naver_stores(self):
        """네이버 스마트스토어만 필터링 (영업종료 및 최신화 완료 제외)"""
        try:
            # 네이버 스마트스토어 URL만 필터링
            naver_stores = self.df[
                self.df[COLUMNS['STORE_URL']].str.contains('smartstore.naver.com', na=False)
            ].copy()
            
            total_naver_stores = len(naver_stores)
            print(f"🔍 전체 네이버 스토어 {total_naver_stores}개 발견")
            
            # 영업종료 항목 확인
            phone_col = COLUMNS['UPDATED_PHONE']
            if phone_col in naver_stores.columns:
                closed_mask = naver_stores[phone_col].astype(str).str.startswith('영업종료', na=False)
                closed_stores = naver_stores[closed_mask]
                
                if len(closed_stores) > 0:
                    print(f"🔍 영업종료 표기된 스토어 {len(closed_stores)}개 발견")
                    for idx, row in closed_stores.head(3).iterrows():
                        store_name = row.get(COLUMNS['COMPANY_NAME'], 'Unknown')
                        phone_value = row.get(phone_col, 'None')
                        print(f"   - {store_name}: {phone_value}")
            
            # 1. 영업종료로 표기된 항목 제외
            before_closed_filter = len(naver_stores)
            naver_stores = naver_stores[
                ~(naver_stores[COLUMNS['UPDATED_PHONE']].astype(str).str.startswith('영업종료', na=False))
            ]
            closed_filtered_count = before_closed_filter - len(naver_stores)
            
            # 2. 이미 최신화된 항목 제외
            before_completed_filter = len(naver_stores)
            completed_mask = (
                (naver_stores[COLUMNS['UPDATED_PHONE']].notna() & 
                 naver_stores[COLUMNS['UPDATED_EMAIL']].notna()) &
                (naver_stores[COLUMNS['UPDATED_PHONE']].astype(str).str.strip() != '') &
                (naver_stores[COLUMNS['UPDATED_EMAIL']].astype(str).str.strip() != '') &
                (~naver_stores[COLUMNS['UPDATED_PHONE']].astype(str).str.startswith('ERROR', na=False))
            )
            
            naver_stores = naver_stores[~completed_mask]
            completed_filtered_count = before_completed_filter - len(naver_stores)
            
            # 아래에서 위로 처리하기 위해 역순으로 정렬
            naver_stores = naver_stores.iloc[::-1].reset_index(drop=True)
            
            remaining_count = len(naver_stores)
            
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
        """스토어를 영업 종료로 표기 (CSV 실시간 저장)"""
        try:
            store_name = store_info[COLUMNS['COMPANY_NAME']]
            
            # 인덱스 찾기
            mask = self.df[COLUMNS['COMPANY_NAME']] == store_name
            indices = self.df[mask].index
            
            if len(indices) > 0:
                idx = indices[0]
                
                # 현재 날짜
                current_date = datetime.now().strftime('%Y%m%d')
                closed_mark = f"영업종료_{current_date}"
                
                # 업데이트
                before_value = self.df.loc[idx, COLUMNS['UPDATED_PHONE']]
                self.df.loc[idx, COLUMNS['UPDATED_PHONE']] = closed_mark
                after_value = self.df.loc[idx, COLUMNS['UPDATED_PHONE']]
                
                print(f"   📝 {before_value} → {after_value}")
                
                # 즉시 저장
                saved_file = self.save()
                if saved_file:
                    logger.info(f"✅ 영업종료 실시간 저장 완료: {store_name}")
                    return True
                else:
                    logger.error(f"❌ 영업종료 저장 실패: {store_name}")
                    return False
            else:
                logger.warning(f"⚠️ 매칭되는 행을 찾을 수 없음: {store_name}")
                return False
                
        except Exception as e:
            logger.error(f"영업종료 표기 실패: {e}")
            return False
    
    def update_seller_info(self, store_info, seller_info):
        """판매자 정보 업데이트 (CSV 실시간 저장)"""
        try:
            store_name = store_info[COLUMNS['COMPANY_NAME']]
            
            # 인덱스 찾기
            mask = self.df[COLUMNS['COMPANY_NAME']] == store_name
            indices = self.df[mask].index
            
            if len(indices) > 0:
                idx = indices[0]
                
                # 최신화 정보 업데이트
                updated_fields = []
                if '전화번호' in seller_info and seller_info['전화번호']:
                    self.df.loc[idx, COLUMNS['UPDATED_PHONE']] = seller_info['전화번호']
                    updated_fields.append('전화번호')
                    
                if '이메일' in seller_info and seller_info['이메일']:
                    self.df.loc[idx, COLUMNS['UPDATED_EMAIL']] = seller_info['이메일']
                    updated_fields.append('이메일')
                
                # 즉시 저장
                if updated_fields:
                    saved_file = self.save()
                    if saved_file:
                        logger.info(f"✅ 실시간 업데이트 완료: {store_name} ({', '.join(updated_fields)})")
                        return True
                    else:
                        logger.error(f"❌ 실시간 저장 실패: {store_name}")
                        return False
                else:
                    logger.warning(f"⚠️ 업데이트할 정보 없음: {store_name}")
                    return False
            else:
                logger.warning(f"⚠️ 매칭되는 행을 찾을 수 없음: {store_name}")
                return False
                
        except Exception as e:
            logger.error(f"정보 업데이트 실패: {e}")
            return False
    
    def log_error(self, store_info, error_msg):
        """에러 정보를 CSV에 기록 (실시간 저장)"""
        try:
            store_name = store_info[COLUMNS['COMPANY_NAME']]
            mask = self.df[COLUMNS['COMPANY_NAME']] == store_name
            indices = self.df[mask].index
            
            if len(indices) > 0:
                idx = indices[0]
                
                if COLUMNS['UPDATED_PHONE'] in self.df.columns:
                    self.df.loc[idx, COLUMNS['UPDATED_PHONE']] = f"ERROR: {error_msg}"
                
                # 즉시 저장
                self.save()
                logger.info(f"에러 정보 실시간 저장: {store_name} - {error_msg}")
                
        except Exception as e:
            logger.error(f"에러 로그 기록 실패: {e}")
    
    def save(self):
        """CSV 파일 저장 (매우 빠름)"""
        try:
            # CSV로 저장 (UTF-8 인코딩)
            self.df.to_csv(self.file_path, index=False, encoding='utf-8')
            logger.info(f"💾 CSV 파일 저장 완료: {self.file_path}")
            return self.file_path
            
        except Exception as e:
            logger.error(f"❌ CSV 저장 실패: {e}")
            print(f"   ❌ CSV 저장 실패: {e}")
            return None
    
    def get_dataframe(self):
        """데이터프레임 반환"""
        return self.df