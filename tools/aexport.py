import subprocess,os,sys
BAT=os.path.join(os.path.expanduser("~"),"Documents","Tools","ghidra-headless.bat");G=r"C:\Games\Quarantine\g3do";n=sys.argv[1]
subprocess.run([BAT,G,"QA","-process",n+".bin","-noanalysis","-readOnly","-scriptPath",G+os.sep+"scripts","-postScript","ExportFuncInfo.java",G+os.sep+"funcinfo_%s.tsv"%n],capture_output=True,creationflags=0x08000000)
