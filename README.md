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
curl --fail-with-body -sS --max-time 190 \
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
- 전체 요청 기본 제한 시간은 180초이며 `CAPTION_TIMEOUT`으로 1~600초를 지정합니다. `504`는 제한 시간 초과, `400`은 모델/빈 입력 오류, `401`은 키 오류, `413`은 용량 초과, `415`는 이미지 오류, `502`는 잘못된 모델 출력입니다.
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
- 생성용 컨텍스트는 16384, 출력 한도는 2400 토큰입니다. 학습용은 8192/1200입니다. 자세한 관찰 때문에 이전보다 VRAM·처리 시간이 늘 수 있습니다. GPU 추론이나 실제 이미지 재현 품질은 별도 확인해야 합니다. 시간 초과 시 원인을 확인하고 필요하면 `CAPTION_TIMEOUT`을 늘리세요(클라이언트 대기는 190초 제한).

최신 Windows 클라이언트에서 용도를 **생성용 (긍정·부정)** 또는 **학습용 캡션**으로 선택할 수 있습니다. 생성용 결과는 긍정과 부정 입력칸에 따로 표시합니다. **이미지 설명에 적용**은 긍정 결과만 참조 캡션으로 옮깁니다. 자동으로 이미지를 생성하거나, 기존 부정 프롬프트를 덮어쓰지는 않습니다.
