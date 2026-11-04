import argparse,json,subprocess
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--mysql',type=Path,required=True);p.add_argument('--defaults',type=Path,required=True)
p.add_argument('--database',required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
if a.out.exists():raise SystemExit('Choose a new output path.')
columns={'item3':['id','name','type','clazz','icon','part','data'],
    'item4':['id','type','price','moneytype'],'item7':['id','type','price','moneytype']}
result={}
for table,names in columns.items():
    def column(name):
        if table=='item3' and name=='icon':return 'iconid'
        if table=='item4' and name=='type':return 'typepotion'
        if table=='item7' and name=='moneytype':return 'pricetype'
        return name
    fields=','.join("'"+name+"',`"+column(name)+'`' for name in names)
    query='SELECT JSON_OBJECT('+fields+') FROM `'+table+'` ORDER BY id;'
    process=subprocess.run([str(a.mysql),'--defaults-file='+str(a.defaults),'--default-character-set=utf8mb4','--batch','--raw','-N',a.database],
        input=query.encode('utf-8'),capture_output=True,check=True)
    result[table]=[json.loads(line) for line in process.stdout.decode('utf-8').splitlines()]
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
print('Exported template fixtures only:',a.out)
