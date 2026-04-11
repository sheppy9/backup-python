import os
import shutil
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables once at module level
load_dotenv()
CONFIG = os.getenv('CONFIG', 'files.csv')
DT_FORMAT = os.getenv('DT_FORMAT', '%Y%m%d-%H%M%S')
DEFAULT_BACKUP_DIR = os.getenv('DEFAULT_BACKUP_DIR', '.')

def parse_config(config_path):
    path = Path(config_path).expanduser()
    if not path.is_file():
        print(f'FileNotFound. {path}')
        return []

    pairs = []
    try:
        with path.open('r') as f:
            # Skip header line
            next(f, None)
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Fast split without regex
                idx = line.find(',')
                if idx == -1:
                    idx = line.find(';')

                if idx != -1:
                    src = line[:idx].strip()
                    dest = line[idx+1:].strip()
                    pairs.append((src, dest))
    except Exception as e:
        print(f'Error reading config: {e}')

    return pairs


def collect_files(src_path, dest_base):
    tasks = []

    if src_path.is_file():
        tasks.append((src_path, dest_base))
    elif src_path.is_dir():
        # Optimized directory traversal
        try:
            for file in src_path.rglob('*'):
                if file.is_file():
                    rel_dir = file.relative_to(src_path).parent
                    tasks.append((file, dest_base / rel_dir))
        except Exception as e:
            print(f'Error scanning {src_path}: {e}')

    return tasks


def backup_file_fast(src, dest):
    try:
        # Create destination directory if needed
        if not dest.exists():
            dest.mkdir(parents=True, exist_ok=True)

        # Use copy2 which preserves metadata
        shutil.copy2(src, dest)
        return True
    except Exception as e:
        print(f'Error backing up {src} to {dest}: {e}')
        return False


def do_backup_optimized(config_path):
    outdir = datetime.now().strftime(DT_FORMAT)

    config_pairs = parse_config(config_path)
    if not config_pairs:
        return 0

    # Collect all backup tasks
    all_tasks = []
    for src_str, dest_str in config_pairs:
        src = Path(src_str)

        if not src.exists():
            print(f'Resource does not exists: {src}')
            continue

        # Determine destination
        dest_base = Path(dest_str if dest_str else DEFAULT_BACKUP_DIR).expanduser() / outdir

        # Collect tasks for this source
        all_tasks.extend(collect_files(src, dest_base))

    if not all_tasks:
        return 0

    # Execute backups in parallel with optimized thread pool
    success_count = 0
    with ThreadPoolExecutor(max_workers=8) as executor:
        # Submit all tasks
        future_to_task = {
            executor.submit(backup_file_fast, src, dest): (src, dest)
            for src, dest in all_tasks
        }

        # Collect results as they complete
        for future in as_completed(future_to_task):
            try:
                if future.result():
                    success_count += 1
            except Exception as e:
                src, dest = future_to_task[future]
                print(f'Task failed for {src}: {e}')

    return success_count


if __name__ == '__main__':
    start = datetime.now()

    count = do_backup_optimized(CONFIG)

    elapsed = datetime.now() - start
    print(f'Backup completed for {count} resources, took {elapsed}')
