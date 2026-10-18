# SNUWCANVAS Caption API

기존 이미지 생성 서버와 독립적으로 실행하는 자동 캡션 API입니다. 기존 이미지 생성 서버와 별도로 동작합니다. 최신 Windows 클라이언트의 일관성 → 자동 캡션에서 이 API에 선택적으로 접속할 수 있습니다. 결과를 확인한 후 이미지 설명에 적용하고 직접 등록하세요.

## Ubuntu에서 시작

이 `caption-api` 폴더 전체를 우분투로 옮깁니다. Python 3.11 이상과 실행 중인 Ollama, **이미지를 읽을 수 있는 설치된 모델**이 필요합니다. 모델을 자동으로 다운로드하지 않습니다.

```bash
cd /설치한/경로/caption-api
bash run.sh
```

첫 실행 때 별도 `.venv`와 비밀 키 파일 `config/caption.env`를 만듭니다. 가상환경 생성이 실패하면 `sudo apt install python3-venv` 후 다시 실행하세요. 기본 주소는 `http://127.0.0.1:8010`입니다. 재실행은 같은 명령을 사용합니다. 종료는 Ctrl+C입니다.

다른 터미널에서, 같은 디렉터리로 이동한 다음:

```bash
set -a
source config/caption.env
set +a

# 설치된 비전 모델 조회 (최대 처음 20개를 검사)
curl --fail-with-body -sS http://127.0.0.1:8010/v1/models \
  -H "X-API-Key: $CAPTION_API_KEY" | python3 -m json.tool
```

출력된 모델 이름을 아래 `MODEL`에 넣습니다. 이미지 경로도 실제 파일로 바꾸세요.

```bash
MODEL='여기에_조회된_모델명'
# 모델 이름의 콜론, 슬래시 등을 안전하게 URL에 넣기
QUERY="$(MODEL="$MODEL" python3 -c 'import os,urllib.parse; print(urllib.parse.urlencode({"model":os.environ["MODEL"],"format":"tags","subject":"Furina"}))')"
curl --fail-with-body -sS --max-time 610 \
  -H "X-API-Key: $CAPTION_API_KEY" \
  -H 'Content-Type: image/png' \
  --data-binary @/실제/이미지.png \
  "http://127.0.0.1:8010/v1/captions?$QUERY" | python3 -m json.tool
```

## API 계약

| 요청 | 용도 |
|---|---|
| `GET /health` | 프로세스 상태. Ollama 연결 여부를 보장하지 않음 |
| `GET /v1/models` | 설치된 비전 모델 목록. `truncated=true`이면 처음 20개만 검사함 |
| `POST /v1/captions?model=...&format=sentence&subject=...` | 이미지 한 장의 영문 캡션 |

`/v1/*`는 `X-API-Key` 헤더가 필요합니다. POST 본문은 **이미지 파일 원본 바이트**이며 multipart, 파일 경로, 이미지 URL은 받지 않습니다. PNG/JPEG/WebP를 지원합니다. `format`은 `sentence` 또는 `tags`, `subject`는 선택적인 대상 이름입니다. 모델은 반드시 이미 설치된 비전 모델이어야 합니다.

응답 예시 (실제 추론 결과가 아닌 형식 설명):

```json
{
  "id": "요청별 고유 ID",
  "model": "선택한 모델명",
  "format": "tags",
  "text": "solo, full body, standing, blue outfit, pale background",
  "caption": "A character in a blue outfit stands against a pale background.",
  "tags": ["solo", "full body", "standing", "blue outfit", "pale background"],
  "image": {"width": 832, "height": 1216}
}
```

한 번 요청해서 결과를 받는 방식으로, 작업 상태 조회나 반복 폴링이 없습니다. 결과를 자동으로 기존 프로필에 저장하지 않습니다. 추후 통합 시 결과 미리보기 → 사용자 수정/승인 → 기존 참조 이미지 업로드 순서로 연결하세요. 자동 캡션도 오인식할 수 있으므로 학습 전에 검토해야 합니다.

## 운영 설정

`config/caption.env`는 Git 제외 파일입니다. 소스 업데이트 때 유지하세요. 비밀 키를 채팅, Git, 로그에 올리지 마세요. 운영 로그에는 이미지, 캡션, 키를 남기지 않습니다.

