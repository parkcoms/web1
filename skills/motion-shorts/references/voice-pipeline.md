# Voice pipeline (ElevenLabs) — details and pitfalls

## Voice
- `박재우 변호사(1)` voice_id `tR2KSgzWczYwLUo9Suqn` (cloned). If it disappears, `creative_list_voices` with search "박재우".
- Model `eleven_v4`. No speed parameter on this connector → speed is applied afterwards (atempo 1.15 in prep_audio.py; pitch unchanged). 1.2+ starts to slur endings.
- `generations_count: 1` (default 4 = 4× credits). One call per scene, all in the same turn with the same `flow_id`.
- Cost seen: ≈ 1 credit per character (a 600-character script ≈ 650–700 credits). Estimate the longest scene first (`estimate_only:true`) and tell the user the total in one line.
- If a call reports a concurrency wait, it retries by itself — poll status again; never call generate again (double charge).

## Word timestamps
- Upload-based transcription fails here: the upload URL is on www.googleapis.com, which the proxy blocks. Do not try it.
- Instead transcribe the speech nodes directly: `creative_transcribe_audio(model_id:'eleven_scribe_v1', flow_id, connect_from:[<speech node_id>])`, one call per scene, all in one turn. Cost shown: 0 credits.
- Then call `creative_get_flow_run_status` once with **all transcription session_ids**. With 10+ scenes the result exceeds the display limit and is saved to a file automatically — pass that file path to `prep_audio.py --status`. If it comes back inline (few scenes), write it to a JSON file first.
- Each transcript has `text`, `words[{text,type,start,end}]` and `source.url` (the original mp3, valid ~2 h). prep_audio.py matches transcripts to script lines by text similarity, so order does not matter.
- Word times are converted: `(t - leading_silence) / speed`. Verified identical to a hand-computed table on a real 11-scene run.

## Verification for free
- prep_audio.py prints MATCH/DIFF per scene by comparing the transcript to the approved script (Hangul/alnum only). All MATCH = the TTS said exactly the script, including numbers like "오 퍼센트". A DIFF means listen to that scene and regenerate only it.

## Placeholder timing
- `prep_audio.py --placeholder` estimates 8 syllables/s with short pauses at punctuation; on two real scripts it was within 2% of the real length (78.2 vs 79.4 s, 74.8 vs 75.0 s). Build scenes against it while the voice is generated; scenes need no changes afterwards because cues are word-based.
