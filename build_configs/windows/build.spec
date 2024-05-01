# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata

datas = [
    ('..\\..\\staking_deposit\\key_handling\\key_derivation\\word_lists\\*.txt', '.\\staking_deposit\\key_handling\\key_derivation\\word_lists'),
    ('..\\..\\staking_deposit\\intl', '.\\staking_deposit\\intl'),
]
datas += copy_metadata('py_ecc')
datas += copy_metadata('ssz')

block_cipher = None


a = Analysis(['..\\..\\staking_deposit\\deposit.py'],
             binaries=[],
             datas=datas,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='deposit',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
