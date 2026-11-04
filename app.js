const DIRECTIONS = [
  { name: 'Norte', dx: 0, dy: -1 },
  { name: 'Este', dx: 1, dy: 0 },
  { name: 'Sur', dx: 0, dy: 1 },
  { name: 'Oeste', dx: -1, dy: 0 },
];
const CONDITIONS = [
  ['frontFree', 'camino al frente libre'], ['frontBlocked', 'frente bloqueado'],
  ['leftFree', 'camino a la izquierda libre'], ['leftBlocked', 'izquierda bloqueada'],
  ['rightFree', 'camino a la derecha libre'], ['rightBlocked', 'derecha bloqueada'],
  ['markerHere', 'hay un marcador aquí'], ['noMarkerHere', 'no hay marcador aquí'],
  ['bagHas', 'hay marcadores en la mochila'], ['bagEmpty', 'mochila vacía'],
  ['north', 'mira al norte'], ['notNorth', 'no mira al norte'],
  ['south', 'mira al sur'], ['notSouth', 'no mira al sur'],
  ['east', 'mira al este'], ['notEast', 'no mira al este'],
  ['west', 'mira al oeste'], ['notWest', 'no mira al oeste'],
];
const BLOCKS = {
  move: { label: 'Avanzar', icon: '↑', bg: '#eaf1ff', ink: '#4569b4' },
  left: { label: 'Girar a la izquierda', icon: '↶', bg: '#f1edfc', ink: '#7661ac' },
  right: { label: 'Girar a la derecha', icon: '↷', bg: '#f1edfc', ink: '#7661ac' },
  pick: { label: 'Recoger marcador', icon: '●', bg: '#e7f5f0', ink: '#36816b' },
  drop: { label: 'Colocar marcador', icon: '◉', bg: '#e7f5f0', ink: '#36816b' },
  repeat: { label: 'Repetir', icon: '⟳', bg: '#fff3dc', ink: '#aa7827' },
  while: { label: 'Mientras', icon: '↻', bg: '#fff0e7', ink: '#b36a3c' },
  if: { label: 'Si / si no', icon: '◇', bg: '#e9f4e8', ink: '#548750' },
};

function makeLevel(name, width, height, start, goal, description, markers = {}, targets = {}, walls = []) {
  const wallSet = new Set();
  const opposite = { N: 'S', E: 'W', S: 'N', W: 'E' };
  const vectors = { N: [0, -1], E: [1, 0], S: [0, 1], W: [-1, 0] };
  for (const [x, y, direction] of walls) {
    wallSet.add(`${x},${y},${direction}`);
    const [dx, dy] = vectors[direction];
    wallSet.add(`${x + dx},${y + dy},${opposite[direction]}`);
  }
  return { name, width, height, start, goal, description, markers, targets, walls: wallSet };
}
const levels = [
  makeLevel('Primeros pasos', 8, 6, { x: 1, y: 3, dir: 1, bag: 0 }, [6, 5], 'Lleva a Karel hasta la estrella. Prueba «Avanzar» y «Repetir».', {}, {}, []),
  makeLevel('Recoge y entrega', 8, 6, { x: 1, y: 4, dir: 1, bag: 0 }, [6, 1], 'Recoge el marcador azul, evita el muro y déjalo sobre el objetivo.', { '3,4': 1 }, { '6,1': 1 }, [[4, 3, 'E'], [4, 2, 'E']]),
  makeLevel('El laberinto', 9, 7, { x: 1, y: 5, dir: 0, bag: 0 }, [7, 1], 'Llega a la estrella. Usa decisiones para avanzar sin chocar.', { '1,2': 1 }, {}, [...Array.from({ length: 6 }, (_, y) => y).filter(y => y !== 4).map(y => [2, y, 'E']), ...Array.from({ length: 5 }, (_, i) => i + 2).filter(x => x !== 5).map(x => [x, 3, 'S']), [5, 1, 'E']]),
  makeLevel('Siembra el jardín', 8, 6, { x: 1, y: 4, dir: 1, bag: 4 }, [6, 4], 'Coloca un marcador en cada objetivo verde y después llega a la estrella.', {}, { '2,4': 1, '3,4': 1, '4,4': 1, '5,4': 1 }, [[3, 1, 'S'], [3, 2, 'E']]),
  makeLevel('Laberinto en zigzag', 10, 8, { x: 1, y: 6, dir: 0, bag: 0 }, [8, 1], 'Sigue el camino en zigzag para llegar a la meta.', { '2,2': 1 }, {}, [...Array.from({ length: 4 }, (_, i) => [3, i * 2, 'E']), ...Array.from({ length: 3 }, (_, i) => [3 + i * 2, 4, 'S'])]),
  makeLevel('Múltiples caminos', 10, 7, { x: 1, y: 5, dir: 0, bag: 0 }, [7, 2], 'Encuentra el camino correcto entre múltiples opciones.', { '3,3': 1 }, {}, [...Array.from({ length: 5 }, (_, i) => [4, i + 1, 'E']), ...Array.from({ length: 5 }, (_, i) => i + 2).filter(x => x !== 5).map(x => [x, 2, 'S']), [6, 4, 'E']]),
];

