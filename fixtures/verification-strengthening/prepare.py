"""Prepare isolated source-skill trial workspaces; never executes agents."""
import json
import shutil
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1]).resolve()
root.mkdir(parents=True, exist_ok=False)

def write(folder, name, body):
    path = folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)

def git(folder, *args):
    return subprocess.check_output(['git', '-C', str(folder), *args], text=True).strip()

def init(folder):
    folder.mkdir()
    git(folder, 'init', '-q')
    git(folder, 'config', 'user.name', 'Fixture')
    git(folder, 'config', 'user.email', 'fixture@example.invalid')

def commit(folder, message):
    git(folder, 'add', '.')
    git(folder, 'commit', '-qm', message)
    return git(folder, 'rev-parse', 'HEAD')

app = '''import json
import shutil
import sys
from pathlib import Path

def save(path, value):
    Path(path).write_text(json.dumps({'value': value}))

def load(path):
    return json.loads(Path(path).read_text())['value']

if __name__ == '__main__':
    save(sys.argv[1], sys.argv[2])
'''
a = root / 'target-a'; init(a)
write(a, 'store.py', app)
write(a, 'verify.py', '''import tempfile
from pathlib import Path
from store import save
with tempfile.TemporaryDirectory() as temp:
    path = Path(temp) / 'record.json'
    save(path, 'receipt')
    assert path.exists()
print('verified')
''')
write(a, 'README.md', 'The store persists the exact supplied string across a fresh process. Supported entry points are save(path, value) and python3 -B store.py PATH VALUE. load(path) reads it back. No services or dependencies.\n')
commit(a, 'Initial store')

b = root / 'target-b'; init(b)
write(b, 'settings.py', '''def select(items, limit=None):
    return items[:len(items) if limit is None else limit]

def ratio(total, count):
    return total / count
''')
write(b, 'README.md', 'select returns all items when limit is None, zero items when limit is 0, otherwise the first limit items. ratio returns 0 when count is 0, otherwise total/count.\n')
base_b = commit(b, 'Initial settings')
write(b, 'settings.py', '''def select(items, limit=None):
    return items[:limit or len(items)]

def ratio(total, count):
    return total / count
''')
patch_b = commit(b, 'Simplify selection')
write(b, 'change.diff', git(b, 'diff', base_b, patch_b) + '\n')

c = root / 'target-c'; init(c)
write(c, 'worker.py', '''def step(state, actor):
    phase = state['phase'][actor]
    if phase == 0:
        state['eligible'][actor] = not state['sent']
        state['phase'][actor] = 1
    elif phase == 1:
        if state['eligible'][actor]:
            state['deliveries'] += 1
            state['sent'] = True
        state['phase'][actor] = 2
''')
write(c, 'model.py', '''from itertools import permutations

def check():
    for order in permutations(range(2)):
        sent = False
        deliveries = 0
        for actor in order:
            if not sent:
                deliveries += 1
                sent = True
        assert deliveries <= 1
    print('all model schedules passed')

if __name__ == '__main__':
    check()
''')
write(c, 'README.md', 'The delivery worker promises at most one delivery across two actors. Each step(state, actor) call is atomic; a scheduler can alternate actors between calls. Initial state has phase=[0,0], eligible=[False,False], sent=False, deliveries=0. Run the existing verification with python3 -B model.py. The model predates the two-phase worker; no synchronized revision is recorded. Audit only.\n')
commit(c, 'Worker and existing model')

d = root / 'target-d'; init(d)
write(d, 'labels.py', '''def label(value):
    return 'unset' if not value else str(value)
''')
write(d, 'README.md', 'label(None) must return unset. Other inputs must return str(value), including 0 and the empty string. Reported issue: zero is displayed as unset.\n')
base_d = commit(d, 'Initial labels')
write(d, 'labels.py', '''def label(value):
    return 'unset' if value is None else str(value)
''')
patch_d = commit(d, 'Preserve zero label')
shutil.copytree(d, root / 'target-e')
print(json.dumps({'root': str(root), 'review': {'base': base_b, 'patch': patch_b}, 'fix': {'base': base_d, 'patch': patch_d}}, indent=2))
