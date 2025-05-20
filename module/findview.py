from playwright.sync_api import sync_playwright, TimeoutError
import time
import logging
import re

def setup_logging(log_file=None, logger=None):
    """로깅 설정 초기화 함수"""
    if logger is None:
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
        logger = logging.getLogger(__name__)
    return logger

def find_post_views(username, post_id, logger=None):
    """
    인스타그램 사용자의 프로필에서 특정 post_id의 조회수를 찾는 함수
    
    Args:
        username: 인스타그램 사용자 이름
        post_id: 찾고자 하는 포스트/릴 ID
        logger: 로거 인스턴스 (없으면 새로 생성)
        
    Returns:
        str: 포스트 조회수 (원본 문자열 그대로, 예: "3.8만") 또는 찾지 못한 경우 None
    """
    if logger is None:
        logger = setup_logging()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        try:
            # 사용자의 reels 페이지로 이동
            profile_url = f"https://www.instagram.com/{username}/reels/"
            logger.info(f"Navigating to: {profile_url}")
            print(f"Navigating to: {profile_url}")
            
            page.goto(profile_url, wait_until="networkidle")
            time.sleep(2)  # 페이지 안정화 대기
            
            # mount ID 찾기
            mount_elements = page.query_selector_all('[id^="mount_"]')
            mount_id = None
            
            if mount_elements:
                mount_id = mount_elements[0].get_attribute("id")
                logger.info(f"Mount ID found: {mount_id}")
            else:
                mount_id = "mount_0_0"  # 기본값
                logger.warning("Mount element not found, using default mount_0_0")
            
            print(f"Using mount ID: {mount_id}")
            
            # 찾고자 하는 post_id가 포함된 링크 검색
            found_post = False
            max_scrolls = 5
            scroll_count = 0
            post_link_element = None
            
            while not found_post and scroll_count < max_scrolls:
                # 현재 페이지에서 모든 링크 요소 검색
                all_links = page.query_selector_all("a")
                
                for link in all_links:
                    href = link.get_attribute("href")
                    if href and post_id in href:
                        logger.info(f"Found post link: {href}")
                        print(f"Found post link: {href}")
                        post_link_element = link
                        found_post = True
                        break
                
                if not found_post:
                    # 스크롤 다운
                    scroll_count += 1
                    logger.info(f"Scrolling down ({scroll_count}/{max_scrolls})")
                    print(f"Scrolling down ({scroll_count}/{max_scrolls})")
                    
                    page.evaluate("window.scrollBy(0, 1500)")
                    time.sleep(2)  # 스크롤 후 로딩 대기
            
            if not found_post:
                logger.warning(f"Post with ID {post_id} not found after {max_scrolls} scrolls")
                print(f"Post with ID {post_id} not found after {max_scrolls} scrolls")
                return None
            
            # 조회수 추출 시도
            try:
                # 링크 요소에서 조회수가 있는 요소 찾기
                views_selector = "span.html-span.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x1hl2dhg.x16tdsg8.x1vvkbs"
                
                # 링크 주변 컨테이너에서 조회수 요소 찾기 (여러 방법 시도)
                view_element = None
                
                # 방법 1: 직접 링크 내부의 span 요소 찾기
                spans_in_link = post_link_element.query_selector_all("span")
                for span in spans_in_link:
                    text = span.inner_text()
                    if text and any(char.isdigit() for char in text):
                        logger.info(f"Found view count in span: {text}")
                        view_element = span
                        break
                
                # 방법 2: 링크의 부모-자식 관계를 탐색하여 조회수 요소 찾기
                if not view_element:
                    # 링크의 부모 컨테이너에서 조회수 관련 요소 탐색
                    container = post_link_element.evaluate("el => el.closest('div[role=\"button\"]')")
                    if container:
                        spans = page.query_selector_all(f"#{mount_id} div[role=\"button\"] span")
                        for span in spans:
                            text = span.inner_text()
                            if text and any(char.isdigit() for char in text):
                                logger.info(f"Found view count in container: {text}")
                                view_element = span
                                break
                
                # 방법 3: XPath를 사용하여 조회수 요소 찾기
                if not view_element:
                    try:
                        # 링크 주변 영역에서 텍스트를 포함하는 span 요소들 검색
                        nearby_spans = page.query_selector_all(f"#{mount_id} div section main div div div div div div span")
                        for span in nearby_spans:
                            text = span.inner_text()
                            if text and any(char.isdigit() for char in text):
                                logger.info(f"Found view count in nearby span: {text}")
                                view_element = span
                                break
                    except Exception as e:
                        logger.error(f"Error when trying XPath approach: {e}")
                
                if view_element:
                    view_count = view_element.inner_text()
                    logger.info(f"Extracted view count: {view_count}")
                    print(f"Extracted view count: {view_count}")
                    return view_count
                else:
                    logger.warning("View count element not found")
                    print("View count element not found")
                    return None
                
            except Exception as e:
                logger.error(f"Error extracting view count: {e}")
                print(f"Error extracting view count: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error during post view search: {e}")
            print(f"Error during post view search: {e}")
            return None
            
        finally:
            browser.close()

# 단독 실행 테스트용 코드
if __name__ == "__main__":
    username = "inssa_elf"
    post_id = "DJtP6KJO4lF"
    views = find_post_views(username, post_id)
    
    if views:
        print(f"Post {post_id} by {username} has {views} views")
    else:
        print(f"Could not find view count for post {post_id} by {username}")