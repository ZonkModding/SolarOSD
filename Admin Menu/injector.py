import sys
import os
import ctypes
from ctypes import wintypes
import time

# Check for 64-bit Python
if sys.maxsize <= 2**32:
    print("WARNING: You are using 32-bit Python.")
    print("For injection into 64-bit process (Win64-Shipping), 64-bit Python is required.")
    sys.exit(1)

# WinAPI Constants
PROCESS_ALL_ACCESS = 0x1F0FFF
MEM_COMMIT = 0x00001000
MEM_RESERVE = 0x00002000
PAGE_READWRITE = 0x04
INFINITE = 0xFFFFFFFF
TH32CS_SNAPPROCESS = 0x00000002

# Data Types
LPVOID = ctypes.c_void_p
SIZE_T = ctypes.c_size_t
LPCTSTR = ctypes.c_char_p # ANSI

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(wintypes.ULONG)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", ctypes.c_char * 260)
    ]

# Load kernel32
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# Function definitions
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE

kernel32.VirtualAllocEx.argtypes = [wintypes.HANDLE, LPVOID, SIZE_T, wintypes.DWORD, wintypes.DWORD]
kernel32.VirtualAllocEx.restype = LPVOID

kernel32.WriteProcessMemory.argtypes = [wintypes.HANDLE, LPVOID, ctypes.c_void_p, SIZE_T, ctypes.POINTER(SIZE_T)]
kernel32.WriteProcessMemory.restype = wintypes.BOOL

kernel32.GetModuleHandleA.argtypes = [LPCTSTR]
kernel32.GetModuleHandleA.restype = wintypes.HMODULE

kernel32.GetProcAddress.argtypes = [wintypes.HMODULE, LPCTSTR]
kernel32.GetProcAddress.restype = LPVOID

kernel32.CreateRemoteThread.argtypes = [wintypes.HANDLE, LPVOID, SIZE_T, LPVOID, LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
kernel32.CreateRemoteThread.restype = wintypes.HANDLE

kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE

kernel32.Process32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
kernel32.Process32First.restype = wintypes.BOOL

kernel32.Process32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
kernel32.Process32Next.restype = wintypes.BOOL

kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL

kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
kernel32.WaitForSingleObject.restype = wintypes.DWORD

kernel32.GetExitCodeThread.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
kernel32.GetExitCodeThread.restype = wintypes.BOOL

def get_pid(process_name):
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == wintypes.HANDLE(-1).value:
        return None

    entry = PROCESSENTRY32()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32)

    if not kernel32.Process32First(snapshot, ctypes.byref(entry)):
        kernel32.CloseHandle(snapshot)
        return None

    while True:
        exe_file = entry.szExeFile.decode('utf-8', errors='ignore')
        if exe_file.lower() == process_name.lower():
            pid = entry.th32ProcessID
            kernel32.CloseHandle(snapshot)
            return pid
        
        if not kernel32.Process32Next(snapshot, ctypes.byref(entry)):
            break

    kernel32.CloseHandle(snapshot)
    return None

def inject_dll(pid, dll_path):
    if not os.path.exists(dll_path):
        print(f"Error: DLL not found at: {dll_path}")
        return False

    dll_path_bytes = dll_path.encode('utf-8')
    dll_path_len = len(dll_path_bytes) + 1

    print(f"Opening process PID: {pid}...")
    h_process = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not h_process:
        print(f"Error: Could not open process. Code: {ctypes.get_last_error()}")
        return False

    try:
        print("Allocating memory...")
        arg_address = kernel32.VirtualAllocEx(h_process, None, dll_path_len, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE)
        if not arg_address:
            print(f"Error: Could not allocate memory. Code: {ctypes.get_last_error()}")
            return False
        
        print(f"Memory allocated at: {hex(arg_address)}")

        print("Writing DLL path...")
        written = SIZE_T(0)
        success = kernel32.WriteProcessMemory(h_process, arg_address, dll_path_bytes, dll_path_len, ctypes.byref(written))
        if not success:
            print(f"Error: Could not write memory. Code: {ctypes.get_last_error()}")
            return False
        
        print("Getting LoadLibraryA address...")
        h_kernel32 = kernel32.GetModuleHandleA(b"kernel32.dll")
        load_library_addr = kernel32.GetProcAddress(h_kernel32, b"LoadLibraryA")
        
        if not load_library_addr:
             print("Error: Could not find LoadLibraryA.")
             return False
        
        print("Creating remote thread...")
        thread_id = wintypes.DWORD(0)
        h_thread = kernel32.CreateRemoteThread(h_process, None, 0, load_library_addr, arg_address, 0, ctypes.byref(thread_id))
        
        if not h_thread:
            print(f"Error: Could not create remote thread. Code: {ctypes.get_last_error()}")
            return False
        
        print(f"Thread created. ID: {thread_id.value}")
        print("Waiting for thread...")
        kernel32.WaitForSingleObject(h_thread, INFINITE)
        
        exit_code = wintypes.DWORD(0)
        kernel32.GetExitCodeThread(h_thread, ctypes.byref(exit_code))
        print(f"Thread exited with code: {exit_code.value}")

        kernel32.CloseHandle(h_thread)
        print("Admin Menu injected successfully!")
        return True

    finally:
        kernel32.CloseHandle(h_process)

if __name__ == "__main__":
    TARGET_PROCESS = "FPVKamikazeDrone-Win64-Shipping.exe"
    # Path to Admin Menu DLL relative to this script
    DLL_REL_PATH = r"..\build_admin\Release\Admin_Menu.dll"
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dll_path = os.path.abspath(os.path.join(current_dir, DLL_REL_PATH))
    
    print(f"--- Admin Menu Injector ---")
    print(f"Looking for process {TARGET_PROCESS}...")
    pid = get_pid(TARGET_PROCESS)
    if pid:
        print(f"Found PID: {pid}")
        print(f"Target DLL: {dll_path}")
        inject_dll(pid, dll_path)
    else:
        print(f"Process {TARGET_PROCESS} not found.")
        print("Please start the game first.")
