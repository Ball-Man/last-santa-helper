from cx_Freeze import setup, Executable
import sys

TARGET = 'last_santa'
ICON = 'resources/image/toys/lightbulb.png'
EXCLUDE = ['tkinter', 'ssl', 'html', 'xml', 'xmlrpc', 'email',
           'distutils', 'concurrent', 'multiprocessing', 'http', 'lib2to3',
           'unittest', 'asyncio', 'pydoc_data']
INCLUDE_FILES = ['resources']

build_options = {'excludes': EXCLUDE, 'optimize': 2,
                 'include_files': INCLUDE_FILES}

base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable('main.py', base=base, target_name=TARGET, icon=ICON),
]

setup(name='L\'ultimo aiutante di Babbo Natale',
      version='1.0.0',
      description='',
      options={'build_exe': build_options},
      executables=executables)
