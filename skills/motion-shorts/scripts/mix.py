#!/usr/bin/env python3
"""Place narration clips on their cues, mix with ducked BGM and SFX, and mux onto the silent video.

  python3 mix.py --work work/ --video work/silent.mp4 --bgm work/bgm.wav --sfx work/sfx.wav --out final.mp4

Expects work/meta.json (from render.js meta) and work/proc/s{i}.wav (from prep_audio.py).
Levels that tested well: narration -16 LUFS (YouTube/Instagram norm), BGM -26 LUFS with
sidechain ducking under the voice, SFX -13 dB. Change with --bgm-lufs / --sfx-db if the user
says music or effects feel too loud or too quiet - no re-render of the video is needed.
"""
import argparse, json, os, subprocess, wave
import numpy as np

def run(*a): subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', *a], check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True); ap.add_argument('--video', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--bgm'); ap.add_argument('--sfx')
    ap.add_argument('--bgm-lufs', type=float, default=-26); ap.add_argument('--sfx-db', type=float, default=-13)
    a = ap.parse_args(); W = a.work; m = json.load(open(os.path.join(W, 'meta.json'))); sr = 44100; T = m['T']
    out = np.zeros(int(sr * T))
    for i, c in enumerate(m['C']):
        with wave.open(os.path.join(W, 'proc', f's{i+1}.wav')) as w:
            x = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768
        s = int(c * sr); e = min(len(out), s + len(x)); out[s:e] += x[:e - s]
        if s + len(x) > len(out): print(f'warning: scene {i+1} narration runs past the end of the video')
    with wave.open(os.path.join(W, 'narr.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
    run('-i', os.path.join(W, 'narr.wav'), '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '44100', os.path.join(W, 'n.wav'))
    inputs = ['-i', os.path.join(W, 'n.wav')]; chain = '[0:a]asplit=2[v][sc];'; mixin = '[v]'; k = 1
    if a.bgm:
        run('-i', a.bgm, '-af', f'loudnorm=I={a.bgm_lufs}:TP=-3', '-ar', '44100', os.path.join(W, 'b.wav'))
        inputs += ['-i', os.path.join(W, 'b.wav')]
        chain += f'[{k}:a][sc]sidechaincompress=threshold=0.03:ratio=4:attack=20:release=400[bg];'; mixin += '[bg]'; k += 1
    else: chain = '[0:a]anull[v];'
    if a.sfx:
        run('-i', a.sfx, '-af', f'volume={a.sfx_db}dB', '-ar', '44100', os.path.join(W, 'x.wav'))
        inputs += ['-i', os.path.join(W, 'x.wav')]; mixin += f'[{k}:a]'; k += 1
    if not a.bgm: chain = chain.replace('asplit=2[v][sc]', 'anull[v]')
    filt = chain + f'{mixin}amix=inputs={k}:duration=first:normalize=0,alimiter=limit=0.95[a]'
    run(*inputs, '-filter_complex', filt, '-map', '[a]', '-ac', '2', '-ar', '44100', os.path.join(W, 'mix.wav'))
    run('-i', a.video, '-i', os.path.join(W, 'mix.wav'), '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', a.out)
    lufs = subprocess.run(['ffmpeg', '-i', os.path.join(W, 'mix.wav'), '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    il = [l for l in lufs.splitlines() if l.strip().startswith('I:')]
    print('final ->', a.out, '| integrated', il[-1].strip() if il else '?', '| size', round(os.path.getsize(a.out) / 1e6, 1), 'MB')

if __name__ == '__main__':
    main()
