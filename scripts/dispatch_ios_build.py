"""Build a private source revision on the public standard Mac runner without storing a PAT there."""
import argparse
import json
import shutil
import subprocess
import urllib.error
import urllib.request

p=argparse.ArgumentParser();p.add_argument('--ref',required=True);p.add_argument('--runner',choices=['macos-15','macos-26'],default='macos-15');a=p.parse_args()
gh=shutil.which('gh') or r'C:\Program Files\GitHub CLI\gh.exe'
private='zuzongdnt/hso-ios-offline-build';public='zuzongdnt/hso-offline-tools'
commit=subprocess.check_output([gh,'api',f'repos/{private}/commits/{a.ref}','--jq','.sha'],text=True).strip()
assert len(commit)==40 and all(c in '0123456789abcdef' for c in commit)
token=subprocess.check_output([gh,'auth','token'],text=True).strip()
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,request,fp,code,msg,headers,newurl):return None
request=urllib.request.Request(f'https://api.github.com/repos/{private}/zipball/{commit}',headers={'Authorization':'Bearer '+token,'User-Agent':'HSO-iOS-Build'})
try:
    urllib.request.build_opener(NoRedirect).open(request,timeout=30)
    raise RuntimeError('Expected the temporary GitHub archive redirect')
except urllib.error.HTTPError as response:
    if response.code!=302:raise
    url=response.headers['Location']
if not url.startswith(f'https://codeload.github.com/{private}/'):
    raise RuntimeError('Unexpected archive host')
subprocess.run([gh,'secret','set','HSO_IOS_SOURCE_URL','--repo',public],input=url,text=True,check=True)
subprocess.run([gh,'workflow','run','ios-world.yml','--repo',public,'-f','source_sha='+commit,'-f','runner='+a.runner],check=True)
print('Dispatched private source',commit,'on',a.runner)
