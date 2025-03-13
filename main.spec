# main.spec

datas = [    
    ('templates/*', 'templates'),  
    ('static/*', 'static'),        
    ('donation_history.txt', '.')]

a = Analysis(
    ['main.py'],
    pathex=[], 
    binaries=[],
    datas=datas,
    hiddenimports=[
        'engineio.async_drivers.gevent',
        'gevent',
        'gevent.monkey',
        'gevent.socket',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    icon='static/AWicon.ico',  
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FundRacer',  
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, 
    icon='static/AWicon.ico',  
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FundRacer',  
)