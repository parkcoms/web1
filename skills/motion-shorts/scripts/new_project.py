#!/usr/bin/env python3
"""Create a motion-shorts project folder from the engine template.

  python3 new_project.py <project_dir> [--theme dark|paper] [--script script.json] [--ending auto|wave|seal|tablet|portrait]

Copies assets/engine.html -> index.html and the Pretendard fonts, and (if --script is given)
copies the approved script and writes placeholder timing so scenes can be built and previewed
before any voice credits are spent.

The closing scene (CONFIG.ending) is picked at random and rotates: every ending is used once
before any repeats, and the last one is never used twice in a row (history in ~/.motion-shorts/).
"""
import argparse, json, os, random, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
ap = argparse.ArgumentParser(); ap.add_argument('dir'); ap.add_argument('--theme', default='dark'); ap.add_argument('--script')
ap.add_argument('--ending', default='auto', choices=['auto', 'wave', 'seal', 'tablet', 'portrait'])
a = ap.parse_args(); d = a.dir; os.makedirs(d, exist_ok=True)
if os.path.exists(os.path.join(d, 'index.html')): sys.exit('index.html already exists - refusing to overwrite')
ENDINGS = ['wave', 'seal', 'tablet', 'portrait']; STATE = os.path.expanduser('~/.motion-shorts/ending_state.json')
try: st = json.load(open(STATE))
except Exception: st = {}
bag = [e for e in st.get('bag', []) if e in ENDINGS] or list(ENDINGS)   # endings not yet used in this round
ending = a.ending
if ending == 'auto': ending = random.choice([e for e in bag if e != st.get('last')] or bag)
if ending in bag: bag.remove(ending)
os.makedirs(os.path.dirname(STATE), exist_ok=True); json.dump({'bag': bag, 'last': ending}, open(STATE, 'w'))
html = open(os.path.join(ROOT, 'assets', 'engine.html')).read().replace("theme:'dark',", f"theme:'{a.theme}',", 1).replace("ending:'wave',", f"ending:'{ending}',", 1)
open(os.path.join(d, 'index.html'), 'w').write(html)
shutil.copytree(os.path.join(ROOT, 'assets', 'fonts'), os.path.join(d, 'fonts'), dirs_exist_ok=True)
shutil.copy(os.path.join(ROOT, 'assets', 'portrait.js'), os.path.join(d, 'portrait.js'))   # for the 'portrait' ending
src = a.script or os.path.join(ROOT, 'assets', 'demo_script.json')
if os.path.abspath(src) != os.path.abspath(os.path.join(d, 'script.json')): shutil.copy(src, os.path.join(d, 'script.json'))
if os.path.exists(os.path.join(d, 'timing.js')):
    print('timing.js already exists (real timing?) - kept as is')
else:
    subprocess.run([sys.executable, os.path.join(HERE, 'prep_audio.py'), '--placeholder', '--script', os.path.join(d, 'script.json'), '--out', d], check=True)
print('project ready:', d, f'(index.html, fonts/, script.json, placeholder timing.js) | ending: {ending}')
