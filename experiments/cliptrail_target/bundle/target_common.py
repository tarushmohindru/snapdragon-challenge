import ctypes
import hashlib
import json
import platform
import struct
import sys
from pathlib import Path


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def write(path,data):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def pe_machine(path):
    with Path(path).open('rb') as f:
        if f.read(2)!=b'MZ':raise ValueError('Not a PE executable')
        f.seek(0x3c);offset=struct.unpack('<I',f.read(4))[0]
        f.seek(offset)
        if f.read(4)!=b'PE\0\0':raise ValueError('Missing PE signature')
        return hex(struct.unpack('<H',f.read(2))[0])


def validate_files(root,manifest):
    for name,expected in manifest['files'].items():
        path=(root/name).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():raise ValueError('Missing/unsafe bundle file: '+name)
        if sha(path)!=expected:raise ValueError('Bundle hash mismatch: '+name)
    return True


def native_probe():
    data={'system':platform.system(),'python':platform.python_version(),'machine':platform.machine(),
          'pointer_bits':struct.calcsize('P')*8,'native_windows_arm64':False}
    if platform.system()!='Windows':return data
    from ctypes import wintypes as w
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetCurrentProcess.restype=w.HANDLE
    kernel.IsWow64Process2.argtypes=[w.HANDLE,ctypes.POINTER(w.USHORT),ctypes.POINTER(w.USHORT)]
    kernel.IsWow64Process2.restype=w.BOOL
    process,native=w.USHORT(),w.USHORT()
    if not kernel.IsWow64Process2(kernel.GetCurrentProcess(),ctypes.byref(process),ctypes.byref(native)):
        raise ctypes.WinError(ctypes.get_last_error())
    data.update(process_machine=hex(process.value),native_machine=hex(native.value),python_pe_machine=pe_machine(sys.executable))
    data['native_windows_arm64']=native.value==0xaa64 and process.value==0 and data['python_pe_machine']=='0xaa64' and data['pointer_bits']==64
    return data


def dependency_probe():
    """Load only named platform dependencies; preserve actionable loader errors."""
    from ctypes import wintypes as w
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetModuleFileNameW.argtypes=[w.HMODULE,w.LPWSTR,w.DWORD]
    kernel.GetModuleFileNameW.restype=w.DWORD
    records=[]
    for name in ('msvcp140.dll','msvcp140_1.dll','libcdsprpc.dll'):
        item={'name':name,'loaded':False,'required_before_ort_import':name.startswith('msvcp')}
        try:
            # System32 only: do not accidentally validate an unrelated DLL in PATH.
            library=ctypes.WinDLL(name,winmode=0x00000800)
            pathbuf=ctypes.create_unicode_buffer(32768)
            if not kernel.GetModuleFileNameW(library._handle,pathbuf,len(pathbuf)):
                raise ctypes.WinError(ctypes.get_last_error())
            path=Path(pathbuf.value)
            item.update(loaded=True,sha256=sha(path),pe_machine=pe_machine(path),
                        location='System32',file_name=path.name)
        except OSError as exc:
            item.update(error=str(exc),winerror=exc.winerror)
        records.append(item)
    return records


def loaded_accelerator_modules(root):
    if platform.system()!='Windows':return []
    from ctypes import wintypes as w
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    psapi=ctypes.WinDLL('psapi',use_last_error=True)
    kernel.GetCurrentProcess.restype=w.HANDLE
    handle=kernel.GetCurrentProcess()
    modules=(w.HMODULE*2048)();needed=w.DWORD()
    psapi.EnumProcessModules.argtypes=[w.HANDLE,ctypes.POINTER(w.HMODULE),w.DWORD,ctypes.POINTER(w.DWORD)]
    psapi.EnumProcessModules.restype=w.BOOL
    psapi.GetModuleFileNameExW.argtypes=[w.HANDLE,w.HMODULE,w.LPWSTR,w.DWORD]
    psapi.GetModuleFileNameExW.restype=w.DWORD
    if not psapi.EnumProcessModules(handle,modules,ctypes.sizeof(modules),ctypes.byref(needed)):
        raise ctypes.WinError(ctypes.get_last_error())
    if needed.value>ctypes.sizeof(modules):raise RuntimeError('Module enumeration buffer exceeded')
    records=[]
    for module in modules[:needed.value//ctypes.sizeof(w.HMODULE)]:
        buf=ctypes.create_unicode_buffer(32768)
        if not psapi.GetModuleFileNameExW(handle,module,buf,len(buf)):continue
        path=Path(buf.value)
        if not path.name.lower().startswith(('qnn','onnxruntime','vcruntime','msvcp','libcdsprpc','libadsprpc')):continue
        inside=path.resolve().is_relative_to(root.resolve())
        display=str(path.resolve().relative_to(root.resolve())) if inside else path.name
        records.append({'name':path.name,'path':display,'inside_bundle':inside,
                        'sha256':sha(path),'pe_machine':pe_machine(path)})
    return records
