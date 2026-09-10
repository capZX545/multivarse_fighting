# PyInstaller spec — دسکتاپ
# -*- mode: python ; coding: utf-8 -*-
import os
block_cipher = None
a = Analysis(['main.py'], pathex=['.'], binaries=[],
             datas=[('assets', 'assets'), ('pyfighter/data/characters.json', 'pyfighter/data')],
             hiddenimports=['pygame', 'numpy', 'pyfighter.characters.gojo', 'pyfighter.characters.naruto'],
             hookspath=[], runtime_hooks=[], excludes=['tkinter', 'scipy', 'PIL'],
             cipher=block_cipher, noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
          name='MultivarseFighting', debug=False, strip=False, upx=True, console=False)
