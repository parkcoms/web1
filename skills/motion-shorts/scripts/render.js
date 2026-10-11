#!/usr/bin/env node
// Render the canvas animation (index.html) with headless Chromium.
//   node render.js <project>/index.html meta   <out.json>            -> {T, C (narration cues), SFX, starts (scene starts, for chapters)}
//   node render.js <project>/index.html stills <outDir> 0 6.2 14.6     -> JPEG stills at given seconds
//   node render.js <project>/index.html sheet  <out.jpg> 0 6.2 14.6 ... -> one contact sheet (300px-wide tiles)
//   node render.js <project>/index.html video  <silent.mp4> [fps=30]   -> H.264 video, no audio
// Console errors from the page (e.g. a word lookup that does not exist) are printed - read them.
const path = require('path'), fs = require('fs'), { spawn, execFileSync } = require('child_process');
let chromium;
for (const p of ['playwright', '/opt/node22/lib/node_modules/playwright']) { try { ({ chromium } = require(p)); break; } catch (e) {} }
if (!chromium) { console.error('playwright not found'); process.exit(1); }

(async () => {
  const [, , html, mode, out, ...rest] = process.argv;
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('console', m => console.log('page:', m.text())); p.on('pageerror', e => console.log('PAGE ERROR', e.message));
  await p.goto('file://' + path.resolve(html) + '?render=1'); await p.evaluate(() => window.ready);
  const total = await p.evaluate(() => window.TOTAL);
  const grab = (t, q = .94) => p.evaluate(([t, q]) => { renderFrame(t); return document.getElementById('c').toDataURL('image/jpeg', q).split(',')[1]; }, [t, q]);
  if (mode === 'meta') {
    const m = await p.evaluate(() => ({ T: window.TOTAL, C: window.CUES, SFX: window.SFX, starts: S.map(s => +s.s.toFixed(2)) }));
    fs.writeFileSync(out, JSON.stringify(m)); console.log('total', m.T.toFixed(2), 's; cues', m.C.length, '; sfx', m.SFX.length);
  } else if (mode === 'stills' || mode === 'sheet') {
    const ts = rest.map(Number); const dir = mode === 'stills' ? out : fs.mkdtempSync('/tmp/sheet-');
    fs.mkdirSync(dir, { recursive: true }); const files = [];
    for (const t of ts) { const f = path.join(dir, `s_${t.toFixed(2)}.jpg`); fs.writeFileSync(f, Buffer.from(await grab(t), 'base64')); files.push(f); }
    if (mode === 'sheet') {
      const cols = Math.min(files.length, 7), rows = Math.ceil(files.length / cols);
      const args = []; files.forEach(f => args.push('-i', f));
      const lay = files.map((_, i) => `${(i % cols) * 300}_${Math.floor(i / cols) * 534}`).join('|');
      const scale = files.map((_, i) => `[${i}:v]scale=300:534[v${i}]`).join(';');
      const inputs = files.map((_, i) => `[v${i}]`).join('');
      const filter = files.length > 1 ? `${scale};${inputs}xstack=inputs=${files.length}:layout=${lay}:fill=black` : `[0:v]scale=300:534`;
      execFileSync('ffmpeg', ['-loglevel', 'error', '-y', ...args, '-filter_complex', filter, '-frames:v', '1', out]);
      console.log('sheet', out, `(${cols}x${rows}, total ${total.toFixed(2)} s)`);
    } else console.log('stills in', dir, '(total', total.toFixed(2), 's)');
  } else if (mode === 'video') {
    const fps = Number(rest[0] || 30), n = Math.round(total * fps);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', '-movflags', '+faststart', out], { stdio: ['pipe', 'ignore', 'inherit'] });
    for (let i = 0; i < n; i++) {
      const buf = Buffer.from(await grab(i / fps), 'base64');
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 300 === 0) console.log('frame', i, '/', n);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r)); console.log('done', n, 'frames ->', out);
  } else console.log('unknown mode', mode);
  await b.close();
})();
