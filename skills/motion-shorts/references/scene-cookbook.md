# Scene cookbook

Read this before writing the SCENES section of `index.html`. Contents:
1. Scene anatomy · 2. Layout map · 3. Helper reference · 4. Recipes by content type ·
5. Transitions · 6. Captions · 7. Quality checklist (mistakes that actually happened)

---

## 1. Scene anatomy

```js
S.push({item:2, lead:.3, tail:.55, f(t,e){
  itemHead(t,2,'작업중지 확대',0,e.w('작업중지가')-.1,{sub:'노동자·근로자대표·명예산업안전감독관',tSub:e.w('작업중지가')+.4,eff:'공포 6개월 후 시행'});
  const pa=P(t,e.w('급박한')-.2,e.w('급박한')+.2), ra=rise(pa,40);           // progress 0..1 around a word
  if(pa>0){ctx.save();ctx.globalAlpha=ra.a;ctx.translate(0,ra.y);
    panel(70,450,940,400,{glow:P(t,e.w('우려되는'),e.w('우려되는')+.3)});     // glow when the key word lands
    checkMark(160,612,1,P(t,e.w('급박한'),e.w('급박한')+.3));
    txt('급박한 위험이 있을 때',210,632,{w:800,size:46});
    ctx.restore();}
},sfx:e=>[['thud',0],['rise',e.w('급박한')-.2],['check',e.w('급박한')]]});
```

- `t` scene-local seconds; `e.w(prefix,n)` start of the n-th word starting with prefix, `e.we` its end, `e.end` narration end.
- `P(t,a,b)` → 0..1 progress; easing `eo` (out), `eio` (in-out), `eb` (back/overshoot). `pop(p)` = overshoot scale, `rise(p,dy)` = {a, y} fade-up.
- Start an element slightly **before** its word (`-.1`…`-.2`) so it is fully visible when the word is heard.
- `lead`: seconds before narration starts in the scene (0.25–0.35; give 0.5+ if a big card must settle first).
  `tail`: seconds after narration (0.5–0.6; CTA 1.2+). `min`: minimum scene length (CTA ≈ 6 s so the question card can be read).
- `item`: which header chip is lit (1..CONFIG.items) or -1.
- **Silent scenes**: add scenes after the last scripted one (no narration line) for a closing card. They get `CLIP=0`, no words and no captions; give them `min` (≈5 s) and time everything with plain seconds. Used for a closing scene without a spoken sign-off — users preferred not reading the sign-off in Shorts because it signals "the end" and works against the loop.
- Wrap groups in `ctx.save()/restore()`; never leave globalAlpha or transforms changed.

## 2. Layout map (design space 1080×1920, scaled by 0.86 into the upper frame)

| design y | what goes there |
|---|---|
| 0–230 | nothing (screen header: series line y≈104, progress chips y≈150 are drawn outside the scene) |
| 250–420 | title row: `itemHead` (number + title + sub at y≈362, hazard line + effective-date chip at y≈404) or `headline` at y≈300 |
| 440–1660 | content: 1–3 panels, x 70…1010 (width 940), inner padding 40 |
| 1660–1700 | footnotes (26–30 px, muted) |
| screen y≈1548 | captions (outside the scene, never place content there) |

Type scale that stays legible on a phone after the 0.86 scale: title 62–72, panel heading 44–50, row text 38–48, labels 30–34, footnotes 26–28. Do not go below 26.

Measure before placing side by side: `tw(text, weight, size)` returns width. Long Korean lines: split manually into two `txt` calls.

## 3. Helper reference

Text & shapes
- `txt(s,x,y,{w,size,color,align,ls,alpha})` · `tw(s,w,size)` · `rr(x,y,w,h,r)` path · `hl(x,y,w,h,p,color)` highlighter that grows with p
- `panel(x,y,w,h,{fill,r,stroke,glow})` card with shadow; `glow` 0..1 adds a yellow glow (use when its key word is spoken)
- `chip(x,y,s,{bg,fg,size,align})` pill label (returns width) · `newBadge(x,y,p,'NEW')` · `tag(x,y,label,p,bg,fg)` slanted section tag
- `stamp(x,y,label,p,{color,size,rot})` slam-in stamp · `burst(x,y,p,color,r0,r1,n)` emphasis rays · `checkMark(x,y,s,p,color)` drawn check
- `arrow(x1,y1,x2,y2,p,{color,wd,head,dash})` drawing arrow · `hazard(x,y,w,h,offset,alpha)` yellow/black stripes (`offset=t*60` animates)
- `countUp(v,p)` integer count-up for numbers (`txt(countUp(5,p)+'%',…)`)
- `headline(lines,t,[start times],{y,size})` pop-in headline with highlighter · `itemHead(t,n,title,t0,tTitle,{sub,tSub,eff})`