const $ = (selector, root = document) => root.querySelector(selector);
const boardEl = $('#board');
const programEl = $('#program-list');
const state = {
  levelIndex: 0, world: null, program: [], scope: [], selectedId: null,
  undo: [], redo: [], id: 0, iterator: null, running: false, paused: false,
  activeId: null, actions: 0, timer: null, completedLevels: new Set(),
};
const clone = value => JSON.parse(JSON.stringify(value));
const directionIndex = name => DIRECTIONS.findIndex(direction => direction.name === name);
const currentLevel = () => levels[state.levelIndex];
const keyAt = (x, y) => `${x},${y}`;
const keyWall = (x, y, d) => `${x},${y},${d}`;

function newWorld() {
  const level = currentLevel();
  return { x: level.start.x, y: level.start.y, dir: level.start.dir, bag: level.start.bag, markers: { ...level.markers }, actions: 0 };
}
function listAtScope() {
  let list = state.program;
  for (const step of state.scope) {
    const parent = list.find(block => block.id === step.id);
    if (!parent || !['repeat', 'while', 'if'].includes(parent.type)) return state.program;
    list = step.branch === 'else' ? parent.elseChildren : parent.children;
  }
  return list;
}
function findBlock(id, list = state.program, parent = null) {
  for (const block of list) {
    if (block.id === id) return { block, list, parent };
    const found = findBlock(id, block.children, block);
    if (found) return found;
    const alternative = findBlock(id, block.elseChildren, block);
    if (alternative) return alternative;
  }
  return null;
}
function totalBlocks(list = state.program) {
  return list.reduce((sum, block) => sum + 1 + totalBlocks(block.children) + totalBlocks(block.elseChildren), 0);
}
function saveHistory() {
  state.undo.push(clone(state.program));
  if (state.undo.length > 50) state.undo.shift();
  state.redo = [];
  renderHistory();
}
function renderHistory() {
  $('#undo-button').disabled = state.undo.length === 0 || state.running;
  $('#redo-button').disabled = state.redo.length === 0 || state.running;
}
function announce(message, kind = '') {
  const feedback = $('#feedback');
  feedback.className = `feedback ${kind}`.trim();
  $('#feedback-text').textContent = message;
}
function setHint(message) { $('#run-hint').textContent = message; }
function setTransport() {
  $('#pause-button').disabled = !state.running;
  $('#stop-button').disabled = !state.iterator && !state.running;
  $('#pause-button').textContent = state.paused ? '▶' : 'Ⅱ';
  $('#pause-button').title = state.paused ? 'Continuar' : 'Pausar';
  $('#run-label').textContent = state.running ? (state.paused ? 'Continuar programa' : 'Ejecutando…') : 'Ejecutar programa';
  $('#run-button').querySelector('.run-glyph').textContent = state.running && !state.paused ? 'Ⅱ' : '▶';
  $('#run-button').setAttribute('aria-label', state.running ? (state.paused ? 'Continuar programa' : 'Pausar programa') : 'Ejecutar programa');
  renderHistory();
}
function setWorld() {
  const level = currentLevel();
  boardEl.style.setProperty('--cols', level.width);
  boardEl.style.setProperty('--rows', level.height);
  boardEl.style.setProperty('aspect-ratio', `${level.width} / ${level.height}`);
  boardEl.innerHTML = '';
  for (let y = 0; y < level.height; y++) {
    for (let x = 0; x < level.width; x++) {
      const cell = document.createElement('div');
      const cellKey = keyAt(x, y);
      cell.className = 'cell';
      cell.dataset.position = cellKey;
      if (level.targets[cellKey]) cell.classList.add('target');
      if (level.goal[0] === x && level.goal[1] === y) {
        cell.classList.add('goal-cell');
        const star = document.createElement('span');
        star.className = 'goal-star'; star.textContent = '✳'; star.setAttribute('aria-hidden', 'true'); cell.append(star);
      }
      for (const [direction, name] of [['N', 'north'], ['E', 'east'], ['S', 'south'], ['W', 'west']]) {
        if (level.walls.has(keyWall(x, y, direction))) cell.classList.add(`wall-${name}`);
      }
      boardEl.append(cell);
    }
  }
  $('#level-title').textContent = level.name;
  $('#level-kicker').textContent = `MUNDO 01 · NIVEL ${String(state.levelIndex + 1).padStart(2, '0')}`;
  $('#level-description').textContent = level.description;
  $('#world-coordinates').textContent = `MUNDO ${level.width} × ${level.height}`;
  $('#level-select').value = String(state.levelIndex);
  renderWorld();
}
function renderWorld() {
  if (!state.world) return;
  boardEl.querySelectorAll('.marker-token,.marker-count,.robot').forEach(element => element.remove());
  for (const [cellKey, count] of Object.entries(state.world.markers)) {
    if (count < 1) continue;
    const cell = boardEl.querySelector(`[data-position="${cellKey}"]`);
    if (!cell) continue;
    const marker = document.createElement('span'); marker.className = 'marker-token'; marker.setAttribute('aria-hidden', 'true'); cell.append(marker);
    if (count > 1) { const amount = document.createElement('span'); amount.className = 'marker-count'; amount.textContent = count; cell.append(amount); }
  }
  const cell = boardEl.querySelector(`[data-position="${keyAt(state.world.x, state.world.y)}"]`);
  if (cell) {
    const robot = document.createElement('div');
    robot.className = 'robot'; robot.style.transform = `rotate(${state.world.dir * 90}deg)`;
    robot.setAttribute('aria-label', `Karel mira al ${DIRECTIONS[state.world.dir].name.toLowerCase()}`);
    robot.innerHTML = '<svg viewBox="0 0 48 48" aria-hidden="true"><path class="robot-core" d="M24 3 43 40H5L24 3Z"/><circle class="robot-face" cx="19" cy="30" r="2.3"/><circle class="robot-face" cx="29" cy="30" r="2.3"/><path d="M20 35q4 3 8 0" fill="none" stroke="#fff9ed" stroke-width="1.7" stroke-linecap="round"/></svg>';
    cell.append(robot);
  }
  $('#bag-count').textContent = String(state.world.bag).padStart(2, '0');
  $('#action-count').textContent = String(state.world.actions).padStart(2, '0');
}
function conditionOptions(selected) {
  return CONDITIONS.map(([value, label]) => `<option value="${value}" ${selected === value ? 'selected' : ''}>${label}</option>`).join('');
}
function blockControl(block) {
  if (block.type === 'repeat') return `<label class="sr-only" for="count-${block.id}">Cantidad de repeticiones</label><input id="count-${block.id}" data-edit="times" data-id="${block.id}" type="number" min="1" max="99" value="${block.times}" title="Veces que se repite" />`;
  if (block.type === 'while' || block.type === 'if') return `<label class="sr-only" for="condition-${block.id}">Condición</label><select id="condition-${block.id}" data-edit="condition" data-id="${block.id}" title="Elegir condición">${conditionOptions(block.condition)}</select>`;
  return '';
}
function renderList(list, depth = 0, branch = 'root') {
  if (depth === 0 && list.length === 0) {
    return '<div class="empty-program"><span class="empty-icon">⌘</span><strong>Tu lienzo está listo</strong><span>Elige un bloque de arriba para empezar a programar a Karel.</span></div>';
  }
  let html = '';
  list.forEach((block, index) => {
    const meta = BLOCKS[block.type];
    const classes = ['block-row'];
    if (state.selectedId === block.id) classes.push('selected');
    if (state.activeId === block.id) classes.push('is-active');
    html += `<article class="${classes.join(' ')}" data-id="${block.id}" style="--block-bg:${meta.bg};--block-ink:${meta.ink}"><div class="block-main"><span class="block-type-icon">${meta.icon}</span><span class="block-title">${meta.label}</span>${blockControl(block)}<span class="block-controls"><button data-action="up" data-id="${block.id}" title="Subir" aria-label="Subir bloque" ${index === 0 ? 'disabled' : ''}>↑</button><button data-action="down" data-id="${block.id}" title="Bajar" aria-label="Bajar bloque" ${index === list.length - 1 ? 'disabled' : ''}>↓</button><button data-action="delete" data-id="${block.id}" title="Eliminar" aria-label="Eliminar bloque">×</button></span></div>`;
    if (['repeat', 'while', 'if'].includes(block.type)) {
      const childLabel = block.type === 'if' ? 'SI SE CUMPLE' : 'CUERPO';
      const childScope = [...state.scope, { id: block.id, branch: 'children' }];
      html += `<div class="block-indent"><span class="branch-label">${childLabel}</span>${renderList(block.children, depth + 1, 'children')}<button class="branch-add" data-enter="${block.id}" data-branch="children">＋ Añadir dentro</button>`;
      if (block.type === 'if') {
        html += `<span class="branch-label else-label">SI NO SE CUMPLE</span>${renderList(block.elseChildren, depth + 1, 'else')}<button class="branch-add" data-enter="${block.id}" data-branch="else">＋ Añadir alternativa</button>`;
      }
      html += '</div>';
    }
    html += '</article>';
    if (index < list.length - 1) html += '<div class="insert-gap" aria-hidden="true"></div>';
  });
  return html;
}
function renderScope() {
  const crumb = $('#scope-crumb');
  const parts = [{ label: 'PROGRAMA', scope: [] }];
  let current = state.program;
  for (const step of state.scope) {
    const block = current.find(item => item.id === step.id);
    if (!block) break;
    const branchName = step.branch === 'else' ? 'SI NO' : block.type === 'if' ? 'SI' : 'CUERPO';
    parts.push({ label: `${BLOCKS[block.type].label} · ${branchName}`, scope: [...parts.at(-1).scope, step] });
    current = step.branch === 'else' ? block.elseChildren : block.children;
  }
  crumb.innerHTML = parts.map((part, index) => `<button class="crumb-button ${index === parts.length - 1 ? 'active' : ''}" data-scope-index="${index}">${part.label}</button>`).join('');
  programEl.innerHTML = renderList(listAtScope());
  $('#block-count').textContent = totalBlocks();
  programEl.scrollTop = programEl.scrollHeight;
}
function renderAll() { renderScope(); renderWorld(); renderHistory(); setTransport(); }
function createBlock(type) {
  return { id: `block-${++state.id}`, type, times: 3, condition: 'frontFree', children: [], elseChildren: [] };
}
function addBlock(type) {
  if (state.running) return;
  saveHistory();
  const block = createBlock(type);
  listAtScope().push(block);
  state.selectedId = block.id;
  renderScope();
  setHint(`${BLOCKS[type].label} añadido al programa`);
}
function updateProgram(change) {
  if (state.running) return;
  saveHistory(); change(); renderAll();
}
function moveBlock(id, offset) {
  const found = findBlock(id); if (!found) return;
  const index = found.list.indexOf(found.block); const target = index + offset;
  if (target < 0 || target >= found.list.length) return;
  updateProgram(() => { found.list.splice(index, 1); found.list.splice(target, 0, found.block); state.selectedId = id; });
}
function deleteBlock(id) {
  const found = findBlock(id); if (!found) return;
  updateProgram(() => { found.list.splice(found.list.indexOf(found.block), 1); state.selectedId = null; state.scope = []; });
}
function isPathAvailable(scope) {
  let list = state.program;
  for (const step of scope) {
    const parent = list.find(block => block.id === step.id);
    if (!parent) return false;
    list = step.branch === 'else' ? parent.elseChildren : parent.children;
  }
  return true;
}
function startLevel(index) {
  stopExecution(false);
  state.levelIndex = index;
  state.world = newWorld();
  state.program = []; state.scope = []; state.selectedId = null; state.undo = []; state.redo = [];
  $('#level-select').value = String(index);
  $('#progress-label').textContent = `${state.completedLevels.size} / ${levels.length} niveles`;
  announce(index === 0 ? '¡Tu próximo reto empieza aquí!' : `Nivel ${index} listo. ¡A programar!`);
  setHint('Añade bloques y dale vida a Karel');
  setWorld(); renderAll();
}
function freeIn(direction) {
  const level = currentLevel(); const delta = DIRECTIONS[direction];
  const nx = state.world.x + delta.dx, ny = state.world.y + delta.dy;
  const walls = { 0: 'N', 1: 'E', 2: 'S', 3: 'W' };
  return nx >= 0 && ny >= 0 && nx < level.width && ny < level.height && !level.walls.has(keyWall(state.world.x, state.world.y, walls[direction]));
}
function conditionIsTrue(condition) {
  const world = state.world; const left = (world.dir + 3) % 4; const right = (world.dir + 1) % 4;
  const present = (world.markers[keyAt(world.x, world.y)] || 0) > 0;
  const checks = {
    frontFree: freeIn(world.dir), frontBlocked: !freeIn(world.dir), leftFree: freeIn(left), leftBlocked: !freeIn(left),
    rightFree: freeIn(right), rightBlocked: !freeIn(right), markerHere: present, noMarkerHere: !present,
    bagHas: world.bag > 0, bagEmpty: world.bag === 0,
    north: world.dir === 0, notNorth: world.dir !== 0, east: world.dir === 1, notEast: world.dir !== 1,
    south: world.dir === 2, notSouth: world.dir !== 2, west: world.dir === 3, notWest: world.dir !== 3,
  };
  return checks[condition];
}
function worldSignature() {
  return JSON.stringify([state.world.x, state.world.y, state.world.dir, state.world.bag, state.world.markers]);
}
function containsAction(blocks) { return blocks.some(block => ['move', 'left', 'right', 'pick', 'drop'].includes(block.type) || containsAction(block.children) || containsAction(block.elseChildren)); }
function* execute(blocks) {
  for (const block of blocks) {
    if (block.type === 'repeat') {
      for (let i = 0; i < block.times; i++) yield* execute(block.children);
    } else if (block.type === 'while') {
      while (conditionIsTrue(block.condition)) {
        if (!containsAction(block.children)) throw new Error('El bloque «Mientras» necesita una acción para poder avanzar.');
        const before = worldSignature();
        yield { id: block.id, message: `Se cumple «${conditionLabel(block.condition)}»` };
        yield* execute(block.children);
        if (before === worldSignature() && conditionIsTrue(block.condition)) throw new Error('El bucle no cambia el mundo y su condición sigue siendo verdadera.');
      }
      yield { id: block.id, message: 'La condición ya no se cumple. Fin del bucle.' };
    } else if (block.type === 'if') {
      const matches = conditionIsTrue(block.condition);
      yield { id: block.id, message: matches ? 'Condición verdadera: rama «Si se cumple».' : 'Condición falsa: rama «Si no se cumple».' };
      yield* execute(matches ? block.children : block.elseChildren);
    } else {
      yield { id: block.id, action: () => perform(block.type), message: BLOCKS[block.type].label };
    }
  }
}
function conditionLabel(id) { return CONDITIONS.find(([value]) => value === id)?.[1] || id; }
function perform(type) {
  const world = state.world; const position = keyAt(world.x, world.y);
  if (type === 'move') {
    if (!freeIn(world.dir)) throw new Error('¡Uy! Hay un muro o se acaba el tablero. Karel no puede avanzar.');
    world.x += DIRECTIONS[world.dir].dx; world.y += DIRECTIONS[world.dir].dy;
  } else if (type === 'left') world.dir = (world.dir + 3) % 4;
  else if (type === 'right') world.dir = (world.dir + 1) % 4;
  else if (type === 'pick') {
    if (!world.markers[position]) throw new Error('Aquí no hay ningún marcador para recoger.');
    world.markers[position] -= 1; if (!world.markers[position]) delete world.markers[position]; world.bag += 1;
  } else if (type === 'drop') {
    if (world.bag < 1) throw new Error('La mochila está vacía. No hay ningún marcador para colocar.');
    world.markers[position] = (world.markers[position] || 0) + 1; world.bag -= 1;
  }
  world.actions += 1;
}
function isComplete() {
  const level = currentLevel();
  return state.world.x === level.goal[0] && state.world.y === level.goal[1] && Object.entries(level.targets).every(([position, count]) => (state.world.markers[position] || 0) >= count);
}
function finishExecution(message, kind = '') {
  state.running = false; state.paused = false; state.iterator = null; state.activeId = null;
  if (state.timer) clearTimeout(state.timer); state.timer = null;
  renderAll(); setTransport();
  if (message) announce(message, kind);
}
function stopExecution(showMessage = true) {
  if (state.timer) clearTimeout(state.timer); state.timer = null;
  if (state.iterator || state.running) finishExecution(showMessage ? 'Ejecución detenida. Puedes ajustar el programa y probar de nuevo.' : '', '');
}
function nextStep() {
  if (!state.iterator) { state.world = newWorld(); state.iterator = execute(state.program); announce('Programa preparado. Ejecuta para ver qué ocurre.'); }
  try {
    const result = state.iterator.next();
    if (result.done) {
      const won = isComplete();
      finishExecution(won ? '¡Nivel superado! Karel llegó a la meta.' : 'Programa terminado. Aún falta llegar a la meta o completar los objetivos.', won ? 'success' : '');
      if (won) {
        state.completedLevels.add(state.levelIndex);
        $('#progress-label').textContent = `${state.completedLevels.size} / ${levels.length} niveles`;
      }
      return false;
    }
    const step = result.value; state.activeId = step.id;
    if (step.action) step.action();
    renderAll(); announce(step.message); return true;
  } catch (error) {
    finishExecution(error.message || 'Algo salió mal al ejecutar este bloque.', 'error'); return false;
  }
}
function runLoop() {
  if (!state.running || state.paused) return;
  const more = nextStep();
  if (!more) return;
  const delay = 1000 - Number($('#speed').value);
  state.timer = setTimeout(runLoop, delay);
}
function runProgram() {
  if (state.running && !state.paused) { state.paused = true; if (state.timer) clearTimeout(state.timer); setTransport(); return; }
  if (state.running && state.paused) { state.paused = false; setTransport(); runLoop(); return; }
  if (!state.program.length) { announce('Añade al menos un bloque antes de ejecutar.', 'error'); return; }
  if (!state.iterator) { state.world = newWorld(); state.iterator = execute(state.program); setWorld(); }
  state.running = true; state.paused = false;
  renderAll(); setTransport(); announce('¡Karel está en marcha!'); runLoop();
}
function stepOnce() {
  if (state.running) { if (!state.paused) { state.paused = true; if (state.timer) clearTimeout(state.timer); setTransport(); } state.running = false; }
  if (!state.iterator) { state.world = newWorld(); state.iterator = execute(state.program); }
  if (!state.program.length) { announce('Añade al menos un bloque antes de ejecutar.', 'error'); return; }
  const more = nextStep();
  if (more) { setHint('Paso ejecutado. Pulsa F10 para continuar.'); setTransport(); }
}
function changeScope(id, branch) {
  state.scope.push({ id, branch }); renderScope();
}

