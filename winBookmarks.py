import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Menu
import os
import shutil
from datetime import datetime
import sys
import subprocess 
import time
import json
import configparser
import hashlib
import threading
import urllib.request
import urllib.error

# 버전 정보 
CURRENT_VERSION = "0.0.0"
GITHUB_REPO = "gloriouslegacy/BrowserBookmarks"
VERSION_CHECK_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# UI 스타일 및 색상 정의
BG_COLOR = "#f0f0f0"          
PRIMARY_COLOR = "#3273a8"     
SECONDARY_COLOR = "#cc4444"   
HOVER_COLOR_P = "#4a8ac2"     
HOVER_COLOR_S = "#e05252"     
TEXT_COLOR = "#333333"        
BUTTON_FG = "#ffffff"

# 다크모드 색상 
DARK_BG_COLOR = "#0d0d0d"
DARK_TEXT_COLOR = "#d0d0d0"
DARK_FRAME_BG = "#0d0d0d"
DARK_ENTRY_BG = "#000000"
DARK_PRIMARY_COLOR = "#1a3a52"
DARK_SECONDARY_COLOR = "#5a1a1a"

def resource_path(relative_path):
    """
    빌드된 실행 파일 환경에서 리소스를 찾는 경로를 반환하고, 
    일반 실행 환경에서는 현재 경로를 반환.
    """
    try:
        # PyInstaller로 빌드된 경우
        base_path = sys._MEIPASS
    except Exception:
        # 일반 Python 스크립트 실행 환경
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)    

def get_appdata_path():
    """
    %APPDATA% 경로 반환
    """
    appdata = os.environ.get('APPDATA')
    app_folder = os.path.join(appdata, 'BrowserBookmarks')
    os.makedirs(app_folder, exist_ok=True)
    return app_folder

# 설정 파일 관리 
class ConfigManager:
    def __init__(self):
        self.config_dir = get_appdata_path()
        self.config_file = os.path.join(self.config_dir, "app_config.json")
        self.default_config = {
            "language": "ko",
            "dark_mode": False,
            "last_backup_dir": os.path.join(os.getcwd(), "Bookmarks_Backup"),
            "last_browser": "Edge",
            "window_width": 600,
            "window_height": 500,
            "auto_update_check": True
        }
        self.config = self.load_config()
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 기본 설정과 병합
                    return {**self.default_config, **loaded_config}
            except Exception as e:
                print(f"설정 로드 실패: {e}")
                return self.default_config.copy()
        return self.default_config.copy()
    
    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"설정 저장 실패: {e}")
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        self.save_config()

