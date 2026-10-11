#!/usr/bin/env python3
"""Turn ElevenLabs narration + Scribe transcripts into processed clips and a word-timing table.

Real mode (after voice + transcription):
  python3 prep_audio.py --status status.json --script script.json --out work/ [--speed 1.15]
    status.json : the creative_get_flow_run_status result that contains `transcripts`
                  (when the tool result is too long it is saved to a file automatically - pass that path)
    script.json : ["scene 1 narration", "scene 2 narration", ...]  (the approved script)
  Produces work/proc/s{i}.wav (silence-trimmed, sped up), work/el/s{i}.mp3 (originals),
  and work/timing.js  (window.TIMINGDATA = {W:[[word,start,end],...] per scene, CLIP:[sec,...]}).
  Prints MATCH / DIFF per scene: a DIFF means the voice said something else - listen before using it.

Placeholder mode (before any credits are spent - lets you build and preview scenes):
  python3 prep_audio.py --placeholder --script script.json --out work/
  Estimates word timings at ~8 Hangul syllables/s (calibrated on two real narrations after 1.15x). Replace later with real mode.
"""
import argparse, json, os, re, subprocess

def syl(s): return len(re.findall(r'[가-힣A-Za-z0-9]', s))
def norm(s): return re.sub(r'[^가-힣A-Za-z0-9]', '', s)

def write_timing(out, W, CLIP):
    with open(os.path.join(out, 'timing.js'), 'w') as fh:
        fh.write('window.TIMINGDATA=' + json.dumps({'W': W, 'CLIP': CLIP}, ensure_ascii=False, separators=(',', ':')) + ';\n')

def placeholder(script, out, rate=8.0):
    W, CLIP = [], []
    for line in script:
        t = 0.0; ws = []
        for w in line.split():
            d = max(.12, syl(w) / rate); ws.append([w, round(t, 3), round(t + d, 3)])
            t += d + (.28 if re.search(r'[.,?!]$', w) else .05)
        W.append(ws); CLIP.append(round(t, 3))
    write_timing(out, W, CLIP); print('placeholder timing written; total speech ≈', round(sum(CLIP), 1), 's')

def ff_dur(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]))

def lead_silence(p, thr='-45dB'):
    o = subprocess.run(['ffmpeg', '-i', p, '-af', f'silencedetect=n={thr}:d=0.01', '-f', 'null', '-'], capture_output=True, text=True).stderr
    st = re.search(r'silence_start: (-?[0-9.]+)', o); en = re.search(r'silence_end: ([0-9.]+)', o)
    return float(en.group(1)) if st and en and float(st.group(1)) <= 0.05 else 0.0

def real(status, script, out, speed):
    d = json.load(open(status)); tr = d.get('transcripts') or []
    if len(tr) < len(script): raise SystemExit(f'only {len(tr)} transcripts for {len(script)} scenes - poll status with every transcription session_id')
    os.makedirs(os.path.join(out, 'el'), exist_ok=True); os.makedirs(os.path.join(out, 'proc'), exist_ok=True)
    used = set(); W = []; CLIP = []; ok = True
    for i, line in enumerate(script):
        # pick the transcript whose text is closest to this scene's line
        def score(j):
            a, b = norm(tr[j]['text']), norm(line)
            return sum(x == y for x, y in zip(a, b)) - abs(len(a) - len(b))
        j = max((k for k in range(len(tr)) if k not in used), key=score); used.add(j); t = tr[j]
        same = norm(t['text']) == norm(line); ok &= same
        print(f'S{i+1}', 'MATCH' if same else f'DIFF  said: {t["text"]}')
        src = os.path.join(out, 'el', f's{i+1}.mp3'); dst = os.path.join(out, 'proc', f's{i+1}.wav')
        subprocess.run(['curl', '-sSf', '-o', src, t['source']['url']], check=True)
        lead = lead_silence(src)
        af = (f'silenceremove=start_periods=1:start_threshold=-45dB,areverse,'
              f'silenceremove=start_periods=1:start_threshold=-45dB,areverse,atempo={speed}')
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-af', af, '-ar', '44100', '-ac', '1', dst], check=True)
        ws = [w for w in t['words'] if w.get('type') == 'word']
        W.append([[w['text'], round(max(0, (w['start'] - lead) / speed), 3), round((w['end'] - lead) / speed, 3)] for w in ws])
        CLIP.append(round(ff_dur(dst), 3))
    write_timing(out, W, CLIP)
    print('clips:', CLIP, 'total speech', round(sum(CLIP), 1), 's')
    if not ok: print('WARNING: at least one scene does not match the script - check pronunciation before continuing')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--status'); ap.add_argument('--script', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--speed', type=float, default=1.15); ap.add_argument('--placeholder', action='store_true')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    script = json.load(open(a.script))
    if a.placeholder: placeholder(script, a.out)
    else:
        if not a.status: raise SystemExit('--status is required (or use --placeholder)')
        real(a.status, script, a.out, a.speed)

if __name__ == '__main__':
    main()
