import sys
import os
import time
import shutil
import subprocess
import zipfile
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import traceback

# 로그 파일 설정
LOG_FILE = os.path.join(os.environ.get('TEMP', '.'), 'updater_log.txt')

def log(message):
    """로그 기록"""
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass

class UpdaterGUI:
    def __init__(self, downloaded_file, target_file):
        self.downloaded_file = downloaded_file
        self.target_file = target_file
        self.is_alive = True
        
        log(f"Updater 시작: {downloaded_file} -> {target_file}")
        
        self.root = tk.Tk()
        self.root.title("업데이트 중...")
        self.root.geometry("450x180")
        self.root.resizable(False, False)
        
        # 항상 최상위
        self.root.attributes('-topmost', True)
        
        # 중앙 배치
        self.root.eval('tk::PlaceWindow . center')
        
        # 상태 레이블
        self.status_label = tk.Label(self.root, text="업데이트를 준비하는 중...", 
                                     font=('맑은 고딕', 11, 'bold'))
        self.status_label.pack(pady=20)
        
        # 프로그레스 바
        self.progress = ttk.Progressbar(self.root, length=400, mode='indeterminate')
        self.progress.pack(pady=10)
        self.progress.start(10)
        
        # 상세 레이블
        self.detail_label = tk.Label(self.root, text="", font=('맑은 고딕', 9), fg='gray')
        self.detail_label.pack(pady=10)
        
        # 업데이트 스레드 시작
        self.update_thread = threading.Thread(target=self.perform_update)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        # GUI 실행
        log("GUI mainloop 시작")
        self.root.mainloop()
        log("GUI mainloop 종료")
    
    def update_status(self, status, detail=""):
        """GUI 상태 업데이트 (스레드 안전)"""
        log(f"상태 업데이트: {status} - {detail}")
        if self.is_alive:
            try:
                self.root.after(0, lambda: self._update_status_ui(status, detail))
            except:
                log("GUI 업데이트 실패")
    
    def _update_status_ui(self, status, detail):
        """실제 UI 업데이트"""
        try:
            self.status_label.config(text=status)
            self.detail_label.config(text=detail)
        except:
            pass
    
    def close_window(self):
        """창 닫기 (스레드 안전)"""
        log("창 닫기 시도")
        self.is_alive = False
        try:
            self.root.after(0, self.root.destroy)
        except:
            pass
    
    def show_error(self, message):
        """에러 메시지 표시 (스레드 안전)"""
        log(f"에러 표시: {message}")
        if self.is_alive:
            try:
                self.root.after(0, lambda: messagebox.showerror("업데이트 실패", message))
            except:
                pass
    
    def perform_update(self):
        """업데이트 실행 (백그라운드 스레드)"""
        try:
            log("업데이트 시작")
            
            # 1. 프로그램 종료 대기
            self.update_status("프로그램 종료 대기 중...", "잠시만 기다려주세요...")
            for i in range(5):
                time.sleep(1)
                self.update_status("프로그램 종료 대기 중...", f"{i+1}/5초")
            
            log("종료 대기 완료")
            
            # 2. 파일 타입 확인 및 처리
            new_exe = None
            is_setup_installer = False
            
            log(f"파일 타입 확인: {self.downloaded_file}")
            
            if self.downloaded_file.lower().endswith('.zip'):
                log("ZIP 파일 처리 시작")
                # ZIP 파일 처리 (Portable)
                self.update_status("ZIP 파일 압축 해제 중...", 
                                  os.path.basename(self.downloaded_file))
                
                extract_dir = os.path.join(os.path.dirname(self.downloaded_file), "extracted")
                if os.path.exists(extract_dir):
                    shutil.rmtree(extract_dir)
                os.makedirs(extract_dir)
                
                with zipfile.ZipFile(self.downloaded_file, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                new_exe = os.path.join(extract_dir, "BrowserBookmarks.exe")
                if not os.path.exists(new_exe):
                    raise Exception("BrowserBookmarks.exe를 찾을 수 없습니다.")
                
                self.update_status("압축 해제 완료", "")
                
            elif self.downloaded_file.lower().endswith('_setup.exe'):
                # Setup 인스톨러
                log("Setup 인스톨러 감지")
                is_setup_installer = True
                
            elif self.downloaded_file.lower().endswith('.exe'):
                new_exe = self.downloaded_file
            else:
                raise Exception(f"지원하지 않는 파일 형식: {self.downloaded_file}")
            
            log(f"파일 타입 확인 완료. is_setup: {is_setup_installer}")
            
            # 3. Setup 인스톨러 처리
            if is_setup_installer:
                log("Setup 처리 시작")
                self.update_status("Setup 인스톨러 실행 중...", "프로그램 종료 확인 중...")
                
                # BrowserBookmarks.exe 프로세스 강제 종료
                target_name = os.path.basename(self.target_file)
                log(f"프로세스 종료 시도: {target_name}")
                
                try:
                    result = subprocess.run(['taskkill', '/F', '/IM', target_name], 
                                 capture_output=True, timeout=5, text=True)
                    log(f"taskkill 결과: {result.returncode}, {result.stdout}")
                    self.update_status("프로그램 종료 완료", "")
                    time.sleep(2)
                except Exception as e:
                    log(f"taskkill 예외: {str(e)}")
                
                log("Setup 실행 시작")
                self.update_status("Setup 실행 중...", "자동 설치가 진행됩니다...")
                
                try:
                    # Setup 프로세스 시작
                    log(f"Setup 명령: {self.downloaded_file}")
                    setup_process = subprocess.Popen([
                        self.downloaded_file,
                        '/VERYSILENT',
                        '/SUPPRESSMSGBOXES',
                        '/NORESTART'
                    ], shell=False)
                    log(f"Setup 프로세스 시작됨. PID: {setup_process.pid}")
                except Exception as e:
                    log(f"Setup 실행 예외: {str(e)}\n{traceback.format_exc()}")
                    raise
                
                # Setup 설치 대기 (고정 시간)
                self.update_status("설치 중...", "설치가 진행 중입니다...")
                
                # 15초 대기 (일반적인 설치 시간)
                for i in range(15):
                    time.sleep(1)
                    self.update_status("설치 중...", f"{i+1}/15초")
                
                # 설치 완료 확인 (파일 존재 여부)
                self.update_status("설치 확인 중...", "")
                time.sleep(2)
                
                if not os.path.exists(self.target_file):
                    # 파일이 없으면 조금 더 대기
                    self.update_status("설치 완료 대기 중...", "")
                    time.sleep(5)
                
                self.update_status("설치 완료", "프로그램을 시작합니다...")
                time.sleep(1)
                
                # 프로그램 재시작
                self.update_status("프로그램 재시작 중...", "")
                time.sleep(1)
                
                # 재시작 시도
                target_dir = os.path.dirname(self.target_file)
                try:
                    subprocess.Popen([self.target_file], shell=False, cwd=target_dir)
                    self.update_status("업데이트 완료!", "프로그램이 시작됩니다.")
                except Exception as e:
                    # 재시작 실패 시 사용자에게 알림
                    self.show_error(f"프로그램 재시작에 실패했습니다.\n수동으로 프로그램을 시작해주세요.\n\n오류: {str(e)}")
                
                time.sleep(2)
                self.close_window()
                return
            
            # 4. Portable 파일 교체
            backup_file = f"{self.target_file}.backup"
            
            # 백업
            self.update_status("기존 파일 백업 중...", "")
            if os.path.exists(self.target_file):
                shutil.copy2(self.target_file, backup_file)
            
            # 파일 교체
            self.update_status("파일 업데이트 중...", "")
            if os.path.exists(self.target_file):
                os.remove(self.target_file)
            shutil.copy2(new_exe, self.target_file)
            
            # 임시 파일 정리
            self.update_status("임시 파일 정리 중...", "")
            if self.downloaded_file.lower().endswith('.zip'):
                if os.path.exists(self.downloaded_file):
                    os.remove(self.downloaded_file)
                if os.path.exists(extract_dir):
                    shutil.rmtree(extract_dir)
            
            # 재시작 준비
            self.update_status("프로그램 재시작 준비 중...", "")
            time.sleep(2)
            
            # 프로그램 재시작
            self.update_status("프로그램 재시작 중...", "")
            target_dir = os.path.dirname(self.target_file)
            subprocess.Popen([self.target_file], shell=False, cwd=target_dir)
            
            self.update_status("업데이트 완료!", "프로그램이 시작됩니다.")
            time.sleep(2)
            self.close_window()
            
        except Exception as e:
            # 에러 처리
            self.show_error(f"업데이트 중 오류가 발생했습니다:\n\n{str(e)}")
            
            # 롤백 시도
            if 'backup_file' in locals() and os.path.exists(backup_file):
                try:
                    if os.path.exists(self.target_file):
                        os.remove(self.target_file)
                    shutil.copy2(backup_file, self.target_file)
                    subprocess.Popen([self.target_file], shell=False)
                except:
                    pass
            
            time.sleep(3)
            self.close_window()

def main():
    if len(sys.argv) < 3:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("오류", "사용법: updater.exe <downloaded_file> <target_file>")
        sys.exit(1)
    
    downloaded_file = sys.argv[1]
    target_file = sys.argv[2]
    
    # GUI 시작
    UpdaterGUI(downloaded_file, target_file)

if __name__ == "__main__":
    main()