# 언어 파일 관리 
class LanguageManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        
        # Portable 버전: 실행 파일 옆 language 폴더 우선 사용
        # Setup 버전: %APPDATA% 사용
        exe_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
        portable_lang_dir = os.path.join(exe_dir, "language")
        
        # Portable language 폴더가 존재하고 쓰기 가능하면 사용
        if os.path.exists(portable_lang_dir) and os.access(portable_lang_dir, os.W_OK):
            self.lang_dir = portable_lang_dir
        else:
            # 없거나 쓰기 불가능하면 %APPDATA% 사용
            app_folder = get_appdata_path()
            self.lang_dir = os.path.join(app_folder, "language")
        
        self.current_lang = config_manager.get("language", "ko")
        self.translations = {}
        self.load_language()
    
    def load_language(self):
        # 언어 파일 항상 재생성 (업데이트된 키 반영)
        self.create_default_language_files()
        
        lang_file = os.path.join(self.lang_dir, f"lang_{self.current_lang}.ini")
        
        config = configparser.ConfigParser()
        try:
            config.read(lang_file, encoding='utf-8')
            for section in config.sections():
                self.translations[section] = dict(config.items(section))
        except Exception as e:
            print(f"언어 파일 로드 실패: {e}")
    
    def create_default_language_files(self):
        os.makedirs(self.lang_dir, exist_ok=True)
        
        # 한국어
        ko_content = """[app]
title = 브라우저 북마크 관리

[menu]
file = 파일
language = 언어 변경
dark_mode = 다크 모드
exit = 종료
help = 도움말
check_update = 업데이트 확인
visit_github = GitHub 방문
about = 정보

[main]
settings = ⚙️ 북마크 백업/복구 설정
browser_select = 브라우저 선택:
path_select = 경로 선택:
folder_select = 폴더 선택
backup_button = 💾 북마크 백업
restore_button = ↩️ 북마크 복구
log_title = 📝 실행 결과 로그
clear_log = 로그 지우기

[messages]
backup_success = 백업 완료
restore_success = 복구 완료
error = 오류
warning = 경고
info = 정보
select_folder = 백업 폴더를 선택해주세요.
file_not_found = 북마크 파일을 찾을 수 없습니다.
restore_file_missing = 복구 파일이 백업 폴더에 없습니다.
browser_running = 브라우저가 실행 중입니다. 종료 후 다시 시도하세요.
sync_warning_title = ⚠️ 브라우저 복구 전: 클라우드 동기화 경고
sync_warning_edge = 엣지(Edge)의 **Microsoft 계정 동기화**
sync_warning_chrome = 크롬(Chrome)의 **Google 계정 동기화**
sync_warning_firefox = 파이어폭스(Firefox)의 **Firefox Sync**
sync_warning_message = **{browser}** 복구 시 **클라우드 동기화 기능**이 복구된 북마크를 이전 상태로 덮어쓸 수 있습니다.
    
    복구 전, **{browser} 브라우저를 수동으로 켜서 {sync_detail} 기능을 '끄기'**로 설정해야 합니다.
    
    **[예]**를 누르면 브라우저를 강제 종료하고 복구 작업을 시작합니다. 동기화를 껐는지 확인 후 진행해 주세요.

[update]
checking = 업데이트 확인 중...
available = 새 버전이 있습니다!
no_update = 최신 버전을 사용 중입니다.
download_progress = 다운로드 중...
installing = 설치 중...
complete = 업데이트 완료
failed = 업데이트 실패
title = 업데이트
current_version = 현재 버전
latest_version = 최신 버전
download_question = 업데이트를 다운로드하시겠습니까?
download_url_error = 다운로드 URL을 찾을 수 없습니다.
download_failed = 다운로드 실패
install_failed = 설치 실패

[about]
version = 버전
developer = 개발자
description = Windows용 브라우저 북마크 백업/복구 도구
"""
        
        # 영어
        en_content = """[app]
title = Browser Bookmark Manager

[menu]
file = File
language = Change Language
dark_mode = Dark Mode
exit = Exit
help = Help
check_update = Check for Updates
visit_github = Visit GitHub
about = About

[main]
settings = ⚙️ Bookmark Backup/Restore Settings
browser_select = Select Browser:
path_select = Select Path:
folder_select = Browse Folder
backup_button = 💾 Backup Bookmarks
restore_button = ↩️ Restore Bookmarks
log_title = 📝 Execution Log
clear_log = Clear Log

[messages]
backup_success = Backup Complete
restore_success = Restore Complete
error = Error
warning = Warning
info = Information
select_folder = Please select a backup folder.
file_not_found = Bookmark file not found.
restore_file_missing = Restore file missing in backup folder.
browser_running = Browser is running. Please close and try again.
sync_warning_title = ⚠️ Before Restore: Cloud Sync Warning
sync_warning_edge = Edge's **Microsoft Account Sync**
sync_warning_chrome = Chrome's **Google Account Sync**
sync_warning_firefox = Firefox's **Firefox Sync**
sync_warning_message = When restoring **{browser}**, **cloud sync** may overwrite your restored bookmarks.
    
    Before restoring, please manually open **{browser}** and **disable {sync_detail}**.
    
    Press **[Yes]** to force close the browser and start restoration. Make sure sync is disabled before proceeding.

[update]
checking = Checking for updates...
available = New version available!
no_update = You are using the latest version.
download_progress = Downloading...
installing = Installing...
complete = Update Complete
failed = Update Failed
title = Update
current_version = Current Version
latest_version = Latest Version
download_question = Would you like to download the update?
download_url_error = Download URL not found.
download_failed = Download failed
install_failed = Installation failed

[about]
version = Version
developer = Developer
description = Browser Bookmark Backup/Restore Tool for Windows
"""
        
        with open(os.path.join(self.lang_dir, "lang_ko.ini"), 'w', encoding='utf-8') as f:
            f.write(ko_content)
        
        with open(os.path.join(self.lang_dir, "lang_en.ini"), 'w', encoding='utf-8') as f:
            f.write(en_content)
    
    def get(self, section, key, default=""):
        return self.translations.get(section, {}).get(key, default)
    
    def change_language(self, lang_code):
        self.current_lang = lang_code
        self.config_manager.set("language", lang_code)
        self.load_language()

