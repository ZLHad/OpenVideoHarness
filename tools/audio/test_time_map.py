"""Time map and reference agreement (JS and Python), events.json headers, time_map.py check. --film: a live page."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from time_map import TimeMap
from time_refs import RefError, Refs, load_events

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'engines/canvas-film/template/src'
# a made-up axis: steps 0..30, held at 10 for two seconds
MAP = {'version': 1, 'axis': {'kind': 'number', 'unit': 'step'},
       'knots': [[2, 0], [4, 10], [6, 10], [10, 30]],
       'events': [{'id': 'e1', 'u': 10, 't': 4, 'lane': 'top'}, {'id': 'e2', 'u': 10, 't': 5.5},
                  {'id': 'e3', 'u': 20, 't': 8, 'end': 9, 'text': 'three', 'data': {'side': 'left'}}]}
TIMELINE = {'segments': [
    {'id': 'a1', 'start': 0.5, 'end': 3.0, 'text': '你好，世界。Hello GPT-4 world!',
     'words': [{'w': '你好', 'start': 0.5, 'end': 1.0}, {'w': '世界', 'start': 1.0, 'end': 1.6}, {'w': 'Hello', 'start': 1.8, 'end': 2.1},
               {'w': 'GPT-4', 'start': 2.1, 'end': 2.5}, {'w': 'world', 'start': 2.5, 'end': 2.9}]},
    {'id': 'a2', 'start': 3.5, 'end': 5.0, 'text': '跟着走﻿，再见',
     'words': [{'w': '跟着', 'start': 3.5, 'end': 4.0}, {'w': '走', 'start': 4.0}, {'w': '在见', 'start': 4.4, 'end': 4.9}]},
    {'id': 'b_3', 'start': 5.5, 'end': 6.0, 'text': 'ＡＢＣ 123'}]}
BEATS = {'bpm': 120, 'duration': 12, 'bars': [[1, 0, 4], [2, 2, 4], [3, 4, 4]]}
REFS = [3.5, '@a1', '@a1>', '@a1:世界', '@a1:hello+0.1', '@a1:GPT-4', '@a1:GPT-4+0', '@a1:GPT-4.0', '@a2:见', '@a2:再见',
        '@a2:走-0.2', '@b_3:abc', '@b_3:１２', '@a1 ', '@a1 ', '@zz', '@a1:不在', '@a1:，', '@', 'a1', '@@a1', ' @a1',
        '@a1:x\ny', '@a1+٣', '@#e3', '@#e3>', '@#e3-0.5', '@#e2+.25', '@#e1>', '@#nope', '@#e 3', '@#e3:x',
        {'$music': [2, 2]}, {'$music': [2, 2], 'offset': -0.1}, {'$music': [9, 1]}, {'$music': [1]}, {'$map': 20},
        {'$map': 5, 'offset': 0.5}, {'$map': 10}, {'$map': 99}, {'$map': 5, 'offset': 'x'}, {'$map': '2101-03-05'},
        True, '3.5', None, {'t': 1}]


def node(code, payload, *files):
    r = subprocess.run(['node', '-e', code, *map(str, files)], input=json.dumps(payload), text=True, capture_output=True)
    if r.returncode: raise AssertionError(r.stderr)
    return json.loads(r.stdout)


JS_MAP = '''const fs=require('node:fs'),vm=require('node:vm');const input=JSON.parse(fs.readFileSync(0,'utf8'));const ctx={input};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8')+`
const call=(f)=>{try{return f()}catch(e){return 'error'}};
let m=null; try{m=new TimeMap(input.data)}catch(e){};
globalThis.result=m===null?'error':{u:input.u.map(t=>call(()=>m.u(t))),t:input.t.map(u=>call(()=>m.t(u))),
at:input.at.map(q=>call(()=>m.at(...q))),rate:input.rate.map(t=>call(()=>m.rate(t))),dur:call(()=>m.dur(0,30)),
day:input.day.map(d=>call(()=>m.day(d))),events:m.events};`,ctx);process.stdout.write(JSON.stringify(ctx.result));'''
# the engine's own cue resolver: 00-core.js (initTimeline, cueT, resolver), 05 (MusicClock) and 06 (TimeMap) in one context
JS_REFS = '''const fs=require('node:fs'),vm=require('node:vm');const input=JSON.parse(fs.readFileSync(0,'utf8'));const ctx={input};
vm.runInNewContext(process.argv.slice(1).map(f=>fs.readFileSync(f,'utf8')).join('\\n')+`
FILM.lead=input.lead; const problems=[]; initTimeline(input.tl, problems);
if(input.beats) MUSIC=new MusicClock(input.beats); if(input.map) TIMEMAP=new TimeMap(input.map);
globalThis.result={problems, times:input.refs.map(r=>{const p=[];const t=resolver('w','k',p).time(r,'t');return p.length?'error':t;})};`,ctx);
process.stdout.write(JSON.stringify(ctx.result));'''


def js_map(data, u=(), t=(), at=(), rate=(), day=()):
    return node(JS_MAP, {'data': data, 'u': list(u), 't': list(t), 'at': list(at), 'rate': list(rate), 'day': list(day)}, SRC / '06-time-map.js')


def py_call(f):
    try: return f()
    except ValueError: return 'error'


class MapTests(unittest.TestCase):
    def test_js_and_python_read_a_map_alike(self):
        q = dict(u=[0, 2, 3, 4, 5, 6, 7.5, 10, 12], t=[0, 5, 10, 20, 30, -1, 31, 2.5],
                 at=[['e1'], ['e2'], ['e3', 'end'], ['e1', 'end'], ['nope'], ['e3', 'middle']], rate=[1, 3, 4, 5, 6, 8, 11], day=['2101-03-05'])
        m = TimeMap(MAP)
        with self.assertRaises(ValueError): m.u(float('nan'))
        py = {'u': [py_call(lambda x=x: m.u(x)) for x in q['u']], 't': [py_call(lambda x=x: m.t(x)) for x in q['t']],
              'at': [py_call(lambda x=x: m.at(*x)) for x in q['at']], 'rate': [py_call(lambda x=x: m.rate(x)) for x in q['rate']],
              'dur': m.dur(0, 30), 'day': [py_call(lambda x=x: m.day(x)) for x in q['day']], 'events': m.events}
        self.assertEqual(py['u'], [0, 0, 5, 10, 10, 10, 17.5, 30, 30])
        self.assertEqual(py['t'], [2, 3, 4, 8, 10, 'error', 'error', 2.5])
        self.assertEqual(py['at'], [4, 5.5, 9, 'error', 'error', 'error'])
        self.assertEqual(py['rate'], [5, 5, 0, 0, 5, 5, 5])
        self.assertEqual(py['day'], ['error'])
        js = js_map(MAP, **q)
        self.assertEqual(js, py)
        altered = m.events; altered[2]['data']['side'] = 'x'
        self.assertEqual(m.events[2]['data']['side'], 'left')

    def test_a_date_axis_counts_whole_days_from_its_origin(self):
        d = {'version': 1, 'axis': {'kind': 'date', 'origin': '2101-02-27'}, 'knots': [[0, 0], [10, 400]], 'events': []}
        days = ['2101-02-28', '2101-03-01', '2102-02-27', '2101-02-29', '2101-3-01', '0099-01-01', 7]
        m = TimeMap(d)
        py = [py_call(lambda x=x: m.day(x)) for x in days]
        self.assertEqual(py, [1, 2, 365, 'error', 'error', 'error', 'error'])
        self.assertEqual(js_map(d, day=days)['day'], py)
        r = Refs(timemap=self.write(d))
        self.assertEqual(r.t({'$map': '2101-03-01'}), 0.05)

    def write(self, data, name='time.map.json'):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        p = Path(tmp.name) / name; p.write_text(json.dumps(data)); return p

    def test_bad_maps_are_refused_on_both_sides(self):
        bad = [None, [], {}, {**MAP, 'version': 2}, {**MAP, 'knots': [[0, 0]]}, {**MAP, 'axis': {'kind': 'date'}},
               {**MAP, 'axis': {'kind': 'warp'}}, {**MAP, 'events': None}, {**MAP, 'axis': {'unit': 3}}]
        for k, v in ((1, [2, 5]), (2, [3, 9]), (0, [-1, 0]), (1, [4, 'x']), (1, [4, True]), (3, [10])):
            d = copy.deepcopy(MAP); d['knots'][k] = v; bad.append(d)
        for k, v in (('id', 'e-1'), ('id', 'e2'), ('t', 7), ('u', 31), ('end', 3), ('lane', 1), ('data', [1]), ('t', None)):
            d = copy.deepcopy(MAP); d['events'][0][k] = v; bad.append(d)
        for d in bad:
            with self.assertRaises(ValueError, msg=json.dumps(d)): TimeMap(d)
            self.assertEqual(js_map(d), 'error', json.dumps(d))
        ok = copy.deepcopy(MAP); ok['events'][1]['t'] = 6.0005   # a millisecond of rounding at the end of a hold is fine
        TimeMap(ok); self.assertNotEqual(js_map(ok), 'error')


class RefTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='vh-refs-'); self.addCleanup(tmp.cleanup)
        self.d = Path(tmp.name)
        for name, data in (('timeline.json', TIMELINE), ('music.beats.json', BEATS), ('time.map.json', MAP)):
            (self.d / name).write_text(json.dumps(data, ensure_ascii=False))

    def refs(self, **kw):
        return Refs(timeline=self.d / 'timeline.json', lead=0.25, music=self.d / 'music.beats.json', timemap=self.d / 'time.map.json', **kw)

    def test_js_and_python_resolve_every_kind_of_reference_alike(self):
        r = self.refs()
        py = [py_call(lambda x=x: r.t(x)) for x in REFS]
        js = node(JS_REFS, {'tl': TIMELINE, 'lead': 0.25, 'beats': BEATS, 'map': MAP, 'refs': REFS},
                  SRC / '00-core.js', SRC / '05-music-clock.js', SRC / '06-time-map.js')
        self.assertEqual(js['problems'], [])
        self.assertEqual(js['times'], py)
        want = {'@a1': 0.75, '@a1>': 3.25, '@a1:世界': 1.25, '@#e3': 8, '@#e3>': 9, '@#e3-0.5': 7.5, '@#e2+.25': 5.75}
        self.assertEqual({k: py[REFS.index(k)] for k in want}, want)
        for k in ('@a1:GPT-4', '@zz', '@a1:，', '@@a1', ' @a1', '@#e1>', '@#nope', '@a1+٣'):
            self.assertEqual(py[REFS.index(k)], 'error', k)
        self.assertEqual(py[REFS.index('@a1 ')], 0.75)
        self.assertEqual(py[REFS.index({'$map': 10})], 4)   # a hold: the first moment the axis gets there
        with self.assertRaisesRegex(RefError, 'reads two ways'): r.t('@a1:GPT-4')
        with self.assertRaisesRegex(RefError, 'nearest: e3'): r.t('@#e33')

    def test_sources_and_a_map_made_on_another_beat_map(self):
        r = self.refs()
        self.assertEqual([Path(s['path']).name for s in r.sources], ['timeline.json', 'music.beats.json', 'time.map.json'])
        self.assertEqual(r.sources[1]['sha256'], hashlib.sha256((self.d / 'music.beats.json').read_bytes()).hexdigest())
        made = {**MAP, 'sources': [{'path': 'music.beats.json', 'sha256': '0' * 64}], 'rebuild': 'python3 make_map.py'}
        (self.d / 'time.map.json').write_text(json.dumps(made))
        with self.assertRaisesRegex(RefError, r'another version of music\.beats\.json.*rebuild it: python3 make_map\.py'): self.refs()
        Refs(timemap=self.d / 'time.map.json')   # a map alone: nothing to compare it with here

    def test_events_files_plain_and_with_a_header(self):
        plain = [{'t': 1.5, 'sfx': 'click'}, {'t': 2, 'sfx': 'whoosh', 'pan': -0.4}]
        p = self.d / 'events.json'; p.write_text(json.dumps(plain))
        self.assertEqual(load_events(p), (plain, [], None))
        p.write_text(json.dumps([{'t': '@a2>', 'sfx': 'click'}]))
        with self.assertRaisesRegex(RefError, 'a plain list takes seconds'): load_events(p)
        head = {'refs': {'timeline': 'timeline.json', 'lead': 0.25, 'timemap': 'time.map.json'},
                'events': [{'id': 'hit1', 't': '@#e3', 'sfx': 'impact'}, {'t': '@a1>', 'sfx': 'whoosh'}, {'t': 4, 'sfx': 'click'}]}
        p.write_text(json.dumps(head))
        events, sources, refs = load_events(p)
        self.assertEqual(events, [{'id': 'hit1', 't': 8, 'sfx': 'impact', 'ref': '@#e3'}, {'t': 3.25, 'sfx': 'whoosh', 'ref': '@a1>'}, {'t': 4, 'sfx': 'click'}])
        self.assertEqual([Path(s['path']).name for s in sources], ['timeline.json', 'time.map.json'])
        self.assertEqual(refs.t('@#e2'), 5.5)
        for change, msg in ((lambda h: h['refs'].update(beats='x'), 'refs.beats'), (lambda h: h.update(extra=1), 'extra'),
                            (lambda h: h['events'][1].update(id='hit1'), 'used twice'), (lambda h: h['events'][1].update(id='a b'), 'letters'),
                            (lambda h: h['events'][1].update(t='@a9'), 'no narration line "a9"'), (lambda h: h['refs'].pop('timemap'), 'no time map'),
                            (lambda h: h['refs'].update(music='nope.json'), 'no .*nope.json')):
            h = copy.deepcopy(head); change(h); p.write_text(json.dumps(h))
            with self.assertRaisesRegex(RefError, msg): load_events(p)


class CheckTests(unittest.TestCase):
    def run_check(self, *args, code=0):
        r = subprocess.run([sys.executable, str(ROOT / 'tools/audio/time_map.py'), 'check', *map(str, args)], capture_output=True, text=True)
        self.assertEqual(r.returncode, code, r.stdout + r.stderr)
        return r.stdout + r.stderr

    def test_check_lists_compares_and_names_a_changed_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp); m = d / 'time.map.json'; beats = d / 'music.beats.json'
            beats.write_text(json.dumps(BEATS))
            made = {**MAP, 'sources': [{'path': 'music.beats.json', 'sha256': hashlib.sha256(beats.read_bytes()).hexdigest()}], 'rebuild': 'python3 make_map.py'}
            m.write_text(json.dumps(made))
            out = self.run_check(m, '--save')
            self.assertIn('3 events', out); self.assertIn('1 hold', out); self.assertIn('as when the map was made', out)
            self.assertIn('axis (number) 0 – 30', out); self.assertRegex(out, r'8\.000  e3\s+20  lane|8\.000  e3\s+20  end 9\.000')
            self.assertTrue((d / 'time.map.checked.json').exists())
            moved = copy.deepcopy(made); moved['knots'][3] = [12, 30]; moved['events'][2]['t'] = 9; moved['events'][2]['end'] = 10
            moved['events'].pop(0); m.write_text(json.dumps(moved))
            out = self.run_check(m)
            self.assertIn('(the map changed): 1 moved, 0 new, 1 gone', out); self.assertIn('8.000 → 9.000 s', out)
            beats.write_text(json.dumps({**BEATS, 'bpm': 60}))
            self.assertIn('changed since the map was made: rebuild the map (python3 make_map.py)', self.run_check(m, code=1))
            m.write_text(json.dumps({'version': 1, 'axis': {'kind': 'date', 'origin': '2101-02-27'}, 'knots': [[0, 0], [10, 400]],
                                     'events': [{'id': 'd1', 'u': 2.5, 't': 0.0625}]}))
            out = self.run_check(m, '--out', d / 'dates.json')
            self.assertIn('axis (date) 2101-02-27 – 2102-04-03', out); self.assertRegex(out, r'd1\s+2101-03-01\+0\.50')
            m.write_text('{"version": 1}')
            self.assertIn('knots', self.run_check(m, code=2))


class FilmMapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='vh-time-map-')
        self.addCleanup(self.tmp.cleanup)
        self.p = Path(self.tmp.name) / 'film'
        shutil.copytree(ROOT / 'engines/canvas-film/template', self.p)
        html = self.p / 'film.html'
        html.write_text(re.sub(r'@font-face\s*\{[^}]*\}', '', html.read_text()))   # timing only; fonts have their own fixtures
        (self.p / 'src/50-shots.js').write_text('''Object.assign(FILM, {timeline:false, duration:12, music:'audio/music.beats.json',
timemap:'data/time.map.json', width:320, height:180, fadeOut:0, grain:0, images:{}});
const CHAPTERS=[{at:0,title:'A'},{at:mapAt(20),title:'B'}];
const COVERS=[{id:'end',at:'@#e3'}];
function paint(t,s){rect(0,0,W,H,{fill:'#111'});const u=mapU(t);rect(10,60,8*u,12,{fill:'#fff'});
label(t,s.t0,'A',16,40,{size:44}); cue('tick', eventT('e3'), {x:10});}
const SHOTS=[{id:'S01',at:0,draw:paint},{id:'S02',at:'@#e2-0.5',o:{hit:mapAt(15,0.25)},draw:paint},{id:'S03',at:'@#e3',draw:paint}];''')
        (self.p / 'audio').mkdir(exist_ok=True); (self.p / 'data').mkdir(exist_ok=True)
        (self.p / 'audio/music.beats.json').write_text(json.dumps(BEATS))
        self.map = self.p / 'data/time.map.json'
        self.map.write_text(json.dumps(MAP))

    def vh(self, *args, code=0):
        r = subprocess.run([os.environ.get('VH_BASH', 'bash'), str(ROOT / 'bin/vh'), *map(str, args)], capture_output=True, text=True)
        self.assertEqual(r.returncode, code, r.stdout + r.stderr)
        return r.stdout + r.stderr

    def test_one_map_moves_cues_shots_and_events_and_frames_stay_pure(self):
        self.vh('cues', self.p, '--save')
        first = json.loads((self.p / 'out/cues.json').read_text())
        self.assertEqual(first['timemap'], {'path': 'data/time.map.json', 'sha256': hashlib.sha256(self.map.read_bytes()).hexdigest()})
        at = {c['id']: c for c in first['cues']}
        self.assertEqual((at['S02.at']['t'], at['S02.at']['ref'], at['S02.o.hit']['t'], at['chapter2.at']['t'], at['cover.end.at']['t']), (5, '@#e2-0.5', 7.25, 8, 8))
        moved = copy.deepcopy(MAP); moved['knots'][2] = [7, 10]; moved['events'][1]['t'] = 6.5
        moved['knots'][3] = [11, 30]; moved['events'][2].update(t=9, end=10); self.map.write_text(json.dumps(moved))
        out = self.vh('cues', self.p)
        self.assertIn('time map changed since the saved cues', out); self.assertIn('S02.at', out); self.assertIn('5.000 → 6.000 s', out)
        self.vh('frames', self.p, '--at', '3.5,9.5', '--out', self.p / 'out/order')
        self.vh('frames', self.p, '--at', '9.5', '--out', self.p / 'out/alone')
        ordered = next((self.p / 'out/order').glob('*t0009.500.png')); alone = next((self.p / 'out/alone').glob('*t0009.500.png'))
        self.assertEqual(ordered.read_bytes(), alone.read_bytes())

    def test_a_missing_event_and_a_map_made_on_other_music_stop_ready(self):
        p = self.p / 'src/50-shots.js'; p.write_text(p.read_text().replace("'@#e2-0.5'", "'@#e9'"))
        self.assertIn('no event "e9"', self.vh('cues', self.p, code=2))
        p.write_text(p.read_text().replace("'@#e9'", "'@#e2-0.5'"))
        made = {**MAP, 'sources': [{'path': '../audio/music.beats.json', 'sha256': '0' * 64}], 'rebuild': 'python3 data/make_map.py'}
        self.map.write_text(json.dumps(made))
        out = self.vh('cues', self.p, code=2)
        self.assertIn('was made on another version of ../audio/music.beats.json', out); self.assertIn('rebuild it: python3 data/make_map.py', out)
        made['sources'][0]['sha256'] = hashlib.sha256((self.p / 'audio/music.beats.json').read_bytes()).hexdigest()
        self.map.write_text(json.dumps(made))
        self.vh('cues', self.p)

    def test_the_check_hashes_the_timeline_the_film_was_built_from(self):
        # the page's fetch gives the timeline on disk the first time and another take after that: a check that fetched the
        # file again would compare the map with the other take, while the cues hang on the first
        take = lambda start: json.dumps({'duration': 4, 'segments': [{'id': 'a1', 'start': start, 'end': start + 1, 'text': '你好',
                                         'words': [{'w': '你好', 'start': start, 'end': start + 1}]}]})
        disk, other = take(1), take(2)
        (self.p / 'audio/timeline.zh.json').write_text(disk)
        (self.p / 'src/50-shots.js').write_text("""const REAL_FETCH = window.fetch; let TIMELINE_FETCHES = 0;
