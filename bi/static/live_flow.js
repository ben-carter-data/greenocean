
(function () {
  const data = JSON.parse(document.getElementById('lf-data').textContent);
  const svg = document.querySelector('.lf-svg');
  const card = document.querySelector('.lf-card');
  const pauseButton = document.getElementById('lf-pause');
  const replayButton = document.getElementById('lf-replay');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const ns = 'http://www.w3.org/2000/svg';
  let paused = false, timer = null, frames = [];
  const node = (id) => document.getElementById('arrow-' + id) || document.getElementById('piece-' + id);
  function clearMarks() {
    document.querySelectorAll('.lf-done, .lf-failed, .lf-working, .lf-active').forEach((el) =>
      el.classList.remove('lf-done', 'lf-failed', 'lf-working', 'lf-active'));
    document.querySelectorAll('.lf-message').forEach((dot) => dot.remove());
    frames.forEach((frame) => cancelAnimationFrame(frame)); frames = [];
  }
  function mark(step, kind) {
    step.elements.forEach((id) => { const el = node(id); if (el) el.classList.add(kind); });
  }
  function travel(path, color, reverse, done) {
    const length = path.getTotalLength();
    const dot = document.createElementNS(ns, 'circle');
    dot.setAttribute('r', '6'); dot.setAttribute('fill', color); dot.setAttribute('class', 'lf-message');
    svg.appendChild(dot);
    const duration = Math.max(700, Math.min(1400, length * 4));
    let start = null;
    function frame(time) {
      if (paused) { start = null; frames.push(requestAnimationFrame(frame)); return; }
      if (start === null) start = time - (dot.progress || 0) * duration;
      const progress = Math.min(1, (time - start) / duration);
      dot.progress = progress;
      const point = path.getPointAtLength((reverse ? 1 - progress : progress) * length);
      dot.setAttribute('cx', point.x); dot.setAttribute('cy', point.y);
      if (progress < 1) frames.push(requestAnimationFrame(frame)); else { dot.remove(); if (done) done(); }
    }
    frames.push(requestAnimationFrame(frame));
  }
  function play(step, onEnd) {
    mark(step, 'lf-working');
    const arrows = step.elements.filter((id) => document.getElementById('arrow-' + id));
    arrows.forEach((id) => document.getElementById('arrow-' + id).classList.add('lf-active'));
    if (reduced || !arrows.length) { timer = setTimeout(onEnd, 1500); return; }
    let left = arrows.length;
    arrows.forEach((id) => {
      const path = document.querySelector('#arrow-' + id + ' .lf-line');
      travel(path, data.request, false, () => travel(path, data.answer, true, () => { if (--left === 0) onEnd(); }));
    });
  }
  function live() {
    clearMarks();
    const index = data.timeline.findIndex((step) => step.state === 'in_progress');
    data.timeline.forEach((step, position) => {
      if (step.state === 'ok' && (index < 0 || position < index)) mark(step, 'lf-done');
      if (step.state === 'failed') mark(step, 'lf-failed');
    });
    if (index < 0) return;
    const loop = () => { if (!paused) play(data.timeline[index], () => { document.querySelectorAll('.lf-message').forEach((d) => d.remove()); loop(); }); else timer = setTimeout(loop, 300); };
    loop();
  }
  function replay() {
    clearMarks(); clearTimeout(timer);
    let position = 0;
    const next = () => {
      if (position > 0) { const before = data.timeline[position - 1]; before.elements.forEach((id) => { const el = node(id); if (el) { el.classList.remove('lf-working', 'lf-active'); el.classList.add(before.state === 'failed' ? 'lf-failed' : 'lf-done'); } }); }
      if (position >= data.timeline.length) return;
      const step = data.timeline[position++];
      document.getElementById('lf-step').textContent = step.name;
      if (paused) { position--; timer = setTimeout(next, 300); return; }
      play(step, next);
    };
    next();
  }
  pauseButton.addEventListener('click', () => {
    paused = !paused;
    pauseButton.textContent = paused ? '▶ ' + data.labels.resume : '⏸ ' + data.labels.pause;
    document.querySelectorAll('.lf-working .lf-tile').forEach((tile) => tile.style.animationPlayState = paused ? 'paused' : 'running');
  });
  if (replayButton) replayButton.addEventListener('click', () => { paused = false; pauseButton.textContent = '⏸ ' + data.labels.pause; replay(); });
  function open(id) {
    const text = data.arrows[id];
    document.querySelectorAll('.lf-open').forEach((el) => el.classList.remove('lf-open'));
    document.getElementById('arrow-' + id).classList.add('lf-open');
    card.querySelector('h3').textContent = text.title;
    const list = card.querySelector('dl'); list.replaceChildren();
    const rows = [['ask', text.ask], ['answer', text.answer], ['when', text.when], ['why', text.why]];
    if (data.facts[id]) rows.push(['last', data.facts[id]]);
    rows.forEach(([key, value]) => {
      const term = document.createElement('dt'); term.textContent = data.labels[key];
      const value_ = document.createElement('dd'); value_.textContent = value;
      list.append(term, value_);
    });
    card.querySelector('.lf-deduced').textContent = text.deduced ? data.labels.deduced : '';
    card.classList.add('lf-show');
  }
  document.querySelectorAll('.lf-arrow').forEach((arrow) => {
    arrow.addEventListener('click', () => open(arrow.dataset.id));
    arrow.addEventListener('keydown', (event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); open(arrow.dataset.id); } });
  });
  card.querySelector('.lf-x').addEventListener('click', () => { card.classList.remove('lf-show'); document.querySelectorAll('.lf-open').forEach((el) => el.classList.remove('lf-open')); });
  if (data.mode === 'live') live();
})();
