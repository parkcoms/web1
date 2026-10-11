#!/usr/bin/env python3
"""Upbeat background-music generator for motion-graphic shorts (pure numpy, no samples).

Six upbeat styles, each re-voiced per video by a seed (key, tempo, melody, drum
variant), so no two videos share the same track. Optional two-style medley with a
crossfade at a chosen time (e.g. at the scene where the video changes topic).

Usage:
  python3 bgm.py --out bgm.wav --length 92.3                 # auto: random style not used recently
  python3 bgm.py --out bgm.wav --length 92.3 --style funky --seed 7
  python3 bgm.py --out bgm.wav --length 92.3 --style sunny_pop,drive --switch-at 48.2
  python3 bgm.py --out bgm.wav --length 92.3 --loop          # loop-friendly ends (seamless replay)
  python3 bgm.py --list
"""
import argparse, json, os, random, time, wave
import numpy as np

SR = 44100
HIST = os.path.expanduser('~/.motion-shorts/bgm_history.json')

def f(m): return 440.0 * 2 ** ((m - 69) / 12)

# ---------------------------------------------------------------- styles
# prog: list of (bass_root_midi, [chord tones midi]) per bar, written in C-ish; transposed by seed.
STYLES = {
  'sunny_pop':  dict(bpm=112, swing=0.0, prog=[(48,[60,64,67]),(43,[59,62,67]),(45,[60,64,69]),(41,[60,65,69])],
                     drums='pop', bass='bounce', comp='stabs', lead='bell', desc='밝은 팝: I–V–vi–IV, 오프비트 스탭, 통통 튀는 베이스'),
  'drive':      dict(bpm=118, swing=0.0, prog=[(45,[57,60,64]),(41,[57,60,65]),(48,[55,60,64]),(43,[55,59,62])],
                     drums='four', bass='eighths', comp='arp16', lead='bell', desc='드라이브: vi–IV–I–V, 포온더플로어, 16분 아르페지오'),
  'funky':      dict(bpm=106, swing=0.10, prog=[(50,[60,62,65,69]),(43,[59,62,65,67]),(48,[59,60,64,67]),(45,[57,60,64,67])],
                     drums='funk', bass='slap', comp='clav', lead='none', desc='펑키: ii–V–I–vi 7th, 싱코페이션 베이스, 클라브 커팅'),
  'house':      dict(bpm=124, swing=0.0, prog=[(41,[57,60,65]),(48,[55,60,64]),(50,[57,62,65]),(46,[58,62,65])],
                     drums='house', bass='offbeat', comp='piano', lead='none', desc='브라이트 하우스: 오프비트 피아노·베이스, 오픈 하이햇'),
  'ukulele':    dict(bpm=100, swing=0.30, prog=[(43,[55,59,62]),(40,[55,59,64]),(48,[55,60,64]),(50,[57,62,66])],
                     drums='shuffle', bass='walk', comp='strum', lead='whistle', desc='우쿨렐레 셔플: 스윙 스트럼, 휘파람 멜로디'),
  'tropical':   dict(bpm=102, swing=0.0, prog=[(46,[58,62,65]),(41,[57,60,65]),(43,[58,62,67]),(39,[58,63,67])],
                     drums='dembow', bass='tropical', comp='marimba', lead='steel', desc='트로피컬: 마림바 패턴, 뎀보 리듬, 스틸드럼'),
}

# ---------------------------------------------------------------- voices
rng = np.random.default_rng(0)
def env(L, a, d):
    t = np.arange(L) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
def lp(x, k): return np.convolve(x, np.ones(k) / k, 'same') if k > 1 else x
def noise(L): return rng.standard_normal(L)

def kick(g=1.0):
    L = int(.28 * SR); t = np.arange(L) / SR; fr = 48 + 95 * np.exp(-t * 32)
    return g * np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 13)
def snare(g=1.0):
    L = int(.2 * SR); t = np.arange(L) / SR; n = noise(L); n = n - lp(n, 6)
    return g * (0.55 * n * np.exp(-t * 20) + 0.35 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30))
def clap(g=1.0):
    L = int(.18 * SR); t = np.arange(L) / SR; x = noise(L); x = x - lp(x, 4)
    e = np.exp(-t * 22) * (1 + .7 * ((t % .011) < .005) * (t < .03))
    return g * .5 * x * e
def hat(open_=False, g=1.0):
    L = int((.16 if open_ else .045) * SR); x = noise(L); x = x - lp(x, 3)
    return g * .3 * x * np.exp(-np.arange(L) / SR * (18 if open_ else 85))