$('#level-select').innerHTML = levels.map((level, index) => `<option value="${index}">${String(index + 1).padStart(2, '0')} · ${level.name}</option>`).join('');
$('#level-select').addEventListener('change', event => startLevel(Number(event.target.value)));
$('.palette-grid').addEventListener('click', event => { const button = event.target.closest('[data-add]'); if (button) addBlock(button.dataset.add); });
programEl.addEventListener('click', event => {
  const enter = event.target.closest('[data-enter]'); if (enter) { changeScope(enter.dataset.enter, enter.dataset.branch); return; }
  const crumb = event.target.closest('[data-scope-index]');
  if (crumb) { state.scope = state.scope.slice(0, Number(crumb.dataset.scopeIndex)); renderScope(); return; }
  const action = event.target.closest('[data-action]');
  if (action) {
    const { id, action: name } = action.dataset;
    if (name === 'delete') deleteBlock(id); else moveBlock(id, name === 'up' ? -1 : 1);
    return;
  }
  const row = event.target.closest('.block-row');
  if (row) { state.selectedId = row.dataset.id; renderScope(); }
});
$('#scope-crumb').addEventListener('click', event => {
  const crumb = event.target.closest('[data-scope-index]');
  if (!crumb) return;
  state.scope = state.scope.slice(0, Number(crumb.dataset.scopeIndex));
  renderScope();
});
programEl.addEventListener('change', event => {
  const input = event.target.closest('[data-edit]'); if (!input) return;
  const found = findBlock(input.dataset.id); if (!found) return;
  const next = input.dataset.edit === 'times' ? Math.min(99, Math.max(1, Number(input.value) || 1)) : input.value;
  updateProgram(() => { found.block[input.dataset.edit] = next; state.selectedId = found.block.id; });
});
$('#undo-button').addEventListener('click', () => { if (!state.undo.length || state.running) return; state.redo.push(clone(state.program)); state.program = state.undo.pop(); state.scope = []; renderAll(); });
$('#redo-button').addEventListener('click', () => { if (!state.redo.length || state.running) return; state.undo.push(clone(state.program)); state.program = state.redo.pop(); state.scope = []; renderAll(); });
$('#clear-button').addEventListener('click', () => { if (!state.program.length || state.running) return; updateProgram(() => { state.program = []; state.scope = []; state.selectedId = null; }); });
$('#run-button').addEventListener('click', runProgram);
$('#pause-button').addEventListener('click', () => { if (state.running) runProgram(); });
$('#step-button').addEventListener('click', stepOnce);
$('#stop-button').addEventListener('click', () => stopExecution());
$('#restart-button').addEventListener('click', () => { state.world = newWorld(); state.iterator = null; finishExecution('', ''); renderWorld(); announce('Nivel reiniciado. Tu programa se conserva.'); setHint('Listo para otra ejecución'); });
$('#speed').addEventListener('input', event => { const value = Number(event.target.value); $('#speed-value').textContent = value < 300 ? 'LENTA' : value > 700 ? 'RÁPIDA' : 'NORMAL'; });
document.addEventListener('keydown', event => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') { event.preventDefault(); runProgram(); }
  else if (event.key === 'F10') { event.preventDefault(); stepOnce(); }
  else if (event.key === 'Escape') stopExecution();
  else if ((event.key === 'Delete' || event.key === 'Backspace') && state.selectedId && !['INPUT', 'SELECT'].includes(document.activeElement.tagName)) deleteBlock(state.selectedId);
  else if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') { event.preventDefault(); (event.shiftKey ? $('#redo-button') : $('#undo-button')).click(); }
  else if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'y') { event.preventDefault(); $('#redo-button').click(); }
});
startLevel(0);
