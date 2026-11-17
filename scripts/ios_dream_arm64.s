// AAPCS64 RoboVM arguments: env, actor, graphics, paintName.
// The reserved zero-fill table has 128 slots, each 32 bytes long.
// Store an inverted actor address so the timer never roots an actor in Boehm GC.
    adrp x9, 0x1c1e000
    lsr x10, x1, #4
    eor x10, x10, x1, lsr #13
    and x10, x10, #127
    add x9, x9, x10, lsl #5
    mvn x10, x1
    ldrh w11, [x1, #0x2ce]
    sub w12, w11, #253
    cmp w12, #1
    b.hi normal_unworn

    stp x29, x30, [sp, #-80]!
    mov x29, sp
    stp x19, x20, [sp, #16]
    stp x21, x22, [sp, #32]
    stp x23, x24, [sp, #48]
    stp x25, x26, [sp, #64]
    mov x19, x0
    mov x20, x1
    mov x21, x2
    mov w22, w3
    mov x23, x9
    mov w26, w11

    ldrsb w8, [x20, #0x323]
    cmp w8, #0
    b.lt unmounted
    b reset
unmounted:
    ldr w8, [x20, #0x160]
    cbnz w8, reset
    ldrb w8, [x20, #0x301]
    cbnz w8, reset
    bl 0x2ad15c
    cbnz w0, reset

    mov x0, x19
    sub w1, w26, #3
    bl 0x2a85e4
    cbz x0, reset
    mov x25, x0
    mov x1, x25
    mov x0, x19
    bl 0x282524
    cbz w0, reset

    mov x0, x19
    bl 0x241750
    mvn x8, x20
    ldr x9, [x23]
    ldr w3, [x20, #0x284]
    ldr w4, [x20, #0x2a0]
    cmp x8, x9
    b.ne begin_idle
    ldp w9, w10, [x23, #16]
    cmp w3, w9
    b.ne begin_idle
    cmp w4, w10
    b.ne begin_idle
    ldr w11, [x23, #24]
    cmp w26, w11
    b.ne begin_idle
    ldr x24, [x23, #8]
    cbz x24, begin_idle
    sub x9, x0, x24
    mov w10, #10000
    cmp x9, x10
    b.lt normal_restore
    sub x9, x9, x10
    cmp x9, #3696
    b.hs begin_idle
    mov w10, #33
    udiv w5, w9, w10
    mov x0, x19
    mov x1, x25
    mov x2, x21
    mov w6, #0
    bl 0x287efc
    ldp x25, x26, [sp, #64]
    ldp x23, x24, [sp, #48]
    ldp x21, x22, [sp, #32]
    ldp x19, x20, [sp, #16]
    ldp x29, x30, [sp], #80
    ret

begin_idle:
    stp x8, x0, [x23]
    stp w3, w4, [x23, #16]
    str w26, [x23, #24]
    b normal_restore
reset:
    stp xzr, xzr, [x23]
normal_restore:
    mov x0, x19
    mov x1, x20
    mov x2, x21
    mov w3, w22
    ldp x25, x26, [sp, #64]
    ldp x23, x24, [sp, #48]
    ldp x21, x22, [sp, #32]
    ldp x19, x20, [sp, #16]
    ldp x29, x30, [sp], #80
    b normal_player
normal_unworn:
    ldr x11, [x9]
    cmp x10, x11
    b.ne normal_player
    stp xzr, xzr, [x9]
normal_player:
    stp x28, x27, [sp, #-64]!
    b 0x2a8a78

// EYE HOOK
    ldrh w8, [x1, #0x2ce]
    sub w8, w8, #253
    cmp w8, #3
    b.hi normal_eye
    b 0x2ad89c
normal_eye:
    ldr w0, [x1, #0x1b8]
    b 0x2ad8b4

// HAIR HOOK
    sub w8, w1, #159
    cmp w8, #1
    b.hi normal_effect
    mov x0, #0
    ret
normal_effect:
    stp x24, x23, [sp, #-64]!
    b 0x2a85e8