window.fetch = (u, o) => String(u).endsWith("timeline.zh.json") && TIMELINE_FETCHES++ > 0
  ? Promise.resolve(new Response(%s)) : REAL_FETCH(u, o);
Object.assign(FILM, { timeline: "audio/timeline.zh.json", timemap: "data/time.map.json", width: 320, height: 180, tail: 1, fadeOut: 0, grain: 0, images: {} });
const SHOTS = [{ id: "S01", at: 0, draw(t) { rect(0, 0, W, H, { fill: "#111" }); } }, { id: "S02", at: "@a1", draw(t) { rect(0, 0, W, H, { fill: "#222" }); } }];
""" % json.dumps(other))
        sha = lambda text: hashlib.sha256(text.encode()).hexdigest()
        for recorded, ok in ((sha(other), False), (sha(disk), True)):
            self.map.write_text(json.dumps({**MAP, 'sources': [{'path': '../audio/timeline.zh.json', 'sha256': recorded}], 'rebuild': 'python3 data/make_map.py'}))
            out = self.vh('cues', self.p, code=0 if ok else 2)
            if ok: self.assertRegex(out, r'1\.000\s+S02\.at')
            else: self.assertIn('was made on another version of ../audio/timeline.zh.json', out)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(FilmMapTests) if '--film' in sys.argv else unittest.TestSuite(
        unittest.TestLoader().loadTestsFromTestCase(c) for c in (MapTests, RefTests, CheckTests))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