def shaker(g=1.0):
    L = int(.07 * SR); x = noise(L); x = x - lp(x, 2); t = np.arange(L) / SR
    return g * .16 * x * np.sin(np.pi * np.minimum(1, t / .07))
def rim(g=1.0):
    L = int(.05 * SR); t = np.arange(L) / SR
    return g * .35 * (np.sin(2 * np.pi * 1700 * t) + .5 * np.sin(2 * np.pi * 820 * t)) * np.exp(-t * 90)

def bass_tone(m, dur, kind='round'):
    L = int(dur * SR); t = np.arange(L) / SR; ph = 2 * np.pi * f(m) * t
    if kind == 'slap':
        y = np.sin(ph) + .5 * np.sin(2 * ph) * np.exp(-t * 18) + .25 * np.sin(3 * ph) * np.exp(-t * 25)
        return y * np.minimum(1, t * 600) * np.exp(-t * 5)
    if kind == 'sub':
        return np.sin(ph) * np.minimum(1, t * 300) * np.exp(-t * 2.5)
    y = np.sin(ph) + .3 * np.sin(2 * ph) + .12 * np.sin(3 * ph)
    return y * np.minimum(1, t * 250) * np.exp(-t * 3)

def pluck(m, dur=.4, bright=1.0):
    L = int(dur * SR); t = np.arange(L) / SR; y = np.zeros(L)
    for h in range(1, 8): y += np.sin(2 * np.pi * f(m) * h * t) / h ** 1.3 * np.exp(-t * (5 + h * 2.5 / bright))
    return y * np.minimum(1, t * 400)
def piano(m, dur=.6):
    L = int(dur * SR); t = np.arange(L) / SR; y = np.zeros(L)
    for h, a in [(1, 1), (2, .45), (3, .22), (4, .12), (5, .06)]:
        y += a * np.sin(2 * np.pi * f(m) * h * 1.0007 ** h * t) * np.exp(-t * (2.6 + h * 1.4))
    return y * np.minimum(1, t * 900)
def clav(m, dur=.16):
    L = int(dur * SR); t = np.arange(L) / SR
    y = np.sign(np.sin(2 * np.pi * f(m) * t)) * .5 + np.sin(2 * np.pi * 2 * f(m) * t) * .4
    return lp(y, 6) * np.exp(-t * 22) * np.minimum(1, t * 800)
def marimba(m, dur=.45):
    L = int(dur * SR); t = np.arange(L) / SR
    return (np.sin(2 * np.pi * f(m) * t) + .35 * np.sin(2 * np.pi * f(m) * 3.93 * t) * np.exp(-t * 30)) * np.exp(-t * 7) * np.minimum(1, t * 800)
def bell(m, dur=.7):
    L = int(dur * SR); t = np.arange(L) / SR
    return (np.sin(2 * np.pi * f(m) * t + 1.2 * np.sin(2 * np.pi * f(m) * 3.5 * t) * np.exp(-t * 6))) * np.exp(-t * 4.5) * np.minimum(1, t * 600)
def steel(m, dur=.5):
    L = int(dur * SR); t = np.arange(L) / SR
    return (np.sin(2 * np.pi * f(m) * t) + .5 * np.sin(2 * np.pi * f(m) * 2.01 * t) + .25 * np.sin(2 * np.pi * f(m) * 3.02 * t)) * np.exp(-t * 6) * np.minimum(1, t * 500)
def whistle(m, dur=.4):
    L = int(dur * SR); t = np.arange(L) / SR; vib = 1 + .006 * np.sin(2 * np.pi * 5.5 * t)
    a = np.minimum(1, t / .04) * np.minimum(1, (dur - t) / .06)
    return np.sin(2 * np.pi * f(m) * vib * t) * np.clip(a, 0, 1) + .02 * noise(L) * np.clip(a, 0, 1)
def pad(ms, dur):
    L = int(dur * SR); t = np.arange(L) / SR; y = np.zeros(L)
    for m in ms:
        for d in (-.07, .07): y += np.sin(2 * np.pi * f(m) * (1 + d / 100) * t)
    a = np.minimum(1, t / .4) * np.clip((dur - t) / .4, 0, 1)
    return lp(y, 8) * a / (2 * len(ms))

