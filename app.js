const DIRECTIONS = [
  { name: 'Norte', dx: 0, dy: -1 },
  { name: 'Este', dx: 1, dy: 0 },
  { name: 'Sur', dx: 0, dy: 1 },
  { name: 'Oeste', dx: -1, dy: 0 },
];
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
function lessonLevel(level, focus, lesson) { return Object.assign(level, { focus, lesson }); }
levels.push(
  lessonLevel(makeLevel('Repite un camino', 8, 6, { x: 1, y: 3, dir: 1, bag: 0 }, [6, 3], 'Avanza cinco casillas con un solo bucle.'), 'REPETIR · MOVIMIENTO', 'Repite 5 veces, hacer Avanzar 1 casilla.'),
  lessonLevel(makeLevel('Giros en cadena', 8, 6, { x: 2, y: 3, dir: 1, bag: 0 }, [2, 3], 'Quédate en el sitio y gira hasta mirar al este otra vez.'), 'REPETIR · GIROS', 'Repite 4 veces, hacer Girar a la derecha.'),
  lessonLevel(makeLevel('Si 10 es mayor que 5', 8, 6, { x: 1, y: 3, dir: 1, bag: 0 }, [2, 3], 'Compara 10 y 5. Si 10 es mayor, avanza una casilla.'), 'SI · COMPARAR', 'Pon 10 > 5 dentro de Si y conecta Avanzar en su cuerpo.'),
  lessonLevel(makeLevel('Cuando la comparación es falsa', 8, 6, { x: 1, y: 3, dir: 1, bag: 0 }, [2, 3], '3 no es mayor que 5. Observa cómo Si omite su cuerpo y sigue con el bloque siguiente.'), 'SI · FALSO', 'Usa Si 3 > 5 con un giro dentro. Después del Si, conecta Avanzar.'),
  lessonLevel(makeLevel('Mientras haya camino', 8, 6, { x: 1, y: 3, dir: 1, bag: 0 }, [7, 3], 'Repite el movimiento solo mientras haya espacio delante.'), 'MIENTRAS · SENSOR', 'Mientras el camino al frente esté libre, avanza una casilla.'),
  lessonLevel(makeLevel('Recoge solo si hay uno', 8, 6, { x: 1, y: 3, dir: 1, bag: 0 }, [3, 3], 'Llega al marcador, comprueba si hay uno y llévalo al objetivo.', { '2,3': 1 }, { '3,3': 1 }), 'SI · MARCADORES', 'Avanza, usa Si hay marcador aquí para Recoger, avanza y Coloca.'),
  lessonLevel(makeLevel('Una variable cuenta pasos', 8, 6, { x: 1, y: 3, dir: 1, bag: 0 }, [4, 3], 'Guarda el número 3 en una variable y úsala para repetir el movimiento.'), 'VARIABLES · REPETIR', 'Crea la variable pasos, asígnale 3 y conéctala a Repetir.'),
);
levels[7].goalDirection = 1;
const CUSTOM_LEVELS_KEY = 'karel-club-custom-levels';
function loadCustomLevels() {
  try {
    const records = JSON.parse(localStorage.getItem(CUSTOM_LEVELS_KEY) || '[]');
    return Array.isArray(records) ? records.filter(level => level.name && level.start && Array.isArray(level.goal)).map(level =>
      makeLevel(level.name, level.width, level.height, level.start, level.goal, level.description || '', level.markers || {}, level.targets || {}, level.walls || [])) : [];
  } catch {
    return [];
  }
}
levels.push(...loadCustomLevels());

