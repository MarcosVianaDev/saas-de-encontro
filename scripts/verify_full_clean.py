import tempfile, shutil
from pathlib import Path
from types import SimpleNamespace
project_root = Path(__file__).resolve().parents[1]
blocks = []
for name in ('full-clean.ps1', 'full-clean.sh'):
    source = (project_root / name).read_text(encoding='utf-8-sig')
    start = source.index('backend_root = Path(settings.BASE_DIR).resolve()')
    end = source.index('with transaction.atomic():', start)
    blocks.append((name, source[start:end]))
for name, code in blocks:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / 'backend'
        root.mkdir()
        backups = root / 'backups'
        backups.mkdir()
        (backups / 'nested').mkdir()
        (backups / 'nested' / 'term.pdf').write_bytes(b'test')
        (backups / '.hidden.zip').write_bytes(b'test')
        media = root / 'media'
        media.mkdir()
        (media / 'photo.jpg').write_bytes(b'preserved')
        outside = Path(temp) / 'outside'
        outside.mkdir()
        (outside / 'keep.txt').write_text('preserved')
        (backups / 'external-link').symlink_to(outside, target_is_directory=True)
        settings = SimpleNamespace(BASE_DIR=root)
        namespace = {'Path': Path, 'shutil': shutil, 'settings': settings}
        exec(code, namespace)
        assert backups.is_dir() and not list(backups.iterdir())
        assert (media / 'photo.jpg').read_bytes() == b'preserved'
        assert (outside / 'keep.txt').exists()
        exec(code, namespace)
        backups.rmdir()
        backups.symlink_to(outside, target_is_directory=True)
        try:
            exec(code, namespace)
            raise AssertionError('Root symlink was accepted')
        except RuntimeError:
            pass
        assert (outside / 'keep.txt').exists()
        backups.unlink()
        exec(code, namespace)
        assert backups.is_dir()
        print(name + ': contents removed, directory/media/external targets preserved; repeat and missing path verified.')
