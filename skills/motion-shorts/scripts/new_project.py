#!/usr/bin/env python3
"""Create a motion-shorts project folder from the engine template.

  python3 new_project.py <project_dir> [--theme dark|paper] [--script script.json]

Copies assets/engine.html -> index.html and the Pretendard fonts, and (if --script is given)
copies the approved script and writes placeholder timing so scenes can be built and previewed
before any voice credits are spent.
"""
import argparse, json, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
ap = argparse.ArgumentParser(); ap.add_argument('dir'); ap.add_argument('--theme', default='dark'); ap.add_argument('--script')
a = ap.parse_args(); d = a.dir; os.makedirs(d, exist_ok=True)
if os.path.exists(os.path.join(d, 'index.html')): sys.exit('index.html already exists - refusing to overwrite')
html = open(os.path.join(ROOT, 'assets', 'engine.html')).read().replace("theme:'dark',", f"theme:'{a.theme}',", 1)
open(os.path.join(d, 'index.html'), 'w').write(html)
shutil.copytree(os.path.join(ROOT, 'assets', 'fonts'), os.path.join(d, 'fonts'), dirs_exist_ok=True)
src = a.script or os.path.join(ROOT, 'assets', 'demo_script.json')
shutil.copy(src, os.path.join(d, 'script.json'))
subprocess.run([sys.executable, os.path.join(HERE, 'prep_audio.py'), '--placeholder', '--script', os.path.join(d, 'script.json'), '--out', d], check=True)
print('project ready:', d, '(index.html, fonts/, script.json, placeholder timing.js)')