const $ = (selector, root = document) => root.querySelector(selector);
const boardEl = $('#board');
const programEl = $('#program-list');
const state = {
  levelIndex: 0, world: null, workspace: null, variables: new Map(), savedPrograms: new Map(),
  programVersion: 'practice', iterator: null, running: false, paused: false, activeId: null,
  timer: null, completedLevels: new Set(), showPath: false, tracePath: [], builderTool: 'start',
  builderDraft: { width: 8, height: 6, start: null, goal: null, markers: {}, targets: {}, walls: new Set() },
};
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
  $('#undo-button').disabled = !state.workspace || state.running;
  $('#redo-button').disabled = !state.workspace || state.running;
  state.workspace?.getAllBlocks(false).forEach(block => block.setMovable(!state.running));
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
  $('#level-focus').hidden = !level.focus;
  $('#level-focus').textContent = level.focus ? `BLOQUE EN FOCO · ${level.focus}  /  ${level.lesson}` : '';
  $('#world-coordinates').textContent = `MUNDO ${level.width} × ${level.height}`;
  $('#level-select').value = String(state.levelIndex);
  renderWorld();
}
function renderWorld() {
  if (!state.world) return;
  boardEl.querySelectorAll('.marker-token,.marker-count,.robot,.route-trace').forEach(element => element.remove());
  for (const [cellKey, count] of Object.entries(state.world.markers)) {
    if (count < 1) continue;
    const cell = boardEl.querySelector(`[data-position="${cellKey}"]`);
    if (!cell) continue;
    const marker = document.createElement('span'); marker.className = 'marker-token'; marker.setAttribute('aria-hidden', 'true'); cell.append(marker);
    if (count > 1) { const amount = document.createElement('span'); amount.className = 'marker-count'; amount.textContent = count; cell.append(amount); }
  }
  if (state.showPath && state.tracePath.length) {
    const level = currentLevel();
    const trace = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    trace.classList.add('route-trace'); trace.setAttribute('viewBox', `0 0 ${level.width} ${level.height}`); trace.setAttribute('preserveAspectRatio', 'none');
    if (state.tracePath.length > 1) {
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
      line.setAttribute('points', state.tracePath.map(([x, y]) => `${x + 0.5},${y + 0.5}`).join(' ')); line.setAttribute('class', 'route-line'); trace.append(line);
    }
    const [startX, startY] = state.tracePath[0];
    const startDot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    startDot.setAttribute('cx', startX + 0.5); startDot.setAttribute('cy', startY + 0.5); startDot.setAttribute('r', '0.14'); startDot.setAttribute('class', 'route-start'); trace.append(startDot);
    boardEl.append(trace);
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
function resetPathTrace() {
  state.tracePath = state.world ? [[state.world.x, state.world.y]] : [];
}
function registerKarelBlocks() {
  Blockly.Blocks.karel_move = { init() {
    this.appendValueInput('STEPS').setCheck('Number').appendField('avanzar');
    this.appendDummyInput().appendField('casillas');
    this.setPreviousStatement(true); this.setNextStatement(true); this.setColour('#4c97ff');
  } };
  Blockly.Blocks.karel_turn = { init() {
    this.appendDummyInput().appendField('girar').appendField(new Blockly.FieldDropdown([['a la izquierda', 'LEFT'], ['a la derecha', 'RIGHT']]), 'DIRECTION');
    this.setPreviousStatement(true); this.setNextStatement(true); this.setColour('#4c97ff');
  } };
  for (const [type, label, colour] of [['karel_pick', 'recoger marcador', '#0fbd8c'], ['karel_drop', 'colocar marcador', '#0fbd8c']]) {
    Blockly.Blocks[type] = { init() { this.appendDummyInput().appendField(label); this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(colour); } };
  }
  Blockly.Blocks.karel_path = { init() {
    this.appendDummyInput().appendField('¿camino').appendField(new Blockly.FieldDropdown([['al frente', 'FRONT'], ['a la izquierda', 'LEFT'], ['a la derecha', 'RIGHT']]), 'DIRECTION').appendField(new Blockly.FieldDropdown([['libre?', 'FREE'], ['bloqueado?', 'BLOCKED']]), 'STATE');
    this.setOutput(true, 'Boolean'); this.setColour('#5cb1d6');
  } };
  Blockly.Blocks.karel_marker_here = { init() { this.appendDummyInput().appendField('¿hay marcador aquí?'); this.setOutput(true, 'Boolean'); this.setColour('#5cb1d6'); } };
  Blockly.Blocks.karel_bag_empty = { init() { this.appendDummyInput().appendField('¿mochila vacía?'); this.setOutput(true, 'Boolean'); this.setColour('#5cb1d6'); } };
  Blockly.Blocks.karel_facing = { init() {
    this.appendDummyInput().appendField('¿mira al').appendField(new Blockly.FieldDropdown([['norte', '0'], ['este', '1'], ['sur', '2'], ['oeste', '3']]), 'DIRECTION');
    this.setOutput(true, 'Boolean'); this.setColour('#5cb1d6');
  } };
  Blockly.Blocks.karel_marker_count = { init() { this.appendDummyInput().appendField('marcadores aquí'); this.setOutput(true, 'Number'); this.setColour('#5cb1d6'); } };
  Blockly.Blocks.karel_bag_count = { init() { this.appendDummyInput().appendField('marcadores en mochila'); this.setOutput(true, 'Number'); this.setColour('#5cb1d6'); } };
  Blockly.Blocks.karel_at_goal = { init() { this.appendDummyInput().appendField('¿en la meta?'); this.setOutput(true, 'Boolean'); this.setColour('#5cb1d6'); } };
}
function makeToolbox() {
  const toolbox = `<xml xmlns="https://developers.google.com/blockly/xml">
    <category name="Movimiento" colour="#4c97ff"><block type="karel_move"><value name="STEPS"><shadow type="math_number"><field name="NUM">1</field></shadow></value></block><block type="karel_turn"></block></category>
    <category name="Marcadores" colour="#0fbd8c"><block type="karel_pick"></block><block type="karel_drop"></block></category>
    <category name="Control" categorystyle="loop_category"><block type="controls_repeat_ext"><value name="TIMES"><shadow type="math_number"><field name="NUM">4</field></shadow></value></block><block type="controls_whileUntil"></block><block type="controls_if"></block><block type="controls_for"></block></category>
    <category name="Sensores" colour="#5cb1d6"><block type="karel_path"></block><block type="karel_marker_here"></block><block type="karel_bag_empty"></block><block type="karel_facing"></block><block type="karel_marker_count"></block><block type="karel_bag_count"></block><block type="karel_at_goal"></block></category>
    <category name="Operadores" categorystyle="logic_category"><block type="logic_compare"></block><block type="logic_operation"></block><block type="logic_negate"></block><block type="logic_boolean"></block><block type="math_number"></block><block type="math_arithmetic"></block><block type="math_single"></block><block type="math_modulo"></block><block type="math_random_int"></block><block type="text"></block><block type="text_join"></block><block type="text_length"></block></category>
    <category name="Variables" custom="VARIABLE" categorystyle="variable_category"></category>
  </xml>`;
  return new DOMParser().parseFromString(toolbox, 'text/xml').documentElement;
}
function updateWorkspaceUI() {
  const workspace = state.workspace;
  if (!workspace) return;
  $('#block-count').textContent = workspace.getAllBlocks(false).filter(block => !block.isShadow()).length;
  $('#undo-button').disabled = state.running || !workspace.undoStack_.length;
  $('#redo-button').disabled = state.running || !workspace.redoStack_.length;
}
function initializeWorkspace() {
  registerKarelBlocks();
  const theme = Blockly.Theme.defineTheme('karelScratch', {
    base: Blockly.Themes.Zelos,
    componentStyles: {
      workspaceBackgroundColour: '#fbfcfa', toolboxBackgroundColour: '#ffffff', toolboxForegroundColour: '#34433b',
      flyoutBackgroundColour: '#f4f7f3', flyoutForegroundColour: '#34433b', flyoutOpacity: 1,
      scrollbarColour: '#cdd8d0', scrollbarOpacity: 0.65, insertionMarkerColour: '#263b32', insertionMarkerOpacity: 0.18,
      markerColour: '#e8694d', cursorColour: '#263b32',
    },
    fontStyle: { family: 'DM Sans, sans-serif', weight: '600', size: 12 },
  });
  state.workspace = Blockly.inject(programEl, {
    toolbox: makeToolbox(), renderer: 'zelos', theme, toolboxPosition: 'start',
    trashcan: true, sounds: false, oneBasedIndex: false,
    grid: { spacing: 24, length: 2, colour: '#e2e8e2', snap: true },
    zoom: { controls: true, wheel: true, startScale: 0.9, maxScale: 1.5, minScale: 0.5, scaleSpeed: 1.1 },
    move: { scrollbars: true, drag: true, wheel: true },
  });
  const toolbox = state.workspace.getToolbox();
  if (toolbox && !toolbox.getSelectedItem()) toolbox.setSelectedItem(toolbox.getToolboxItems()[0]);
  state.workspace.addChangeListener(event => {
    if (!event.isUiEvent) updateWorkspaceUI();
  });
  updateWorkspaceUI();
}
function initializeLevelSelector() {
  $('#level-select').innerHTML = levels.map((level, index) => `<option value="${index}">${String(index + 1).padStart(2, '0')} · ${level.name}</option>`).join('');
  $('#progress-label').textContent = `0 / ${levels.length} niveles`;
}
function programSlot(index, version) { return `${index}:${version}`; }
function createDemoBlock(type) {
  const block = state.workspace.newBlock(type);
  block.initSvg(); block.render();
  return block;
}
function createDemoNumber(value) {
  const block = createDemoBlock('math_number');
  block.setFieldValue(String(value), 'NUM');
  return block;
}
function connectDemoSequence(blocks) {
  for (let index = 0; index < blocks.length - 1; index++) blocks[index].nextConnection.connect(blocks[index + 1].previousConnection);
  return blocks[0] || null;
}
function createDemoMove(steps = 1) {
  const block = createDemoBlock('karel_move');
  block.getInput('STEPS').connection.connect(createDemoNumber(steps).outputConnection);
  return block;
}
function createDemoTurn(direction = 'RIGHT') {
  const block = createDemoBlock('karel_turn');
  block.setFieldValue(direction, 'DIRECTION');
  return block;
}
function createDemoRepeat(count, children) {
  const block = createDemoBlock('controls_repeat_ext');
  block.getInput('TIMES').connection.connect(typeof count === 'number' ? createDemoNumber(count).outputConnection : count.outputConnection);
  const body = connectDemoSequence(children);
  if (body) block.getInput('DO').connection.connect(body.previousConnection);
  return block;
}
function createDemoComparison(left, operator, right) {
  const block = createDemoBlock('logic_compare');
  block.setFieldValue(operator, 'OP');
  block.getInput('A').connection.connect(createDemoNumber(left).outputConnection);
  block.getInput('B').connection.connect(createDemoNumber(right).outputConnection);
  return block;
}
function createDemoPathCondition(direction = 'FRONT', status = 'FREE') {
  const block = createDemoBlock('karel_path');
  block.setFieldValue(direction, 'DIRECTION'); block.setFieldValue(status, 'STATE');
  return block;
}
function createDemoIf(condition, children) {
  const block = createDemoBlock('controls_if');
  block.getInput('IF0').connection.connect(condition.outputConnection);
  const body = connectDemoSequence(children);
  if (body) block.getInput('DO0').connection.connect(body.previousConnection);
  return block;
}
function shortestDirections(level, start, goal) {
  const queue = [{ x: start.x, y: start.y, directions: [] }];
  const visited = new Set([keyAt(start.x, start.y)]);
  const edges = ['N', 'E', 'S', 'W'];
  while (queue.length) {
    const current = queue.shift();
    if (current.x === goal[0] && current.y === goal[1]) return current.directions;
    for (let direction = 0; direction < DIRECTIONS.length; direction++) {
      const { dx, dy } = DIRECTIONS[direction];
      const x = current.x + dx; const y = current.y + dy; const position = keyAt(x, y);
      if (x < 0 || y < 0 || x >= level.width || y >= level.height || visited.has(position) || level.walls.has(keyWall(current.x, current.y, edges[direction]))) continue;
      visited.add(position);
      queue.push({ x, y, directions: [...current.directions, direction] });
    }
  }
  return null;
}
function createRouteDemo(level, guardMoves = false) {
  const blocks = [];
  const position = { x: level.start.x, y: level.start.y };
  let facing = level.start.dir;
  function travelTo(destination) {
    const route = shortestDirections(level, position, destination);
    if (!route) return false;
    for (let cursor = 0; cursor < route.length;) {
      const direction = route[cursor];
      const turns = (direction - facing + 4) % 4;
      if (turns === 1) blocks.push(createDemoTurn('RIGHT'));
      else if (turns === 3) blocks.push(createDemoTurn('LEFT'));
      else if (turns === 2) blocks.push(createDemoTurn('RIGHT'), createDemoTurn('RIGHT'));
      facing = direction;
      let run = 0;
      while (route[cursor] === direction) {
        position.x += DIRECTIONS[direction].dx; position.y += DIRECTIONS[direction].dy;
        cursor++; run++;
      }
      if (guardMoves) blocks.push(createDemoRepeat(run, [createDemoIf(createDemoPathCondition(), [createDemoMove()])]));
      else if (run > 1) blocks.push(createDemoRepeat(run, [createDemoMove()]));
      else blocks.push(createDemoMove());
    }
    return true;
  }
  const requiredTargets = Object.keys(level.targets).length > 0;
  if (requiredTargets) {
    for (const [positionKey, count] of Object.entries(level.markers)) {
      const [x, y] = positionKey.split(',').map(Number);
      if (!travelTo([x, y])) return [];
      for (let index = 0; index < count; index++) blocks.push(createDemoBlock('karel_pick'));
    }
    for (const [positionKey, count] of Object.entries(level.targets)) {
      const [x, y] = positionKey.split(',').map(Number);
      if (!travelTo([x, y])) return [];
      for (let index = 0; index < count; index++) blocks.push(createDemoBlock('karel_drop'));
    }
  }
  if (!travelTo(level.goal)) return [];
  return blocks;
}
function addDemoProgram(levelIndex) {
  let blocks;
  switch (levelIndex) {
    case 0: blocks = [createDemoRepeat(5, [createDemoMove()]), createDemoTurn(), createDemoRepeat(2, [createDemoMove()])]; break;
    case 1: blocks = [createDemoMove(2), createDemoBlock('karel_pick'), createDemoMove(), createDemoTurn('LEFT'), createDemoRepeat(3, [createDemoMove()]), createDemoTurn(), createDemoRepeat(2, [createDemoMove()]), createDemoBlock('karel_drop')]; break;
    case 2: blocks = createRouteDemo(currentLevel(), true); break;
    case 3: blocks = [createDemoRepeat(4, [createDemoMove(), createDemoBlock('karel_drop')]), createDemoMove()]; break;
    case 4: case 5: blocks = createRouteDemo(currentLevel(), levelIndex === 5); break;
    case 6: blocks = [createDemoRepeat(5, [createDemoMove()])]; break;
    case 7: blocks = [createDemoRepeat(4, [createDemoTurn()])]; break;
    case 8: blocks = [createDemoIf(createDemoComparison(10, 'GT', 5), [createDemoMove()])]; break;
    case 9: blocks = [createDemoIf(createDemoComparison(3, 'GT', 5), [createDemoTurn('LEFT')]), createDemoMove()]; break;
    case 10: {
      const loop = createDemoBlock('controls_whileUntil');
      loop.setFieldValue('WHILE', 'MODE'); loop.getInput('BOOL').connection.connect(createDemoPathCondition().outputConnection);
      loop.getInput('DO').connection.connect(createDemoMove().previousConnection); blocks = [loop]; break;
    }
    case 11: blocks = [createDemoMove(), createDemoIf(createDemoBlock('karel_marker_here'), [createDemoBlock('karel_pick')]), createDemoMove(), createDemoBlock('karel_drop')]; break;
    case 12: {
      const variable = state.workspace.getVariableMap().createVariable('pasos');
      const assign = createDemoBlock('variables_set'); assign.setFieldValue(variable.getId(), 'VAR');
      assign.getInput('VALUE').connection.connect(createDemoNumber(3).outputConnection);
      const get = createDemoBlock('variables_get'); get.setFieldValue(variable.getId(), 'VAR');
      blocks = [assign, createDemoRepeat(get, [createDemoMove()])]; break;
    }
    default: blocks = createRouteDemo(currentLevel(), false);
  }
  const first = connectDemoSequence(blocks);
  if (first) first.moveBy(42, 42);
}
function updateProgramVersionUI() {
  const isDemo = state.programVersion === 'demo';
  $('#practice-version').classList.toggle('active', !isDemo);
  $('#demo-version').classList.toggle('active', isDemo);
  $('#practice-version').setAttribute('aria-pressed', String(!isDemo));
  $('#demo-version').setAttribute('aria-pressed', String(isDemo));
  $('#program-heading').textContent = isDemo ? 'Ejemplo' : 'Tu programa';
}
function startLevel(index, nextVersion = state.programVersion) {
  stopExecution(false);
  if (state.workspace) {
    state.savedPrograms.set(programSlot(state.levelIndex, state.programVersion), Blockly.serialization.workspaces.save(state.workspace));
    state.workspace.clear();
    state.workspace.clearUndo();
  }
  state.levelIndex = index; state.programVersion = nextVersion;
  state.world = newWorld(); resetPathTrace();
  state.variables = new Map();
  const savedProgram = state.savedPrograms.get(programSlot(index, nextVersion));
  if (savedProgram) Blockly.serialization.workspaces.load(savedProgram, state.workspace);
  else if (nextVersion === 'demo') addDemoProgram(index);
  state.workspace.clearUndo();
  updateProgramVersionUI();
  $('#level-select').value = String(index);
  $('#progress-label').textContent = `${state.completedLevels.size} / ${levels.length} niveles`;
  announce(index === 0 ? '¡Tu próximo reto empieza aquí!' : `Nivel ${index + 1} listo. ¡A programar!`);
  setHint(nextVersion === 'demo' ? 'Ejecuta el ejemplo y observa los bloques' : 'Arrastra bloques al espacio y únelos');
  setWorld(); updateWorkspaceUI(); renderWorld();
}
function showBuilderMessage(message, kind = '') {
  $('#builder-feedback').className = `feedback ${kind}`.trim();
  $('#builder-feedback').querySelector('span:last-child').textContent = message;
}
function updateBuilderTool(tool) {
  state.builderTool = tool;
  document.querySelectorAll('.builder-tool').forEach(button => button.classList.toggle('active', button.dataset.tool === tool));
  $('#wall-direction-field').hidden = tool !== 'wall';
  $('.direction-field:not(#wall-direction-field)').hidden = tool !== 'start';
}
function toggleBuilderWall(x, y, direction) {
  const vectors = { N: [0, -1, 'S'], E: [1, 0, 'W'], S: [0, 1, 'N'], W: [-1, 0, 'E'] };
  const [dx, dy, opposite] = vectors[direction];
  const edge = keyWall(x, y, direction);
  const otherEdge = keyWall(x + dx, y + dy, opposite);
  if (state.builderDraft.walls.has(edge)) {
    state.builderDraft.walls.delete(edge); state.builderDraft.walls.delete(otherEdge);
  } else {
    state.builderDraft.walls.add(edge); state.builderDraft.walls.add(otherEdge);
  }
}
function editBuilderCell(x, y) {
  const draft = state.builderDraft;
  const position = keyAt(x, y);
  if (state.builderTool === 'start') draft.start = { x, y, dir: Number($('#builder-direction').value), bag: 0 };
  else if (state.builderTool === 'goal') draft.goal = [x, y];
  else if (state.builderTool === 'wall') toggleBuilderWall(x, y, $('#wall-direction').value);
  else if (state.builderTool === 'marker') draft.markers[position] = (draft.markers[position] || 0) % 9 + 1;
  else if (state.builderTool === 'target') draft.targets[position] = (draft.targets[position] || 0) % 9 + 1;
  else {
    delete draft.markers[position]; delete draft.targets[position];
    if (draft.start?.x === x && draft.start?.y === y) draft.start = null;
    if (draft.goal?.[0] === x && draft.goal?.[1] === y) draft.goal = null;
    for (const direction of ['N', 'E', 'S', 'W']) {
      const current = keyWall(x, y, direction);
      const [dx, dy, opposite] = { N: [0, -1, 'S'], E: [1, 0, 'W'], S: [0, 1, 'N'], W: [-1, 0, 'E'] }[direction];
      draft.walls.delete(current); draft.walls.delete(keyWall(x + dx, y + dy, opposite));
    }
  }
  renderBuilder();
}
function renderBuilder() {
  const draft = state.builderDraft;
  const board = $('#builder-board');
  board.style.setProperty('--cols', draft.width);
  board.style.setProperty('--rows', draft.height);
  board.style.setProperty('aspect-ratio', `${draft.width} / ${draft.height}`);
  board.innerHTML = '';
  for (let y = 0; y < draft.height; y++) {
    for (let x = 0; x < draft.width; x++) {
      const position = keyAt(x, y);
      const cell = document.createElement('button');
      cell.type = 'button'; cell.className = 'cell builder-cell'; cell.setAttribute('role', 'gridcell');
      cell.setAttribute('aria-label', `Casilla ${x + 1}, ${y + 1}`);
      if (draft.targets[position]) cell.classList.add('target');
      if (draft.goal?.[0] === x && draft.goal?.[1] === y) cell.classList.add('goal-cell');
      for (const [direction, name] of [['N', 'north'], ['E', 'east'], ['S', 'south'], ['W', 'west']]) {
        if (draft.walls.has(keyWall(x, y, direction))) cell.classList.add(`wall-${name}`);
      }
      if (draft.start?.x === x && draft.start?.y === y) {
        const start = document.createElement('span'); start.className = 'builder-start'; start.style.transform = `rotate(${draft.start.dir * 90}deg)`; start.textContent = '▲'; cell.append(start);
      }
      if (draft.goal?.[0] === x && draft.goal?.[1] === y) {
        const goal = document.createElement('span'); goal.className = 'goal-star'; goal.textContent = '✳'; cell.append(goal);
      }
      if (draft.markers[position]) {
        const marker = document.createElement('span'); marker.className = 'marker-token'; cell.append(marker);
        if (draft.markers[position] > 1) { const amount = document.createElement('span'); amount.className = 'marker-count'; amount.textContent = draft.markers[position]; cell.append(amount); }
      }
      if (draft.targets[position]) {
        const amount = document.createElement('span'); amount.className = 'target-count'; amount.textContent = draft.targets[position] > 1 ? draft.targets[position] : '◆'; cell.append(amount);
      }
      cell.addEventListener('click', () => editBuilderCell(x, y));
      board.append(cell);
    }
  }
  $('#builder-size-label').textContent = `${draft.width} × ${draft.height}`;
}
function resizeBuilder(axis, rawValue) {
  const draft = state.builderDraft;
  const value = Math.max(5, Math.min(12, Math.floor(Number(rawValue) || 8)));
  draft[axis] = value;
  $(`#custom-${axis}`).value = value;
  if (draft.start && (draft.start.x >= draft.width || draft.start.y >= draft.height)) draft.start = null;
  if (draft.goal && (draft.goal[0] >= draft.width || draft.goal[1] >= draft.height)) draft.goal = null;
  const inside = position => { const [x, y] = position.split(',').map(Number); return x < draft.width && y < draft.height; };
  for (const position of Object.keys(draft.markers)) if (!inside(position)) delete draft.markers[position];
  for (const position of Object.keys(draft.targets)) if (!inside(position)) delete draft.targets[position];
  for (const edge of [...draft.walls]) { const [x, y] = edge.split(','); if (Number(x) >= draft.width || Number(y) >= draft.height) draft.walls.delete(edge); }
  renderBuilder();
}
function switchMode(mode) {
  const isBuilder = mode === 'builder';
  $('#play-tab-button').classList.toggle('active', !isBuilder);
  $('#builder-tab-button').classList.toggle('active', isBuilder);
  $('#play-tab-button').setAttribute('aria-selected', String(!isBuilder));
  $('#builder-tab-button').setAttribute('aria-selected', String(isBuilder));
  $('#play-mode').hidden = isBuilder;
  $('#split-control').hidden = isBuilder;
  $('#level-builder').hidden = !isBuilder;
  if (!isBuilder) requestAnimationFrame(() => Blockly.svgResize(state.workspace));
}
function saveCustomLevel(event) {
  event.preventDefault();
  const draft = state.builderDraft;
  const name = $('#custom-name').value.trim();
  if (!name || !draft.start || !draft.goal) {
    showBuilderMessage('Añade un nombre, coloca a Karel y marca la meta.', 'error'); return;
  }
  const description = $('#custom-description').value.trim() || 'Llega a la meta y completa los objetivos.';
  const direction = Number($('#builder-direction').value);
  const start = { ...draft.start, dir: direction, bag: 0 };
  const goal = [...draft.goal];
  const walls = [...draft.walls].map(edge => { const [x, y, side] = edge.split(','); return [Number(x), Number(y), side]; });
  const record = { name, width: draft.width, height: draft.height, start, goal, description, markers: { ...draft.markers }, targets: { ...draft.targets }, walls };
  const saved = [...levels.slice(6).map(level => ({ name: level.name, width: level.width, height: level.height, start: level.start, goal: level.goal, description: level.description, markers: level.markers, targets: level.targets, walls: [...level.walls].map(edge => { const [x, y, side] = edge.split(','); return [Number(x), Number(y), side]; }) })), record];
  try { localStorage.setItem(CUSTOM_LEVELS_KEY, JSON.stringify(saved)); }
  catch { showBuilderMessage('No se pudo guardar el nivel en este navegador.', 'error'); return; }
  const newIndex = levels.length;
  levels.push(makeLevel(record.name, record.width, record.height, record.start, record.goal, record.description, record.markers, record.targets, record.walls));
  $('#level-select').add(new Option(`${String(newIndex + 1).padStart(2, '0')} · ${record.name}`, String(newIndex)));
  state.builderDraft = { width: 8, height: 6, start: null, goal: null, markers: {}, targets: {}, walls: new Set() };
  $('#custom-name').value = 'Mi primer nivel'; $('#custom-description').value = 'Guía a Karel hasta la meta.';
  $('#custom-width').value = 8; $('#custom-height').value = 6; updateBuilderTool('start'); renderBuilder();
  switchMode('play'); startLevel(newIndex);
}
function initializeBuilder() {
  document.querySelectorAll('.builder-tool').forEach(button => button.addEventListener('click', () => updateBuilderTool(button.dataset.tool)));
  $('#custom-width').addEventListener('change', event => resizeBuilder('width', event.target.value));
  $('#custom-height').addEventListener('change', event => resizeBuilder('height', event.target.value));
  $('#builder-form').addEventListener('submit', saveCustomLevel);
  $('#reset-level-button').addEventListener('click', () => {
    const { width, height } = state.builderDraft;
    state.builderDraft = { width, height, start: null, goal: null, markers: {}, targets: {}, walls: new Set() };
    renderBuilder(); showBuilderMessage('Diseño vaciado. Coloca a Karel y la meta.');
  });
  $('#play-tab-button').addEventListener('click', () => switchMode('play'));
  $('#builder-tab-button').addEventListener('click', () => switchMode('builder'));
  renderBuilder(); updateBuilderTool('start');
}
function initializeSplitSlider() {
  const slider = $('#split-size');
  const update = () => {
    const mapShare = Number(slider.value);
    $('.play-mode').style.gridTemplateColumns = `minmax(0, ${mapShare}fr) minmax(0, ${100 - mapShare}fr)`;
    $('#split-value').textContent = `${mapShare} / ${100 - mapShare}`;
    requestAnimationFrame(() => Blockly.svgResize(state.workspace));
  };
  slider.addEventListener('input', update); update();
}
function freeIn(direction) {
  const level = currentLevel(); const delta = DIRECTIONS[direction];
  const nx = state.world.x + delta.dx, ny = state.world.y + delta.dy;
  const walls = { 0: 'N', 1: 'E', 2: 'S', 3: 'W' };
  return nx >= 0 && ny >= 0 && nx < level.width && ny < level.height && !level.walls.has(keyWall(state.world.x, state.world.y, walls[direction]));
}
function worldSignature() {
  return JSON.stringify([state.world.x, state.world.y, state.world.dir, state.world.bag, state.world.markers, [...state.variables]]);
}
function conditionValue(block) {
  if (!block) return false;
  if (block.type === 'logic_boolean') return block.getFieldValue('BOOL') === 'TRUE';
  if (block.type === 'logic_compare') {
    const left = evaluateValue(block.getInputTargetBlock('A'));
    const right = evaluateValue(block.getInputTargetBlock('B'));
    return ({ EQ: () => left === right, NEQ: () => left !== right, LT: () => left < right, LTE: () => left <= right, GT: () => left > right, GTE: () => left >= right })[block.getFieldValue('OP')]();
  }
  if (block.type === 'logic_operation') {
    const left = conditionValue(block.getInputTargetBlock('A'));
    const right = conditionValue(block.getInputTargetBlock('B'));
    return block.getFieldValue('OP') === 'AND' ? left && right : left || right;
  }
  if (block.type === 'logic_negate') return !conditionValue(block.getInputTargetBlock('BOOL'));
  if (block.type === 'karel_path') {
    const offsets = { FRONT: 0, RIGHT: 1, LEFT: 3 };
    const open = freeIn((state.world.dir + offsets[block.getFieldValue('DIRECTION')]) % 4);
    return block.getFieldValue('STATE') === 'FREE' ? open : !open;
  }
  if (block.type === 'karel_marker_here') return (state.world.markers[keyAt(state.world.x, state.world.y)] || 0) > 0;
  if (block.type === 'karel_bag_empty') return state.world.bag === 0;
  if (block.type === 'karel_facing') return state.world.dir === Number(block.getFieldValue('DIRECTION'));
  if (block.type === 'karel_at_goal') return state.world.x === currentLevel().goal[0] && state.world.y === currentLevel().goal[1];
  return Boolean(evaluateValue(block));
}
function evaluateValue(block) {
  if (!block) return 0;
  if (block.type === 'math_number') return Number(block.getFieldValue('NUM')) || 0;
  if (block.type === 'text') return block.getFieldValue('TEXT') || '';
  if (block.type === 'logic_boolean') return block.getFieldValue('BOOL') === 'TRUE';
  if (block.type === 'variables_get') return state.variables.get(block.getFieldValue('VAR')) ?? 0;
  if (block.type === 'karel_marker_count') return state.world.markers[keyAt(state.world.x, state.world.y)] || 0;
  if (block.type === 'karel_bag_count') return state.world.bag;
  if (block.type === 'logic_compare' || block.type === 'logic_operation' || block.type === 'logic_negate' || block.type === 'karel_path' || block.type === 'karel_marker_here' || block.type === 'karel_bag_empty' || block.type === 'karel_facing' || block.type === 'karel_at_goal') return conditionValue(block);
  if (block.type === 'math_arithmetic') {
    const a = Number(evaluateValue(block.getInputTargetBlock('A'))); const b = Number(evaluateValue(block.getInputTargetBlock('B')));
    return ({ ADD: () => a + b, MINUS: () => a - b, MULTIPLY: () => a * b, DIVIDE: () => b === 0 ? 0 : a / b, POWER: () => a ** b })[block.getFieldValue('OP')]();
  }
  if (block.type === 'math_modulo') return Number(evaluateValue(block.getInputTargetBlock('DIVIDEND'))) % (Number(evaluateValue(block.getInputTargetBlock('DIVISOR'))) || 1);
  if (block.type === 'math_single') {
    const number = Number(evaluateValue(block.getInputTargetBlock('NUM'))); const op = block.getFieldValue('OP');
    return ({ ROOT: () => Math.sqrt(Math.max(0, number)), ABS: () => Math.abs(number), NEG: () => -number, ROUND: () => Math.round(number), ROUNDUP: () => Math.ceil(number), ROUNDDOWN: () => Math.floor(number), SIN: () => Math.sin(number * Math.PI / 180), COS: () => Math.cos(number * Math.PI / 180), TAN: () => Math.tan(number * Math.PI / 180), LN: () => Math.log(number), LOG10: () => Math.log10(number), EXP: () => Math.exp(number), '10_POW': () => 10 ** number })[op]?.() ?? 0;
  }
  if (block.type === 'math_random_int') {
    const from = Math.ceil(Number(evaluateValue(block.getInputTargetBlock('FROM')))); const to = Math.floor(Number(evaluateValue(block.getInputTargetBlock('TO'))));
    return Math.floor(Math.random() * (to - from + 1)) + from;
  }
  if (block.type === 'text_join') return block.inputList.filter(input => input.type === Blockly.inputTypes.VALUE).map(input => String(evaluateValue(block.getInputTargetBlock(input.name)))).join('');
  if (block.type === 'text_length') return String(evaluateValue(block.getInputTargetBlock('VALUE'))).length;
  return 0;
}
function* executeStack(firstBlock) {
  let block = firstBlock;
  while (block) { if (block.isEnabled()) yield* executeBlock(block); block = block.getNextBlock(); }
}
function* executeWorkspace() {
  for (const block of state.workspace.getTopBlocks(true)) yield* executeStack(block);
}
function* executeBlock(block) {
  const type = block.type;
  if (type === 'controls_repeat_ext') {
    const count = Math.max(0, Math.min(10000, Math.floor(Number(evaluateValue(block.getInputTargetBlock('TIMES'))))));
    for (let index = 0; index < count; index++) yield* executeStack(block.getInputTargetBlock('DO'));
    return;
  }
  if (type === 'controls_whileUntil') {
    let turns = 0;
    while (conditionValue(block.getInputTargetBlock('BOOL')) === (block.getFieldValue('MODE') === 'WHILE')) {
      if (turns++ >= 10000) throw new Error('Este bucle superó 10 000 repeticiones. Revisa su condición.');
      const before = worldSignature();
      yield { id: block.id, message: 'Evaluando la condición del bucle' };
      yield* executeStack(block.getInputTargetBlock('DO'));
      if (before === worldSignature() && conditionValue(block.getInputTargetBlock('BOOL')) === (block.getFieldValue('MODE') === 'WHILE')) throw new Error('El bucle no cambia el mundo ni sus variables. Ajusta la condición o el cuerpo.');
    }
    return;
  }
  if (type === 'controls_if') {
    const branches = block.inputList.filter(input => /^IF\d+$/.test(input.name));
    for (const input of branches) {
      if (conditionValue(block.getInputTargetBlock(input.name))) { yield* executeStack(block.getInputTargetBlock(`DO${input.name.slice(2)}`)); return; }
    }
    yield* executeStack(block.getInputTargetBlock('ELSE'));
    return;
  }
  if (type === 'controls_for') {
    const variable = block.getFieldValue('VAR'); const start = Number(evaluateValue(block.getInputTargetBlock('FROM'))); const end = Number(evaluateValue(block.getInputTargetBlock('TO'))); const increment = Number(evaluateValue(block.getInputTargetBlock('BY'))) || 1;
    let turns = 0;
    for (let value = start; increment > 0 ? value <= end : value >= end; value += increment) {
      if (turns++ >= 10000) throw new Error('Este bucle superó 10 000 repeticiones. Revisa sus valores.');
      state.variables.set(variable, value); yield* executeStack(block.getInputTargetBlock('DO'));
    }
    return;
  }
  if (type === 'variables_set') { state.variables.set(block.getFieldValue('VAR'), evaluateValue(block.getInputTargetBlock('VALUE'))); return; }
  if (type === 'math_change') { const variable = block.getFieldValue('VAR'); state.variables.set(variable, Number(state.variables.get(variable) || 0) + Number(evaluateValue(block.getInputTargetBlock('DELTA')))); return; }
  if (type === 'karel_move') {
    const steps = Math.max(0, Math.min(10000, Math.floor(Number(evaluateValue(block.getInputTargetBlock('STEPS'))))));
    for (let index = 0; index < steps; index++) yield { id: block.id, action: () => perform('move'), message: 'Avanzar', trace: true };
    return;
  }
  if (type === 'karel_turn') { yield { id: block.id, action: () => perform(block.getFieldValue('DIRECTION') === 'LEFT' ? 'left' : 'right'), message: 'Girar' }; return; }
  if (type === 'karel_pick' || type === 'karel_drop') { yield { id: block.id, action: () => perform(type === 'karel_pick' ? 'pick' : 'drop'), message: type === 'karel_pick' ? 'Recoger marcador' : 'Colocar marcador' }; }
}
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
  return state.world.x === level.goal[0] && state.world.y === level.goal[1] && (level.goalDirection === undefined || state.world.dir === level.goalDirection) && Object.entries(level.targets).every(([position, count]) => (state.world.markers[position] || 0) >= count);
}
function finishExecution(message, kind = '') {
  state.running = false; state.paused = false; state.iterator = null; state.activeId = null;
  if (state.timer) clearTimeout(state.timer); state.timer = null;
  state.workspace?.highlightBlock(null);
  renderWorld(); updateWorkspaceUI(); setTransport();
  if (message) announce(message, kind);
}
function stopExecution(showMessage = true) {
  if (state.timer) clearTimeout(state.timer); state.timer = null;
  if (state.iterator || state.running) finishExecution(showMessage ? 'Ejecución detenida. Puedes ajustar el programa y probar de nuevo.' : '', '');
}
function nextStep() {
  if (!state.iterator) { state.world = newWorld(); state.variables.clear(); state.iterator = executeWorkspace(); announce('Programa preparado. Ejecuta para ver qué ocurre.'); }
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
    state.workspace.highlightBlock(step.id);
    if (step.action) step.action();
    if (step.trace) state.tracePath.push([state.world.x, state.world.y]);
    renderWorld(); updateWorkspaceUI(); setTransport(); announce(step.message); return true;
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
  if (!state.workspace.getTopBlocks(false).length) { announce('Arrastra al menos un bloque al espacio antes de ejecutar.', 'error'); return; }
  if (!state.iterator) { state.world = newWorld(); resetPathTrace(); state.variables.clear(); state.iterator = executeWorkspace(); setWorld(); }
  state.running = true; state.paused = false;
  renderWorld(); updateWorkspaceUI(); setTransport(); announce('¡Karel está en marcha!'); runLoop();
}
function stepOnce() {
  if (state.running) { if (!state.paused) { state.paused = true; if (state.timer) clearTimeout(state.timer); setTransport(); } state.running = false; }
  if (!state.workspace.getTopBlocks(false).length) { announce('Arrastra al menos un bloque al espacio antes de ejecutar.', 'error'); return; }
  if (!state.iterator) { state.world = newWorld(); resetPathTrace(); state.variables.clear(); state.iterator = executeWorkspace(); }
  const more = nextStep();
  if (more) { setHint('Paso ejecutado. Pulsa F10 para continuar.'); setTransport(); }
}
initializeWorkspace();
initializeLevelSelector();
initializeBuilder();
initializeSplitSlider();
$('#level-select').addEventListener('change', event => startLevel(Number(event.target.value)));
$('#practice-version').addEventListener('click', () => startLevel(state.levelIndex, 'practice'));
$('#demo-version').addEventListener('click', () => startLevel(state.levelIndex, 'demo'));
$('#undo-button').addEventListener('click', () => { if (!state.running) state.workspace.undo(false); });
$('#redo-button').addEventListener('click', () => { if (!state.running) state.workspace.undo(true); });
$('#clear-button').addEventListener('click', () => { if (state.running) return; state.savedPrograms.delete(state.levelIndex); state.workspace.clear(); updateWorkspaceUI(); });
$('#run-button').addEventListener('click', runProgram);
$('#pause-button').addEventListener('click', () => { if (state.running) runProgram(); });
$('#step-button').addEventListener('click', stepOnce);
$('#stop-button').addEventListener('click', () => stopExecution());
$('#restart-button').addEventListener('click', () => { state.world = newWorld(); resetPathTrace(); state.iterator = null; finishExecution('', ''); renderWorld(); announce('Nivel reiniciado. Tu programa se conserva.'); setHint('Listo para otra ejecución'); });
$('#path-toggle').addEventListener('click', () => {
  state.showPath = !state.showPath;
  $('#path-toggle').setAttribute('aria-pressed', String(state.showPath));
  $('#path-toggle').classList.toggle('active', state.showPath);
  $('#path-toggle-label').textContent = state.showPath ? 'Ruta visible' : 'Ruta';
  $('#path-toggle').title = state.showPath ? 'Ocultar el camino recorrido' : 'Mostrar el camino recorrido';
  renderWorld();
});
$('#speed').addEventListener('input', event => { const value = Number(event.target.value); $('#speed-value').textContent = value < 300 ? 'LENTA' : value > 700 ? 'RÁPIDA' : 'NORMAL'; });
document.addEventListener('keydown', event => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') { event.preventDefault(); runProgram(); }
  else if (event.key === 'F10') { event.preventDefault(); stepOnce(); }
  else if (event.key === 'Escape') stopExecution();
  else if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') { event.preventDefault(); state.workspace.undo(event.shiftKey); }
  else if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'y') { event.preventDefault(); state.workspace.undo(true); }
});
startLevel(0);
