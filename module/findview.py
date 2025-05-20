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

def find_post_views(username, post_id, logger=None, content_type='reels', page=None):
    """
    인스타그램 사용자의 프로필에서 특정 post_id의 조회수를 찾는 함수
    
    Args:
        username: 인스타그램 사용자 이름
        post_id: 찾고자 하는 포스트/릴 ID
        logger: 로거 인스턴스 (없으면 새로 생성)
        content_type: 컨텐츠 타입 ('post' 또는 'reels', 기본값: 'reels')
        page: 기존 Playwright 페이지 객체 (없으면 새로 생성)
        
    Returns:
        str: 포스트 조회수 (원본 문자열 그대로, 예: "3.8만") 또는 찾지 못한 경우 None
    """
    if logger is None:
        logger = setup_logging()
        
    # 일반 포스트인 경우 조회수 추출 건너뛰기
    if content_type == 'post':
        logger.info("Content type is 'post', skipping view count extraction")
        print("Content type is 'post', skipping view count extraction")
        return None
    
    # 페이지 객체가 제공되지 않은 경우 새로 생성 (독립 실행용)
    should_close_browser = False
    if page is None:
        should_close_browser = True
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()
            
            try:
                # 로직 실행 후 결과 반환
                return _find_views_logic(page, username, post_id, logger)
            finally:
                browser.close()
    else:
        # 기존 페이지 객체 사용
        return _find_views_logic(page, username, post_id, logger)

def _find_views_logic(page, username, post_id, logger):
    """조회수 추출 로직을 분리한 내부 함수"""
    try:
        # 사용자의 reels 페이지로 이동
        profile_url = f"https://www.instagram.com/{username}/reels/"
        logger.info(f"Navigating to: {profile_url}")
        print(f"Navigating to: {profile_url}")
        
        # 먼저 쿠키가 제대로 설정되도록 인스타그램 홈페이지 방문
        page.goto("https://www.instagram.com/")
        print("Visited homepage to maintain session")
        time.sleep(2)
        
        # 이제 프로필 페이지로 이동 (타임아웃 늘리고 대기 조건 변경)
        try:
            print(f"Navigating to profile page with increased timeout...")
            page.goto(profile_url, wait_until="load", timeout=60000)  # 60초 타임아웃, load 이벤트만 기다림
            print("Profile page loaded, waiting for content to stabilize...")
            time.sleep(5)  # 페이지 안정화를 위해 더 오래 대기
        except Exception as e:
            print(f"Navigation timeout, but continuing anyway: {e}")
            # 타임아웃이 발생해도 계속 진행
        
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
        
        # 조회수 추출 시도 - crawler.py와 동일한 방법 사용
        try:
            print("Found post link, attempting to extract view count...")
            
            # 방법 1: 선택자 문제를 피하기 위해 JavaScript로 직접 자식 요소 탐색
            # 업데이트된 경로: div[2]/div[2]/div/div/div/span/span
            print("Using JavaScript DOM navigation approach with updated path...")
            logger.info("Using JavaScript DOM navigation approach with updated path...")
            
            view_count = post_link_element.evaluate("""
                link => {
                    console.log("Link children:", link.children.length);
                    
                    // Log HTML structure for debugging
                    console.log("Link HTML structure:", link.outerHTML.substring(0, 500) + "...");
                    
                    // Get second div child (div[2])
                    if (link.children.length < 2) {
                        console.log("Link has fewer than 2 children");
                        return null;
                    }
                    
                    // Navigate to div:nth-child(2)
                    const div2 = link.children[1];
                    console.log("Found div:nth-child(2), children:", div2.children.length);
                    
                    // Get second div in div2 (div[2]/div[2])
                    if (div2.children.length < 2) {
                        console.log("Div2 has fewer than 2 children");
                        return null;
                    }
                    const innerDiv = div2.children[1]; // Get second div
                    console.log("Found inner div (second child)");
                    
                    // Find div in innerDiv (div[2]/div[2]/div)
                    const divLevel3 = innerDiv.querySelector('div');
                    if (!divLevel3) {
                        console.log("No div level 3 found");
                        return null;
                    }
                    console.log("Found div level 3");
                    
                    // Find div in divLevel3 (div[2]/div[2]/div/div)
                    const divLevel4 = divLevel3.querySelector('div');
                    if (!divLevel4) {
                        console.log("No div level 4 found");
                        return null;
                    }
                    console.log("Found div level 4");
                    
                    // Find div in divLevel4 (div[2]/div[2]/div/div/div)
                    const divLevel5 = divLevel4.querySelector('div');
                    if (!divLevel5) {
                        console.log("No div level 5 found");
                        return null;
                    }
                    console.log("Found div level 5");
                    
                    // Find span in divLevel5 (div[2]/div[2]/div/div/div/span)
                    const spanContainer = divLevel5.querySelector('span');
                    if (!spanContainer) {
                        console.log("No span container found");
                        return null;
                    }
                    console.log("Found span container");
                    
                    // Find span in spanContainer (div[2]/div[2]/div/div/div/span/span)
                    const viewSpan = spanContainer.querySelector('span');
                    if (!viewSpan) {
                        console.log("No view span found");
                        return null;
                    }
                    console.log("Found view span with text:", viewSpan.innerText);
                    
                    return viewSpan.innerText;
                }
            """)
            
            if view_count:
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
        # 외부에서 전달된 page 객체는 여기서 닫지 않음
        pass

# 단독 실행 테스트용 코드
if __name__ == "__main__":
    import argparse
    
    # 테스트용 명령행 인자 설정
    parser = argparse.ArgumentParser(description='Instagram View Count Finder')
    parser.add_argument('-u', '--username', default="inssa_elf", help='Instagram username')
    parser.add_argument('-id', '--post_id', default="DJtP6KJO4lF", help='Post or Reels ID')
    parser.add_argument('-t', '--type', choices=['post', 'reels'], default='reels', help='Content type (post or reels)')
    
    args = parser.parse_args()
    
    # 테스트 실행
    views = find_post_views(args.username, args.post_id, content_type=args.type)
    
    if views:
        print(f"{args.type.capitalize()} {args.post_id} by {args.username} has {views} views")
    else:
        print(f"Could not find view count for {args.type} {args.post_id} by {args.username}")