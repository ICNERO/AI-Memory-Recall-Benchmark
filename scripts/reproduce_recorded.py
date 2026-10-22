"""Replay archived predictions and compare against restored original scores."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METHODS = ('random', 'earliest', 'latest', 'bm25', 'tfidf', 'bm25_first_frame')


def normalized_summary(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    if 'private_gold_sha256' in data:
        data['published_gold_sha256'] = data.pop('private_gold_sha256')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/replayed')
    args = parser.parse_args()
    out = args.output.resolve()
    if out == ROOT or ROOT / 'results' == out or ROOT / 'results' in out.parents:
        parser.error('Do not overwrite the repository or archived results.')
    checks = []
    for method in METHODS:
        destination = out / method
        subprocess.run([sys.executable, '-m', 'r2bench', 'score', '--predictions',
                        str(ROOT / 'results/raw' / (method + '.jsonl')),
                        '--output', str(destination)], cwd=ROOT, check=True)
        expected = ROOT / 'results/scores' / method
        files = {name: (destination / name).read_bytes() == (expected / name).read_bytes()
                 for name in ('per_query.jsonl', 'failures.jsonl', 'excluded_queries.jsonl')}
        files['summary.json_normalized'] = normalized_summary(destination / 'summary.json') == normalized_summary(expected / 'summary.json')
        checks.append({'method': method, 'files': files})
    report = {'recorded_predictions': 3000, 'all_equal': all(all(c['files'].values()) for c in checks),
              'scope': 'Recorded-output replay; not new timing or independent semantic review', 'checks': checks}
    out.mkdir(parents=True, exist_ok=True)
    (out / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))
    if not report['all_equal']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

