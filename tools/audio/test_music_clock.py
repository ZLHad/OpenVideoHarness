"""Clock agreement and real-page checks. --film also exercises the browser CLIs."""
import copy
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from music_clock import MusicClock

ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / 'engines/canvas-film/template/src/05-music-clock.js'
BASE = {'bpm': 120, 'duration': 8, 'offset': 0.25,
        'bars': [[1, 0.25, 1], [2, 0.75, 3], [3, 2.25, 6], [4, 5.25, 4]],
        'notes': [{'t': 1.3, 'end': 1.8, 'part': 'keys', 'midi': 60},
                  {'t': 0.8, 'end': 1.2, 'part': 'keys', 'midi': 64}]}


def js_result(data, queries):
    code = '''const fs=require('node:fs'),vm=require('node:vm');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const ctx={input};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8')+`
try { const c=new MusicClock(input.data); globalThis.result={times:input.queries.map(q=>{
try {return c.at(...q)} catch{return 'error'}}), notes:c.noteMap===null?null:c.notes('keys')};
} catch {globalThis.result='error'};`,ctx);
process.stdout.write(JSON.stringify(ctx.result));'''
    r = subprocess.run(['node', '-e', code, str(JS)], input=json.dumps({'data': data, 'queries': queries}),
                       text=True, capture_output=True, check=True)
    return json.loads(r.stdout)


class ClockTests(unittest.TestCase):
    def test_js_python_agree_on_mixed_meters_pickup_and_boundaries(self):
        queries = [[1], [1, 2], [2, 2], [3, 6.5], [4, 5], [2, 1, 0.1]]
        expected = [0.25, 0.75, 1.25, 5, 7.25, 0.85]
        c = MusicClock(BASE)
        self.assertEqual([c.at(*q) for q in queries], expected)
        self.assertEqual(js_result(BASE, queries)['times'], expected)
        self.assertEqual(c.notes('keys'), js_result(BASE, [])['notes'])
        altered = c.notes('keys'); altered[0]['t'] = 999
        self.assertEqual(c.notes('keys')[0]['t'], 0.8)

    def test_invalid_positions_and_trimmed_last_bar(self):
        data = copy.deepcopy(BASE); data['duration'] = 6
        queries = [[0], [5], [1.5], [True], [1, 0], [1, 3], [1, True], [4, 4], [1, 1, -1], [2, 1, '1']]
        c = MusicClock(data)
        for q in queries:
            with self.assertRaises(ValueError): c.at(*q)
        self.assertEqual(js_result(data, queries)['times'], ['error'] * len(queries))
        self.assertEqual(c.at(4, 2.5), 6)

    def test_missing_or_inconsistent_data_never_guesses_a_clock(self):
        bad = [None, {}, {**BASE, 'bars': []}, {**BASE, 'bpm': 0}, {**BASE, 'notes': None}]
        for field, value in ((0, 3), (1, 1), (2, 0), (2, True)):
            d = copy.deepcopy(BASE); d['bars'][1][field] = value; bad.append(d)
        for d in bad:
            with self.assertRaises(ValueError): MusicClock(d)
            self.assertEqual(js_result(d, []), 'error')
        no_notes = {k: v for k, v in BASE.items() if k != 'notes'}
        with self.assertRaisesRegex(ValueError, 'note_map'): MusicClock(no_notes).notes('keys')

    def test_source_hash_and_rounded_bar_starts(self):
        data = {'bpm': 137, 'duration': 8, 'bars': [[1, 0, 4], [2, 1.752, 3], [3, 3.066, 6]]}
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'music.beats.json'; p.write_text(json.dumps(data))
            c = MusicClock.load(p)
            self.assertEqual(c.source['sha256'], hashlib.sha256(p.read_bytes()).hexdigest())
            self.assertEqual(c.at(1, 5), 1.752)
            self.assertEqual(js_result(data, [[1, 5]])['times'], [1.752])


class FilmClockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='vh-music-clock-')
        self.addCleanup(self.tmp.cleanup)
        self.p = Path(self.tmp.name) / 'film'
        shutil.copytree(ROOT / 'engines/canvas-film/template', self.p)
        html = self.p / 'film.html'
        # Timing tests use system fallback text; font availability has its own CI fixtures.
        html.write_text(re.sub(r'@font-face\s*\{[^}]*\}', '', html.read_text()))
        (self.p / 'src/50-shots.js').write_text('''Object.assign(FILM, {timeline:false, music:'audio/music.beats.json',
width:320,height:180,tail:99,lead:9,fadeOut:0,grain:0,images:{}});
const CHAPTERS=[{at:0,title:'A'},{at:musicAt(3),title:'B'}];
const COVERS=[{id:'end',at:musicAt(3,2)}];
function paint(t,s){rect(0,0,W,H,{fill:'#111'});label(t,s.t0,'A',16,70,{size:44});
const at=musicT(2,2); rect(20,100,10+at,10,{fill:'#fff'}); musicNotesT('keys');}
const SHOTS=[{id:'S01',at:0,draw:paint},{id:'S04a',at:musicAt(2),o:{hit:musicAt(3,2)},draw:paint},
{id:'end',at:musicAt(3),draw:paint}];''')
        self.map = self.p / 'audio/music.beats.json'
        self.write_map(120)

    def write_map(self, bpm):
        beat = 60 / bpm
        self.map.write_text(json.dumps({'bpm': bpm, 'duration': 10 * beat,
            'bars': [[1, 0, 1], [2, beat, 3], [3, 4 * beat, 6]],
            'notes': [{'part': 'keys', 't': beat, 'end': beat * 2, 'midi': 60}]}))

    def vh(self, *args, code=0):
        r = subprocess.run([os.environ.get('VH_BASH', 'bash'), str(ROOT / 'bin/vh'), *map(str, args)], capture_output=True, text=True)
        self.assertEqual(r.returncode, code, r.stdout + r.stderr)
        return r.stdout + r.stderr

    def test_one_map_moves_cues_reads_chapters_and_preserves_determinism(self):
        self.vh('cues', self.p, '--save')
        first = json.loads((self.p / 'out/cues.json').read_text())
        self.assertEqual(first['music']['sha256'], hashlib.sha256(self.map.read_bytes()).hexdigest())
        self.assertEqual(next(c['t'] for c in first['cues'] if c['id'] == 'S04a.at'), 0.5)
        self.vh('readcheck', self.p, '--export')
        reads = json.loads((self.p / 'out/texts.json').read_text())
        self.write_map(60)
        output = self.vh('cues', self.p, '--save')
        self.assertIn('music map changed', output)
        second = json.loads((self.p / 'out/cues.json').read_text())
        self.assertEqual(next(c['t'] for c in second['cues'] if c['id'] == 'S04a.at'), 1)
        self.assertEqual(next(c['t'] for c in second['cues'] if c['id'] == 'chapter2.at'), 4)
        self.vh('readcheck', self.p, '--export', '--force')
        self.assertNotEqual(reads, json.loads((self.p / 'out/texts.json').read_text()))
        self.vh('frames', self.p, '--at', '1.5,4.5', '--out', self.p / 'out/order')
        self.vh('frames', self.p, '--at', '4.5', '--out', self.p / 'out/alone')
        ordered = next((self.p / 'out/order').glob('*t0004.500.png'))
        alone = next((self.p / 'out/alone').glob('*t0004.500.png'))
        self.assertEqual(ordered.read_bytes(), alone.read_bytes())
        self.vh('frames', self.p, '--at', '10', code=2)  # the map sets duration; voice lead/tail were not added

    def test_missing_map_and_bad_bar_fail_in_ready(self):
        d = json.loads(self.map.read_text()); d.pop('bars'); self.map.write_text(json.dumps(d))
        self.assertIn('no bars table', self.vh('cues', self.p, code=2))
        self.write_map(120)
        p = self.p / 'src/50-shots.js'; p.write_text(p.read_text().replace('at:musicAt(2)', 'at:musicAt(99)'))
        self.assertIn('no bar 99', self.vh('cues', self.p, code=2))
        self.map.unlink()
        self.assertIn('HTTP 404', self.vh('cues', self.p, code=2))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(FilmClockTests if '--film' in sys.argv else ClockTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
