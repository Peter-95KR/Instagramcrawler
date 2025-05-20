from playwright.sync_api import sync_playwright
import logging
import re
import json
import os
from datetime import datetime

# 로깅 설정
def setup_logging(log_file=None):
    """로깅 설정을 초기화하는 함수"""
    # 로깅 설정 기본 정의
    config = {
        'level': logging.INFO,
        'format': '%(asctime)s - %(levelname)s - %(message)s',
    }
    
    # 로그 파일이 지정된 경우, 파일에도 로깅
    if log_file:
        config['filename'] = log_file
        config['filemode'] = 'a'
    
    # 설정 적용
    logging.basicConfig(**config)
    return logging.getLogger(__name__)

def normalize_instagram_url(url):
    """
    Instagram URL을 표준 형식으로 변환하는 함수
    reel, reels 형식 URL을 /p/ 형식으로 통일
    
    Args:
        url: Instagram URL
        
    Returns:
        str: 정규화된 Instagram URL
    """
    # ID 추출
    pattern = r'/(p|reel|reels)/([A-Za-z0-9_-]+)'
    match = re.search(pattern, url)
    
    if match:
        post_id = match.group(2)
        # /p/ 형식으로 URL 재구성
        return f"https://www.instagram.com/p/{post_id}/"
    
    # 매치되지 않으면 원본 URL 반환
    return url

def extract_reel_id(url):
    """Instagram URL에서 Reel ID 추출하는 함수"""
    pattern = r'/(p|reel|reels)/([A-Za-z0-9_-]+)'
    match = re.search(pattern, url)
    if match:
        return match.group(2)
    return None

def extract_username(description):
    """OG description에서 사용자 이름 추출하는 함수"""
    pattern = r'- (\w+) on'
    match = re.search(pattern, description)
    if match:
        return match.group(1)
    return None

def extract_date(description):
    """OG description에서 작성일 추출하는 함수"""
    pattern = r'on ([A-Za-z]+ \d+, \d{4}):'
    match = re.search(pattern, description)
    if match:
        return match.group(1)
    return None

def get_post_info(url, logger=None):
    """
    Instagram 포스트 정보를 스크랩하는 함수
    
    Args:
        url: Instagram 포스트의 URL
        logger: 로거 인스턴스 (없으면 새로 생성)
        
    Returns:
        dict: 포스트 정보를 담은 딕셔너리 또는 실패 시 None
    """
    if logger is None:
        logger = setup_logging()
    
    # URL 정규화
    url = normalize_instagram_url(url)
    logger.info(f"정규화된 URL: {url}")
        
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        try:
            # 페이지 로드
            page.goto(url, wait_until="networkidle")
            
            # OG 설명 추출
            og_description = page.evaluate('''() => {
                const meta_tag = document.querySelector('meta[property="og:description"]');
                return meta_tag ? meta_tag.getAttribute('content') : null;
            }''')
            
            if not og_description:
                logger.warning(f"URL: {url}, OG Description 태그를 찾을 수 없습니다.")
                return None
            
            # 좋아요 수 및 댓글 수 추출 (OG description에서 파싱)
            likes_match = re.search(r'(\d+) likes', og_description)
            comments_match = re.search(r'(\d+) comments', og_description)
            
            likes = int(likes_match.group(1)) if likes_match else None
            comments = int(comments_match.group(1)) if comments_match else None
            
            # 사용자 이름 및 작성일 추출
            username = extract_username(og_description)
            post_date = extract_date(og_description)
            
            # 실제 description 내용 추출 (콜론 이후의 텍스트)
            description_content = og_description.split(':', 1)[1].strip() if ':' in og_description else ""
            
            # 결과 생성
            post_id = extract_reel_id(url)
            result = {
                "post_id": post_id,
                "username": username,
                "post_date": post_date,
                "likes": likes,
                "comments_count": comments,
                "description": description_content,
                "url": url,
                "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"URL: {url}, 데이터 추출 성공")
            return result
                
        except Exception as e:
            logger.error(f"URL: {url}, 에러 발생: {str(e)}")
            print(f"에러 발생: {str(e)}")
            return None
        finally:
            browser.close()

def save_to_json(data, filename="instagram_data.json", logger=None):
    """
    데이터를 JSON 파일로 저장하는 함수
    
    Args:
        data: 저장할 데이터 (딕셔너리 또는 리스트)
        filename: 저장할 파일 이름
        logger: 로거 인스턴스 (없으면 새로 생성)
        
    Returns:
        bool: 성공 시 True, 실패 시 False
    """
    if logger is None:
        logger = setup_logging()
        
    try:
        # 현재 시간으로 타임스탬프 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 파일 이름에 타임스탬프 추가 (확장자 앞에)
        base_name, ext = os.path.splitext(filename)
        filename_with_timestamp = f"{base_name}_{timestamp}{ext}"
        
        with open(filename_with_timestamp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"{filename_with_timestamp} 파일에 데이터 저장 완료")
        print(f"{filename_with_timestamp} 파일에 데이터 저장 완료")
        return filename_with_timestamp
    except Exception as e:
        logger.error(f"JSON 저장 중 에러 발생: {str(e)}")
        print(f"JSON 저장 중 에러 발생: {str(e)}")
        return False