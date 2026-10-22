"""Copy only frozen retrieval inputs; does not create an OS sandbox."""
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    if target == ROOT or ROOT in target.parents:
        parser.error('Choose an input directory outside this repository.')
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        parser.error('Output must be an empty directory to avoid retaining answers.')
    target.mkdir(parents=True, exist_ok=True)
    for name in ('histories.jsonl', 'rounds.jsonl', 'queries.jsonl'):
        shutil.copyfile(ROOT / 'public' / name, target / name)
    print(f'Copied three Public inputs to {target}. Apply OS isolation separately.')


if __name__ == '__main__':
    main()

