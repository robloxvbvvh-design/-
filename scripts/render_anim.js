// Рендер мультфильма в video.mp4: node scripts/render_anim.js (нужны playwright, ffmpeg, python3)
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const ROOT = path.resolve(__dirname, '..'), FPS = 30, PORT = 8765;
(async () => {
  const server = spawn('python3', ['-m', 'http.server', String(PORT)], { cwd: ROOT, stdio: 'ignore' });
  await new Promise(r => setTimeout(r, 800));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => console.error('page error:', e.message));
  await page.goto(`http://localhost:${PORT}/index.html`);
  await page.evaluate(() => window.ready);
  const dur = Number(process.argv[2]) || 41.87;
  const ff = spawn('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-i', 'audio.mp3', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', process.argv[3] || 'video.mp4'], { cwd: ROOT, stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.ceil(dur * FPS);
  for (let i = 0; i < n; i++) {
    const url = await page.evaluate(t => window.renderAt(t), i / FPS);
    if (!ff.stdin.write(Buffer.from(url.split(',')[1], 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 150 === 0) console.log(`кадр ${i}/${n}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close(); server.kill();
  console.log('готово');
})();
