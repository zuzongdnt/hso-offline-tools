.method private offlineDream(LCLib/mGraphics;)Z
    .locals 8
    iget-short v0, p0, LGameObjects/MainObject;->idHair:S
    const/16 v1, 0x9f
    if-eq v0, v1, :outfit
    const/16 v1, 0xa0
    if-ne v0, v1, :reset
    :outfit
    iget-byte v1, p0, LGameObjects/MainObject;->typeMount:B
    if-ltz v1, :unmounted
    const/16 v2, 0x18
    if-lt v1, v2, :reset
    :unmounted
    iget v1, p0, LGameObjects/MainObject;->Action:I
    if-nez v1, :reset
    iget-boolean v1, p0, LGameObjects/MainObject;->isTanHinh:Z
    if-nez v1, :reset
    invoke-virtual {p0}, LGameObjects/MainObject;->checktanghinh()Z
    move-result v1
    if-nez v1, :reset
    add-int/lit8 v0, v0, 0x5b
    invoke-static {v0}, LGameObjects/MainObject;->getEffMatNa(I)LGameObjects/DataSkillEff;
    move-result-object v0
    invoke-virtual {v0}, LGameObjects/DataSkillEff;->isHavedata()Z
    move-result v1
    if-eqz v1, :reset
    invoke-static {}, LCLib/mSystem;->currentTimeMillis()J
    move-result-wide v2
    iget-wide v4, p0, LGameObjects/MainObject;->offlineDreamTime:J
    const-wide/16 v6, 0x0
    cmp-long v1, v4, v6
    if-nez v1, :elapsed
    iput-wide v2, p0, LGameObjects/MainObject;->offlineDreamTime:J
    goto :no
    :elapsed
    sub-long/2addr v2, v4
    const-wide/16 v6, 0x2710
    cmp-long v1, v2, v6
    if-ltz v1, :no
    sub-long/2addr v2, v6
    const-wide/16 v6, 0x21
    div-long/2addr v2, v6
    long-to-int v4, v2
    const/16 v1, 0x70
    if-lt v4, v1, :draw
    goto :reset
    :draw
    move-object v1, p1
    iget v2, p0, LGameObjects/MainObject;->x:I
    iget v3, p0, LGameObjects/MainObject;->y:I
    const/4 v5, 0x0
    invoke-virtual/range {v0 .. v5}, LGameObjects/DataSkillEff;->paintBottomAll(LCLib/mGraphics;IIII)V
    const/4 v0, 0x1
    return v0
    :reset
    const-wide/16 v2, 0x0
    iput-wide v2, p0, LGameObjects/MainObject;->offlineDreamTime:J
    :no
    const/4 v0, 0x0
    return v0
.end method

.method private offlineRabbit(LCLib/mGraphics;)V
    .locals 7
    iget-short v0, p0, LGameObjects/MainObject;->idMatna:S
    const/16 v1, 0xf9
    if-ne v0, v1, :done
    iget v0, p0, LGameObjects/MainObject;->Action:I
    const/4 v1, 0x4
    if-eq v0, v1, :done
    invoke-virtual {p0}, LGameObjects/MainObject;->checktanghinh()Z
    move-result v0
    if-nez v0, :done
    const/16 v0, 0xfc
    invoke-static {v0}, LGameObjects/MainObject;->getEffMatNa(I)LGameObjects/DataSkillEff;
    move-result-object v0
    move-object v1, p1
    iget v2, p0, LGameObjects/MainObject;->x:I
    iget v3, p0, LGameObjects/MainObject;->y:I
    iget v4, p0, LGameObjects/MainObject;->dyMount:I
    sub-int/2addr v3, v4
    iget v4, p0, LGameObjects/MainObject;->dy:I
    sub-int/2addr v3, v4
    iget v4, p0, LGameObjects/MainObject;->ysai:I
    sub-int/2addr v3, v4
    iget v4, p0, LGameObjects/MainObject;->yjum:I
    sub-int/2addr v3, v4
    iget v4, p0, LGameObjects/MainObject;->dyWater:I
    add-int/2addr v3, v4
    iget v4, p0, LGameObjects/MainObject;->Direction:I
    const/4 v5, 0x0
    invoke-virtual/range {v0 .. v5}, LGameObjects/DataSkillEff;->paintBottomAll(LCLib/mGraphics;IIII)V
    :done
    return-void
.end method