# ---------------------------------------------------------------- arranger
def render_style(name, T, seed, loop=False):
    st = STYLES[name]; R = random.Random(seed)
    trans = R.choice([-2, -1, 0, 0, 1, 2, 3]); bpm = st['bpm'] + R.choice([-3, -2, 0, 0, 2, 3])
    beat = 60 / bpm; bar = 4 * beat; swing = st['swing']
    n = int(SR * (T + 2)); out = np.zeros(n)
    def add(sig, t0, g=1.0):
        s = int(t0 * SR); e = min(n, s + len(sig))
        if 0 <= s < n: out[s:e] += g * sig[:e - s]
    def at(b, pos):  # bar b, position in beats (swing applied to off-8ths)
        frac = pos % 1
        if swing and abs(frac - .5) < 1e-6: pos += swing * .5
        return b * bar + pos * beat
    prog = [(r + trans, [c + trans for c in cs]) for r, cs in st['prog']]
    # melody: random walk over chord tones, 2-bar motif repeated with variation
    motif = [R.choice([0, 1, 2, 1]) for _ in range(8)]
    rhythm = R.choice([[0, 1, 1.5, 2.5, 3], [0, .5, 1.5, 2, 3], [0, 1, 2, 2.5, 3.5], [.5, 1, 2, 3, 3.5]])
    drum_var = R.random() < .5
    nb = int(T / bar) + 2
    for b in range(nb):
        root, ch = prog[b % len(prog)]
        sec = (b // 8) % 3          # A, B, A' sections of 8 bars
        intro = b < 2; brk = (b % 24) in (22, 23); fill = (b % 8) == 7
        last = b * bar > T - bar
        D = st['drums']
        # ---- drums
        if not brk:
            if D in ('four', 'house'):
                for k in range(4): add(kick(), at(b, k), .95 if not intro else .5)
                for k in (1, 3): add(clap(), at(b, k), .55 if not intro else 0)
                for e in range(8): add(hat(open_=(D == 'house' and e % 2 == 1)), at(b, e / 2), .35 if e % 2 else .18)
                if D == 'four':
                    for s_ in range(16): add(hat(g=.5), b * bar + s_ * beat / 4, .12)
            elif D == 'pop':
                for k in ((0, 2) if not drum_var else (0, 1.5, 2)): add(kick(), at(b, k), .9)
                if not intro:
                    for k in (1, 3): add(clap(), at(b, k), .55)
                for e in range(8): add(hat(open_=(e == 7)), at(b, e / 2), .3 if e % 2 else .15)
            elif D == 'funk':
                for k in (0, 1.75, 2.5): add(kick(), at(b, k), .9)
                if not intro:
                    for k in (1, 3): add(snare(), at(b, k), .6)
                    add(snare(), at(b, 3.75), .18)  # ghost
                for s_ in range(16): add(hat(g=1), b * bar + s_ * beat / 4, .2 if s_ % 2 else .1)
            elif D == 'shuffle':
                for k in (0, 2): add(kick(), at(b, k), .75)
                if not intro:
                    for k in (1, 3): add(clap(), at(b, k), .45)
                for e in range(8): add(shaker(), at(b, e / 2), 1.0 if e % 2 else .6)
            elif D == 'dembow':
                for k in (0, 2): add(kick(), at(b, k), .9)
                if not intro:
                    for k in (.75, 1.5, 2.75, 3.5): add(rim(), at(b, k), .8)
                for e in range(8): add(shaker(), at(b, e / 2), .9)
            if fill and not intro:
                for s_ in range(4): add(snare(), at(b, 3 + s_ / 4), .25 + .1 * s_)
        # ---- bass
        Bk = st['bass']
        if not intro or Bk in ('walk',):
            if Bk == 'bounce':
                for e in range(8): add(bass_tone(root + (12 if e in (2, 6) else 0), beat / 2 * .9), at(b, e / 2), .55)
            elif Bk == 'eighths':
                for e in range(8): add(bass_tone(root, beat / 2 * .85), at(b, e / 2), .5)
            elif Bk == 'slap':
                for pos, dm in [(0, 0), (.75, 12), (1.5, 0), (2, 7), (2.75, 12), (3.5, 10)]: add(bass_tone(root + dm, beat * .45, 'slap'), at(b, pos), .55)
            elif Bk == 'offbeat':
                for k in range(4): add(bass_tone(root, beat * .45, 'sub'), at(b, k + .5), .6)
            elif Bk == 'walk':
                for k, dm in enumerate([0, 4, 7, 9]): add(bass_tone(root + dm, beat * .85), at(b, k), .5)
            elif Bk == 'tropical':
                for pos, dm in [(0, 0), (1.5, 7), (2, 0), (3, 12)]: add(bass_tone(root + dm, beat * .7), at(b, pos), .55)
        # ---- comping
        Cp = st['comp']
        if Cp == 'stabs':
            for pos in (.5, 1.5, 2, 2.5, 3.5):
                for m in ch: add(pluck(m, .35), at(b, pos), .2)
        elif Cp == 'arp16':
            seq = (ch + [ch[0] + 12, ch[1] + 12])
            for s_ in range(16): add(pluck(seq[(s_ + b) % len(seq)] + 12, .22, 1.4), b * bar + s_ * beat / 4, .12)
        elif Cp == 'clav':
            for pos in (.25, .75, 1.5, 2.25, 2.75, 3.5):
                for m in ch[1:]: add(clav(m + 12), at(b, pos), .14)
        elif Cp == 'piano':
            for k in range(4):
                for m in ch: add(piano(m + 12, .3), at(b, k + .5), .2)
        elif Cp == 'strum':
            for pos, d in [(0, 1), (1, 1), (1.5, -1), (2.5, -1), (3, 1), (3.5, -1)]:
                for j, m in enumerate(ch if d > 0 else ch[::-1]): add(pluck(m + 12, .35, 1.2), at(b, pos) + j * .012, .16)
        elif Cp == 'marimba':
            pat = [0, .75, 1.5, 2, 2.75, 3.5]
            for i, pos in enumerate(pat): add(marimba(ch[i % len(ch)] + 12, .4), at(b, pos), .3)
        if sec == 1 and Cp not in ('strum',):
            add(pad(ch, bar), b * bar, .18)   # B section gets a soft pad lift
        # ---- lead melody (sparse; B and A' sections only so narration stays clear)
        Ld = st['lead']
        if Ld != 'none' and b >= 4 and sec != 0:
            tones = sorted(ch + [c + 12 for c in ch]); voice = {'bell': bell, 'steel': steel, 'whistle': whistle}[Ld]
            for i, pos in enumerate(rhythm):
                m = tones[(motif[(i + b) % 8] + i + (b % 2)) % len(tones)] + 12
                add(voice(m, beat * .9), at(b, pos), .13)
        if last: break
    out = out[:int(SR * T)]
    t = np.arange(len(out)) / SR
    fi, fo = (0.03, 0.35) if loop else (0.6, 2.0)
    out *= np.minimum(1, t / fi) * np.clip((T - t) / fo, 0, 1)
    meta = dict(style=name, seed=seed, bpm=bpm, transpose=trans)
    return out, meta

def save(path, x):
    x = np.tanh(x * 1.15); x = x / (np.abs(x).max() + 1e-9) * .85
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())

