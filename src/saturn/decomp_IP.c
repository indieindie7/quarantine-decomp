// ==== ip0_LoopCalc_023e6 @ 060023e6 size=22

/* Hand-named: ip0_LoopCalc_023e6 (hand provisional structural name: LoopCalc near ip0 code, 22
   bytes, 0 callees, 1 callers) */

int ip0_LoopCalc_023e6(void)

{
  *DAT_06002400 = 1;
  do {
  } while (*DAT_06002400 == 1);
  return *DAT_06002400;
}


// ==== ip0_LoopCalc_0245c @ 0600245c size=42

/* Hand-named: ip0_LoopCalc_0245c (hand provisional structural name: LoopCalc near ip0 code, 42
   bytes, 0 callees, 1 callers) */

int ip0_LoopCalc_0245c(short *param_1,int param_2,short param_3)

{
  int iStack_8;
  short *psStack_4;
  
  iStack_8 = param_2;
  psStack_4 = param_1;
  do {
    *psStack_4 = param_3;
    iStack_8 = iStack_8 + -1;
    psStack_4 = psStack_4 + 1;
  } while (iStack_8 != 0);
  return (int)param_3;
}


// ==== ip0_SetupObj_024d8 @ 060024d8 size=56

/* Hand-named: ip0_SetupObj_024d8 (hand provisional structural name: SetupObj near ip0 code, 56
   bytes, 0 callees, 1 callers) */

int ip0_SetupObj_024d8(short param_1)

{
  int iVar1;
  
  iVar1 = *(int *)PTR_LAB_06002558 + (int)DAT_06002554;
  *(short *)(iVar1 + 0x14) = param_1;
  *(short *)(iVar1 + 0x16) = param_1;
  *(short *)(iVar1 + 0x18) = param_1;
  return (int)param_1;
}


// ==== ip0_ForEach_02510 @ 06002510 size=68

/* Hand-named: ip0_ForEach_02510 (hand provisional structural name: ForEach near ip0 code, 68 bytes,
   4 callees, 0 callers) */

undefined4 ip0_ForEach_02510(short param_1)

{
  undefined4 uVar1;
  undefined2 local_8;
  
  for (local_8 = DAT_06002554; (int)(uint)local_8 < (int)DAT_06002556; local_8 = local_8 + param_1)
  {
    ip0_SetupObj_024d8((int)(short)local_8);
    ip0_LoopCalc_023e6();
  }
  ip0_SetupObj_024d8((int)DAT_06002556);
  uVar1 = ip0_LoopCalc_023e6();
  return uVar1;
}


// ==== ip0_ForEach_02594 @ 06002594 size=278

/* Hand-named: ip0_ForEach_02594 (hand provisional structural name: ForEach near ip0 code, 278
   bytes, 1 callees, 0 callers) */

undefined4 ip0_ForEach_02594(void)

{
  short sVar1;
  int iVar2;
  undefined2 *local_30;
  undefined2 *puStack_2c;
  uint uStack_8;
  
  ip0_LoopCalc_0245c(*(undefined4 *)PTR_LAB_060025d4,(int)DAT_060025c6,0);
  iVar2 = *(int *)PTR_LAB_060025d4;
  *(undefined2 *)(iVar2 + 0x20) = 1;
  puStack_2c = (undefined2 *)PTR_DAT_060025d8;
  local_30 = (undefined2 *)(iVar2 + 0x10);
  for (uStack_8 = 0; uStack_8 < 8; uStack_8 = uStack_8 + 1) {
    *local_30 = *puStack_2c;
    local_30 = local_30 + 1;
    puStack_2c = puStack_2c + 1;
  }
  iVar2 = *(int *)PTR_LAB_060026b4;
  *(short *)(iVar2 + 0x30) = (short)DAT_060026b8;
  *(undefined2 *)(iVar2 + 0x40) = DAT_060026aa;
  *(undefined2 *)(iVar2 + 0x42) = DAT_060026aa;
  iVar2 = *(int *)PTR_LAB_060026b4;
  *(undefined4 *)(iVar2 + 0x78) = DAT_060026bc;
  *(undefined4 *)(iVar2 + 0x7c) = DAT_060026bc;
  *(undefined4 *)(iVar2 + 0x88) = DAT_060026bc;
  *(undefined4 *)(iVar2 + 0x8c) = DAT_060026bc;
  *(int *)(iVar2 + 0xac) = (int)DAT_060026ac;
  *DAT_060026c0 = 0;
  *(undefined2 *)(*(int *)PTR_LAB_060026b4 + (int)DAT_060026ae) = 0x20;
  *(undefined2 *)(*(int *)PTR_LAB_060026b4 + (int)DAT_060026b0 + 8) = 7;
  iVar2 = *(int *)PTR_LAB_060026b4 + (int)DAT_060026b2;
  *(undefined2 *)(iVar2 + 0x10) = 1;
  sVar1 = DAT_060026b2;
  *(short *)(iVar2 + 0x18) = DAT_060026b2;
  *(short *)(iVar2 + 0x16) = sVar1;
  *(short *)(iVar2 + 0x14) = sVar1;
  return 1;
}


// ==== ip0_FillLoop_0270a @ 0600270a size=98

/* Hand-named: ip0_FillLoop_0270a (hand provisional structural name: FillLoop near ip0 code, 98
   bytes, 0 callees, 0 callers) */

void ip0_FillLoop_0270a(byte param_1,int param_2)

{
  uint uVar1;
  int in_r0;
  byte in_r1;
  int in_r2;
  int iVar2;
  uint unaff_r8;
  byte *unaff_r9;
  
  if (param_2 < 1) {
    if ((((in_r0 != 0xc) && (in_r0 != 0xe)) && (in_r0 != 0xd)) && (in_r0 != 0xf)) {
      if ((unaff_r8 & 1) != 1) {
        return;
      }
      *unaff_r9 = in_r1 | (byte)in_r0;
      return;
    }
  }
  else if (param_2 == 1) {
    iVar2 = in_r2 * 0x10 + in_r0 + 2;
    do {
      uVar1 = unaff_r8 & 1;
      unaff_r8 = unaff_r8 >> 1;
      if (uVar1 == 1) {
        in_r1 = in_r1 | param_1;
        *unaff_r9 = in_r1;
        unaff_r9 = unaff_r9 + 1;
      }
      else {
        unaff_r8 = unaff_r8 + 1;
        in_r1 = param_1 << 4;
      }
      iVar2 = iVar2 + -1;
    } while (iVar2 != 0);
  }
  return;
}


// ==== ip0_Access_02ff0 @ 06002ff0 size=16

/* WARNING: Control flow encountered bad instruction data */
/* Hand-named: ip0_Access_02ff0 (hand provisional structural name: Access near ip0 code, 16 bytes, 0
   callees, 0 callers) */

void ip0_Access_02ff0(undefined2 *param_1,undefined2 param_2,uint param_3)

{
  if ((int)((uint)param_1 & param_3) <= (int)param_3) {
    *param_1 = param_2;
                    /* WARNING: Bad instruction - Truncating control flow here */
    halt_baddata();
  }
                    /* WARNING: Bad instruction - Truncating control flow here */
  halt_baddata();
}


