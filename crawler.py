#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from playwright.sync_api import sync_playwright
import argparse
import json
import os
import time
import datetime
import sys

# 모듈 가져오기
from module.getinfo import get_post_info, normalize_instagram_url, save_to_json, setup_logging
from module.login import instagram_login
from module.comment import collect_instagram_comments
from module.findview import find_post_views


def main():
    # 명령행 인자 설정
    parser = argparse.ArgumentParser(description='Instagram Post Data Collector')
    parser.add_argument('-u', '--username', help='Instagram username')
    parser.add_argument('-p', '--password', help='Instagram password')
    parser.add_argument('-url', '--url', help='Instagram post URL')
    parser.add_argument('-o', '--output', default='instagram_data.json', help='Output JSON filename')
    parser.add_argument('--no-log', action='store_true', help='Disable log file creation')
    
    args = parser.parse_args()
    
    # 로거 설정
    log_file = None if args.no_log else 'instagram_scraping.log'
    logger = setup_logging(log_file)
    print("Instagram crawler started")
    
    # 입력값 처리
    username = args.username
    password = args.password
    url = args.url
    output_file = args.output
    
    # 명령행으로 URL이 제공되지 않은 경우 대화식으로 입력받기
    if not url:
        url = input("Enter Instagram post URL: ")
    
    # URL 유효성 검사
    if not url or "instagram.com" not in url:
        print("Valid Instagram URL is required.")
        sys.exit(1)
    
    # URL 정규화 (reel/reels -> p 형식)
    url = normalize_instagram_url(url)
    print(f"Processing URL: {url}")
    
    # 로그인 필요 여부 확인
    need_login = False
    if username and password:
        need_login = True
    elif not username and not password:
        login_choice = input("Login is required to collect comments. Would you like to login? (y/n): ").lower()
        if login_choice == 'y':
            username = input("Enter Instagram username: ")
            password = input("Enter Instagram password: ")
            need_login = True
    
    # 결과 데이터 구조 초기화
    result_data = {
        "post_info": None,
        "comments": None,
        "metadata": {
            "collected_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "with_login": need_login
        }
    }
    
    # 1단계: 게시물 정보 수집 (로그인 불필요)
    print("\n1. Collecting basic post information...")
    post_info = get_post_info(url, logger)
    
    if not post_info:
        print("Could not retrieve post information. Exiting program.")
        sys.exit(1)
    
    print("Post information collection complete!")
    print(f"Post ID: {post_info['post_id']}")
    print(f"Author: {post_info['username']}")
    print(f"Likes: {post_info['likes']}")
    print(f"Comments: {post_info['comments_count']}")
    
    # 결과 데이터에 게시물 정보 추가
    result_data["post_info"] = post_info
    
    # 2단계: 로그인, 조회수 확인, 댓글 수집 (같은 브라우저 세션에서)
    if need_login:
        print("\n2. Logging into Instagram...")
        
        with sync_playwright() as p:
            # 안정적인 세션 처리를 위한 브라우저 설정
            browser = p.chromium.launch(headless=False)
            
            # 적절한 세션 처리를 위한 컨텍스트 구성 - Asia/Seoul 시간대 사용
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                locale="ko-KR",
                timezone_id="Asia/Seoul",
                accept_downloads=True
            )
            
            # 세션 안정성 향상을 위한 쿠키 설정 (모든 쿠키 허용)
            context.add_cookies([{
                "name": "ig_cb", 
                "value": "1",
                "domain": ".instagram.com",
                "path": "/",
            }])
            
            # 적절한 세션 처리를 위한 페이지 생성
            page = context.new_page()
            
            try:
                # 먼저 로그인 수행
                login_success = instagram_login(page, username, password)
                
                if not login_success:
                    print("Login failed. Skipping view count and comment collection.")
                else:
                    print("Login successful!")
                    
                    # 3단계: 로그인 후 조회수 확인
                    print("\n3. Finding view count for the post...")
                    view_count = None
                    
                    if post_info["username"]:
                        print(f"Looking for post {post_info['post_id']} in profile of {post_info['username']}...")
                        
                        # 사용자의 릴스 페이지로 이동
                        print("Going to user's reels page...")
                        profile_url = f"https://www.instagram.com/{post_info['username']}/reels/"
                        
                        # 먼저 쿠키가 제대로 설정되도록 인스타그램 홈페이지 방문
                        page.goto("https://www.instagram.com/")
                        print("Visited homepage to maintain session")
                        time.sleep(2)
                        
                        # 이제 프로필 페이지로 이동
                        print(f"Navigating to: {profile_url}")
                        page.goto(profile_url)
                        print("Waiting 5 seconds for page to load...")
                        time.sleep(5)  # Longer wait for better stability
                        
                        # mount ID 찾기
                        mount_elements = page.query_selector_all('[id^="mount_"]')
                        mount_id = None
                        
                        if mount_elements:
                            mount_id = mount_elements[0].get_attribute("id")
                        else:
                            mount_id = "mount_0_0"  # Default value
                        
                        print(f"Using mount ID: {mount_id}")
                        
                        # 주어진 post_id로 게시물 검색
                        found_post = False
                        max_scrolls = 5
                        scroll_count = 0
                        post_link_element = None
                        
                        while not found_post and scroll_count < max_scrolls:
                            # 현재 페이지의 모든 링크 찾기
                            all_links = page.query_selector_all("a")
                            
                            for link in all_links:
                                href = link.get_attribute("href")
                                if href and post_info["post_id"] in href:
                                    print(f"Found post link: {href}")
                                    post_link_element = link
                                    found_post = True
                                    break
                            
                            if not found_post:
                                # 스크롤 다운
                                scroll_count += 1
                                print(f"Scrolling down ({scroll_count}/{max_scrolls})")
                                
                                page.evaluate("window.scrollBy(0, 1500)")
                                time.sleep(2)  # Wait after scrolling
                        
                        if found_post:
                            # 방법 1만 사용하여 조회수 추출 시도 - 직접 자식 요소 탐색
                            try:
                                print("Found post link, attempting to extract view count...")
                                
                                # 방법 1: 선택자 문제를 피하기 위해 JavaScript로 직접 자식 요소 탐색
                                # 업데이트된 경로: div[2]/div[2]/div/div/div/span/span
                                print("Using JavaScript DOM navigation approach with updated path...")
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
                                
                            except Exception as e:
                                print(f"Error extracting view count: {e}")
                        else:
                            print(f"Post with ID {post_info['post_id']} not found after {max_scrolls} scrolls")
                    else:
                        print("Username not found in post info, skipping view count collection")
                    
                    # 결과 데이터에 조회수 저장
                    result_data["post_info"]["views"] = view_count
                    
                    # 4단계: 댓글 수집 (같은 브라우저 세션 사용)
                    print("\n4. Collecting comments...")
                    
                    # 게시물 URL로 이동
                    print("\nNavigating to the post page for comment collection...")
                    
                    # 세션 유지를 위해 먼저 인스타그램 홈페이지 다시 방문
                    page.goto("https://www.instagram.com/")
                    print("Visited homepage to ensure session continuity")
                    time.sleep(2)
                    
                    # 이제 게시물 URL로 이동
                    print(f"Going to post URL: {url}")
                    page.goto(url)
                    print("Waiting 5 seconds for post page to fully load...")
                    time.sleep(5)  # Longer wait for better stability
                    
                    # 댓글 수집
                    comments_data = collect_instagram_comments(page, url)
                    
                    # 결과 데이터에 댓글 정보 추가
                    result_data["comments"] = comments_data["comments"]
                    result_data["metadata"]["comments_collected"] = len(comments_data["comments"])
                    result_data["metadata"]["total_scrolls"] = comments_data["metadata"]["total_scrolls"]
                    
                    print(f"Total of {len(comments_data['comments'])} comments were collected.")
                
                # 자동 종료 전 페이지를 볼 수 있도록 짧게 일시 정지
                print("Browser will close automatically in 3 seconds...")
                time.sleep(3)
                
            except Exception as e:
                print(f"Processing error: {e}")
            
            finally:
                browser.close()
    else:
        # 로그인하지 않은 경우 조회수 및 댓글 수집 건너뛰기
        print("Login credentials not provided. Skipping view count and comment collection.")
        result_data["post_info"]["views"] = None
    
    # 5단계: 결과를 JSON으로 저장 (마지막 단계)
    print("\n5. Saving collected data...")
    saved_file = save_to_json(result_data, output_file, logger)
    
    if saved_file:
        print(f"\nAll tasks completed successfully!")
        print(f"Result file: {saved_file}")
    else:
        print("Failed to save data.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    except Exception as e:
        print(f"Unexpected error occurred: {e}")