def pick_auto(R):
    try: hist = json.load(open(HIST))
    except Exception: hist = []
    recent = set(hist[-3:])
    pool = [s for s in STYLES if s not in recent] or list(STYLES)
    return R.choice(pool)

def remember(styles):
    try: hist = json.load(open(HIST))
    except Exception: hist = []
    os.makedirs(os.path.dirname(HIST), exist_ok=True)
    json.dump((hist + styles)[-12:], open(HIST, 'w'))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out'); ap.add_argument('--length', type=float)
    ap.add_argument('--style', default='auto', help="style name, 'auto', or 'a,b' for a medley")
    ap.add_argument('--switch-at', type=float, help='medley switch time in seconds (default: middle)')
    ap.add_argument('--seed', type=int); ap.add_argument('--loop', action='store_true'); ap.add_argument('--list', action='store_true')
    a = ap.parse_args()
    if a.list:
        for k, v in STYLES.items(): print(f'{k:10s} {v["bpm"]:>3} BPM  {v["desc"]}')
        return
    seed = a.seed if a.seed is not None else int(time.time()) % 100000
    R = random.Random(seed)
    names = [pick_auto(R)] if a.style == 'auto' else a.style.split(',')
    if a.style == 'auto,auto':
        names = [pick_auto(R)]; names.append(R.choice([s for s in STYLES if s != names[0]]))
    for nm in names:
        if nm not in STYLES: raise SystemExit(f'unknown style {nm}; use --list')
    if len(names) == 1:
        x, meta = render_style(names[0], a.length, seed, a.loop); metas = [meta]
    else:
        sw = a.switch_at or a.length / 2; xf = 1.5
        x1, m1 = render_style(names[0], a.length, seed, a.loop)
        x2, m2 = render_style(names[1], a.length, seed + 1, a.loop)
        t = np.arange(len(x1)) / SR; g = np.clip((t - (sw - xf / 2)) / xf, 0, 1)
        g = .5 - .5 * np.cos(np.pi * g)            # equal-ish power crossfade
        x = x1 * (1 - g) + x2[:len(x1)] * g; metas = [m1, dict(m2, starts_at=sw)]
    save(a.out, x); remember(names)
    print(json.dumps(metas, ensure_ascii=False))

if __name__ == '__main__':
    main()
