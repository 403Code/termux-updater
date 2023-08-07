#!/usr/bin/env python

import os
import sys
import tempfile
import bs4
import requests
import time
import math

parser = lambda resp: bs4.BeautifulSoup(resp, 'html.parser')
versioning = lambda vers: '.'.join(map(str, vers))
version_parse = lambda version_str: tuple(map(int, version_str.split('.'))) if '.' in version_str else None
terminal_columns = lambda: os.get_terminal_size().columns

program = "termux-updater"

__doc__ = '''
Usage:
  {0} [OPTIONS]
  {0} [--help | -h | -v | --version]

Example:
  {0}    # update termux app if exists

Options:
  -h, --help        show this messages
  -v, --version     show tool version
  -q, --quiet       hide the output if there is no update
'''.format(program)

__version__ = '1.0.0'

def convert_size(size_bytes) -> str:
	if size_bytes == 0: return "0B"
	size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
	i = int(math.floor(math.log(size_bytes, 1024)))
	p = math.pow(1024, i)
	s = round(size_bytes / p, 2)
	return "%s%s" % (s, size_name[i])

class Updater():
	url = 'https://f-droid.org/id/packages/com.termux/'
	req = requests

	def __init__(self) -> None:
		self.quiet = False
		args = sys.argv[1:]
		for arg in args:
			arg = arg.strip()
			if arg in ('-h', '--help'):
				exit(__doc__)
			elif arg in ('-v', '--version'):
				exit(__version__)
			elif arg in ('-q', '--quiet'):
				self.quiet = True
			else:
				exit(f'{program}: options with {repr(arg)} not recognized.\n{__doc__}')
		try: version, link, size = self.parse_latest_version(self.req.get(self.url).content)
		except: exit(f'[{program}] failed to fetch data.')
		current_release, current_version = self.application_info()
		if current_release != 'F_DROID': print ('[warning] you installed termux not from f-droid.')
		' Control version update '
		if current_version < version:
			print ('\n'.join([
				'[*] update available!',
				f'[*] version: {versioning(version)}',
				f'[*] size: {size}',
				'[!] note: we use temporary file to',
				'          write data, so if you',
				'          cancel the install, you',
				'          must download it again.'
			]))
			choose = 'x'
			while choose not in ['y', 'n']:
				try:
					choose = input('[*] download and install now? [y/n]: ').strip().lower()
					if len(choose) != 0 and choose[0] == 'y':
						self.download_and_install(link, size)
					else: break
				except (KeyboardInterrupt, EOFError):
					exit()
		else:
			exit(0 if self.quiet else '[*] Hooray, you installed latest version!')

	def download_and_install(self, link, dummy_size) -> None:
		block_size = 512
		data = self.req.get(link, stream = True)
		dummy_size = ((int(dummy_size.split()[0]) + 1) * 0x100000) # content-length handle which 1 mebibyte is 1048576 bytes.
		web_size = int(data.headers.get('content-length') or 0)
		size = web_size if web_size != 0 else dummy_size
		temp = tempfile.NamedTemporaryFile(delete = False, suffix = '.apk')
		step = 1
		start = time.time()
		for chunk in data.iter_content(chunk_size = block_size):
			if not chunk: break
			duration = time.time() - start
			progress = int(step * block_size)
			if duration == 0: duration = 0.1
			speed = int(progress / (1024 * duration))
			percent = int(step * block_size * 100 / size)
			animate = '\r[*] %d%% • %s/%s • %s/s' % (percent, convert_size(progress), convert_size(size), convert_size(speed * 1024))
			animate += (terminal_columns() - len(animate)) * ' '
			print(animate, flush = True, end = '\r')
			temp.write(chunk)
			step += 1
		time.sleep(1)
		os.system('xdg-open %s' % temp.name)
		temp.close()

	def parse_latest_version(self, data) -> None:
		parse = parser(data)
		package = parse.find('li', {'class': 'package-version', 'id': 'latest'})
		download = package.find('p', {'class': 'package-version-download'})
		latest_version = version_parse(self.get_version(package))
		latest_link = self.get_link(download)
		latest_size = self.get_size(download)
		return (latest_version, latest_link, latest_size)

	def get_version(self, parse) -> str:
		for name in parse.findAll('a', {'name': True}):
			if version_parse(name['name']): break
			else: continue
		return name['name']

	def get_link(self, parse) -> str:
		for link in parse.findAll('a'):
			res = link['href'] if link['href'].endswith('.apk') else False
			if res is not False: break
		return res

	def get_size(self, parse) -> str:
		" Maybe in the future this parsing not working. "
		raw_text = parse.text
		for a_link in parse.findAll('a'):
			raw_text = raw_text.replace(a_link.text, '').strip()
		return raw_text[:-1].strip()

	def application_info(self) -> tuple:
		try: return (os.environ['TERMUX_APK_RELEASE'], version_parse(os.environ['TERMUX_VERSION']))
		except: exit('[!] you are running this not in termux.')
