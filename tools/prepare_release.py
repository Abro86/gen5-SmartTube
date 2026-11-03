"""Select a verified stable APK and stop when port source needs review."""
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def get(path):
    req = urllib.request.Request('https://api.github.com/'+path, headers={
        'Accept': 'application/vnd.github+json',
        'Authorization': 'Bearer '+os.environ['GH_TOKEN'],
        'User-Agent': 'Abro-SmartTube-maintenance'})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def main():
    base = json.loads((ROOT/'upstream-base.json').read_text())
    repo = os.environ['GITHUB_REPOSITORY']
    if repo != 'Abro86/gen5-SmartTube':
        raise SystemExit('Configure fork identity explicitly before running elsewhere')
    current = get(f'repos/{base["port_repository"]}/commits/main')['sha']
    if current != base['port_commit']:
        raise SystemExit('Gen5W port changed; review its diff and update upstream-base.json before building. No source is automatically merged.')
    tag = os.environ.get('INPUT_UPSTREAM_TAG', '').strip()
    if tag and not re.fullmatch(r'[0-9]+(?:\.[0-9]+)*s?', tag):
        raise SystemExit('Use a numeric stable upstream tag, e.g. 32.68s')
    release = get('repos/yuliskov/SmartTube/releases/'+('tags/'+tag if tag else 'latest'))
    if release['draft'] or release['prerelease']:
        raise SystemExit('Only stable upstream releases are accepted')
    tag = release['tag_name']
    if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)*s?', tag):
        raise SystemExit('Unexpected upstream stable tag')
    assets = [a for a in release['assets'] if a['name'].endswith('_armeabi-v7a.apk') and 'stable' in a['name'].lower()]
    if len(assets) != 1 or not re.fullmatch(r'sha256:[0-9a-f]{64}', assets[0].get('digest') or ''):
        raise SystemExit('Expected one stable ARM APK with GitHub SHA256')
    version = tag.removesuffix('s')
    revision = os.environ.get('INPUT_REVISION', '').strip() or str(base['fork_revision'])
    if not re.fullmatch(r'[0-9]+', revision) or not 51 <= int(revision) <= 99:
        raise SystemExit('Fork revisions must be 51-99')
    fork_tag = f'v{version}-gen5w.{revision}'
    # Include drafts. A completed draft is not rebuilt by the next scheduled run.
    found = False
    page = 1
    while True:
        items = get(f'repos/{repo}/releases?per_page=100&page={page}')
        if any(r['tag_name'] == fork_tag for r in items):
            found = True
            break
        if len(items) < 100:
            break
        page += 1
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as out:
        for k,v in {'needed':str(not found).lower(), 'upstream_tag':tag,
                    'version':version, 'revision':revision, 'tag':fork_tag}.items():
            out.write(f'{k}={v}\n')
    (ROOT/'build-provenance.json').write_text(json.dumps({
        'fork_commit':os.environ['GITHUB_SHA'], 'gen5w_port_commit':current,
        'upstream_tag':tag, 'upstream_asset':assets[0]['browser_download_url'],
        'upstream_sha256':assets[0]['digest'], 'fork_tag':fork_tag,
        'vehicle_tested':False}, indent=2)+'\n')
    print(f'{fork_tag}: '+('already built' if found else 'build candidate'))

if __name__ == '__main__':
    main()
