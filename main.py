# main.py
"""
네이버 판매자 정보 수집기 메인 실행 파일
"""

import logging
from config import LOG_FORMAT, LOG_LEVEL, EXCEL_FILE_PATH
from collector import NaverSellerInfoCollector

def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT
    )

def main():
    """메인 함수"""
    # 로깅 설정
    setup_logging()
    
    # 수집기 실행
    collector = NaverSellerInfoCollector(EXCEL_FILE_PATH)
    collector.run()

if __name__ == "__main__":
    main()