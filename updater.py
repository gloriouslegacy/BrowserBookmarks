import sys
import os
import time
import shutil
import subprocess
import zipfile
import tkinter as tk
from tkinter import ttk

class UpdaterGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("업데이트 중...")
        self.root.geometry("400x150")
        self.root.resizable(False, False)
        
        # 중앙 배치
        self.root.eval('tk::PlaceWindow . center')
        
        # 상태 레이블
        self.status_label = tk.Label(self.root, text="업데이트를 준비하는 중...", font=('맑은 고딕', 10))
        self.status_label.pack(pady=20)
        
        # 프로그레스 바
        self.progress = ttk.Progressbar(self.root, length=350, mode='indeterminate')
        self.progress.pack(pady=10)
        self.progress.start(10)
        
        # 상세 레이블
        self.detail_label = tk.Label(self.root, text="", font=('맑은 고딕', 8), fg='gray')
        self.detail_label.pack(pady=10)
        
    def update_status(self, status, detail=""):
        self.status_label.config(text=status)
        self.detail_label.config(text=detail)
        self.root.update()
    
    def close(self):
        self.root.destroy()

def main():
    """
    업데이터 프로그램
    사용법: updater.exe <다운로드한_파일> <대상_파일>
    - 다운로드한 파일은 ZIP 또는 EXE
    """
    if len(sys.argv) < 3:
        root = tk.Tk()
        root.withdraw()
        from tkinter import messagebox
        messagebox.showerror("오류", "사용법: updater.exe <downloaded_file> <target_file>")
        sys.exit(1)
    
    downloaded_file = sys.argv[1]
    target_file = sys.argv[2]
    
    # GUI 시작
    gui = UpdaterGUI()
    
    # 프로그램 종료 대기
    gui.update_status("프로그램 종료 대기 중...", "잠시만 기다려주세요...")
    for i in range(5):
        time.sleep(1)
        gui.update_status("프로그램 종료 대기 중...", f"{i+1}/5초")
    
    
    # 파일 타입 확인
    new_exe = None
    is_setup_installer = False
    
    if downloaded_file.lower().endswith('.zip'):
        # ZIP 파일 처리 (Portable)
        gui.update_status("ZIP 파일 압축 해제 중...", downloaded_file)
        extract_dir = os.path.join(os.path.dirname(downloaded_file), "extracted")
        
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir)
        
        with zipfile.ZipFile(downloaded_file, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # BrowserBookmarks.exe 찾기
        new_exe = os.path.join(extract_dir, "BrowserBookmarks.exe")
        if not os.path.exists(new_exe):
            gui.close()
            root = tk.Tk()
            root.withdraw()
            from tkinter import messagebox
            messagebox.showerror("오류", "BrowserBookmarks.exe를 찾을 수 없습니다.")
            sys.exit(1)
        
        gui.update_status("압축 해제 완료", "")
        
    elif downloaded_file.lower().endswith('_setup.exe'):
        # Setup 인스톨러 파일 (Setup 버전 업데이트)
        gui.update_status("Setup 인스톨러 감지", "")
        is_setup_installer = True
        
    elif downloaded_file.lower().endswith('.exe'):
        # 일반 EXE 파일
        new_exe = downloaded_file
        
    else:
        gui.close()
        root = tk.Tk()
        root.withdraw()
        from tkinter import messagebox
        messagebox.showerror("오류", f"지원하지 않는 파일 형식: {downloaded_file}")
        sys.exit(1)
    
    # Setup 인스톨러 처리
    if is_setup_installer:
        try:
            gui.update_status("Setup 인스톨러 실행 중...", "잠시만 기다려주세요...")
            # Setup.exe를 자동 설치 모드로 실행
            subprocess.Popen([
                downloaded_file,
                '/VERYSILENT',
                '/SUPPRESSMSGBOXES',
                '/CLOSEAPPLICATIONS',
                '/NORESTART'
            ], shell=False)
            
            # Setup이 설치를 완료할 때까지 대기
            for i in range(10):
                time.sleep(1)
                gui.update_status("설치 중...", f"{i+1}/10초")
            
            # 프로그램 재시작
            gui.update_status("프로그램 재시작 중...", "")
            target_dir = os.path.dirname(target_file)
            subprocess.Popen([target_file], shell=False, cwd=target_dir)
            
            gui.update_status("업데이트 완료!", "프로그램이 곧 시작됩니다.")
            time.sleep(1)
            gui.close()
            sys.exit(0)
            
        except Exception as e:
            gui.close()
            root = tk.Tk()
            root.withdraw()
            from tkinter import messagebox
            messagebox.showerror("오류", f"Setup 실행 실패:\n{str(e)}")
            sys.exit(1)
    
    # 백업 생성 (Portable만)
    backup_file = f"{target_file}.backup"
    try:
        gui.update_status("기존 파일 백업 중...", backup_file)
        if os.path.exists(target_file):
            shutil.copy2(target_file, backup_file)
    except Exception as e:
        pass  # 백업 실패해도 계속 진행
    
    # 파일 교체 (Portable)
    try:
        gui.update_status("파일 업데이트 중...", "")
        if os.path.exists(target_file):
            os.remove(target_file)
        shutil.copy2(new_exe, target_file)
        
        # 임시 파일 정리
        gui.update_status("임시 파일 정리 중...", "")
        if downloaded_file.lower().endswith('.zip'):
            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
        
        # 프로그램 재시작 전 대기
        gui.update_status("프로그램 재시작 준비 중...", "")
        time.sleep(2)
        
        # 프로그램 재시작
        gui.update_status("프로그램 재시작 중...", "")
        target_dir = os.path.dirname(target_file)
        subprocess.Popen([target_file], shell=False, cwd=target_dir)
        
        gui.update_status("업데이트 완료!", "프로그램이 곧 시작됩니다.")
        time.sleep(1)
        gui.close()
        
    except Exception as e:
        gui.close()
        
        # 롤백 시도
        if os.path.exists(backup_file):
            try:
                if os.path.exists(target_file):
                    os.remove(target_file)
                shutil.copy2(backup_file, target_file)
                
                # 원래 프로그램 재시작
                subprocess.Popen([target_file], shell=False)
            except:
                pass
        
        root = tk.Tk()
        root.withdraw()
        from tkinter import messagebox
        messagebox.showerror("업데이트 실패", f"업데이트 중 오류가 발생했습니다:\n{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()