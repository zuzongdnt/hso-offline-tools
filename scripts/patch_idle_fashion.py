"""Wire the local-world fashion renderer into the existing Android client."""
import re
from pathlib import Path


def patch_idle_fashion(text):
    pattern = r'(?ms)^\.method public paintPlayer\(LCLib/mGraphics;I\)V.*?^\.end method'
    actor = 'LGameObjects/MainObject;'
    match = re.search(pattern, text)
    assert match
    body = match[0]
    insert = re.search(r'    \.locals \d+\n', body).end()
    body = body[:insert] + """
    invoke-direct/range {p0 .. p1}, LGameObjects/MainObject;->offlineDream(LCLib/mGraphics;)Z
    move-result v0
    if-eqz v0, :offline_normal_player
    return-void
    :offline_normal_player
""" + body[insert:]
    lookup = f'    iget-short v1, v0, {actor}->idMatna:S'
    assert body.count(lookup) == 1
    body = body.replace(lookup, lookup + """
    const/16 v5, 0xf9
    if-ne v1, v5, :offline_normal_mask
    const/4 v1, -0x1
    :offline_normal_mask""")
    horse = '    invoke-virtual/range {v1 .. v6}, LGameObjects/DataSkillEff;->paintTopHorse(LCLib/mGraphics;IIII)V'
    # The target branch label also reaches this point when no mount is equipped.
    anchor = re.search(r'(?m)^    invoke-virtual/range \{p0 \.\. p0\}, LGameObjects/MainObject;->canpaintDataSkillEff\(\)Z$', body)
    assert body.count(horse) == 1 and anchor
    body = body[:anchor.start()] + f'    invoke-direct/range {{p0 .. p1}}, {actor}->offlineRabbit(LCLib/mGraphics;)V\n\n' + body[anchor.start():]
    fields = '.field private offlineDreamTime:J\n\n'
    hooks = Path(__file__).with_name('idle_fashion.smali').read_text(encoding='utf8')
    result = text[:match.start()] + body + text[match.end():]
    loader = r'(\.method public static getEffMatNa\(I\)LGameObjects/DataSkillEff;\n    \.locals \d+\n)'
    result, count = re.subn(loader, lambda m: m[0] + """
    const/16 v0, 0x9f
    if-eq p0, v0, :offline_no_hair_overlay
    const/16 v0, 0xa0
    if-ne p0, v0, :offline_load_effect
    :offline_no_hair_overlay
    const/4 v0, 0x0
    return-object v0
    :offline_load_effect
""", result)
    assert count == 1
    eye = '    :pswitch_2\n    iget p1, p0, LGameObjects/MainObject;->eye:I'
    assert result.count(eye) == 1
    result = result.replace(eye, """    :pswitch_2
    iget-short v1, p0, LGameObjects/MainObject;->idBody:S
    const/16 v2, 0xfd
    if-lt v1, v2, :offline_default_eye
    const/16 v2, 0x100
    if-gt v1, v2, :offline_default_eye
    :offline_dream_eye
    return v0
    :offline_default_eye
    iget p1, p0, LGameObjects/MainObject;->eye:I""")
    return result.replace('# instance fields\n', '# instance fields\n'+fields, 1) + '\n' + hooks
