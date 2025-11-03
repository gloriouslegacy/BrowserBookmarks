# Language Folder

다국어 지원을 위한 언어 파일 폴더입니다.

## 자동 생성

애플리케이션 첫 실행 시 다음 파일들이 자동으로 생성됩니다:

- `lang_ko.ini` - 한국어 (기본)
- `lang_en.ini` - 영어

## 언어 파일 형식

INI 파일 형식을 사용합니다:

```ini
[섹션명]
키 = 값

[app]
title = 브라우저 북마크 관리

[menu]
file = 파일
help = 도움말
```

## 새 언어 추가 방법

1. 기존 언어 파일을 복사
2. `lang_XX.ini` 형식으로 이름 변경 (XX는 언어 코드)
3. 모든 텍스트를 해당 언어로 번역
4. `winBookmarks.py`의 언어 메뉴에 추가

예제:
```python
lang_menu.add_command(label="日本語", command=lambda: self._change_language("ja"))
```

## 지원 섹션

- `[app]` - 애플리케이션 정보
- `[menu]` - 메뉴 항목
- `[main]` - 메인 화면 레이블
- `[messages]` - 메시지 및 알림
- `[update]` - 업데이트 관련 메시지
- `[about]` - 정보 대화상자

## 파일이 없을 경우

언어 파일이 없으면 애플리케이션이 자동으로 기본 언어 팩(한국어, 영어)을 생성합니다.
