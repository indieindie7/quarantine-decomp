import subprocess,os,sys
BAT=os.path.join(os.path.expanduser("~"),"Documents","Tools","ghidra-headless.bat");G=r"C:\Users\USER\Documents\Quarantine\ghidra";n=sys.argv[1]
subprocess.run([BAT,G,"Q","-process",n+".bin","-noanalysis","-readOnly","-scriptPath",G+r"\scripts","-postScript","ExportFuncInfo.java",G+r"\funcinfo_%s.tsv"%n],capture_output=True,creationflags=0x08000000)
