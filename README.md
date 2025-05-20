# Instagram Data Collector

Instagram 포스트 및 릴(Reel) 데이터 수집 도구입니다.

## 기능

- 인스타그램 포스트 기본 정보 수집 (로그인 필요 없음)
  - 포스트 ID, 사용자 이름, 게시일, 좋아요 수, 댓글 수, 설명 텍스트
- 인스타그램 로그인 기능
- 포스트 댓글 수집 기능 (로그인 필요)
- 모든 데이터를 하나의 JSON 파일로 저장

## 요구사항

- Python 3.8+
- Playwright
- 필요한 패키지 설치:
  ```
  pip install playwright
  python -m playwright install
  ```

## 사용 방법

### 직접 실행

```bash
python crawler.py --url "https://www.instagram.com/p/POSTID/"
```

### 로그인 및 댓글 수집 포함

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

## 모듈 구조

- `module/getinfo.py`: 포스트 기본 정보 수집 (로그인 필요 없음)
- `module/login.py`: 인스타그램 로그인 처리
- `module/comment.py`: 인스타그램 댓글 수집

## URL 형식 지원

다음 URL 형식이 모두 지원됩니다 (자동으로 `/p/` 형식으로 정규화):
- `https://www.instagram.com/p/POSTID/`
- `https://www.instagram.com/reel/POSTID/`
- `https://www.instagram.com/reels/POSTID/`