- 기본 로컬 접속만 허용합니다. 다른 컴퓨터에서 접속하려면 `CAPTION_HOST=0.0.0.0`으로 변경하고 재시작하세요. 인터넷 공개 시 HTTPS 프록시와 방화벽을 먼저 구성하세요. Ollama의 11434 포트는 외부에 공개할 필요가 없습니다.
- 파일 최대 8 MiB / 2천만 픽셀. 추론 전 긴 변을 1536px 이하로 줄이고 이미지 메타데이터를 제거합니다. 업로드 이미지와 생성 캡션은 디스크에 저장하지 않습니다.
- 동시에 1개만 처리하고 나머지는 `503`으로 즉시 거절합니다. 인증된 요청은 분당 기본 30회입니다. `429`/`503`일 때만 `Retry-After` 후 재시도하세요. 자동 재시도는 구현하지 않았습니다.
- 전체 요청 기본 제한 시간은 540초이며 `CAPTION_TIMEOUT`으로 1~600초를 지정합니다. `504`는 제한 시간 초과, `400`은 모델/빈 입력 오류, `401`은 키 오류, `413`은 용량 초과, `415`는 이미지 오류, `502`는 잘못된 모델 출력입니다.
- 단일 프로세스로 실행합니다. 여러 worker로 실행하면 동시 처리 제한이 서로 공유되지 않습니다.
- `keep_alive=0`으로 응답 후 Ollama 모델을 해제하도록 요청합니다. 기존 ComfyUI/LoRA 학습과의 GPU 스케줄링은 아직 통합하지 않았으므로 12GB GPU에서는 동시에 학습·생성을 돌리지 말고 따로 테스트하세요.
- 원격 Ollama 주소, 외부 이미지 URL, 임의 프롬프트, 모델 다운로드 요청은 지원하지 않습니다.

## 테스트

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

테스트는 가짜 Ollama만 사용합니다. 실제 모델의 캡션 품질은 우분투에서 별도로 확인해야 합니다.

