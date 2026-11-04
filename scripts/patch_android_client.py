"""Patch a user-supplied v403b APK decoded by Apktool. No game binaries are bundled."""
import argparse,re
from pathlib import Path

def patch(folder):
    session=next(folder.glob('smali*/CLib/Session_ME.smali'))
    text=session.read_text(encoding='utf-8')
    pattern=r'(\.method public connect\(Ljava/lang/String;I\)V\n\s*\.locals \d+\n)(.*?)(\.end method)'
    def connect(match):
        body=re.sub(r'\n\s*const-string p1, "(?:127\.0\.0\.1|100\.[\d.]+)"\n\s*const/16 p2, 0x[\da-f]+\n','\n',match[2],count=1)
        return match[1]+'\n    const-string p1, "127.0.0.1"\n    const/16 p2, 0x4ac3\n'+body+match[3]
    text,count=re.subn(pattern,connect,text,flags=re.S)
    assert count==1,'Unexpected Session_ME.connect layout'
    session.write_text(text,encoding='utf-8')
    midlet=next(folder.glob('smali*/com/silverbat/knightage/TemMidlet.smali'))
    text=midlet.read_text(encoding='utf-8')
    text,count=re.subn(r'\.method public static connectHTTP\(Ljava/lang/String;\)Ljava/lang/String;.*?\.end method',
        '.method public static connectHTTP(Ljava/lang/String;)Ljava/lang/String;\n    .locals 1\n    const-string v0, "Offline:127.0.0.1:19139:0"\n    return-object v0\n.end method',text,flags=re.S)
    assert count==1,'Unexpected server-list method'
    hook='    invoke-static {p0}, Loffline/OfflineEngine;->start(Landroid/app/Activity;)V'
    if hook not in text:
        marker='    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V'
        assert text.count(marker)==1
        text=text.replace(marker,marker+'\n\n'+hook)
    def pause(match):
        body=match[1]
        if 'Loffline/OfflineEngine;->save()V' not in body:
            body=body.replace('    return-void','    invoke-static {}, Loffline/OfflineEngine;->save()V\n\n    return-void')
        assert body.count('Loffline/OfflineEngine;->save()V')==1
        return body+match[2]
    text,count=re.subn(r'(\.method public onPause\(\)V\n.*?)(\.end method)',pause,text,flags=re.S)
    assert count==1,'Missing pause lifecycle hook'
    midlet.write_text(text,encoding='utf-8')
    manifest=folder/'AndroidManifest.xml'
    text=manifest.read_text(encoding='utf-8')
    text,count=re.subn(r'package="(?:com\.silverbat\.knightage|com\.zuzong\.hso403|com\.zuzong\.hso\.offline403)"','package="com.zuzong.hso.offline403"',text,count=1)
    assert count==1,'Unexpected APK package'
    manifest.write_text(text,encoding='utf-8')
    for strings in folder.glob('res/values*/strings.xml'):
        text=strings.read_text(encoding='utf-8')
        text=re.sub(r'(<string name="app_name">).*?(</string>)',r'\1HSO Offline\2',text)
        strings.write_text(text,encoding='utf-8')
    info=folder/'apktool.yml'
    text=info.read_text(encoding='utf-8')
    for key,value in [('minSdkVersion','33'),('versionCode','214'),('versionName','4.0.3-offline.2')]:
        text,count=re.subn(r'(?m)^(\s*'+key+r':).*$',lambda m:m[1]+' '+value,text)
        assert count==1,'Missing APK build setting '+key
    info.write_text(text,encoding='utf-8')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('decoded',type=Path)
    patch(parser.parse_args().decoded)
    print('Client uses app-local server 19139, offline list, separate package and pause-save hook.')
