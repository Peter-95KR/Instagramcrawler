# Instagram Data Collector with Playwright

Instagram 포스트 및 릴(Reel) 데이터 수집 도구입니다. Playwright를 활용한 강력하고 안정적인 웹 스크래핑 솔루션으로, 인스타그램의 동적 콘텐츠를 효과적으로 추출합니다.

## 주요 기능

- **고급 데이터 수집 기능**
  - 인스타그램 포스트/릴 기본 정보 추출 (로그인 불필요)
    - 포스트 ID, 사용자 이름, 게시일, 좋아요 수, 댓글 수, 설명 텍스트
  - 댓글 데이터 수집 (로그인 필요)
    - 작성자, 내용, 날짜, 좋아요 수 포함
  - 릴 조회수 자동 추출 (로그인 필요)
  - 모든 데이터를 구조화된 JSON 파일로 저장

- **기술적 특징**
  - Playwright 기반의 자동화된 브라우저 제어
  - 동적으로 로드되는 콘텐츠 처리 가능
  - 세션 관리 및 로그인 상태 유지
  - XPath 및 CSS 선택자를 통한 정확한 데이터 추출
  - 자동 스크롤링으로 모든 댓글 수집
  - 안정적인 오류 처리 및 로깅 시스템

## 요구사항

- Python 3.8 이상
- Playwright 라이브러리
- 필요한 패키지 설치:
  ```bash
  pip install playwright
  python -m playwright install chromium
  ```

## 사용 방법

### 직접 실행

기본 포스트 정보만 수집 (로그인 불필요):
```bash
python crawler.py --url "https://www.instagram.com/p/POSTID/"
```

### 로그인 및 모든 데이터 수집

댓글과 조회수를 포함한 전체 데이터 수집:
```bash
python crawler.py --username "your_username" --password "your_password" --url "https://www.instagram.com/p/POSTID/"
```

### 커맨드라인 매개변수

- `-u`, `--username`: 인스타그램 사용자 이름
- `-p`, `--password`: 인스타그램 비밀번호
- `-url`, `--url`: 인스타그램 포스트 URL (reel/reels/p 형식 모두 지원)
- `-o`, `--output`: 출력 JSON 파일 이름 (기본값: instagram_data.json)
- `--no-log`: 로그 파일 생성 비활성화 (로그가 콘솔에만 출력됨)

### 대화형 실행

명령어 매개변수를 생략하면 대화형으로 입력을 요청합니다:
```bash
python crawler.py
```

## 기술적 구현 세부사항

### 브라우저 및 세션 관리
- 최적화된 브라우저 설정으로 인스타그램의 봇 탐지 회피
- 지속적인 세션 관리를 통한 로그인 상태 유지
- 적응형 대기 시간 구현으로 비동기적 콘텐츠 로딩 처리

### 고급 DOM 탐색
- XPath와 CSS 선택자의 하이브리드 접근 방식
- JavaScript 기반 DOM 탐색으로 동적 UI 변경에 대응
- 미세 조정된 선택자로 인스타그램 UI 업데이트에 강인함

### 데이터 추출 메커니즘
- 점진적인 스크롤링 알고리즘으로 모든 댓글 수집
- 스마트 중복 방지 메커니즘으로 데이터 정확성 보장
- 최적화된 데이터 구조화 및 저장 방식

## 모듈 구조

- `module/getinfo.py`: 포스트 기본 정보 수집 (로그인 필요 없음)
- `module/login.py`: 인스타그램 로그인 처리 및 세션 관리
- `module/comment.py`: 인스타그램 댓글 수집 및 구조화
- `module/findview.py`: 릴 조회수 탐색 및 추출

## URL 형식 지원

다음 URL 형식이 모두 지원됩니다 (자동으로 `/p/` 형식으로 정규화):
- `https://www.instagram.com/p/POSTID/`
- `https://www.instagram.com/reel/POSTID/`
- `https://www.instagram.com/reels/POSTID/`

## 주의사항

- 이 도구는 교육 및 연구 목적으로만 사용해야 합니다
- 인스타그램 서비스 약관 및 이용 정책을 준수하여 사용하세요
- 과도한 요청은 계정 제한을 초래할 수 있습니다