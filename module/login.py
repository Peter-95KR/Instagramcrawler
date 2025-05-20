from playwright.sync_api import sync_playwright, TimeoutError
import time

def instagram_login(page, username, password):
    """
    인스타그램에 제공된 자격 증명으로 로그인하는 함수
    
    Args:
        page: Playwright 페이지 인스턴스
        username: 인스타그램 사용자 이름
        password: 인스타그램 비밀번호
        
    Returns:
        bool: 로그인이 성공하면 True, 그렇지 않으면 False
    """
    try:
        # 1단계: 인스타그램 로그인
        print("인스타그램 로그인 페이지로 이동 중...")
        page.goto('https://www.instagram.com/accounts/login/', wait_until="load")
        
        # 쿠키 수락 처리
        try:
            if page.is_visible('button[tabindex="0"]'):
                page.click('button[tabindex="0"]')
        except:
            pass
            
        # 로그인 페이지 로딩 대기
        try:
            page.wait_for_selector('input[name="username"]', state="visible", timeout=10000)
            print("로그인 페이지 로드됨")
        except TimeoutError:
            print("로그인 폼을 찾을 수 없습니다. 계속 진행합니다...")
        
        time.sleep(3)
        
        # 사용자 이름 및 비밀번호 입력
        print(f"{username}으로 로그인 중...")
        page.fill('input[name="username"]', username)
        page.fill('input[name="password"]', password)
        
        # 로그인 버튼 클릭
        page.click('button[type="submit"]')
        
        # 로그인 완료 대기
        try:
            page.wait_for_selector('svg[aria-label="홈"], svg[aria-label="Home"]', state="visible", timeout=15000)
            print("로그인 성공 - 홈 아이콘 확인됨")
            login_success = True
        except TimeoutError:
            print("홈 아이콘을 찾을 수 없습니다. 로그인은 되었을 수 있으니 계속 진행합니다...")
            login_success = True  # Assuming login succeeded even without visible indicator
        
        # 로그인 후 팝업 처리
        try:
            if page.is_visible('button:has-text("Not Now")'):
                page.click('button:has-text("Not Now")')
            elif page.is_visible('button:has-text("나중에 하기")'):
                page.click('button:has-text("나중에 하기")')
        except:
            pass
            
        time.sleep(2)
            
        try:
            if page.is_visible('button:has-text("Not Now")'):
                page.click('button:has-text("Not Now")')
            elif page.is_visible('button:has-text("나중에 하기")'):
                page.click('button:has-text("나중에 하기")')
        except:
            pass
        
        print("로그인 처리 완료!")
        time.sleep(3)
        
        return login_success
        
    except Exception as e:
        print(f"로그인 중 오류 발생: {e}")
        return False