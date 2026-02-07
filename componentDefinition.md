아래는 Cartoon Diary 프론트엔드 구현용 컴포넌트 단위 화면 명세서입니다.
기준은 **React(웹/React Native 모두 호환 가능한 구조)**로 적되, Flutter로 옮겨도 동일하게 매핑되도록 “역할 중심”으로 써놨어요.

⸻

프론트엔드 화면/컴포넌트 명세서 (Implementation Spec)

공통 규칙

라우팅(권장)
	•	/ : Home(리스트)
	•	/write : Write Diary
	•	/options : Style & Options
	•	/generate/:jobId : Generating
	•	/result/:artifactId : Result
	•	/regenerate/:artifactId : Regenerate
	•	/share/:artifactId : Save/Share

상태 관리(권장)
	•	전역: user, settings, draftDiary, jobs, artifacts
	•	화면 단위: 로딩/에러/입력값/선택값

API 호출 공통
	•	요청/응답 구조는 “Job 기반 비동기”로 통일
	•	Polling 또는 SSE/WebSocket 중 택1
	•	에러는 표준화: { code, message, retryable, detail }

⸻

1) Home / Diary List

Screen: HomeScreen

책임
	•	사용자 생성 결과(4컷) 목록 로드 및 표시
	•	새 일기 작성 진입

컴포넌트 트리(권장)
	•	AppShell
	•	TopBar
	•	TodayBadge
	•	PrimaryButton(New Diary)
	•	DiaryGridOrList
	•	DiaryCard * N
	•	EmptyState

컴포넌트 명세

DiaryCard
	•	Props
	•	artifactId: string
	•	date: string
	•	thumbnailUrl: string
	•	summary: string
	•	stylePreset: string
	•	UI
	•	썸네일 이미지
	•	날짜/스타일 태그
	•	요약 한 줄
	•	행동
	•	클릭: /result/:artifactId

API
	•	GET /api/artifacts?limit=20&cursor=...
	•	Response
	•	items: ArtifactSummary[]
	•	nextCursor?: string

빈 상태
	•	조건: items.length === 0
	•	CTA: “Write your first diary”

⸻

2) Write Diary

Screen: WriteDiaryScreen

책임
	•	일기 텍스트 입력 + 기분 선택
	•	Draft 저장
	•	다음 화면으로 이동(옵션 선택)

컴포넌트 트리
	•	AppShell
	•	TopBar(Back)
	•	DiaryEditor
	•	MultiLineTextInput
	•	CharCount(optional)
	•	MoodPicker
	•	StickyCTA
	•	PrimaryButton(Turn into a Comic)

컴포넌트 명세

DiaryEditor
	•	State
	•	text: string
	•	Validation
	•	최소 길이: 10자(권장), 미만이면 경고만 표시하고 진행은 허용
	•	이벤트
	•	onChange(text)
	•	onBlur 시 saveDraft()

MoodPicker
	•	Props
	•	value: number | string
	•	onChange
	•	UI 옵션
	•	이모지 5개(😄🙂😐🙁😫) 또는 슬라이더 1~5

화면 행동
	•	CTA 클릭 시:
	•	draft 저장
	•	/options 이동

Local Draft (권장)
	•	Key: cartoonDiaryDraft
	•	내용: { text, mood, updatedAt }

⸻

3) Style & Option Select

Screen: OptionsScreen

책임
	•	스타일 프리셋 선택
	•	주인공 닉네임 설정
	•	생성 시작(서버에 Job 생성)

컴포넌트 트리
	•	AppShell
	•	TopBar(Back)
	•	StylePresetSelector
	•	StyleCard * N
	•	CharacterSettings
	•	TextInput(name optional)
	•	AdvancedOptionsAccordion
	•	Toggle(More funny)
	•	Toggle(Focus on emotions)
	•	Toggle(Less text)
	•	StickyCTA
	•	PrimaryButton(Generate)

컴포넌트 명세

StylePresetSelector
	•	Presets
	•	cute, comedy, drama, minimal
	•	State
	•	selectedPreset

AdvancedOptionsAccordion
	•	State
	•	moreFunny: boolean
	•	focusEmotion: boolean
	•	lessText: boolean

API (생성 시작)
	•	POST /api/generate
	•	Request

{
  "diaryText": "...",
  "mood": "🙂",
  "stylePreset": "cute",
  "protagonistName": "Min",
  "options": {
    "moreFunny": true,
    "focusEmotion": false,
    "lessText": true
  }
}

	•	Response

{ "jobId": "job_123" }

성공 시
	•	/generate/:jobId 이동

⸻

4) Generating (Progress)

Screen: GeneratingScreen

책임
	•	Job 상태를 주기적으로 조회
	•	단계별 진행 UI 표시
	•	완료 시 결과 화면으로 이동

컴포넌트 트리
	•	AppShell
	•	TopBar(Cancel optional)
	•	ProgressStepper
	•	ProgressBar
	•	StatusMessage

단계 정의(서버/클라 공통 코드로 맞추기)
	•	READING_DIARY
	•	BUILDING_STORYBOARD
	•	GENERATING_IMAGES
	•	COMPOSING_STRIP
	•	DONE
	•	FAILED

