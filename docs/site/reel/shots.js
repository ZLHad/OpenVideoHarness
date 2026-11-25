/* The shots shown on the homepage's film wall (docs/site/index.html) and in the one-take page (docs/site/reel/): one list
   for both. Each is 3.5–5.5 s cut from a finished film, silent, its end dissolved into its start so it loops. A shot says
   what is on screen and what kind of film it is from, never the film's title. The clips are in the release "media"
   (tools/media.txt); their first frames are in posters/. docs/site/README.md says how to add one. */
window.REEL = (() => {
  // what kind of film a shot is from: what it is and what drew it
  const films = {
    ashare:  { zh: '9 分半数据片 · canvas-film + Three.js', en: '9½-minute data film · canvas-film + Three.js' },
    ice:     { zh: '7 分半物理科普 · HyperFrames，Canvas 2D', en: '7½-minute physics explainer · HyperFrames, Canvas 2D' },
    send:    { zh: '2 分半通信科普 · HyperFrames，Canvas 2D', en: '2½-minute explainer · HyperFrames, Canvas 2D' },
    think:   { zh: '33 分钟思考片 · canvas-film，部分底图是生成的', en: '33-minute essay film · canvas-film, some generated backdrops' },
    folk:    { zh: '3 分钟民俗短片 · canvas-film', en: '3-minute folk-history short · canvas-film' },
    biz:     { zh: '8 分钟商业拆解 · canvas-film，场景底图是生成的', en: '8-minute business breakdown · canvas-film, generated backdrops' },
    math:    { zh: '3 分钟数学故事 · HyperFrames，Canvas 2D + Three.js', en: '3-minute maths story · HyperFrames, Canvas 2D + Three.js' },
    proof:   { zh: '12 分钟数学时评 · canvas-film', en: '12-minute film on a proof · canvas-film' },
    writer:  { zh: '9 分钟作家小传 · Canvas 2D', en: '9-minute portrait of a writer · Canvas 2D' },
    machine: { zh: '14 分钟机械拆解 · Three.js', en: '14-minute machine teardown · Three.js' },
    soft:    { zh: '4 分钟技术故事 · canvas-film + Three.js', en: '4-minute tech story · canvas-film + Three.js' },
    tools:   { zh: '3 分钟科技史 · HyperFrames，Canvas 2D', en: '3-minute history of tools · HyperFrames, Canvas 2D' },
    chem:    { zh: '2 分钟化学科普 · Canvas 2D + Three.js', en: '2-minute chemistry explainer · Canvas 2D + Three.js' },
    intro:   { zh: '这个仓库的介绍片 · Blender + Three.js', en: "this repo's intro film · Blender + Three.js" },
    drawn:   { zh: '12 秒手绘短片 · p5.brush', en: '12-second hand-drawn short · p5.brush' },
    lesson:  { zh: '25 秒数学讲解 · Manim', en: '25-second maths lesson · Manim' },
  };
  // the one take, in order: [id, film, word zh, word en, power of ten (metres), what is on screen zh, en, where the next shot
  // opens inside this one (x, y, width as fractions of the frame; its shape), the colour the interface takes]
  const dive = [
    ['galaxy', 'ashare', '星系', 'Galaxy', 21, '两条一路走来的线，最后化进一个星系', 'Two lines that ran side by side end as a galaxy', [.505, .485, .15, 'iris'], '#c9d3ff'],
    ['blackhole', 'ice', '黑洞', 'Black hole', 13, '光绕着黑洞弯过去，喷流正对着地球', 'Light bends around a black hole; its jet points at Earth', [.505, .50, .16, 'iris'], '#ffd77a'],
    ['planet', 'ashare', '行星', 'Planet', 7, '两道光从夜半球升起', 'Two lights rise from the night side', [.50, .57, .16, 'iris'], '#ff9a5c'],
    ['satellites', 'send', '天与海', 'Sky and sea', 6, '卫星、飞艇、无人机和一条船，织成一张网', 'Satellites, airships, drones and one boat become a network', [.36, .88, .16, 'iris'], '#86bfe0'],
    ['island', 'think', '岛', 'Island', 5, '已知的边界，是一座发光的岛', 'The edge of what is known, as a glowing island', [.50, .58, .17, 'iris'], '#ffd89a'],
    ['mountains', 'folk', '山', 'Mountains', 4, '青绿山水，一首登高的诗', 'Blue-and-green mountains and a poem about climbing', [.72, .62, .15, 'iris'], '#4fbf9f'],
    ['ring', 'think', '漩涡', 'Vortex', 4, '流体把自己越卷越紧', 'A flow winds itself ever tighter', [.49, .73, .15, 'iris'], '#5cc8ff'],
    ['detector', 'ice', '冰', 'Ice', 3, '一立方公里的冰，被一个中微子点亮', 'A cubic kilometre of ice, lit by one neutrino', [.43, .63, .15, 'iris'], '#7fffc0'],
    ['inkridge', 'ashare', '山脊', 'Ridge', 3, '2010 年，同一条曲线是一道水墨山脊', '2010: the same curve as a ridge in ink', [.52, .50, .18, 'line'], '#7fa8e0'],
    ['papercity', 'ashare', '纸城', 'Paper city', 3, '2008 年，它穿过一座灰色的纸城', '2008: it crosses a grey paper city', [.50, .44, .18, 'line'], '#ff5147'],
    ['neon', 'ashare', '霓虹', 'Neon', 3, '2015 年，它是霓虹', '2015: it is neon', [.60, .20, .16, 'iris'], '#ff66d4'],
    ['port', 'ashare', '港口', 'Harbour', 2, '2018 年，它开进一座积木港口', '2018: it runs into a toy harbour', [.28, .66, .15, 'door'], '#ffce3a'],
    ['windows', 'folk', '灯火', 'Windows', 2, '一栋楼，一扇亮着的窗，一个等电话的人', 'A building, one lit window, someone by the phone', [.50, .36, .15, 'door'], '#ffd27a'],
    ['taxi', 'biz', '街', 'Street', 1, '雨夜里打表的出租车', 'A taxi on the meter, in the rain', [.46, .40, .14, 'iris'], '#ffb14a'],
    ['arcade', 'biz', '街机厅', 'Arcade', 1, '一句话在这里被切成代币', 'A sentence is cut into tokens here', [.49, .17, .20, 'door'], '#3df0c8'],
    ['stairs', 'folk', '楼道', 'Stairwell', 1, '老楼没有电梯，这一回没有少一个人', 'No lift in the old block; this time no one is missing', [.515, .42, .15, 'door'], '#ff9c6b'],
    ['boat', 'math', '船', 'Boat', 1, '论文像雪一样落进海里，一个人一篇篇地读', 'Papers fall on the sea like snow; one person reads them', [.47, .66, .14, 'iris'], '#ffcf87'],
    ['lamp', 'think', '路灯', 'Street lamp', 1, '只在有光的地方找钥匙', 'Looking for the keys only where there is light', [.475, .12, .15, 'iris'], '#ffae3b'],
    ['eniac', 'tools', '机房', 'Machine hall', 1, '一间装得下一台计算机的大厅', 'A hall the size of one computer', [.50, .47, .18, 'door'], '#ff9a56'],
    ['puppets', 'folk', '皮影', 'Shadow play', 0, '皮影，一家人登高', 'Shadow puppets: a family climbs the hill', [.70, .22, .15, 'iris'], '#ff9440'],
    ['wings', 'writer', '翅膀', 'Wings', 0, '把翅膀藏在外套底下的男孩', 'A boy who hides his wings under his coat', [.355, .50, .13, 'iris'], '#ff544c'],
    ['disc', 'machine', '刹车盘', 'Brake disc', -1, '一脚刹车，用热成像看', 'One stop, seen in heat', [.555, .55, .15, 'iris'], '#ff8b1f'],
    ['cylinder', 'machine', '主缸', 'Master cylinder', -1, '剖开制动主缸，油推着活塞走', 'A master cylinder cut open; the fluid does the pushing', [.33, .33, .14, 'iris'], '#ffcf6a'],
    ['tree', 'think', '书', 'Book', -1, '书里长出一棵树，树上亮起问题', 'A tree grows out of a book and lights up with questions', [.50, .33, .15, 'iris'], '#ffd75e'],
    ['layers', 'soft', '软件', 'Software', -1, '按一下复制，它穿过了几层', 'One press of Copy, and the layers it goes through', [.505, .28, .14, 'iris'], '#9db8ff'],
    ['hand', 'tools', '手', 'Hand', -1, '四万年前的手印，和这一次的手印', 'A handprint forty thousand years old, and a new one', [.64, .62, .14, 'iris'], '#6fe6ff'],
    ['brush', 'tools', '笔', 'Brush', -2, '一支毛笔当场画出造纸', 'A brush draws how paper is made', [.60, .72, .14, 'iris'], '#d9b777'],
    ['flea', 'tools', '跳蚤', 'Flea', -3, '显微镜下的跳蚤，一刀一刀刻出来', 'A flea under the microscope, engraved stroke by stroke', [.80, .30, .13, 'iris'], '#cdbd97'],
    ['molecules', 'chem', '分子', 'Molecule', -9, '一个氨基酸分子慢慢转身', 'An amino acid slowly turns', [.43, .40, .13, 'iris'], '#ff9d9d'],
    ['cherenkov', 'ice', '粒子', 'Particle', -15, '它跑得比冰里的光还快，拖出一道光锥', 'Faster than light in ice, it drags a cone of light', [.80, .525, .13, 'iris'], '#7fd0ff'],
    ['light', 'ashare', '光', 'Light', null, '最后只剩一点光', 'In the end, one point of light', null, '#ffffff'],
  ];
  // on the wall only: [id, film, what is on screen zh, en]
  const more = [
    ['observatory', 'think', '望远镜看得更远，人还是会抬头', 'Telescopes see further; people still look up'],
    ['sunset', 'think', '海边捡贝壳的孩子', 'A child by the sea'],
    ['infinity', 'think', '人和机器，一个走不完的回路', 'A person and a machine in one endless loop'],
    ['pinkring', 'think', '速度冲向无穷大的流体', 'A flow whose speed runs to infinity'],
    ['capsules', 'soft', '发现沿着轨道一个个亮起来', 'Findings light up along the track'],
    ['lockbox', 'soft', '黑盒子被打开', 'The black box opens'],
    ['boxbook', 'writer', '一本打开是盒子的书', 'A book that opens as a box'],
    ['inkgarden', 'folk', '水墨，菊花丛里等酒的人', 'Ink: waiting for wine among chrysanthemums'],
    ['songstreet', 'folk', '北宋的街市', 'A Song-dynasty street'],
    ['moonpalace', 'folk', '月夜的长安', 'A moonlit capital'],
    ['hanpalace', 'folk', '汉代宫里的灯', 'Lamps in a Han palace'],
    ['lanterns', 'folk', '举着火把上山', 'Climbing with torches'],
    ['blueprint', 'tools', '蒸汽机，晒成蓝图', 'A steam engine turns into a blueprint'],
    ['swirl', 'tools', '几千年的工具绕成一圈', 'Thousands of years of tools in orbit'],
    ['reader', 'proof', '站在一千七百万行代码前面的人', 'Someone in front of seventeen million lines'],
    ['oranges', 'proof', '橙子怎么堆最密', 'The tightest way to stack oranges'],
    ['glasscar', 'machine', '没有人踩踏板，车自己刹住', 'No foot on the pedal; the car stops itself'],
    ['hotdisc', 'machine', '刹车盘烧红', 'The disc glows'],
    ['finger', 'ice', '穿过指甲的中微子，一秒一秒地数', 'Neutrinos through a fingernail, counted'],
    ['earth', 'ice', '二十来台望远镜，看向同一片天', 'Some twenty telescopes turn to one patch of sky'],
    ['sandcity', 'ashare', '2020 年，它冲过一座沙城', '2020: it runs through a city of sand'],
    ['clawd', 'drawn', '想拍下一片落叶', 'Trying to film a falling leaf'],
    ['fourier', 'lesson', '用正弦波搭出方波', 'Building a square wave from sine waves'],
    ['filmsea', 'intro', '影片的海', 'A sea of films'],
  ];
  // the wall's order, which is also the order of the tiles in the mosaic video (reel-wall, 8 to a row): neighbours contrast
  const order = ['wings', 'galaxy', 'tree', 'port', 'molecules', 'hand', 'oranges', 'sunset',
    'windows', 'brush', 'mountains', 'earth', 'satellites', 'cylinder', 'puppets', 'light',
    'taxi', 'boat', 'pinkring', 'arcade', 'observatory', 'boxbook', 'blueprint', 'glasscar',
    'eniac', 'papercity', 'swirl', 'moonpalace', 'finger', 'lanterns', 'blackhole', 'lamp',
    'island', 'detector', 'capsules', 'fourier', 'ring', 'inkridge', 'flea', 'hotdisc',
    'disc', 'neon', 'clawd', 'cherenkov', 'stairs', 'filmsea', 'hanpalace', 'planet',
    'inkgarden', 'lockbox', 'songstreet', 'sandcity', 'infinity', 'reader', 'layers'];
  const shots = {};
  dive.forEach(([id, film, wz, we, exp, zh, en, port, ac], i) => { shots[id] = { id, film, wz, we, exp, zh, en, port, ac, n: i }; });
  more.forEach(([id, film, zh, en]) => { shots[id] = { id, film, zh, en }; });
  return {
    films, shots, order, dive: dive.map(d => d[0]),
    mosaic: { cols: 8, w: 320, h: 180 },
    release: { arcade: 'f1047c22', blackhole: '78db7c2b', blueprint: '62a1ad9e', boat: '6bbabc2c', boxbook: '54deb206', brush: '10c240e6', capsules: 'bee2dbb8', cherenkov: '67a278ed', clawd: '0152b2c0', cylinder: '8cd9c776', detector: '1888312a', disc: '0b936548', earth: '0e7356e3', eniac: '2e7561aa', filmsea: '00c5c6f6', finger: 'cd8dea79', flea: '388d0177', fourier: 'fe72e5de', galaxy: '38bd20e6', glasscar: 'b824f3f5', hand: '818f9e39', hanpalace: '09436844', hotdisc: 'e406030b', infinity: '5615e594', inkgarden: '099ce84f', inkridge: '8a555158', island: 'fba65256', lamp: '02ab1bba', lanterns: 'd8d93cd5', layers: '2678214a', light: '58ccb842', lockbox: '7f03f39a', molecules: '57421986', moonpalace: 'af35354e', mountains: '7e1fc405', neon: 'd348a2e9', observatory: '6ea327cf', oranges: '0b036e68', papercity: 'b178d10d', pinkring: '015b1cd1', planet: 'a55cf510', port: 'df6acb54', puppets: '4a894a5c', reader: '9102688d', ring: '4ca72bc1', sandcity: 'f1f9a988', satellites: '646140c9', songstreet: '90d1f628', stairs: 'df3da2ce', sunset: '126ed8ef', swirl: 'dfd380a9', taxi: '8599b071', tree: '146e907f', windows: '3fd00e97', wings: '9ca462f8', 'reel-wall': '6ceb60c2', 'styles-wall': '072a21c2' },   // each file's sha256, its first 8: reel-<id>-<8>.mp4 in the release (docs/site/README.md)
  };
})();
