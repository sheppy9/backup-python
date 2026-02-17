import re
import os
import shutil

from glob import glob
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

def get_files(config):
	files = []
	if config is None or len(config) == 0:
		return files

	path = Path(config).expanduser()
	if not path.exists() or not path.is_file():
		print(f'FileNotFound. {path}')
		return files

	with path.open() as infile:
		for line in infile.readlines()[1:]:
			yield line.strip()

def get_from_src(src):
	if src is None:
		return []
	if src.is_file():
		# if it's file, return None
		return None
	if not src.exists() or not src.is_dir():
		return []
	return [Path(_) for _ in glob(f'{src}/**/*', recursive=True) if Path(_).is_file()]

def backup_file(src, dest, resources):
	print(f'Backing up file {src} to {dest}')
	try:
		dest.mkdir(parents=True, exist_ok=True)
		shutil.copy2(src, dest)
		resources.append(dest)
	except:
		print(f'Error backing up {src} to {dest}')

def do_backup(lines):
	resources = []
	outdir = datetime.now().strftime(os.getenv('DT_FORMAT', '%Y%m%d-%H%M%S'))

	backup_pair = []
	for line in lines:
		src, dest = re.split(f'[,;]', line)

		src = Path(src.strip())
		if not src.exists():
			print(f'Resource does not exists: {src}')
			continue

		dest = dest.strip()
		if len(dest) == 0:
			# When no destination provided, use default defined in .env, else use current directory
			dest = os.getenv('DEFAULT_BACKUP_DIR', dest)

		dest = Path(dest.strip()).expanduser() / outdir

		files = get_from_src(src)
		if files is None:
			backup_pair.append((src, dest))
		else:
			for file in files:
				to_dir = dest / file.relative_to(src)
				backup_pair.append((file, to_dir.parent))

	with ThreadPoolExecutor(max_workers=8) as executor:
		for src, dest in backup_pair:
			executor.submit(backup_file, src, dest, resources)
	return resources

if __name__ == '__main__':
	start = datetime.now()

	files = get_files(os.getenv('CONFIG', 'files.csv'))
	resources = do_backup(files)

	print(f'Backup completed for {len(resources)} resources, took {datetime.now() - start}')
