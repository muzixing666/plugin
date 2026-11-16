"""Build the standalone panel plugin from the readable wrapper and engine."""
import base64
import gzip
import hashlib
from pathlib import Path
import textwrap

root = Path(__file__).resolve().parent
engine = (root / 'microsoft_rewards_engine.js').read_bytes()
source = (root / 'bing_rewards_plugin_source.py').read_text(encoding='utf-8')
encoded = base64.b64encode(gzip.compress(engine, mtime=0)).decode('ascii')
payload = 'ENGINE_DATA = (\n' + ''.join('    ' + repr(line) + '\n' for line in textwrap.wrap(encoded, 100)) + ')'
source = source.replace('ENGINE_DATA = None', payload, 1)
source = source.replace('ENGINE_SHA256 = None', 'ENGINE_SHA256 = ' + repr(hashlib.sha256(engine).hexdigest()), 1)
(root.parent / 'plugins' / '必应积分任务.py').write_text(source, encoding='utf-8')
