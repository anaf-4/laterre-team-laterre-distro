# LaTerre 전용 런처 - 모드 자동 설치 설정 가이드

## 배경

처음 분석했던 `Hanwol Launcher-setup-1.0.0.exe`는 **HeliosLauncher**(오픈소스, Electron 기반)를 리브랜딩한 빌드였고, 배포 서버 주소(`hanwol-update.skhidc.net`)가 코드에 하드코딩되어 있었습니다. 하지만 이 도메인은 본인 소유가 아니므로 그대로 쓸 수 없습니다.

대신 지금은 HeliosLauncher 소스를 직접 `git clone` 받아 본인 PC에 두셨으니, 여기서:

1. 배포 매니페스트(`distribution.json`)는 **GitHub 저장소**(`anaf-4/laterre-team-laterre-distro`)의 raw 링크로 호스팅
2. 마인크래프트 서버 주소는 **`laterre.kro.kr`**
3. 런처 소스 안의 `REMOTE_DISTRO_URL`을 이 GitHub raw 주소로 바꿔서 본인 것으로 재빌드

하는 방식으로 진행합니다.

`LaTerre.zip`(Fabric 서버 폴더)에서 실제 설치된 모드 20개와 버전 정보를 그대로 추출해서 `distribution.json`을 만들었습니다.

- Minecraft `1.21.4`
- Fabric Loader `0.19.3`
- 모드 20개 (`mods/` 폴더에 실제 파일로 들어있음)
- 서버 주소: `laterre.kro.kr` (기본 포트 25565)

## 폴더 구성

```
hanwol-distribution/
├── distribution.json          ← 런처가 읽는 최종 매니페스트 (이미 생성됨, GitHub raw 링크 기준)
├── generate_distribution.py   ← 모드 목록이 바뀔 때마다 다시 실행하는 생성 스크립트
├── complete-distribution.js   ← Fabric 로더 파일을 받아서 해시를 채우는 스크립트
├── mods/                      ← 서버에서 추출한 모드 jar 20개 (실제 파일)
└── loader/                    ← complete-distribution.js 실행 후 생성됨 (로더 jar + 버전 매니페스트)
```

## 1단계 — 로더 해시 채우기

작업 환경에 외부 인터넷 접근이 없어서 Fabric 로더 원본 파일과 버전 매니페스트의 해시를 직접 계산할 수 없었습니다. 인터넷이 되는 본인 PC(방금 HeliosLauncher를 클론한 그 PC)에서 실행하세요.

```bash
cd hanwol-distribution
node complete-distribution.js       # 로더 jar + 버전 매니페스트 다운로드 & 해시 계산 → loader/ 생성
python3 generate_distribution.py    # distribution.json에 해시 반영
```

## 2단계 — GitHub 저장소에 업로드

`anaf-4/laterre-team-laterre-distro` 저장소에 `hanwol-distribution/` 폴더 안의 내용을 **루트 기준으로 그대로** 올리세요 (폴더명은 안 올려도 됨, 안의 파일/폴더만).

```bash
git clone https://github.com/anaf-4/laterre-team-laterre-distro.git
cd laterre-team-laterre-distro
# hanwol-distribution 폴더 안의 distribution.json, mods/, loader/ 를 여기로 복사
git add .
git commit -m "add distribution files"
git push
```

push 후 최종 링크는 이렇게 됩니다 (기본 브랜치가 `main`이 아니라 `master`면 `generate_distribution.py`의 `BASE_URL`을 수정하고 재실행하세요):

```
https://raw.githubusercontent.com/anaf-4/laterre-team-laterre-distro/main/distribution.json
https://raw.githubusercontent.com/anaf-4/laterre-team-laterre-distro/main/mods/sodium-fabric-0.6.13+mc1.21.4.jar  (등 20개)
https://raw.githubusercontent.com/anaf-4/laterre-team-laterre-distro/main/loader/fabric-loader-0.19.3.jar
https://raw.githubusercontent.com/anaf-4/laterre-team-laterre-distro/main/loader/fabric-loader-0.19.3-1.21.4.json
```

> 저장소가 private면 raw 링크에 인증이 필요해서 런처가 못 받아옵니다. **public 저장소**여야 합니다.

## 3단계 — 런처 소스에서 배포 주소 교체

클론받은 `HeliosLauncher` 폴더에서 아래 파일을 엽니다.

```
HeliosLauncher/app/assets/js/distromanager.js
```

이 줄을 찾아서:

```js
exports.REMOTE_DISTRO_URL = 'https://hanwol-update.skhidc.net/hanwol/distribution.json'
```

이렇게 바꾸세요:

```js
exports.REMOTE_DISTRO_URL = 'https://raw.githubusercontent.com/anaf-4/laterre-team-laterre-distro/main/distribution.json'
```

## 4단계 — 이름/아이콘 리브랜딩 (선택)

`package.json`의 `productName`, `name`, 그리고 `build/` 폴더의 아이콘 이미지들을 원하는 이름/로고로 바꾸면 런처 창 제목·설치 파일 이름도 그대로 바뀝니다. (지금은 남의 이름인 "Hanwol Launcher" 그대로이니 최소한 이 부분은 바꾸는 걸 추천드려요.)

## 5단계 — 테스트 후 설치 파일 빌드

```bash
npm start          # 우선 실행해서 서버 목록에 LaTerre가 뜨고 모드가 자동으로 받아지는지 확인
npm run dist:win   # 문제없으면 설치 파일(exe) 빌드
```

## 이후 모드를 추가/삭제/업데이트할 때

1. `mods/` 폴더의 jar 파일을 교체(추가/삭제)
2. `generate_distribution.py`의 `DISTRO_VERSION`을 올림 (예: `1.0.1`)
3. `python3 generate_distribution.py` 재실행
4. 바뀐 `distribution.json`과 `mods/` 폴더를 GitHub 저장소에 다시 push

끝입니다. 유저는 런처를 실행하기만 하면 다음 접속 때 자동으로 새 모드가 설치/업데이트됩니다. 런처 자체를 다시 빌드/재배포할 필요는 없고, GitHub 쪽만 갱신하면 됩니다.

## 참고: 왜 모드 파일을 직접 호스팅하나요?

Sodium, Iris처럼 Modrinth/CurseForge에 공식 등록된 모드는 원래 그쪽 CDN 링크를 그대로 써도 되지만, 서버에 이미 특정 커스텀 조합(버전, 비공식 모드 포함)으로 설치돼 있는 상태라 실수로 다른 버전을 가리킬 위험이 있습니다. 지금 갖고 계신 jar 파일 그대로를 GitHub에 자체 호스팅하면 서버와 클라이언트 모드 버전이 100% 일치하는 게 보장됩니다. Fabric 로더 자체는 공식 Fabric Maven(`maven.fabricmc.net`) 링크를 그대로 사용하도록 구성했습니다.
