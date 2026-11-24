import subprocess,os,sys
BAT=os.path.join(os.path.expanduser("~"),"Documents","Tools","ghidra-headless.bat");G=r"C:\Games\Quarantine\gsat";n=sys.argv[1]
for s,o in (("ExportFuncInfo.java","funcinfo_%s.tsv"),("CsDumpAll.java","decomp_%s.c")):
    subprocess.run([BAT,G,"QS","-process",n+".BIN","-noanalysis","-readOnly","-scriptPath",G+"\scripts","-postScript",s,G+"\\"+o%n],capture_output=True,creationflags=0x08000000)
