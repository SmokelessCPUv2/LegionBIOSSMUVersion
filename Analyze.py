from operator import length_hint
from pipes import Template
import psptool
import urllib.request
import os
import shutil
from zipfile import ZipFile


LogType = ['PSP_FW_BOOT_LOADER','PSP_FW_TRUSTED_OS','PSP_BOOT_TIME_TRUSTLETS','SMU_OFFCHIP_FW','SMU_OFF_CHIP_FW_2']

def DownloadInnoextract():
    urllib.request.urlretrieve("https://constexpr.org/innoextract/files/innoextract-1.9-windows.zip","innoextract.zip")
    ZipFile("innoextract.zip").extractall(".")

def DownloadUEFIExtract():
    urllib.request.urlretrieve("https://github.com/LongSoft/UEFITool/releases/download/A62/UEFIExtract_NE_A62_win32.zip","UEFIExtract.zip")
    ZipFile("UEFIExtract.zip").extractall(".")

def DowloadFromLenovo(url,Pattern,Folder, start,end):
    try:
        os.mkdir(Folder)
    except:
        None
    for i in range(start,end+1):
        Name = Pattern.format(i)
        if Name + ".exe" not in os.listdir(Folder):
            remote_url = url + Name + ".exe"
            local_file_name = Folder + "/"+Name + ".exe"
            try:
                urllib.request.urlretrieve(remote_url,local_file_name)
            except:
                print(Name + " Doesn't Exist on lenovo Server")
        else:
                print(Name + " Already Downloaded")
def InnoextractAll(dir):
    try:
        shutil.rmtree(dir+"_Extracted/")
    except:
        None
    for file in os.listdir(dir):
        os.system("innoextract.exe -s {}/{} -d {}".format(dir,file,dir+"_Extracted"))
    for folder in os.listdir(dir+"_Extracted"):
        for file in os.listdir(dir+"_Extracted/" + folder):
            if ".exe" in file:
                exe_name=dir+"_Extracted/" + folder + "/" + file
                outname = dir+"_Extracted/"+file[:-4]
                os.system("7z x {} -o{}".format(exe_name,outname))
                for file in os.listdir(outname):
                    if ".fd" in file:
                        shutil.move(outname+"/"+ file,outname+"/"+"BIOS.fd")
        shutil.rmtree(dir+"_Extracted/" + folder)


def AnalizeAllDir(dir):

     Result = []
     for folder in os.listdir(dir+"_Extracted"):
        Dirpath = dir+"_Extracted/"+ folder +"/"
        path = Dirpath + "BIOS.fd"
        psp = psptool.PSPTool.from_file(path)
        os.system(".\\UEFIExtract.exe {} 29D40F30-E8BF-4803-88A6-4247A29A5318 -o {} -m body".format(path,Dirpath+"AMDVersion"))
        with open(Dirpath+"AMDVersion/body_1.bin","rb") as f:
            body = f.read()
            AgesaHandle=body.find(b'\x41\x47\x45\x53\x41\x21\x56\x39') # Find "AGESA!V9"
            VersionHandle=body[AgesaHandle+9:-1]
            VersionHandle=VersionHandle[0: VersionHandle.find(b'\x00') ]# Find Extract Version String
        #Parse Main Directory
        TempResult = []
        for rom_index, rom in enumerate(psp.blob.roms):
            for index, directory in enumerate(rom.directories):
                for entry in directory.entries:
                    try:
                       # print(entry.DIRECTORY_ENTRY_TYPES[entry.type])
                       if entry.DIRECTORY_ENTRY_TYPES[entry.type] in LogType:
                            exist = False
                            for temp_sav in TempResult:
                                if temp_sav[0] == entry.DIRECTORY_ENTRY_TYPES[entry.type]:
                                    exist = True
                            if exist == False:
                                TempResult.append([entry.DIRECTORY_ENTRY_TYPES[entry.type],entry.get_readable_version(),entry.signed,entry.rom_size,entry.size_uncompressed,entry.get_readable_signed_by(), entry.md5()])
                    except:
                        None
        Result.append([folder,TempResult,str(VersionHandle,"utf-8")])
     return Result

def VersionToDec(version):
    ver = ''
    for dec in version.split('.'):
        ver += str(int(dec,16)) + "."
    return ver[:-1]

def CreateTable(PSPReult,outName):
    with open("{}.md".format(outName),"w") as f:
        f.write("| BIOS Name |")
        f.write( "AGESA Version" + "|")
        for Header in LogType:
            f.write(Header + "|")
        f.write("\n")
        f.write("| :-: |:-: |")
        for Header in LogType:
            f.write(":-:|")
        f.write("\n")
        for bios in PSPReult:
            f.write("|" + bios[0] + "|")
            f.write(bios[2] + "|")
            for Type in LogType:
                for inst in bios[1]:
                    if inst[0]==Type:
                        f.write(VersionToDec(inst[1])+"<br/>")
                        f.write( "( {} )<br/>".format(inst[1]))
                        f.write( "Signed:  {}<br/>".format(inst[2]))
                        f.write( "Signed by: {}<br/>".format(inst[5]))
                        f.write( "Size: {}<br/>".format(inst[3]))
                        f.write( "Size Uncompressed: {}<br/>".format(inst[4]))
                        f.write( "MD5: {}<br/>".format(inst[6]))
                        f.write("|")
                        break;
            f.write("\n")

DownloadInnoextract()
DownloadUEFIExtract()
BIOS_TO_CHECK = ["FSCN","EUCN", "GKCN", "GHCN"]
for BIOS in BIOS_TO_CHECK:
    DowloadFromLenovo("https://download.lenovo.com/consumer/mobiles/",BIOS+"{}WW",BIOS,0,60)
    InnoextractAll(BIOS)
    CreateTable(AnalizeAllDir(BIOS),BIOS)

with open("README.md","w") as f:
    with open("Template.md","r") as template:
        f.write(template.read())
        f.write("\n")
    for BIOS in BIOS_TO_CHECK:
        f.write("# {}\n".format(BIOS))
        with open("{}.md".format(BIOS),"r") as BIOS_Data:
              f.write(BIOS_Data.read())
              f.write("\n")
