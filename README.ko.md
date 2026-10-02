[![English](https://img.shields.io/badge/README-English-24292f?style=for-the-badge)](./README.md) [![한국어](https://img.shields.io/badge/README-%ED%95%9C%EA%B5%AD%EC%96%B4-24292f?style=for-the-badge)](./README.ko.md)

# JP Play — 해외(일본 등) 앱 다운로더

한국 플레이스토어에서 안 보이는 일본 앱 등을 PC에서 받아 USB로 폰에 설치하는 도구입니다.

## 실행
`run.bat` 더블클릭 (또는 `python jpplay.py`). 처음 쓸 때 필요한 도구(`apkeep`, `adb`)를 `tools/`에 자동으로 받습니다.

## 사용법
1. **앱 찾기**: 앱 이름을 입력하고 국가(JP)를 고른 뒤 "웹에서 검색"을 누릅니다. 브라우저에 일본 Play 스토어가 열립니다.
2. **다운로드**: 앱 페이지 주소(`...details?id=jp.xxx`)를 붙여넣고 "다운로드"를 누릅니다. 파일은 `downloads/`에 저장됩니다.
   - **APKPure**: 로그인 없이 받을 수 있습니다. 일본 앱도 대부분 있습니다.
   - **Google Play**: 공식 파일을 받습니다. Google 계정 이메일과 AAS 토큰이 필요합니다.
3. **설치**: 폰에서 개발자 옵션 → USB 디버깅을 켜고 PC에 연결한 뒤 "연결된 기기 확인"을 누릅니다. 폰에 뜨는 허용 창을 승인하고 설치합니다. `.apk`, `.xapk`(분할 APK + OBB)를 모두 지원합니다.

### Google Play AAS 토큰 발급 (선택)
1. PC 브라우저에서 https://accounts.google.com/EmbeddedSetup 에 로그인합니다.
2. 개발자도구(F12) → Application → Cookies에서 `oauth_token` 값을 복사합니다.
3. 아래 명령을 실행합니다.
   `tools\apkeep.exe -e 이메일 --oauth-token 복사한값 -d google-play -a com.android.chrome downloads`
4. 출력된 AAS 토큰을 프로그램에 입력합니다. 토큰은 비밀번호처럼 관리하세요.

## 폰에서 바로 쓰는 방법 (가장 간편)
PC 없이 폰 안에서 "모든 나라 플레이스토어"처럼 쓰려면 **Aurora Store**(오픈소스 Play 스토어 클라이언트)를 사용하세요.
- 설치: https://auroraoss.com 또는 F-Droid
- 익명(Anonymous) 로그인 → 일본 VPN을 켠 상태로 검색하면 일본 앱이 보이고 바로 설치됩니다.

## 참고
- 공식 Play 스토어 앱 자체는 수정할 수 없습니다. Google 서명이 되어 있고, 국가는 Google 서버가 계정 결제 국가와 IP로 판단하기 때문입니다. 그래서 이 도구나 Aurora Store 같은 우회 방식을 씁니다.
- 일부 일본 앱(은행, PayPay, 게임 등)은 설치해도 앱 안에서 일본 IP나 일본 전화번호를 요구할 수 있습니다.
- 앱 업데이트는 자동으로 되지 않습니다. 다시 받아서 설치하세요(Aurora Store는 업데이트를 지원합니다).
