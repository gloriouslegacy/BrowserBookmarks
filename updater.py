import sys
import os
import time
import shutil
import subprocess
import zipfile

def main():
    """
    업데이터 프로그램
    사용법: updater.exe <다운로드한_파일> <대상_파일>
    - 다운로드한 파일은 ZIP 또는 EXE
    """
    if len(sys.argv) < 3:
        print("Usage: updater.exe <downloaded_file> <target_file>")
        time.sleep(3)
        sys.exit(1)
    
    downloaded_file = sys.argv[1]
    target_file = sys.argv[2]
    
    print("="*50)
    print("Browser Bookmarks Manager - Updater")
    print("="*50)
    print(f"\n다운로드 파일: {downloaded_file}")
    print(f"대상 파일: {target_file}")
    
    # 프로그램 종료 대기
    print("\n프로그램 종료 대기 중...")
    for i in range(5):
        time.sleep(1)
        print(f"대기 중... ({i+1}/5초)")
    print("✓ 대기 완료")
    
    # 파일 타입 확인
    new_exe = None
    
    if downloaded_file.lower().endswith('.zip'):
        # ZIP 파일 처리
        print("\nZIP 파일 압축 해제 중...")
        extract_dir = os.path.join(os.path.dirname(downloaded_file), "extracted")
        
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir)
        
        with zipfile.ZipFile(downloaded_file, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # BrowserBookmarks.exe 찾기
        new_exe = os.path.join(extract_dir, "BrowserBookmarks.exe")
        if not os.path.exists(new_exe):
            print(f"✗ 오류: BrowserBookmarks.exe를 찾을 수 없습니다.")
            time.sleep(5)
            sys.exit(1)
        
        print("✓ 압축 해제 완료")
    elif downloaded_file.lower().endswith('.exe'):
        # EXE 파일 그대로 사용
        new_exe = downloaded_file
    else:
        print(f"✗ 지원하지 않는 파일 형식: {downloaded_file}")
        time.sleep(5)
        sys.exit(1)
    
    # 백업 생성
    backup_file = f"{target_file}.backup"
    try:
        if os.path.exists(target_file):
            print(f"\n기존 파일 백업 중: {backup_file}")
            shutil.copy2(target_file, backup_file)
            print("✓ 백업 완료")
    except Exception as e:
        print(f"✗ 백업 실패: {e}")
    
    # 파일 교체
    try:
        print(f"\n파일 교체 중...")
        if os.path.exists(target_file):
            os.remove(target_file)
        shutil.copy2(new_exe, target_file)
        print("✓ 업데이트 완료")
        
        # 임시 파일 정리
        if downloaded_file.lower().endswith('.zip'):
            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            print("✓ 임시 파일 삭제")
        
        # 프로그램 재시작
        print(f"\n프로그램 재시작 중...")
        subprocess.Popen([target_file], shell=False)
        print("✓ 재시작 완료")
        
        print("\n업데이트가 성공적으로 완료되었습니다!")
        time.sleep(2)
        
    except Exception as e:
        print(f"\n✗ 업데이트 실패: {e}")
        
        # 롤백 시도
        if os.path.exists(backup_file):
            try:
                print("\n롤백 시도 중...")
                if os.path.exists(target_file):
                    os.remove(target_file)
                shutil.copy2(backup_file, target_file)
                print("✓ 롤백 완료")
                
                # 원래 프로그램 재시작
                subprocess.Popen([target_file], shell=False)
            except Exception as rollback_error:
                print(f"✗ 롤백 실패: {rollback_error}")
        
        time.sleep(5)
        sys.exit(1)

if __name__ == "__main__":
    main()