구현 기준: [Ollama Vision API](https://docs.ollama.com/capabilities/vision), [Chat API 및 JSON schema 출력](https://docs.ollama.com/api/chat).

## 0.2: 상세 프롬프트 생성

기본 `mode=prompt`는 등록된 `src/snuwcaption/system_prompt.txt`(사용자 제공 UNIVERSAL IMAGE PROMPT ENGINEERING SYSTEM v3)를 사용합니다. 채팅의 두 코드 블록 형식은 API에서 `positive_prompt`와 `negative_prompt`라는 JSON 필드로 바꿉니다. 그 외 관찰 근거·일관성·국소 색상·의상 구분·모델 호환성 규칙을 적용합니다. 소스 업데이트 시 이 텍스트 파일도 함께 올려야 합니다.

- `mode=prompt`: 원본 전체와 겹치는 두 세부 크롭을 같은 요청에서 관찰하고, 상세 긍정·부정 프롬프트를 반환합니다. 복잡한 대상은 의미 있는 세부 특징을 충분히 기록하도록 요청하지만, 단어 수를 채우기 위한 환각은 허용하지 않습니다.
- `mode=training`: 관찰한 학습용 설명만 반환합니다. 부정 프롬프트는 빈 문자열입니다. LoRA 캡션에 부정 프롬프트를 합치지 마세요.
- `pipeline=sdxl|illustrious|flux2_klein`: 생성 모델 계열입니다. FLUX에는 이 API가 부정 조건을 전달하지 않으며 `negative_supported=false`로 반환합니다.
- 기존 `text`, `caption`, `tags`는 유지하며 `positive_prompt`, `negative_prompt`, `negative_tags`, `uncertainties`, `mode`, `pipeline`, `negative_supported`가 추가됩니다. `uncertainties`는 모델이 불확실하다고 보고한 항목이며 측정된 정확도 점수가 아닙니다.
- 긍정/부정의 완전히 같은 태그는 충돌 제거합니다. 의미가 다른 표현 사이의 충돌이나 시각 오인식을 모두 자동 검증하는 것은 아닙니다.
- 생성용 컨텍스트는 16384, 출력 한도는 2400 토큰입니다. 학습용은 8192/1200입니다. 자세한 관찰 때문에 이전보다 VRAM·처리 시간이 늘 수 있습니다. GPU 추론이나 실제 이미지 재현 품질은 별도 확인해야 합니다. 시간 초과 시 원인을 확인하고 필요하면 `CAPTION_TIMEOUT`을 늘리세요(클라이언트 대기는 최신 버전에서 600초 제한).

최신 Windows 클라이언트에서 용도를 **생성용 (긍정·부정)** 또는 **학습용 캡션**으로 선택할 수 있습니다. 생성용 결과는 긍정과 부정 입력칸에 따로 표시합니다. **이미지 설명에 적용**은 긍정 결과만 참조 캡션으로 옮깁니다. 자동으로 이미지를 생성하거나, 기존 부정 프롬프트를 덮어쓰지는 않습니다.

## 0.3: 상세도·버전 확인

- 복잡한 생성용 이미지는 70~120개 근거 있는 태그 및 180~350단어 설명을 목표로 요청합니다. 학습용은 30~70개 태그 및 100~250단어를 목표로 하되 간단한 이미지를 억지로 늘리지 않습니다.
- 출력 한도: 생성용 4096 / 학습용 2000 토큰. 목표보다 짧으면 동일 이미지로 **최대 한 번** 세부 관찰 보완을 시도하고, 정보량이 늘어난 유효 결과를 사용합니다. 무한 재시도는 없습니다. 수치상 길이가 늘었다고 정확성이 검증된 것은 아닙니다.
- 긍정·부정은 같은 Ollama 응답의 필드입니다. 부정 프롬프트만 따로 생성하는 요청은 없습니다. 보완이 필요한 경우 긍정·부정을 한 묶음으로 최대 두 번 추론하므로 시간이 더 걸릴 수 있습니다.
- 기본 전체 제한 시간은 540초, 최신 클라이언트 제한 시간은 600초입니다. `config/caption.env`에 기존 `CAPTION_TIMEOUT=180`을 직접 설정했다면 원하는 값(최대 600)으로 바꿔야 합니다. CLI 예제의 `--max-time`도 610으로 늘려 사용할 수 있습니다.
- `/health`, `/v1/models`, 캡션 응답에 `api_version=0.3.0`을 반환합니다. 클라이언트는 구버전 API를 감지해 서버 업데이트를 안내합니다.
- 캡션의 `diagnostics`에는 `positive_tags`, `caption_words`, `refinement_attempted`, `refinement_used`, `elapsed_seconds`가 포함됩니다. 이는 길이·처리 정보이며 화질/정확도 평가 점수가 아닙니다.

서버에 소스(특히 service.py와 system_prompt.txt)를 모두 갱신하고 기존 프로세스를 종료한 뒤 `bash run.sh`로 재시작하세요. 원격 서버를 이 작업에서 자동으로 업데이트한 것은 아닙니다.

## 0.3 호환 패치: 모델 출력 복구

JSON 코드 블록, JSON 앞뒤 설명, `positive_prompt`/`negative_prompt` 필드, 쉼표 태그 문자열, 두 개의 긍정/부정 코드 블록을 정규화합니다. `uncertainties` 생략과 부가 설명 필드는 허용하지만, 숫자/객체를 태그로 변환하거나 잘린 JSON을 추측해서 완성하지 않습니다.

긍정 설명이 유효하고 부정만 빠졌다면 기존 최대 한 번 보완 범위에서 재확인합니다. 계속 빠지면 긍정을 보존하고 `negative_complete=false`와 진단 경고를 반환합니다. 없는 부정 프롬프트를 생성했다고 표시하지 않습니다. 긍정 자체를 읽을 수 없으면 `invalid_json`, `missing_positive`, `schema_validation` 등 원인을 구분해 502를 반환합니다. 로그에 원본 응답이나 API 키는 기록하지 않습니다. 응답 계약은 호환되므로 api_version은 0.3.0을 유지합니다.

## 출력 제한 수정

`invalid_fields`는 실제 설명이 없을 때뿐 아니라 개별 태그 160자 초과, 부정 태그 160자 초과, 불확실성 설명 500자 초과도 한꺼번에 거절하던 문제였습니다. 개별 구절 길이만으로 전체 캡션을 버리지 않으며, 긍정/부정 전체는 각각 UTF-8 16000바이트 한도를 적용합니다. 지나치게 큰 부정은 보완을 시도하고 긍정은 보존합니다. 비필수 불확실성 설명만 길면 최대 2000자로 제한하고 진단에 표시합니다. 빈 태그 목록이지만 정상 caption이 있으면 해당 설명을 사용합니다.

`GET /health`의 `build=output-limits-2`로 이번 패치 적용 여부를 확인할 수 있습니다. 이번 수정은 캡션 API 소스만 업데이트하고 재시작하면 됩니다. 키 설정이나 이미지 생성 서버, 클라이언트 EXE는 변경하지 않아도 됩니다.

## 반복·추측 억제 패치

태그/단어 개수 목표와 짧다는 이유만으로 재생성하던 처리를 제거했습니다. 더 긴 후보를 자동으로 우선하지 않습니다. 참조에서 보이는 외형, 의상 레이어, 국소 색상, 포즈와 화풍을 정확하게 구분하는 것이 우선입니다. 모델의 시각 오인식을 이 문자열 정리만으로 교정하거나 정확도를 보장하는 것은 아닙니다.

대소문자·공백 차이를 포함한 중복을 제거하고, JSON 배열 내부에 한 덩어리로 들어온 쉼표 목록도 정리합니다. `anime character hair` 같은 범주 채우기와 `bad gamma`, `extra clothing`, `extra accessory` 같은 과도한 부정 나열을 제거합니다. 서로 다른 장갑 색, 의상/머리 지역색, 외곽선·채색 방식 같은 실제 차이는 유지합니다.

부정이 누락된 경우에만 최대 한 번 복구하며, 이미 승인된 긍정 설명을 그 복구 결과로 바꾸지 않습니다. `/health`의 build 값은 `grounded-cleanup-3`입니다. 캡션 API 소스 전체(새 quality.py 포함)를 갱신하고 재시작하면 됩니다. 클라이언트 변경은 없습니다.

## 로그

콘솔은 Rich 컬러 로그와 시작 패널을 표시합니다. 저장 로그는 `runtime/logs/caption.log`에 날짜·레벨·이벤트를 일반 텍스트로 기록합니다. ANSI 색상 코드는 저장하지 않으며 5MiB × 최대 백업 3개로 회전합니다. Linux 디렉터리/파일 권한은 700/600입니다. `CAPTION_LOG_DIR`로 위치를 바꿀 수 있습니다. 기존 이미지·프롬프트·API 키 비기록 원칙은 유지합니다.
