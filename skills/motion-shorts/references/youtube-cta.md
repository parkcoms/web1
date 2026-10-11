# YouTube metadata and subtle CTA

Write `$W/youtube_meta.md` with these sections so the user can paste field by field. Base everything on the approved script and the source only — a wrong line costs the channel's credibility. Send the file with SendUserFile (display 'attach').

## Title (3 candidates, ≤100 chars, mark one [추천])
- Lead with the core question or conclusion; only the first ~40 chars show on mobile.
- Numbers and concrete terms beat adjectives ("1년 3명 사망 시 영업이익 5% 과징금").
- No clickbait ("충격", "망함"). Calm, credible tone.

## Description
1. First 2 lines (~150 chars): the question and the answer.
2. Summary: the items/case in short bullets, with effective dates if any.
3. 챕터: `0:00 …` lines from scene start times (render.js meta → scene starts). YouTube needs the first at 0:00, ≥3 chapters, each ≥10 s — merge short scenes. Chapters may not display on Shorts; harmless to include.
4. 출처: exact source title/date as printed in the material. Never invent case numbers.
5. 고지: any disclaimer printed in the source (e.g. "가상 사례입니다") + "이 영상은 일반 정보 제공 목적이며 개별 사안에 대한 법률 자문이 아닙니다." + unknowns (e.g. 공포일 미정).
6. `상생의 노동법 | 박재우 변호사` (+ contact only if printed in the source).
7. 3–5 hashtags at the very end (first three show above the title).

## Tags
15–25 comma-separated, total ≤500 chars: core terms + practical search phrases + broad topics + channel name. Nothing that identifies a private person or company the source anonymised.

## Pinned comment
A reusable summary (e.g. effective-date table or checklist) + the same question as the closing card. Pinned summaries get saved and shared.

## Other settings
Category 교육, language 한국어; vertical ≤3 min → Shorts; thumbnail = a frame with title + character/icon (3–6 s); the cloned voice means the user should decide on the "altered or synthetic content" disclosure — point it out, don't decide for them.

## Subtle CTA inside the video (default: all three)
Explicit "구독·좋아요" only if the user asks. These work by being useful, not by asking:
1. **Seamless loop** (`CONFIG.loop`): the last 0.5 s wipes into frame 0, the progress bar returns to 0, BGM uses short fades (`--loop`). Shorts auto-replay; viewers often watch a second time without noticing → watch-through and replays go up.
2. **Save chip** on the scene worth revisiting (dates, checklist): `bookmark` + "○○ 확인용으로 저장해 두세요". Reads as a hint, not a request.
3. **Question card** after the closing line: a concrete question the target viewer can answer from their own workplace ("우리 회사는 작업중지 요구, 누가 어떻게 받나요?"). On screen only, no narration.
Optional (upload screen): link a related long video; pinned comment above.
Avoid teasing a "next episode" unless the user actually plans it.