Icons (all take a centre and scale; most animate with t)
`worker(x,y,s,{hat,run:phase|null,stopHand})` hard-hat pictogram (run = t*10 to run) · `stopSign` · `exitSign` · `building(x,y,w,h,label)` ·
`crane` · `thermo` · `snow` · `coin` · `megaphone` · `gear` · `ship` · `bookmark` · `commentIcon` · `lockIcon` · `govIcon` · `personIcon(x,y,r,color)`

Characters & speech
- `person(x,y,s,{top,hair:'bob'|'short',mood:'flat'|'smile'|'worry'|'sad',look,blink,talk,nod,arm,glasses,tie,shirt,cut,t})`
  head centre at (x,y). `talk:flap(t,a,b)` moves the mouth while speaking a<t<b; `nod:nodv(t,at)` nods at a word;
  `blink:(t%3)>2.9`; `cut` (local px) hides the body below a desk line; pass `t` for breathing and the palm wave.
- `lawyer(x,y,s,{t,talk,arm,cut})` = person with glasses/tie. Wave: `arm:lerp(.2,-2.15,eo(P(t,.1,.6)))+Math.sin(t*3)*.1`.
- `bubble(cx,cy,[lines],p,{size,w,tail:[dx,dy],think,fill})` speech/thought bubble; the tail points to (cx+dx, cy+dy).
- Draw the desk **after** the person so it covers the body, or use `cut`.

Make new icons in the same flat style (2–3 colours from `C`, rounded rects, 8–12 px strokes) instead of importing images.

## 4. Recipes by content type

**Hook (frame 0)** – big title already visible (`P(t,-.2,.1)`), hazard bands or a character with a bubble, then the promise ("핵심 n가지") as numbered tiles that pop in on the number word. Thumbnail is usually taken here.

**Law change / "before → after"** – grey row for the existing rule, then a yellow-outlined row sliding in with "+ 새 요건" and a `newBadge`, the panel `glow`ing on the key word. Effective date as the `eff` chip in the title row.

**Conditions → consequence** – vertical chain of 2–3 cards connected by arrows, the last card red with `lockIcon`/`stamp`; or a timeline bar ("3년간") with stamps landing on each count word and a blinking dashed slot for "또 대상".

**Numbers** – person icons turning red one by one on the count word, a giant `countUp` number, a gauge filled to the value, `coin` popping on "과징금/포상금".

**Who does what** – `building('원청')` vs `worker` with an arrow labelled by a chip ("작업중지 요구"), `burst` on the verb.

**Story / case (paper theme)** – 2 characters, bubbles keyed to the sentences, mouth `flap` while their line is narrated, a document/checklist card where a field stays blank with a blinking caret and a red "?" (what was not asked).

**Timeline of effective dates** – vertical line filling with progress, nodes popping per date word, the node relevant to the takeaway glows; add the save chip ("시행일 확인용으로 저장해 두세요" + `bookmark`).

**Takeaway / CTA** – lawyer waving with open palm while saying the closing line, brand pill on "상생의", then the question card after narration ends, recap icons fading out first. Loop wipe follows automatically.

## 5. Transitions

`TRANS[i-1]` is the transition into scene i (0.42 s, starts at the boundary). Mix them – one type throughout feels templated.
- `push-left` (next topic) · `push-up` (continuation / drill-down) · `zoom` (open/close, conclusion) ·
  `iris` (focus on a point: set `IRIS[k]=toScr(x,y)` at the element the previous scene ended on) · `hazard` (dark theme accent wipe)
The final loop wipe back to frame 0 is automatic when `CONFIG.loop` is true.

## 6. Captions

`CAPS[i]` = array of lines for scene i, each line = the next transcript words joined by spaces (punctuation dropped). render.js prints `caption mismatch` if a line does not match. 8–16 syllables per line, break at meaning units, never start a line with a one-syllable word. `null` (or `noCap:true`) for scenes whose on-screen text already equals the narration.

## 7. Quality checklist (each of these actually went wrong once)

- Giant item number overlapping the title or the header chips → use `itemHead`, which measures the number.
- A card appearing empty seconds early because `e.w('확인')` matched an earlier word ("확인 후가") → use a longer prefix or the nth match.
- Stamps/chips placed on top of other labels or a ship/crane icon → check every stamp position in stills.
- First frame faded or empty → start hook elements at negative times; no fade from black.
- A 2-second silent gap after the hook because the scene had too many timed elements → hook scene ≤ 4.5 s, fewer elements.
- Closed fist + thumb read as thumbs-down → only open-palm gestures.
- Text from the source changed or embellished on screen → copy wording from the source; anything added must be flagged in the approval message.
- Bodies of characters showing below the desk → draw the desk after the person or set `cut`.
