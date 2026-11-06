"""Regression: a clean world needs its system boss but must exclude player saves."""
import json
import runpy
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


class CleanWorldTest(unittest.TestCase):
    def test_keeps_system_boss_and_excludes_private_data(self):
        script = Path(__file__).resolve().parents[1] / 'scripts/export_world.py'

        def mysql(args, input, **kwargs):
            query = input.decode('utf-8')
            if query == 'SHOW TABLES;':
                output = 'account\nplayer'
            elif query.startswith('SHOW COLUMNS'):
                output = 'id\tint\tNO\tPRI\tNULL\tauto_increment\nname\tvarchar(32)\tYES\t\tNULL\t'
            elif 'FROM `player`' in query:
                rows = [[-1, 'system-boss']]
                if 'WHERE `id` = -1' not in query:
                    rows.append([7, 'private-character'])
                output = '\n'.join(json.dumps(row) for row in rows)
            else:
                self.fail('Exporter queried private table: ' + query)
            return subprocess.CompletedProcess(args, 0, output.encode('utf-8'), b'')

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'data').mkdir()
            config = root / 'hso.conf'
            config.write_text('port: 1\nmysql-host: original\nmysql-password: private\n', encoding='utf-8')
            argv = [str(script), '--mysql', 'mysql', '--defaults', 'local.ini', '--database', 'test',
                    '--data', str(root / 'data'), '--config', str(config), '--out', str(root / 'output')]
            with patch.object(sys, 'argv', argv), patch('subprocess.run', side_effect=mysql):
                runpy.run_path(str(script), run_name='__main__')
            with sqlite3.connect(root / 'output/hso.sqlite') as db:
                self.assertEqual(db.execute('SELECT * FROM player').fetchall(), [(-1, 'system-boss')])
                self.assertEqual(db.execute('SELECT COUNT(*) FROM account').fetchone()[0], 0)
            db.close()
            with zipfile.ZipFile(root / 'output/offline-world.zip') as z:
                self.assertNotIn('private', z.read('hso.conf').decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
