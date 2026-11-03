"""Contract checks for source merges and the final decoded APK.

Unknown future implementations still require review; this is not a general
proof of runtime behavior. No vehicle settings or services are changed.
"""
import argparse
import ast
import re
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = 'Abro86/gen5-SmartTube'
UPDATE_URL = f'https://github.com/{REPO}/releases/latest/download/smarttube-gen5w.json'
MARKERS = ('DrivingGuard', 'com.hkmc.regulation', 'com/hkmc/regulation',
           'ACTION_ENTER_REGULATION', 'AUTOMOTIVE_REGULATION')

def check_source(root):
    conf = (root/'smarttube.conf').read_text()
    if f'UPDATE_REPO="{REPO}"' not in conf:
        raise ValueError('Fork update feed changed; review required')
    if not re.search(r'^SIGNING_CERT_SHA256="[0-9a-f]{64}"$', conf, re.M):
        raise ValueError('A fixed signing certificate is required')
    descriptor = (root/'package/NEMESIS.data').read_text()
    if '\nid=local.abro.smarttube\n' not in descriptor:
        raise ValueError('Fork NEMESIS package identity changed')
    tree = ast.parse((root/'tools/patch.py').read_text())
    calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    required = {'patch_get_tasks', 'patch_conscrypt', 'patch_update_urls',
                'patch_version_code', 'patch_edge_slide', 'patch_slider_layout'}
    if not required <= calls or 'patch_driving_guard' in calls:
        raise ValueError('Compatibility patch set changed')

def check_decoded(root, url):
    if url != UPDATE_URL:
        raise ValueError('Only the fork update feed is allowed')
    files = [root/'AndroidManifest.xml'] + sorted(root.glob('smali*/**/*.smali'))
    if len(files) < 2:
        raise ValueError('Decoded dex files are missing')
    for p in files:
        text = p.read_text(encoding='utf-8')
        for marker in MARKERS:
            if marker in text:
                raise ValueError(f'Regulation marker {marker} in {p.relative_to(root)}; review required')
    manifest = ET.parse(root/'AndroidManifest.xml')
    android = '{http://schemas.android.com/apk/res/android}'
    permissions = {e.get(android+'name') for e in manifest.findall('uses-permission')}
    if 'android.permission.GET_TASKS' not in permissions:
        raise ValueError('GET_TASKS compatibility fix missing')
    arrays = ET.parse(root/'res/values/arrays.xml')
    feeds = [e for e in arrays.getroot() if e.tag == 'string-array' and e.get('name') == 'update_urls']
    if len(feeds) != 1 or [e.text for e in feeds[0]] != [url]:
        raise ValueError('APK update feed does not match the fork')
    def one(name):
        matches = list(root.glob(f'smali*/**/{name}.smali'))
        if len(matches) != 1:
            raise ValueError(f'Expected one {name}, got {len(matches)}')
        return matches[0].read_text()
    net = one('NetworkData')
    method = re.search(r'\.method public isConscryptEnabled\(\)Z\n(.*?)\.end method', net, re.S)
    if not method or 'const/4 v0, 0x1' not in method[1] or 'return v0' not in method[1]:
        raise ValueError('Conscrypt compatibility fix missing')
    mother = one('MotherActivity')
    edge = re.search(r'\.method private initEdgeSlide\(\)V\n(.*?)\.end method', mother, re.S)
    if not edge or 'const/16 v1, 0x13' not in edge[1] or 'Lcom/r0adkll/slidr/Slidr;->attach' not in edge[1]:
        raise ValueError('KitKat Back gesture fix missing')
    slider = one('SliderPanel')
    if ' onLayout(ZIIII)V' not in slider or '->offsetLeftAndRight(I)V' not in slider:
        raise ValueError('Back gesture relayout fix missing')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path)
    parser.add_argument('--decoded', type=Path)
    parser.add_argument('--url', default=UPDATE_URL)
    args = parser.parse_args()
    if not args.source and not args.decoded:
        parser.error('provide --source or --decoded')
    try:
        if args.source:
            check_source(args.source)
        if args.decoded:
            check_decoded(args.decoded, args.url)
    except (ValueError, OSError, ET.ParseError) as e:
        raise SystemExit(f'Fork verification failed: {e}')
    print('Fork contract verified')

if __name__ == '__main__':
    main()
