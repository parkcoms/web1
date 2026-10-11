#!/usr/bin/env python3
"""Synthesize the sound-effect track from the SFX cue list exported by the animation.

  python3 sfx.py --meta work/meta.json --out work/sfx.wav

meta.json comes from `node render.js index.html meta work/meta.json`; its SFX entries are
[kind, start_seconds, duration_seconds]. Kinds (pick by what happens on screen):
  pop      bubble / card / icon pops in            tick     list item or counter step
  click    button press                             type     typing (needs duration)
  check    check mark drawn                         ding     highlight, key point lands
  stamp    stamp slams down                         thud     big emphatic hit (warning, title slam)
  whoosh   scene transition (added automatically)   swoosh   object flies / arrow draws
  rise     panel slides up                          beep     alert / danger two-tone
  coin     money, reward                            count    number counting up (needs duration)
  scribble pen circling (needs duration)           sparkle  positive reveal (badge, success)
  buzz     negative / "not allowed"                 riser    0.6 s build-up before a reveal
"""
import argparse, json, wave
import numpy as np

SR = 44100
rng = np.random.default_rng(3)
def lp(x, k): return np.convolve(x, np.ones(k) / k, 'same')
def env(L, a, d): t = np.arange(L) / SR; return np.minimum(1, t / a) * np.exp(-t / d)
def tone(fr, L, d, a=.002): t = np.arange(L) / SR; return np.sin(2 * np.pi * fr * t) * env(L, a, d)
def sweep(f0, f1, L, d): fr = np.linspace(f0, f1, L); return np.sin(2 * np.pi * np.cumsum(fr) / SR) * env(L, .003, d)
def noise(L): return rng.standard_normal(L)
def pad_to(x, L): return np.concatenate([x, np.zeros(max(0, L - len(x)))])[:L]

def mk(kind, dur=0):
    if kind == 'pop':   L = int(.12 * SR); return .5 * sweep(380, 900, L, .04)
    if kind == 'tick':  L = int(.06 * SR); return .35 * tone(1800, L, .012) + .2 * tone(2700, L, .008)
    if kind == 'click': L = int(.05 * SR); return .5 * lp(noise(L), 3) * env(L, .0005, .006) + .3 * tone(1200, L, .01)
    if kind == 'check': L = int(.25 * SR); return .3 * tone(1318, L, .06) + .25 * pad_to(np.concatenate([np.zeros(int(.07 * SR)), tone(1760, L, .08)]), L)
    if kind == 'ding':  L = int(.9 * SR); return .22 * (tone(1568, L, .35) + .4 * tone(3136, L, .15) + .2 * tone(2350, L, .25))
    if kind == 'stamp':
        L = int(.35 * SR); t = np.arange(L) / SR
        return .9 * np.sin(2 * np.pi * np.cumsum(60 + 140 * np.exp(-t * 40)) / SR) * np.exp(-t * 12) + .4 * lp(noise(L), 6) * np.exp(-t * 30)
    if kind == 'thud':
        L = int(.6 * SR); t = np.arange(L) / SR
        return np.sin(2 * np.pi * np.cumsum(45 + 90 * np.exp(-t * 25)) / SR) * np.exp(-t * 6) + .25 * lp(noise(L), 20) * np.exp(-t * 10)
    if kind in ('whoosh', 'swoosh', 'rise'):
        L = int({'whoosh': .45, 'swoosh': .5, 'rise': .35}[kind] * SR); t = np.arange(L) / L; x = noise(L)
        k = 8 if kind == 'rise' else 14; y = lp(x, k) - lp(x, k * 6)
        return {'whoosh': .55, 'swoosh': .45, 'rise': .25}[kind] * y * np.sin(np.pi * t) ** 2 * 4
    if kind == 'type':
        dur = dur or .4; L = int(dur * SR); y = np.zeros(L); t0 = 0
        while t0 < dur - .03:
            s = int(t0 * SR); c = mk('click') * rng.uniform(.4, .8); e = min(L, s + len(c)); y[s:e] += c[:e - s]; t0 += rng.uniform(.06, .11)
        return y * .8
    if kind == 'scribble':
        dur = dur or .4; L = int(dur * SR); t = np.arange(L) / SR; x = lp(noise(L), 4) - lp(noise(L), 30)
        return .35 * x * (.5 + .5 * np.abs(np.sin(t * 2 * np.pi * 7))) * np.minimum(1, (dur - t) * 10)
    if kind == 'beep':
        L = int(.22 * SR); t = np.arange(L) / SR
        return .28 * (np.sin(2 * np.pi * 880 * t) * (t < .09) + np.sin(2 * np.pi * 660 * t) * (t >= .11)) * np.minimum(1, t / .003) * np.exp(-t * 4)
    if kind == 'coin':  L = int(.5 * SR); return .25 * (tone(1975, L, .08) + pad_to(np.concatenate([np.zeros(int(.08 * SR)), tone(2637, L, .25)]), L))
    if kind == 'count':
        L = int(max(dur, .2) * SR); y = np.zeros(L)
        for k, t0 in enumerate(np.linspace(0, max(dur, .2) - .05, 6)):
            s = int(t0 * SR); c = tone(900 + k * 120, int(.05 * SR), .015) * .35; y[s:s + len(c)] += c[:L - s]
        return y
    if kind == 'sparkle':
        L = int(.7 * SR); y = np.zeros(L)
        for k, fr in enumerate([2093, 2637, 3136, 4186]):
            s = int(k * .05 * SR); c = tone(fr, L - s, .18) * .14; y[s:] += c
        return y
    if kind == 'buzz':
        L = int(.35 * SR); t = np.arange(L) / SR
        return .22 * np.sign(np.sin(2 * np.pi * 140 * t)) * lp(np.ones(L), 1) * np.minimum(1, t / .005) * np.clip((.35 - t) / .05, 0, 1)
    if kind == 'riser':
        L = int(.6 * SR); t = np.arange(L) / L; x = noise(L); y = lp(x, 6) - lp(x, 40)
        return .35 * y * t ** 2 + .12 * sweep(300, 1400, L, 10) * t
    raise ValueError(f'unknown sfx kind {kind}')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--meta', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args(); meta = json.load(open(a.meta)); T = meta['T']; n = int(SR * T) + SR; out = np.zeros(n)
    for kind, t0, d in meta['SFX']:
        s = mk(kind, d); i = int(t0 * SR)
        if i < 0: s = s[-i:]; i = 0
        e = min(n, i + len(s)); out[i:e] += s[:e - i]
    out = np.tanh(out[:int(SR * T)] * 1.1) * .8
    with wave.open(a.out, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
    print('sfx events', len(meta['SFX']), '->', a.out)

if __name__ == '__main__':
    main()
