import re
import os
import csv
import shutil
import asyncio

from pathlib import Path
from datetime import datetime

SOURCE_FILE = 'files.csv'
BACKUP_DIR = './backup'
DATE_TIME_FORMAT = '%Y%m%d %H%M%S'

# Create backup folder
datetime_folder = datetime.now().strftime(DATE_TIME_FORMAT)

def setup():
	srcfile = Path(SOURCE_FILE)
	if not srcfile.exists():
		required_setup = input(f'[{datetime.now()}] {SOURCE_FILE} not found. proceed to setup [y/n]? ')
		if len(required_setup) == 0 or required_setup.lower() != 'y':
			return
		
		separator = os.sep
		split_regex = r'[\\/]'
		configs = {}
		while True:
			src = input(f'[{datetime.now()}] Enter source [enter to complete]: ')
			if len(src) == 0:
				break

			dest = input(f'[{datetime.now()}] Enter destination: ')
			if len(dest) == 0:
				dest = ''
			
			src = src.replace('"', '').replace("'", '')
			dest = dest.replace('"', '').replace("'", '')

			src = separator.join(re.split(split_regex, src))
			dest = separator.join(re.split(split_regex, dest))
			configs[src] = dest

		if len(configs) == 0:
			return

		with open(srcfile, 'w+') as outfile:
			outfile.write('source,destination\n')
			for src, dest in configs.items():
				outfile.write(f'{src},{dest}\n')
		print(f'[{datetime.now()}] {SOURCE_FILE} created.')

def read_files():
	srcfile = Path(SOURCE_FILE)
	if not srcfile.exists():
		print(f'[{datetime.now()}] {SOURCE_FILE} not found, nothing to backup.')
		return
	entries = {}
	sfile = open(SOURCE_FILE)
	for row in csv.DictReader(sfile):
		# Ensure source is provided
		src = row.get('source', '').strip()
		if len(src) <= 0:
			continue

		# Ensure given source exists
		srcpath = Path(src)
		if not srcpath.exists():
			continue

		# Ensure given source is either file or folder
		if not srcpath.is_file() and not srcpath.is_dir():
			print(f'[{datetime.now()}] Given entry is neither file or folder. {src}')
			continue

		# Check for duplication
		srcname = srcpath.name
		if srcname in entries:
			print(f'[{datetime.now()}] Found duplicated file/ folder for backup, skipping backup from {src}')
			continue

		# Get destination and use default if not provided
		dest = row.get('destination').strip()
		if len(dest) <= 0:
			dest = BACKUP_DIR
			row['destination'] = str(Path(dest).absolute())
		
		entries[srcname] = row
	sfile.close()
	return entries

async def backup_single(entry):
	# Create destination directory
	dest = entry['destination']
	destpath = Path(f'{dest}/{datetime_folder}')
	destpath.mkdir(parents=True, exist_ok=True)

	src = entry['source']
	srcpath = Path(src)

	#  Join the source and destination path
	filename = Path(entry['source']).name
	backup_file = destpath.joinpath(filename)

	# Create backup
	if srcpath.is_file():
		# shutil.copy2(srcpath, backup_file)
		await asyncio.get_event_loop().run_in_executor(None, shutil.copy2, srcpath, backup_file)
	elif srcpath.is_dir():
		# shutil.copytree(srcpath, backup_file, dirs_exist_ok=True, copy_function=shutil.copy2)
		await asyncio.get_event_loop().run_in_executor(None, shutil.copytree, srcpath, backup_file)
	else:
		print(f'[{datetime.now()}] Failed to backup entry due to neither file or folder. {src}')
		return 'failed'
	print(f'[{datetime.now()}] Successful backup from: {src} to: {backup_file}')
	return 'success'

async def backup(entries):
	tasks = [backup_single(entry) for entry in entries.values()]
	return await asyncio.gather(*tasks)

setup()

print(f'[{datetime.now()}] Backup started')
entries = read_files()

if entries is not None and len(entries) > 0:
	results = asyncio.run(backup(entries))
	failed = list(filter(lambda x: x == 'failed', results))
	print(f'[{datetime.now()}] Backup completed. Failed count: {len(failed)}')
