"""Export a private MySQL world for the Android SQLite backend. Does not upload anything."""
import argparse,json,re,sqlite3,subprocess,zipfile
from pathlib import Path

p=argparse.ArgumentParser()
for name in ['mysql','defaults','data','config','out']:p.add_argument('--'+name,type=Path,required=True)
p.add_argument('--database',required=True)
p.add_argument('--include-private-save',action='store_true')
a=p.parse_args()
if a.out.exists():raise SystemExit('Output already exists; use a new path.')
a.out.mkdir(parents=True)
def sql(query):
    result=subprocess.run([str(a.mysql),'--defaults-file='+str(a.defaults),'--default-character-set=utf8mb4',
        '--batch','--raw','-N',a.database],input=query.encode('utf-8'),capture_output=True,check=True)
    return result.stdout.decode('utf-8').rstrip('\r\n')
private={'account','player','clan','naptien','pet','wedding','giftcode'}
database=a.out/'hso.sqlite'
with sqlite3.connect(database) as db:
    for table in sql('SHOW TABLES;').splitlines():
        if not re.fullmatch(r'[a-zA-Z0-9_]+',table):raise ValueError('Unexpected table name')
        cols=[line.split('\t') for line in sql('SHOW COLUMNS FROM `'+table+'`;').splitlines()]
        primary=[c[0] for c in cols if c[3]=='PRI'];definitions=[];binary=[]
        for name,typ,nullable,key,default,extra in cols:
            if not re.fullmatch(r'[a-zA-Z0-9_]+',name):raise ValueError('Unexpected column name')
            typ=typ.lower();kind='INTEGER' if 'int' in typ else 'REAL' if any(x in typ for x in ['float','double','decimal']) else 'BLOB' if 'blob' in typ or 'binary' in typ else 'TEXT'
            binary.append(kind=='BLOB');definition='"'+name+'" '+kind
            if len(primary)==1 and primary[0]==name:
                definition+=' PRIMARY KEY'
                if kind=='INTEGER' and 'auto_increment' in extra:definition+=' AUTOINCREMENT'
            elif key=='UNI':definition+=' UNIQUE'
            definitions.append(definition)
        if len(primary)>1:definitions.append('PRIMARY KEY ('+','.join('"'+x+'"' for x in primary)+')')
        db.execute('CREATE TABLE "'+table+'" ('+','.join(definitions)+')')
        if table in private and not a.include_private_save and table!='player':continue
        fields=','.join(('HEX(`'+c[0]+'`)' if binary[i] else '`'+c[0]+'`') for i,c in enumerate(cols))
        rows=[]
        # id=-1 is the server's world-boss template, not a player save. Startup needs it.
        where=' WHERE `id` = -1' if table=='player' and not a.include_private_save else ''
        for line in sql('SELECT JSON_ARRAY('+fields+') FROM `'+table+'`'+where+';').splitlines():
            row=json.loads(line)
            for i,b in enumerate(binary):
                if b and row[i] is not None:row[i]=bytes.fromhex(row[i])
            rows.append(row)
        if rows:db.executemany('INSERT INTO "'+table+'" VALUES ('+','.join('?' for _ in cols)+')',rows)
    db.commit();assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
db.close()
with zipfile.ZipFile(a.out/'offline-world.zip','w',zipfile.ZIP_DEFLATED) as archive:
    archive.write(database,'hso.sqlite')
    config=a.config.read_text(encoding='utf-8-sig')
    for key,value in [('port','19139'),('mysql-host','127.0.0.1'),('mysql-password','offline')]:
        config=re.sub(r'(?m)^'+key+r':.*$',key+': '+value,config)
    archive.writestr('hso.conf',config)
    for file in a.data.rglob('*'):
        if file.is_file():archive.write(file,'data/'+file.relative_to(a.data).as_posix())
print('Private local world:',a.out/'offline-world.zip')
print('Player/account data included:',a.include_private_save)
