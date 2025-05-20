# Instagram Data Crawler with Playwright

Instagram 포스트 및 릴스(Reels) 데이터 수집 도구입니다.




## 주요 기능

- **데이터 수집**
  - 인스타그램 포스트/릴 기본 정보 추출 (로그인 불필요)
    - 포스트 ID, 사용자 이름, 게시일, 좋아요 수, 댓글 수, 설명 텍스트
  - 댓글 데이터 수집
    - 작성자, 내용, 날짜(n일 전, n시간 전 등으로 저장), 좋아요 수 포함
  - 릴스 조회수 추출 로직 구현
  - 모든 데이터를 구조화된 JSON 파일로 저장

- **기술적 특징**
  - Playwright 기반
  - 자동 로그인
  - Xpath 변경시 코드 업데이트 필요

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

일반 포스트 수집 (조회수 추출 과정 없음):
```bash
python crawler.py --url "https://www.instagram.com/p/POSTID/" --type post
```

릴스 수집 (조회수 추출 과정 포함):
```bash
python crawler.py --url "https://www.instagram.com/reel/POSTID/" --type reels
```

### 로그인 및 모든 데이터 수집

댓글과 조회수를 포함한 전체 데이터 수집:
```bash
python crawler.py --username "your_username" --password "your_password" --url "https://www.instagram.com/p/POSTID/" --type reels
```

### 커맨드라인 매개변수

- `-u`, `--username`: 인스타그램 사용자 이름
- `-p`, `--password`: 인스타그램 비밀번호
- `-url`, `--url`: 인스타그램 포스트 URL (reel/reels/p 형식 모두 지원)
- `-o`, `--output`: 출력 JSON 파일 이름 (기본값: instagram_data.json)
- `--no-log`: 로그 파일 생성 비활성화 (로그가 콘솔에만 출력됨)
- `-t`, `--type`: 컨텐츠 타입 선택 (post 또는 reels, 기본값: reels)
  - reels: 조회수 추출 과정을 포함
  - post: 조회수 추출 과정을 건너뜀

### 대화형 실행

명령어 매개변수를 생략하면 대화형으로 입력을 요청합니다:
```bash
python crawler.py
```

## 모듈 구조

- `module/getinfo.py`: 포스트 기본 정보 수집 (로그인 필요 없음)
- `module/login.py`: 인스타그램 로그인 처리 및 세션 관리
- `module/comment.py`: 인스타그램 댓글 수집 및 구조화
- `module/findview.py`: 릴스 조회수 탐색 및 추출

## URL 형식 지원

다음 URL 형식이 모두 지원됩니다 (자동으로 `/p/` 형식으로 정규화):
- `https://www.instagram.com/p/POSTID/`
- `https://www.instagram.com/reel/POSTID/`
- `https://www.instagram.com/reels/POSTID/`

## 주의사항

- 이 도구는 교육 및 연구 목적으로만 사용해야 합니다
- 인스타그램 서비스 약관 및 이용 정책을 준수하여 사용하세요
- 과도한 요청은 계정 제한을 초래할 수 있습니다