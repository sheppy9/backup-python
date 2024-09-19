# Python Backup Script
A simple python script that helps to backup files/ folder.

Configuration is just a simple csv file (files.csv) with source and destination.

- Source
	- If file is provided, script will only backup a single file
	- If a folder is provided, script will backup the whole folder recursively
- Destination
	- If folder is provided, script will backup provided folder
	- If none is provided, script will automatically backup based on `BACKUP_DIR` (defaulted to `./backup` directory)

## Configuration
The following configuration can be updated according to preference, configuration is located on top of `backup.py`
- SOURCE_FILE (defaulted to 'files.csv')
- BACKUP_DIR (defaulted to './backup')
- DATE_TIME_FORMAT (defaulted to '%Y%m%d %H%M%S')


# Installation Guide
- Install python
- Download [backup.py](backup.py)
- Move to desired location
- Executing script by running `python backup.py`
	- script will automatically asked for source and destination for initial setup (if files.csv not found)