API (Polling)
	•	GET /api/jobs/:jobId
	•	Response

{
  "jobId": "job_123",
  "status": "RUNNING",
  "step": "GENERATING_IMAGES",
  "progress": 0.65,
  "artifactId": null,
  "error": null
}

완료 시
	•	artifactId 받으면 /result/:artifactId 이동

실패 시
	•	에러 모달:
	•	message
	•	Retry(가능 시)
	•	Back

⸻

5) Result – 4컷 만화 결과

Screen: ResultScreen

책임
	•	4컷 최종 결과 표시(한 장 + 컷별 보기 옵션)
	•	재생성/저장/공유 진입

컴포넌트 트리
	•	AppShell
	•	TopBar
	•	DateLabel
	•	StyleTag
	•	ComicStripViewer
	•	Image(finalStripUrl)
	•	ZoomView(optional)
	•	ActionBar
	•	SecondaryButton(Regenerate)
	•	PrimaryButton(Save/Share)

API
	•	GET /api/artifacts/:artifactId
	•	Response

{
  "artifactId": "art_1",
  "finalStripUrl": "https://...",
  "panelUrls": ["...","...","...","..."],
  "storyboard": { "panels": [ ... ] },
  "stylePreset": "cute",
  "createdAt": "..."
}

상호작용
	•	이미지 탭: 확대
	•	Regenerate: /regenerate/:artifactId
	•	Save/Share: /share/:artifactId

⸻

6) Regenerate (컷 단위 재생성)

Screen: RegenerateScreen

책임
	•	전체/특정 컷 재생성 요청
	•	옵션 조절 후 재생성 job 생성
	•	완료 시 결과 갱신

컴포넌트 트리
	•	AppShell
	•	TopBar
	•	PanelPicker
	•	PanelThumbnail(1~4)
	•	RegenerateOptions
	•	Toggle(More funny)
	•	Toggle(Less text)
	•	Toggle(Stronger emotion)
	•	StickyCTA
	•	PrimaryButton(Regenerate)

컴포넌트 명세

PanelPicker
	•	State
	•	selectedPanels: number[] (예: [2] 또는 [1,3])
	•	UX
	•	“Regenerate all” 체크 제공

API
	•	POST /api/regenerate
	•	Request

{
  "artifactId": "art_1",
  "panels": [2],
  "options": { "lessText": true }
}

	•	Response

{ "jobId": "job_456" }

완료 처리
	•	/generate/:jobId 로 이동 후 완료되면 새 artifactId로 /result/:artifactId

⸻

7) Save / Share

Screen: ShareScreen

책임
	•	저장 및 공유 액션 제공
	•	해커톤 심사용 “링크 공유” 제공(옵션)

컴포넌트 트리
	•	AppShell
	•	TopBar
	•	ComicPreviewCard
	•	ShareActions
	•	Button(Download)
	•	Button(Copy Link)
	•	Button(Share Sheet - mobile)
	•	InfoNote

API
	•	GET /api/artifacts/:artifactId/share-link (선택)
	•	Response

{ "url": "https://app/cartoon/art_1" }

UX
	•	다운로드는 브라우저 기본 다운로드 또는 네이티브 저장
	•	링크 복사는 토스트 표시

⸻

공통 UI 컴포넌트 라이브러리 (권장)

AppShell
	•	SafeArea/패딩/공통 배경
	•	모바일/웹 대응 레이아웃

TopBar
	•	Back, Title, Action(옵션)

PrimaryButton / SecondaryButton
	•	disabled/loading 상태 포함

Toast / Modal
	•	네트워크 오류/재시도 안내

LoadingSkeleton
	•	리스트/결과 로딩 시

⸻

공통 유틸/훅 (권장)

useJobPolling(jobId)
	•	1~2초 간격 polling
	•	DONE/FAILED 시 자동 stop
	•	화면 전환 콜백 제공

useDraftDiary()
	•	localStorage/secure storage 연동
	•	write screen ↔ options screen 간 데이터 유지

apiClient
	•	baseURL, timeout, retryable 에러 처리
	•	표준 에러 매핑

⸻

MVP 구현 우선순위

P0 (필수)
	•	Home 리스트(최소)
	•	Write Diary
	•	Options
	•	Generating + Polling
	•	Result(최종 이미지 표시)
	•	Regenerate(전체 재생성만이라도)
	•	Share(Download만)

P1 (하면 점수 올라감)
	•	컷 단위 재생성
	•	Progress stepper 실제 단계 연동
	•	링크 공유

P2 (시간 남으면)
	•	컷별 보기/확대
	•	히스토리 검색/태그

⸻

개발자 체크 포인트(해커톤 점수용)
	•	Generating 화면에 “에이전트 단계(Reading → Storyboard → Image → Compose)”를 보여주면, 심사자가 Agentic AI를 한눈에 이해합니다.
	•	Regenerate에서 “특정 컷만 재생성”은 기술 구현 점수에 강하게 먹힙니다(비용/시간 최적화도 설명 가능).

⸻

원하시면, 이 명세를 그대로 기반으로 React(웹) 컴포넌트 폴더 구조 + 라우터 코드 뼈대 + 타입(TypeScript) 인터페이스까지 한 번에 잡아드릴게요.