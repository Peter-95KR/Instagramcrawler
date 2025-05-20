from playwright.sync_api import TimeoutError
import time
import datetime
import os
import json

def collect_instagram_comments(page, post_url):
    """
    Collect comments from an Instagram post
    
    Args:
        page: Playwright page instance
        post_url: URL of the Instagram post to scrape
        
    Returns:
        dict: Dictionary containing collected comments and metadata
    """
    try:
        # 2단계: 지정된 릴 페이지로 이동
        print(f"릴 페이지로 이동 중: {post_url}")
        page.goto(post_url, wait_until="load")
        print("기본 페이지 로드 완료")
        
        # 페이지 로딩 완료 확인을 위해 특정 요소 대기
        try:
            page.wait_for_selector('video, img[alt], section div ul, ul._a9ym, div.x5yr21d', 
                                state="visible", timeout=15000)
            print("페이지 주요 콘텐츠 로드됨")
        except TimeoutError:
            print("페이지 주요 콘텐츠를 찾을 수 없습니다. 계속 진행합니다...")
        
        # 추가 안전 대기 시간
        time.sleep(5)
        
        # 3단계: 동적 mount ID 찾기와 XPath 생성
        print("mount ID 찾는 중...")
        
        # 모든 mount 요소 찾기
        mount_elements = page.query_selector_all('[id^="mount_"]')
        mount_id = None
        
        if mount_elements:
            # 첫 번째 mount 요소의 ID 가져오기
            mount_id = mount_elements[0].get_attribute("id")
            print(f"mount ID 발견: {mount_id}")
        else:
            print("mount 요소를 찾을 수 없습니다.")
            mount_id = "mount_0_0"  # 기본값
        
        # 제공된 XPath에서 mount ID 부분만 바꾸기
        comments_xpath = f"//*[@id='{mount_id}']/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div[1]/div/div[2]/div/div[2]"
        print(f"사용할 XPath: {comments_xpath}")
        
        # 새로운 댓글 수집 방법 구현
        print("댓글 수집 시작...")
        all_collected_comments = {}  # 새로운 댓글 데이터 저장 구조
        # 이미 처리한 댓글의 고유 ID를 저장하는 세트
        processed_comment_ids = set()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 4단계: 댓글 영역 찾고 스크롤 다운
        try:
            # 댓글 영역 찾기
            comment_area = page.locator(f"xpath={comments_xpath}")
            is_visible = comment_area.is_visible()
            
            if is_visible:
                print("댓글 영역을 찾았습니다!")
                
                # 5단계: 댓글 영역에서 스크롤 수행
                print("댓글 영역에 마우스 올리고 스크롤 시작...")
                
                # 먼저 마우스를 댓글 영역으로 이동
                comment_area.hover()
                time.sleep(1)
                
                # 댓글 영역 내에서 스크롤 수행
                scroll_count = 0
                max_scrolls = 50  # 최대 스크롤 횟수
                previous_scroll_height = 0
                consecutive_same_height = 0
                total_new_comments = 0
                
                while scroll_count < max_scrolls:
                    # 현재 스크롤 높이 확인
                    current_scroll_height = page.evaluate(f"""
                        () => {{
                            const element = document.evaluate(
                                "{comments_xpath.replace('"', '\\"')}", 
                                document, 
                                null, 
                                XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                null
                            ).singleNodeValue;
                            
                            if (element) {{
                                return element.scrollHeight;
                            }}
                            return 0;
                        }}
                    """)
                    
                    # 모든 댓글 컨테이너를 순회하여 데이터 수집
                    print(f"스크롤 {scroll_count+1}/{max_scrolls} 후 댓글 수집 중...")
                    
                    # 새로 로드된 댓글 수집
                    comments_count_before = len(all_collected_comments)
                    new_comments_this_scroll = 0
                    
                    # 모든 댓글 컨테이너를 순회 
                    for comment_index in range(1, 500):  # 충분히 큰 범위 설정 
                        try:
                            # 먼저 특정 댓글이 실제로 존재하는지 확인
                            content_xpath = f"//*[@id='{mount_id}']/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div[1]/div/div[2]/div/div[2]/div/div[2]/div[{comment_index}]/div[1]/div/div[2]/div[1]/div[1]/div/div[2]/span"
                            
                            # 요소가 존재하는지 확인
                            if page.locator(f"xpath={content_xpath}").count() > 0:
                                # 댓글이 존재하면 더 상세한 내용 추출
                                content = page.locator(f"xpath={content_xpath}").inner_text()
                                
                                # 고유 식별자로 사용할 내용 해시 생성 (댓글 내용과 인덱스 조합)
                                comment_id = f"{comment_index}_{hash(content)}"
                                
                                # 이미 처리되지 않은 댓글만 추가
                                if comment_id not in processed_comment_ids:
                                    # 나머지 정보 추출
                                    try:
                                        author_xpath = f"//*[@id='{mount_id}']/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div[1]/div/div[2]/div/div[2]/div/div[2]/div[{comment_index}]/div[1]/div/div[2]/div[1]/div[1]/div/div[1]/span[1]/span/span/div/a/div/div/span"
                                        author = page.locator(f"xpath={author_xpath}").inner_text()
                                    except:
                                        author = "작성자 미상"
                                    
                                    try:
                                        date_xpath = f"//*[@id='{mount_id}']/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div[1]/div/div[2]/div/div[2]/div/div[2]/div[{comment_index}]/div[1]/div/div[2]/div[1]/div[1]/div/div[1]/span[2]/a/time"
                                        date = page.locator(f"xpath={date_xpath}").inner_text()
                                    except:
                                        date = ""
                                    
                                    try:
                                        likes_xpath = f"//*[@id='{mount_id}']/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div[1]/div/div[2]/div/div[2]/div/div[2]/div[{comment_index}]/div[1]/div/div[2]/div[1]/div[2]/div[1]/span/span"
                                        if page.locator(f"xpath={likes_xpath}").count() > 0:
                                            likes = page.locator(f"xpath={likes_xpath}").inner_text()
                                            # "답글 달기"가 텍스트에 포함되어 있으면 좋아요 수를 0으로 설정
                                            if "답글 달기" in likes:
                                                likes = "0"
                                        else:
                                            likes = "0"
                                    except:
                                        likes = "0"
                                    
                                    # 댓글 정보 저장
                                    comment_data = {
                                        "author": author,
                                        "content": content,
                                        "date": date,
                                        "likes": likes,
                                        "index": comment_index
                                    }
                                    
                                    all_collected_comments[comment_id] = comment_data
                                    processed_comment_ids.add(comment_id)
                                    new_comments_this_scroll += 1
                            else:
                                # 해당 인덱스에 댓글이 없는 경우 다음 인덱스로 이동
                                continue
                        except Exception as e:
                            print(f"댓글 #{comment_index} 추출 중 오류: {e}")
                            # 오류가 발생해도 다음 댓글로 계속 진행
                            continue
                    
                    # 새로 추가된 댓글 수 및 총 댓글 수 출력
                    total_new_comments += new_comments_this_scroll
                    print(f"새로 추가된 댓글 수: {new_comments_this_scroll}, 총 댓글 수: {len(all_collected_comments)}")
                    
                    # 스크롤 수행 - 1500px로 스크롤
                    page.evaluate(f"""
                        () => {{
                            const element = document.evaluate(
                                "{comments_xpath.replace('"', '\\"')}", 
                                document, 
                                null, 
                                XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                null
                            ).singleNodeValue;
                            
                            if (element) {{
                                element.scrollTop += 1500;
                                return true;
                            }}
                            return false;
                        }}
                    """)
                    
                    scroll_count += 1
                    print(f"댓글 영역 스크롤 {scroll_count}/{max_scrolls}: 현재 scrollHeight={current_scroll_height}")
                    
                    # 스크롤 후 로딩 대기 - 더 긴 대기 시간
                    time.sleep(3)
                    
                    # 새 댓글이 발견되지 않고, 스크롤 높이도 변하지 않으면 중단
                    if new_comments_this_scroll == 0 and current_scroll_height == previous_scroll_height:
                        consecutive_same_height += 1
                        if consecutive_same_height >= 3:  # 3번 연속으로 새 댓글이 없고 높이가 변하지 않으면 중단
                            print(f"더 이상 새 콘텐츠가 로드되지 않음. 스크롤 중단.")
                            break
                    else:
                        consecutive_same_height = 0
                    
                    previous_scroll_height = current_scroll_height
                
            else:
                print("XPath로 댓글 영역을 찾을 수 없습니다.")
        
        except Exception as e:
            print(f"댓글 수집 중 오류 발생: {e}")
        
        # 결과 데이터 준비
        result = {
            "metadata": {
                "url": post_url,
                "extraction_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_comments": len(all_collected_comments),
                "total_scrolls": scroll_count
            },
            "comments": all_collected_comments
        }
        
        return result
        
    except Exception as e:
        print(f"댓글 수집 중 오류 발생: {e}")
        return {
            "metadata": {
                "url": post_url,
                "extraction_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e),
                "total_comments": 0,
                "total_scrolls": 0
            },
            "comments": {}
        }


def save_comments_to_file(comments_data):
    """
    Save the collected comments to a JSON file
    
    Args:
        comments_data: Dictionary containing comments data and metadata
        
    Returns:
        str: Path to the saved JSON file
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    final_json_file = f"instagram_comments_{timestamp}_final.json"
    
    with open(final_json_file, "w", encoding="utf-8") as f:
        json.dump(comments_data, f, ensure_ascii=False, indent=2)
    
    print(f"최종 댓글 데이터가 다음 위치에 저장되었습니다: {os.path.abspath(final_json_file)}")
    print(f"총 {comments_data['metadata']['total_comments']}개의 댓글이 추출되었습니다.")
    
    return os.path.abspath(final_json_file)