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
        """업데이트 실행 (백그라운드 스레드) - Portable 버전만 처리"""
        try:
            log("업데이트 시작 (Portable 전용)")
            
            # 1. 프로그램 종료 대기
            self.update_status("프로그램 종료 대기 중...", "잠시만 기다려주세요...")
            for i in range(5):
                time.sleep(1)
                self.update_status("프로그램 종료 대기 중...", f"{i+1}/5초")
            
            log("종료 대기 완료")
            
            # 2. 파일 타입 확인 및 처리 (Portable만)
            new_exe = None
            
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
                log("ZIP 압축 해제 완료")
                
            elif self.downloaded_file.lower().endswith('.exe'):
                log("단일 EXE 파일 처리")
                new_exe = self.downloaded_file
            else:
                raise Exception(f"지원하지 않는 파일 형식: {self.downloaded_file}")
            
            log(f"파일 타입 확인 완료. new_exe: {new_exe}")
            
            # 3. Portable 파일 교체
            backup_file = f"{self.target_file}.backup"
            
            # 백업
            self.update_status("기존 파일 백업 중...", "")
            if os.path.exists(self.target_file):
                shutil.copy2(self.target_file, backup_file)
                log("백업 완료")
            
            # 파일 교체
            self.update_status("파일 업데이트 중...", "")
            if os.path.exists(self.target_file):
                os.remove(self.target_file)
            shutil.copy2(new_exe, self.target_file)
            log("파일 교체 완료")
            
            # 임시 파일 정리
            self.update_status("임시 파일 정리 중...", "")
            if self.downloaded_file.lower().endswith('.zip'):
                if os.path.exists(self.downloaded_file):
                    os.remove(self.downloaded_file)
                if os.path.exists(extract_dir):
                    shutil.rmtree(extract_dir)
            log("임시 파일 정리 완료")
            
            # 재시작 준비
            self.update_status("프로그램 재시작 준비 중...", "")
            time.sleep(2)
            
            # 프로그램 재시작
            self.update_status("프로그램 재시작 중...", "")
            target_dir = os.path.dirname(self.target_file)
            subprocess.Popen([self.target_file], shell=False, cwd=target_dir)
            log("프로그램 재시작 완료")
            
            self.update_status("업데이트 완료!", "프로그램이 시작됩니다.")
            time.sleep(2)
            self.close_window()
            log("업데이트 프로세스 완료")
            
        except Exception as e:
            # 에러 처리
            log(f"업데이트 실패: {str(e)}\n{traceback.format_exc()}")
            self.show_error(f"업데이트 중 오류가 발생했습니다:\n\n{str(e)}")
            
            # 롤백 시도
            if 'backup_file' in locals() and os.path.exists(backup_file):
                try:
                    log("롤백 시도")
                    if os.path.exists(self.target_file):
                        os.remove(self.target_file)
                    shutil.copy2(backup_file, self.target_file)
                    subprocess.Popen([self.target_file], shell=False)
                    log("롤백 완료")
                except Exception as rollback_e:
                    log(f"롤백 실패: {str(rollback_e)}")
            
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
    
    log(f"=== Updater 시작 ===")
    log(f"Downloaded: {downloaded_file}")
    log(f"Target: {target_file}")
    
    # GUI 시작
    UpdaterGUI(downloaded_file, target_file)
    
    log("=== Updater 종료 ===")

if __name__ == "__main__":
    main()