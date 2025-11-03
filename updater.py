import sys
import os
import time
import shutil
import subprocess

def main():
    """
    업데이터 프로그램
    사용법: updater.exe <새_파일_경로> <대상_파일_경로>
    """
    if len(sys.argv) < 3:
        print("Usage: updater.exe <new_file> <target_file>")
        time.sleep(3)
        sys.exit(1)
    
    new_file = sys.argv[1]
    target_file = sys.argv[2]
    
    print("="*50)
    print("Browser Bookmarks Manager - Updater")
    print("="*50)
    print(f"\n새 파일: {new_file}")
    print(f"대상 파일: {target_file}")
    print("\n프로그램 종료 대기 중...")
    
    # 메인 프로그램이 종료될 때까지 대기
    time.sleep(3)
    
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
        shutil.copy2(new_file, target_file)
        print("✓ 업데이트 완료")
        
        # 임시 파일 삭제
        if os.path.exists(new_file):
            os.remove(new_file)
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