# 업데이트 관리자 
class UpdateManager:
    def __init__(self, lang_manager):
        self.lang_manager = lang_manager
        self.check_url = VERSION_CHECK_URL
        self.current_version = CURRENT_VERSION
        
    def check_for_updates(self, callback=None):
        """업데이트 확인 (비동기)"""
        thread = threading.Thread(target=self._check_updates_thread, args=(callback,))
        thread.daemon = True
        thread.start()
    
    def _check_updates_thread(self, callback):
        try:
            with urllib.request.urlopen(self.check_url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                latest_version = data.get('tag_name', '').replace('v', '')
                
                if latest_version and self._is_newer_version(latest_version):
                    version_info = {
                        'version': latest_version,
                        'download_url': None,
                        'body': data.get('body', '')
                    }
                    
                    # 다운로드 URL 찾기 - Setup 또는 Portable
                    # Setup 버전이 설치되어 있으면 Setup 다운로드, 아니면 Portable
                    is_setup_installed = self._is_setup_installed()
                    
                    for asset in data.get('assets', []):
                        name = asset['name'].lower()
                        if is_setup_installed:
                            # Setup 버전 찾기
                            if name.endswith('_setup.exe'):
                                version_info['download_url'] = asset['browser_download_url']
                                version_info['is_setup'] = True
                                break
                        else:
                            # Portable 버전 찾기 (ZIP)
                            if 'portable' in name and name.endswith('.zip'):
                                version_info['download_url'] = asset['browser_download_url']
                                version_info['is_setup'] = False
                                break
                    
                    if callback:
                        callback(True, version_info)
                else:
                    if callback:
                        callback(False, None)
        except Exception as e:
            print(f"업데이트 확인 실패: {e}")
            if callback:
                callback(False, None)
    
    def _is_newer_version(self, remote_version):
        """버전 비교"""
        try:
            current = tuple(map(int, self.current_version.split('.')))
            remote = tuple(map(int, remote_version.split('.')))
            return remote > current
        except:
            return False
    
    def _is_setup_installed(self):
        """Setup 버전으로 설치되었는지 확인"""
        exe_path = sys.executable if getattr(sys, 'frozen', False) else __file__
        exe_dir = os.path.dirname(exe_path)
        
        # unins000.exe가 있으면 Setup 버전 (Inno Setup uninstaller)
        # 설치 경로와 무관하게 uninstaller 존재 여부로 판단
        uninstaller = os.path.join(exe_dir, "unins000.exe")
        return os.path.exists(uninstaller)
    
    def download_update(self, download_url, progress_callback=None):
        """업데이트 다운로드"""
        try:
            download_path = os.path.join(get_appdata_path(), "update_temp")
            os.makedirs(download_path, exist_ok=True)
            
            file_name = download_url.split('/')[-1]
            local_file = os.path.join(download_path, file_name)
            
            def report_progress(block_num, block_size, total_size):
                if progress_callback and total_size > 0:
                    downloaded = block_num * block_size
                    percent = min(100, int((downloaded / total_size) * 100))
                    progress_callback(percent)
            
            urllib.request.urlretrieve(download_url, local_file, reporthook=report_progress)
            return local_file
        except Exception as e:
            print(f"다운로드 실패: {e}")
            return None
    
    def create_backup(self):
        """현재 실행 파일 백업"""
        try:
            exe_path = sys.executable if getattr(sys, 'frozen', False) else __file__
            backup_path = f"{exe_path}.backup"
            shutil.copy2(exe_path, backup_path)
            return backup_path
        except Exception as e:
            print(f"백업 실패: {e}")
            return None
    
    def install_update(self, update_file, is_setup=False):
        """업데이트 설치"""
        try:
            exe_path = sys.executable if getattr(sys, 'frozen', False) else __file__
            
            if is_setup:
                # Setup 파일 자동 설치 (Very Silent)
                subprocess.Popen([update_file, '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'], shell=False)
                return True
            else:
                # Portable: updater.exe 사용
                exe_dir = os.path.dirname(exe_path)
                updater_path = os.path.join(exe_dir, "updater.exe")
                
                if not os.path.exists(updater_path):
                    # ZIP 파일에서 직접 추출 필요
                    import zipfile
                    temp_dir = os.path.join(get_appdata_path(), "update_extract")
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    with zipfile.ZipFile(update_file, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    # 추출된 파일 찾기
                    new_exe = os.path.join(temp_dir, "BrowserBookmarks.exe")
                    new_updater = os.path.join(temp_dir, "updater.exe")
                    
                    if os.path.exists(new_updater):
                        updater_path = new_updater
                
                if not os.path.exists(updater_path):
                    messagebox.showerror("오류", "updater.exe를 찾을 수 없습니다.")
                    return False
                
                # Portable ZIP에서 추출된 새 EXE 경로
                if update_file.endswith('.zip'):
                    temp_dir = os.path.join(get_appdata_path(), "update_extract")
                    new_exe_file = os.path.join(temp_dir, "BrowserBookmarks.exe")
                else:
                    new_exe_file = update_file
                
                # updater.exe 실행
                subprocess.Popen([updater_path, new_exe_file, exe_path], shell=False)
                return True
        except Exception as e:
            print(f"설치 실패: {e}")
            return False

# 브라우저별 북마크 경로 정의 
def get_browser_paths():
    """각 브라우저의 기본 북마크 파일 경로를 반환"""
    user_profile = os.environ.get('USERPROFILE')
    
    paths = {
        "Edge": os.path.join(user_profile, 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data', 'Default', 'Bookmarks'),
        "Chrome": os.path.join(user_profile, 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'Bookmarks'),
        "Firefox": None, 
    }
    
    firefox_profile_root = os.path.join(user_profile, 'AppData', 'Roaming', 'Mozilla', 'Firefox', 'Profiles')
    
    if os.path.exists(firefox_profile_root):
        latest_profile_path = None
        latest_mtime = 0
        
        for profile_name in os.listdir(firefox_profile_root):
            profile_path = os.path.join(firefox_profile_root, profile_name)
            places_sqlite_path = os.path.join(profile_path, 'places.sqlite')
            
            if os.path.isdir(profile_path) and os.path.exists(places_sqlite_path):
                try:
                    mtime = os.path.getmtime(places_sqlite_path)
                    if mtime > latest_mtime:
                        latest_mtime = mtime
                        latest_profile_path = places_sqlite_path
                except OSError:
                    continue
        
        if latest_profile_path:
            paths["Firefox"] = latest_profile_path
            
    return paths

BROWSER_PATHS = get_browser_paths()
BACKUP_FILENAME_MAP = {
    "Edge": "Edge_Bookmarks",
    "Chrome": "Chrome_Bookmarks",
    "Firefox": "firefox_places.sqlite" 
}
BROWSER_EXE_MAP = {
    "Edge": "msedge.exe",
    "Chrome": "chrome.exe",
    "Firefox": "firefox.exe"
}

# 핵심 로직 함수 
def perform_backup(browser_name, backup_dir):
    """지정된 브라우저의 북마크 파일을 지정된 디렉토리에 백업."""
    src_path = BROWSER_PATHS.get(browser_name)
    backup_filename = BACKUP_FILENAME_MAP.get(browser_name)
    
    if not src_path or not os.path.exists(src_path):
        display_path = src_path if src_path else "자동 감지 실패"
        log_message(f"[오류] {browser_name} 북마크 파일을 찾을 수 없습니다.")
        messagebox.showerror("오류", f"{browser_name} 북마크 파일을 찾을 수 없습니다.\n경로 확인:\n{display_path}")
        return False

    if not backup_dir:
        messagebox.showwarning("경고", "백업 폴더를 선택해주세요.")
        return False

    os.makedirs(backup_dir, exist_ok=True)
    dst_path = os.path.join(backup_dir, backup_filename)
    
    try:
        shutil.copy2(src_path, dst_path)
        log_message(f"[성공] {browser_name} 백업 완료: {dst_path}")
        return True
    except Exception as e:
        log_message(f"[오류] {browser_name} 백업 실패: {e}")
        messagebox.showerror("오류", f"{browser_name} 백업 중 오류 발생: {e}")
        return False

def perform_restore(browser_name, restore_dir):
    """지정된 브라우저의 북마크 파일을 백업 디렉토리에서 복구합니다."""
    dst_path = BROWSER_PATHS.get(browser_name)
    backup_filename = BACKUP_FILENAME_MAP.get(browser_name)
    src_path = os.path.join(restore_dir, backup_filename)
    browser_exe = BROWSER_EXE_MAP.get(browser_name)

    if not os.path.exists(src_path):
        messagebox.showerror("오류", f"복구 파일이 백업 폴더에 없습니다.\n필요한 파일: {backup_filename}")
        return False

    if not dst_path or not os.path.exists(os.path.dirname(dst_path)):
         log_message(f"[오류] {browser_name} 복구 대상 경로를 찾을 수 없습니다.")
         messagebox.showerror("오류", f"{browser_name} 복구 대상 경로를 찾을 수 없습니다.\n브라우저를 한 번 실행해 보세요.")
         return False
    
    
    # 복구 전 프로세스 종료 로직
    try:
        if browser_exe:
            log_message(f"[정보] {browser_name} 프로세스 ({browser_exe}) 종료 시도...")
            subprocess.run(['taskkill', '/f', '/im', browser_exe], check=True, capture_output=True, text=True)
            log_message(f"[정보] {browser_name} 프로세스 종료 완료.")
            time.sleep(1) 
    except subprocess.CalledProcessError:
        log_message(f"[정보] {browser_name} 프로세스가 실행 중이 아니거나 이미 종료되었습니다.")
    except Exception as e:
        log_message(f"[오류] 프로세스 종료 중 예외 발생: {e}")
        messagebox.showwarning("경고", "브라우저 프로세스 종료에 실패했습니다. 수동으로 종료해 주세요.")
        
    
    # 복구 실행
    restore_success = False
    try:
        if os.path.exists(dst_path):
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            backup_old_path = f"{dst_path}.{timestamp}.bak"
            shutil.copy2(dst_path, backup_old_path)
            log_message(f"[정보] 기존 북마크 백업: {backup_old_path}")
            
        shutil.copy2(src_path, dst_path)
        log_message(f"[성공] {browser_name} 복구 완료: {dst_path}")
        restore_success = True
        
    except Exception as e:
        log_message(f"[오류] {browser_name} 복구 실패: {e}")
        messagebox.showerror("오류", f"{browser_name} 복구 중 오류 발생: {e}")
        
    # 복구 후 프로세스 재실행 로직
    if restore_success and browser_exe:
        try:
            log_message(f"[정보] {browser_name} 재실행 시도...")
            subprocess.Popen(['start', browser_exe], shell=True)
            log_message(f"[성공] {browser_name} 재실행 완료.")
        except Exception as e:
            log_message(f"[오류] 브라우저 재실행 실패: {e}")
            messagebox.showwarning("경고", "브라우저 재실행에 실패했습니다. 수동으로 시작해 주세요.")
            
    return restore_success

# GUI 클래스 
class BookmarkManagerGUI:
    def __init__(self, master):
        self.master = master
        self.config_manager = ConfigManager()
        self.lang_manager = LanguageManager(self.config_manager)
        self.update_manager = UpdateManager(self.lang_manager)
        
        # 창 크기 최적화 (70%)
        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()
        window_width = int(600 * 0.7)
        window_height = int(600 * 0.7)
        
        # 창을 화면 중앙에 배치
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        master.geometry(f"{window_width}x{window_height}+{x}+{y}")
        master.title(self.lang_manager.get("app", "title"))
        
        # 아이콘 설정
        try:
            icon_path = resource_path(os.path.join('icon', 'icon.ico'))
            if os.path.exists(icon_path):
                master.iconbitmap(icon_path)
        except Exception:
            pass 

        self.browser_list = list(BROWSER_PATHS.keys())
        self.selected_browser = tk.StringVar(value=self.config_manager.get("last_browser", self.browser_list[0]))
        self.backup_dir = tk.StringVar(value=self.config_manager.get("last_backup_dir"))
        self.log_text = None
        self.dark_mode = self.config_manager.get("dark_mode", False)
        
        # 위젯 참조 저장
        self.widgets = {}
        
        self._create_menu()
        self._create_widgets()
        self._apply_theme()
        
        # 자동 업데이트 확인
        if self.config_manager.get("auto_update_check", True):
            self.update_manager.check_for_updates(self._on_update_check_complete)
        
    def _create_menu(self):
        """메뉴바 생성"""
        menubar = Menu(self.master)
        self.master.config(menu=menubar)
        
        # File 메뉴
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.lang_manager.get("menu", "file"), menu=file_menu)
        
        # 언어 변경 서브메뉴
        lang_menu = Menu(file_menu, tearoff=0)
        lang_menu.add_command(label="한국어", command=lambda: self._change_language("ko"))
        lang_menu.add_command(label="English", command=lambda: self._change_language("en"))
        file_menu.add_cascade(label=self.lang_manager.get("menu", "language"), menu=lang_menu)
        
        self.dark_mode_var = tk.BooleanVar(value=self.dark_mode)
        file_menu.add_checkbutton(label=self.lang_manager.get("menu", "dark_mode"), 
                                   command=self._toggle_dark_mode,
                                   variable=self.dark_mode_var)
        file_menu.add_separator()
        file_menu.add_command(label=self.lang_manager.get("menu", "exit"), command=self._on_exit)
        
        # Help 메뉴
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.lang_manager.get("menu", "help"), menu=help_menu)
        help_menu.add_command(label=self.lang_manager.get("menu", "check_update"), 
                              command=self._manual_update_check)
        help_menu.add_command(label=self.lang_manager.get("menu", "visit_github"), 
                              command=self._visit_github)
        help_menu.add_separator()
        help_menu.add_command(label=self.lang_manager.get("menu", "about"), 
                              command=self._show_about)
        
    def _create_widgets(self):
        # Tkinter 기본 스타일 설정
        style = ttk.Style(self.master)
        style.theme_use('clam')
        
        # 1. 설정 섹션
        settings_frame = ttk.LabelFrame(self.master, 
                                        text=self.lang_manager.get("main", "settings"), 
                                        padding="10 10 10 10")
        settings_frame.pack(padx=10, pady=10, fill="x")
        self.widgets['settings_frame'] = settings_frame

        # 브라우저 선택 드롭다운
        browser_label = ttk.Label(settings_frame, text=self.lang_manager.get("main", "browser_select"))
        browser_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.widgets['browser_label'] = browser_label
        
        browser_menu = ttk.OptionMenu(settings_frame, self.selected_browser, self.browser_list[0], *self.browser_list)
        browser_menu.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.widgets['browser_menu'] = browser_menu

        # 백업/복구 경로 선택
        path_label = ttk.Label(settings_frame, text=self.lang_manager.get("main", "path_select"))
        path_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.widgets['path_label'] = path_label
        
        self.dir_entry = ttk.Entry(settings_frame, textvariable=self.backup_dir, width=30)
        self.dir_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.widgets['dir_entry'] = self.dir_entry
        
        browse_btn = ttk.Button(settings_frame, 
                   text=self.lang_manager.get("main", "folder_select"), 
                   command=self.select_directory)
        browse_btn.grid(row=1, column=2, padx=5, pady=5)
        self.widgets['browse_btn'] = browse_btn
        
        settings_frame.grid_columnconfigure(1, weight=1)

        # 2. 실행 섹션 
        action_frame = ttk.Frame(self.master)
        action_frame.pack(padx=10, pady=5, fill="x")
        self.widgets['action_frame'] = action_frame
        
        # 백업 버튼 
        self.backup_btn = tk.Button(action_frame, 
                                    text=self.lang_manager.get("main", "backup_button"), 
                                    command=self.handle_backup, 
                                    bg=PRIMARY_COLOR, fg=BUTTON_FG, height=2, bd=0, relief='flat', 
                                    font=('Malgun Gothic', 9, 'bold'), 
                                    activebackground=HOVER_COLOR_P, activeforeground=BUTTON_FG)
        self.backup_btn.pack(side="left", fill="x", expand=True, padx=5)
        self.backup_btn.bind("<Enter>", lambda e: self.backup_btn.config(bg=HOVER_COLOR_P))
        self.backup_btn.bind("<Leave>", lambda e: self.backup_btn.config(bg=PRIMARY_COLOR if not self.dark_mode else DARK_PRIMARY_COLOR))
        self.widgets['backup_btn'] = self.backup_btn

        # 복구 버튼
        self.restore_btn = tk.Button(action_frame, 
                                     text=self.lang_manager.get("main", "restore_button"), 
                                     command=self.handle_restore, 
                                     bg=SECONDARY_COLOR, fg=BUTTON_FG, height=2, bd=0, relief='flat',
                                     font=('Malgun Gothic', 9, 'bold'), 
                                     activebackground=HOVER_COLOR_S, activeforeground=BUTTON_FG)
        self.restore_btn.pack(side="left", fill="x", expand=True, padx=5)
        self.restore_btn.bind("<Enter>", lambda e: self.restore_btn.config(bg=HOVER_COLOR_S))
        self.restore_btn.bind("<Leave>", lambda e: self.restore_btn.config(bg=SECONDARY_COLOR if not self.dark_mode else DARK_SECONDARY_COLOR))
        self.widgets['restore_btn'] = self.restore_btn
        
        # 3. 로그 섹션
        log_frame = ttk.LabelFrame(self.master, 
                                   text=self.lang_manager.get("main", "log_title"), 
                                   padding="10 10 10 10")
        log_frame.pack(padx=10, pady=10, fill="both", expand=True)
        self.widgets['log_frame'] = log_frame

        self.log_text = tk.Text(log_frame, height=8, state='disabled', 
                               bg='white', fg=TEXT_COLOR, bd=1, relief='flat', 
                               wrap='word', font=('Malgun Gothic', 8))
        self.log_text.pack(fill="both", expand=True, padx=0, pady=5)
        self.widgets['log_text'] = self.log_text
        
        # 로그 초기화 버튼
        clear_btn = ttk.Button(log_frame, 
                   text=self.lang_manager.get("main", "clear_log"), 
                   command=self.clear_log)
        clear_btn.pack(pady=2, fill="x")
        self.widgets['clear_btn'] = clear_btn

    def _apply_theme(self):
        """테마 적용"""
        if self.dark_mode:
            bg = DARK_BG_COLOR
            fg = DARK_TEXT_COLOR
            frame_bg = DARK_FRAME_BG
            primary = DARK_PRIMARY_COLOR
            secondary = DARK_SECONDARY_COLOR
            text_bg = DARK_ENTRY_BG
            text_fg = DARK_TEXT_COLOR
            entry_bg = DARK_ENTRY_BG
        else:
            bg = BG_COLOR
            fg = TEXT_COLOR
            frame_bg = BG_COLOR
            primary = PRIMARY_COLOR
            secondary = SECONDARY_COLOR
            text_bg = 'white'
            text_fg = TEXT_COLOR
            entry_bg = 'white'
        
        # 메인 윈도우 배경
        self.master.configure(bg=bg)
        
        # ttk 스타일 설정
        style = ttk.Style(self.master)
        style.theme_use('clam')  # clam 테마 사용
        
        # LabelFrame 스타일
        style.configure('TLabelFrame', background=frame_bg, foreground=fg, borderwidth=0, relief='flat')
        style.configure('TLabelFrame.Label', background=frame_bg, foreground=fg, font=('Malgun Gothic', 9))
        
        # Frame 스타일
        style.configure('TFrame', background=frame_bg)
        
        # Label 스타일
        style.configure('TLabel', background=frame_bg, foreground=fg, font=('Malgun Gothic', 9))
        
        # Entry 스타일
        style.configure('TEntry', fieldbackground=entry_bg, foreground=fg, borderwidth=0)
        style.map('TEntry', fieldbackground=[('readonly', entry_bg), ('disabled', entry_bg)])
        
        # Button 스타일 (ttk)
        style.configure('TButton', background=text_bg, foreground=fg, borderwidth=0, font=('Malgun Gothic', 9), relief='flat')
        style.map('TButton', 
                  background=[('active', text_bg), ('pressed', text_bg)],
                  foreground=[('active', fg)])
        
        # OptionMenu (Combobox) 스타일
        style.configure('TMenubutton', background=entry_bg, foreground=fg, borderwidth=0, relief='flat')
        style.map('TMenubutton',
                  background=[('active', entry_bg), ('pressed', entry_bg)])
        
        # 개별 위젯 배경색 적용
        for widget_name, widget in self.widgets.items():
            try:
                if isinstance(widget, (ttk.LabelFrame, ttk.Frame, ttk.Label, ttk.Button)):
                    pass
                elif isinstance(widget, ttk.Entry):
                    widget.configure(style='TEntry')
            except:
                pass
        
        # tk 버튼 색상 (백업/복구 버튼)
        if hasattr(self, 'backup_btn'):
            self.backup_btn.config(bg=primary, fg='#000000' if self.dark_mode else BUTTON_FG, 
                                  activebackground=primary, activeforeground='#000000' if self.dark_mode else BUTTON_FG)
        if hasattr(self, 'restore_btn'):
            self.restore_btn.config(bg=secondary, fg='#000000' if self.dark_mode else BUTTON_FG,
                                   activebackground=secondary, activeforeground='#000000' if self.dark_mode else BUTTON_FG)
        
        # 로그 텍스트 위젯
        if hasattr(self, 'log_text'):
            self.log_text.config(bg=text_bg, fg=text_fg, insertbackground=text_fg, 
                                borderwidth=0 if self.dark_mode else 1)

    # 핸들러 함수 
    def select_directory(self):
        chosen_dir = filedialog.askdirectory(initialdir=self.backup_dir.get())
        if chosen_dir:
            self.backup_dir.set(chosen_dir)
            self.config_manager.set("last_backup_dir", chosen_dir)
            log_message(f"[정보] 경로 설정: {chosen_dir}")
            
    def handle_backup(self):
        browser = self.selected_browser.get()
        dir_path = self.backup_dir.get()
        self.config_manager.set("last_browser", browser)
        perform_backup(browser, dir_path)
        
    def handle_restore(self):
        browser = self.selected_browser.get()
        dir_path = self.backup_dir.get()
        self.config_manager.set("last_browser", browser)
        
        # 브라우저별 동기화 설명 (다국어)
        sync_key_map = {
            "Edge": "sync_warning_edge",
            "Chrome": "sync_warning_chrome",
            "Firefox": "sync_warning_firefox"
        }
        sync_detail = self.lang_manager.get("messages", sync_key_map.get(browser, "sync_warning_edge"))
        
        # 경고 메시지
        pre_sync_title = self.lang_manager.get("messages", "sync_warning_title")
        pre_sync_message = self.lang_manager.get("messages", "sync_warning_message").format(
            browser=browser,
            sync_detail=sync_detail
        )
        
        must_proceed = messagebox.askyesno(pre_sync_title, pre_sync_message, icon='warning')
        
        if must_proceed:
            perform_restore(browser, dir_path)

    def clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        log_message("로그 초기화 완료.")
    
    def _change_language(self, lang_code):
        """언어 변경"""
        self.lang_manager.change_language(lang_code)
        messagebox.showinfo(
            self.lang_manager.get("messages", "info"),
            "Language changed. Please restart the application." if lang_code == "en" else "언어가 변경되었습니다. 프로그램을 재시작해주세요."
        )
    
    def _toggle_dark_mode(self):
        """다크모드 토글"""
        self.dark_mode = not self.dark_mode
        self.config_manager.set("dark_mode", self.dark_mode)
        self.dark_mode_var.set(self.dark_mode)
        self._apply_theme()
    
    def _manual_update_check(self):
        """수동 업데이트 확인"""
        log_message(f"[정보] {self.lang_manager.get('update', 'checking')}")
        self.update_manager.check_for_updates(self._on_manual_update_check)
    
    def _on_update_check_complete(self, has_update, version_info):
        """자동 업데이트 확인 완료 (백그라운드)"""
        if has_update:
            self._show_update_dialog(version_info)
    
    def _on_manual_update_check(self, has_update, version_info):
        """수동 업데이트 확인 완료"""
        if has_update:
            self._show_update_dialog(version_info)
        else:
            messagebox.showinfo(
                self.lang_manager.get("update", "title"),
                self.lang_manager.get("update", "no_update")
            )
    
    def _show_update_dialog(self, version_info):
        """업데이트 다이얼로그 표시"""
        message = f"{self.lang_manager.get('update', 'available')}\n\n"
        message += f"{self.lang_manager.get('update', 'current_version')}: {CURRENT_VERSION}\n"
        message += f"{self.lang_manager.get('update', 'latest_version')}: {version_info['version']}\n\n"
        message += self.lang_manager.get('update', 'download_question')
        
        if messagebox.askyesno(self.lang_manager.get("update", "title"), message):
            self._download_and_install_update(version_info)
    
    def _download_and_install_update(self, version_info):
        """업데이트 다운로드 및 설치"""
        if not version_info.get('download_url'):
            messagebox.showerror(
                self.lang_manager.get("messages", "error"),
                self.lang_manager.get("update", "download_url_error")
            )
            return
        
        progress_window = tk.Toplevel(self.master)
        progress_window.title(self.lang_manager.get("update", "title"))
        progress_window.geometry("400x150")
        progress_window.resizable(False, False)
        
        ttk.Label(progress_window, 
                  text=self.lang_manager.get("update", "download_progress")).pack(pady=20)
        
        progress_bar = ttk.Progressbar(progress_window, length=300, mode='determinate')
        progress_bar.pack(pady=10)
        
        progress_label = ttk.Label(progress_window, text="0%")
        progress_label.pack()
        
        def update_progress(percent):
            progress_bar['value'] = percent
            progress_label.config(text=f"{percent}%")
            progress_window.update()
        
        def download_thread():
            try:
                # 다운로드
                download_url = version_info.get('download_url')
                is_setup = version_info.get('is_setup', False)
                update_file = self.update_manager.download_update(download_url, update_progress)
                
                if not update_file:
                    raise Exception(self.lang_manager.get("update", "download_failed"))
                
                # 백업 생성 (Portable만)
                if not is_setup:
                    self.update_manager.create_backup()
                
                # 설치
                progress_window.destroy()
                
                if self.update_manager.install_update(update_file, is_setup):
                    messagebox.showinfo(
                        self.lang_manager.get("update", "title"),
                        self.lang_manager.get("update", "complete")
                    )
                    # 프로그램 강제 종료
                    self.master.after(100, lambda: os._exit(0))
                else:
                    raise Exception(self.lang_manager.get("update", "install_failed"))
                    
            except Exception as e:
                progress_window.destroy()
                messagebox.showerror(
                    self.lang_manager.get("messages", "error"),
                    f"{self.lang_manager.get('update', 'failed')}\n{str(e)}"
                )
        
        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()
    
    def _visit_github(self):
        """GitHub 방문"""
        import webbrowser
        webbrowser.open(f"https://github.com/{GITHUB_REPO}")
    
    def _show_about(self):
        """About 다이얼로그"""
        about_text = f"{self.lang_manager.get('app', 'title')}\n\n"
        about_text += f"{self.lang_manager.get('about', 'version')}: {CURRENT_VERSION}\n"
        about_text += f"{self.lang_manager.get('about', 'description')}\n\n"
        about_text += f"GitHub: {GITHUB_REPO}"
        
        messagebox.showinfo(self.lang_manager.get("menu", "about"), about_text)
    
    def _on_exit(self):
        """종료 시 설정 저장"""
        self.config_manager.set("last_browser", self.selected_browser.get())
        self.config_manager.set("last_backup_dir", self.backup_dir.get())
        self.master.quit()

# 전역 로그 함수 
gui_instance = None
def log_message(message):
    timestamp = datetime.now().strftime("[%H:%M:%S]")
    full_message = f"{timestamp} {message}\n"
    
    try:
        sys.stdout.buffer.write(full_message.encode('utf-8'))
    except Exception:
        print(full_message.strip())
    
    if gui_instance and gui_instance.log_text:
        gui_instance.log_text.config(state='normal')
        gui_instance.log_text.insert(tk.END, full_message)
        gui_instance.log_text.yview(tk.END)
        gui_instance.log_text.config(state='disabled')
        
# 메인 실행
if __name__ == "__main__":
    root = tk.Tk()
    gui_instance = BookmarkManagerGUI(root)
    root.mainloop()