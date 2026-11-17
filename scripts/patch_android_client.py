"""Patch a user-supplied v403b APK decoded by Apktool. No game binaries are bundled."""
import argparse,re
from pathlib import Path

MIN_SDK = 29

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
    network=next(folder.glob('smali*/CLib/Session_ME$NetworkInit.smali'))
    text=network.read_text(encoding='utf-8')
    marker='    .line 117\n    iget-object v0, p0, LCLib/Session_ME$NetworkInit;->this$0:LCLib/Session_ME;'
    assert text.count(marker)==1,'Unexpected offline connection worker'
    text=text.replace(marker,
        '    invoke-static {}, Loffline/OfflineEngine;->awaitServerReady()V\n\n'+marker)
    network.write_text(text,encoding='utf-8')
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
    lock='    invoke-static {p0}, Loffline/OfflineEngine;->lockLandscape(Landroid/app/Activity;)V'
    resume='    invoke-super {p0}, Landroid/app/Activity;->onResume()V'
    assert text.count(resume)==1,'Missing resume lifecycle hook'
    if resume+'\n\n'+lock not in text:
        text=text.replace(resume,resume+'\n\n'+lock)
    config='onConfigurationChanged(Landroid/content/res/Configuration;)V'
    if f'.method public {config}' not in text:
        text+=f'\n.method public {config}\n    .locals 0\n\n'
        text+=f'    invoke-super {{p0, p1}}, Landroid/app/Activity;->{config}\n\n'
        text+=lock+'\n\n    return-void\n.end method\n'
    midlet.write_text(text,encoding='utf-8')
    reader=next(folder.glob('smali*/netcommand/global/ReadMessenge.smali'))
    text=reader.read_text(encoding='utf-8')
    map_start = '.method public changeMap(Lnet/Message;)V\n    .locals 13\n'
    assert text.count(map_start) == 1
    text = text.replace(map_start, map_start + '''
    const/4 v0, 0x0
    sput-boolean v0, LGameObjects/Player;->isLockKey:Z
    const/4 v0, 0x1
    sput-boolean v0, LGameObjects/Player;->isSendMove:Z
''')
    for line in (314, 5556, 5578, 5636, 5651):
        pattern=rf'(\.line {line}\b(?:(?!\.line).)*?)readByte\(\)B'
        text,count=re.subn(pattern,r'\1readShort()S',text,count=1,flags=re.S)
        assert count == 1, f'Missing inventory field at smali line {line}'
    text,count=re.subn(r'(sget-short (\w+), LGameObjects/Player;->maxInven:S)(\s+div-int/lit8)',
                       r'\1\n\n    add-int/lit8 \2, \2, 0x29\3',text)
    assert count == 1, 'Missing main inventory page calculation'
    assign_pet = '    sput-object v1, LGameScreen/GameScreen;->pet:LGameObjects/Pet;'
    assert text.count(assign_pet) == 1, 'Missing local follower assignment'
    text = text.replace(assign_pet, '    invoke-static {}, Lnetcommand/global/ReadMessenge;->offlineRemoveOldPet()V\n\n' + assign_pet)
    text += """
.method private static offlineRemoveOldPet()V
    .locals 2
    sget-object v0, LGameScreen/GameScreen;->pet:LGameObjects/Pet;
    if-eqz v0, :finish
    sget-object v1, LGameScreen/GameScreen;->Vecplayers:LCLib/mVector;
    invoke-virtual {v1, v0}, LCLib/mVector;->removeElement(Ljava/lang/Object;)V
    :finish
    return-void
.end method
"""
    reader.write_text(text,encoding='utf-8')
    tab=next(folder.glob('smali*/InterfaceComponents/TabShopNew.smali'))
    text=tab.read_text(encoding='utf-8')
    text,count=re.subn(r'(sget-short (\w+), LGameObjects/Player;->maxInven:S)(\s+div-int/2addr)',
                       r'\1\n\n    add-int/lit8 \2, \2, 0x29\3',text)
    assert count == 2, 'Missing inventory tab page calculations'
    tab.write_text(text,encoding='utf-8')
    actor=next(folder.glob('smali*/GameObjects/MainObject.smali'))
    text=actor.read_text(encoding='utf-8')
    draw_skin='    invoke-virtual/range {v1 .. v6}, LGameObjects/DataSkillEff;->paintTopWeaPon(LCLib/mGraphics;IIII)V'
    draw_gem='    invoke-direct/range {p0 .. p1}, LGameObjects/MainObject;->paintEffectWeapon(LCLib/mGraphics;)V'
    section=re.search(r'(?ms)^\.method public paintPlayer\(LCLib/mGraphics;I\)V.*?^\.end method',text)
    assert section and section[0].count(draw_skin)==2,'Unexpected animated weapon renderer'
    text=text[:section.start()]+section[0].replace(draw_skin, draw_skin+'\n\n'+draw_gem)+text[section.end():]
    mount = re.search(r'(?ms)^\.method public updateMount\(\)V.*?^\.end method', text)
    assert mount and '.locals 15' in mount[0], 'Unexpected mount updater'
    mount_body = mount[0]
    # Use the visible mount frame to choose the side-view rider height.
    for line, side in ((3310, 'right'), (3337, 'left')):
        marker = f'    iput-byte v0, p0, LGameObjects/MainObject;->frameMount:B\n\n    .line {line}'
        assert mount_body.count(marker) == 1, f'Missing {side} movement frame'
        mount_body = mount_body.replace(marker, f"""    iget-byte v13, p0, LGameObjects/MainObject;->typeMount:B
    const/16 v14, 0x18
    if-lt v13, v14, :offline_mount_{side}
    iget v0, p0, LGameObjects/MainObject;->Fhorse:I
    int-to-byte v0, v0
    :offline_mount_{side}
{marker}""")
    text = text[:mount.start()] + mount_body + text[mount.end():]
    from patch_idle_fashion import patch_idle_fashion
    text = patch_idle_fashion(text)
    body_frame = '.method public getFrameBody()I\n    .locals 2\n'
    assert text.count(body_frame) == 1
    text = text.replace(body_frame, body_frame + '''
    iget-short v0, p0, LGameObjects/MainObject;->idBody:S
    add-int/lit16 v0, v0, -0xfd
    if-ltz v0, :native_body_frame
    const/4 v1, 0x1
    if-gt v0, v1, :native_body_frame
    iget v0, p0, LGameObjects/MainObject;->Direction:I
    if-lez v0, :dream_front_frame
    const/4 v1, 0x2
    if-le v0, v1, :dream_front_frame
    const/4 v0, 0x2
    :dream_front_frame
    mul-int/lit8 v0, v0, 0x6
    iget v1, p0, LGameObjects/MainObject;->frame:I
    rem-int/lit8 v1, v1, 0x6
    if-gez v1, :dream_pose_frame
    const/4 v1, 0x0
    :dream_pose_frame
    add-int/2addr v0, v1
    return v0
    :native_body_frame
''')
    # Costume data now has all native phases; keep the original frame selector.
    begin = text.index('    iget-short v0, p0, LGameObjects/MainObject;->idBody:S', text.index(body_frame))
    end = text.index('    :native_body_frame\n', begin) + len('    :native_body_frame\n')
    text = text[:begin] + text[end:]
    actor.write_text(text,encoding='utf-8')
    config_tab=next(folder.glob('smali*/InterfaceComponents/TabConfig.smali'))
    text=config_tab.read_text(encoding='utf8')
    payment = ('    iget-object v1, p0, LInterfaceComponents/TabConfig;->cmdDiamond:LInterfaceComponents/iCommand;\n\n'
               '    invoke-virtual {v0, v1}, LCLib/mVector;->addElement(Ljava/lang/Object;)V\n')
    assert text.count(payment) == 1, 'Expected one top-up menu entry'
    text = text.replace(payment, '')
    marker='    :cond_e\n    iput-object v0, p0, LInterfaceComponents/TabConfig;->vecConfig:LCLib/mVector;'
    assert text.count(marker)==1, 'Missing settings command list'
    text=text.replace(marker, marker+'\n    invoke-direct {p0, v0}, LInterfaceComponents/TabConfig;->offlineSpeedCommand(LCLib/mVector;)V')
    marker='.method public commandPointer(II)V\n    .locals 10\n'
    assert text.count(marker)==1, 'Missing settings command handler'
    text=text.replace(marker, marker+"""
    const/16 v0, 0x63
    if-ne p1, v0, :original_commands
    invoke-direct {p0}, LInterfaceComponents/TabConfig;->offlineToggleSpeed()V
    return-void
    :original_commands
""")
    text=text.replace('# instance fields', '.field public static offlineFast:Z\n\n# instance fields', 1)
    assert '.field public static offlineFast:Z' in text
    text+="""
.method private offlineSpeedCommand(LCLib/mVector;)V
    .locals 3
    new-instance v0, LInterfaceComponents/iCommand;
    sget-boolean v1, LInterfaceComponents/TabConfig;->offlineFast:Z
    if-eqz v1, :normal
    const-string v1, "Tốc độ game x2"
    goto :create
    :normal
    const-string v1, "Tốc độ game x1"
    :create
    const/16 v2, 0x63
    invoke-direct {v0, v1, v2, p0}, LInterfaceComponents/iCommand;-><init>(Ljava/lang/String;ILModel/AvMain;)V
    const/4 v1, 0x0
    invoke-virtual {p1, v0, v1}, LCLib/mVector;->insertElementAt(Ljava/lang/Object;I)V
    return-void
.end method

.method private offlineToggleSpeed()V
    .locals 2
    sget-boolean v0, LInterfaceComponents/TabConfig;->offlineFast:Z
    xor-int/lit8 v0, v0, 0x1
    sput-boolean v0, LInterfaceComponents/TabConfig;->offlineFast:Z
    if-eqz v0, :normal
    const-string v1, "/offline-speed-2"
    goto :send
    :normal
    const-string v1, "/offline-speed-1"
    :send
    invoke-static {}, Lnetcommand/global/GlobalService;->gI()Lnetcommand/global/GlobalService;
    move-result-object v0
    invoke-virtual {v0, v1}, Lnetcommand/global/GlobalService;->chatPopup(Ljava/lang/String;)V
    invoke-virtual {p0}, LInterfaceComponents/TabConfig;->init()V
    return-void
.end method
"""
    marker='    :cond_e\n    iput-object v0, p0, LInterfaceComponents/TabConfig;->vecConfig:LCLib/mVector;'
    text=text.replace(marker, marker+'\n    invoke-direct {p0, v0}, LInterfaceComponents/TabConfig;->offlineToolsCommand(LCLib/mVector;)V')
    marker='.method public commandPointer(II)V\n    .locals 10\n'
    text=text.replace(marker, marker+'''
    const/16 v0, 0x64
    if-ne p1, v0, :offline_original_tools
    invoke-static {}, Loffline/OfflineEngine;->openTools()V
    return-void
    :offline_original_tools
''')
    text+='''
.method private offlineToolsCommand(LCLib/mVector;)V
    .locals 3
    new-instance v0, LInterfaceComponents/iCommand;
    const-string v1, "Sao lưu và cập nhật"
    const/16 v2, 0x64
    invoke-direct {v0, v1, v2, p0}, LInterfaceComponents/iCommand;-><init>(Ljava/lang/String;ILModel/AvMain;)V
    const/4 v1, 0x0
    invoke-virtual {p1, v0, v1}, LCLib/mVector;->insertElementAt(Ljava/lang/Object;I)V
    return-void
.end method
'''
    config_tab.write_text(text,encoding='utf8')
    canvas=next(folder.glob('smali*/com/silverbat/knightage/TemCanvas.smali'))
    text=canvas.read_text(encoding='utf8')
    tick='    invoke-virtual {v0}, LMain/GameCanvas;->update()V'
    assert text.count(tick)==1, 'Missing game loop tick'
    text=text.replace(tick,tick+"""

    sget-boolean v1, LInterfaceComponents/TabConfig;->offlineFast:Z
    if-eqz v1, :offline_normal_speed
    sget-object v1, LMain/GameCanvas;->currentScreen:LGameScreen/MainScreen;
    instance-of v1, v1, LGameScreen/GameScreen;
    if-eqz v1, :offline_normal_speed
    invoke-virtual {v0}, LMain/GameCanvas;->update()V
    :offline_normal_speed
""")
    canvas.write_text(text,encoding='utf8')
    manifest=folder/'AndroidManifest.xml'
    text=manifest.read_text(encoding='utf-8')
    text,count=re.subn(r'package="(?:com\.silverbat\.knightage|com\.zuzong\.hso403|com\.zuzong\.hso\.offline403)"','package="com.zuzong.hso.offline403"',text,count=1)
    assert count==1,'Unexpected APK package'
    text=text.replace('</application>', '''<activity android:name="offline.ToolsActivity" android:exported="false" android:configChanges="orientation|screenSize" />
    <provider android:name="offline.UpdateProvider" android:authorities="com.zuzong.hso.offline403.updates" android:exported="false" android:grantUriPermissions="true" />
    </application>''')
    text=text.replace('<application', '<uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES"/><application', 1)
    if 'android:appCategory="game"' not in text:
        text,count=re.subn(r'<application\b', '<application android:appCategory="game"', text)
        assert count==1,'Missing application element'
    activity=r'<activity\b(?=[^>]*android:name="com\.silverbat\.knightage\.TemMidlet")[^>]*>'
    def lock_landscape(match):
        tag=re.sub(r' android:resizeableActivity="[^"]*"', '', match[0])
        tag,count=re.subn(r'android:screenOrientation="[^"]*"',
                          'android:screenOrientation="landscape" android:resizeableActivity="false"',tag)
        assert count==1,'Missing game orientation'
        return tag
    text,count=re.subn(activity,lock_landscape,text)
    assert count==1,'Missing game activity'
    manifest.write_text(text,encoding='utf-8')
    security = folder / 'res/xml/network_security_config.xml'
    text = security.read_text(encoding='utf-8')
    text = text.replace('</network-security-config>', '''    <domain-config cleartextTrafficPermitted="true">
        <domain>127.0.0.1</domain>
        <domain>localhost</domain>
    </domain-config>
</network-security-config>''')
    security.write_text(text, encoding='utf-8')
    for strings in folder.glob('res/values*/strings.xml'):
        text=strings.read_text(encoding='utf-8')
        text=re.sub(r'(<string name="app_name">).*?(</string>)',r'\1HSO Offline\2',text)
        strings.write_text(text,encoding='utf-8')
    info=folder/'apktool.yml'
    text=info.read_text(encoding='utf-8')
    for key,value in [('minSdkVersion',str(MIN_SDK)),('versionCode','240'),('versionName','4.0.3-offline.28')]:
        text,count=re.subn(r'(?m)^(\s*'+key+r':).*$',lambda m:m[1]+' '+value,text)
        assert count==1,'Missing APK build setting '+key
    info.write_text(text,encoding='utf-8')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('decoded',type=Path)
    patch(parser.parse_args().decoded)
    print('Client uses app-local server 19139, offline list, separate package and pause-save hook.')
