"""
Gmail 앱 비밀번호를 Windows 자격 증명 관리자에 저장합니다.
최초 1회만 실행하면 됩니다.
"""
import keyring, getpass, sys

SERVICE = "AIData_DailyReport"
ACCOUNT = "parkharm@gmail.com"

existing = keyring.get_password(SERVICE, ACCOUNT)
if existing:
    print(f"이미 저장된 자격 증명이 있습니다 ({ACCOUNT})")
    overwrite = input("덮어쓰시겠습니까? [y/N]: ").strip().lower()
    if overwrite != "y":
        print("취소되었습니다.")
        sys.exit(0)

password = getpass.getpass("Gmail 앱 비밀번호 (16자리, 입력 시 화면에 표시 안 됨): ")
password = password.replace(" ", "")

if len(password) != 16:
    print(f"오류: 앱 비밀번호는 16자리여야 합니다 (입력: {len(password)}자리)")
    sys.exit(1)

keyring.set_password(SERVICE, ACCOUNT, password)
print("✅ Windows 자격 증명 관리자에 암호화 저장 완료")
print("   확인: 제어판 → 자격 증명 관리자 → Windows 자격 증명 → AIData_DailyReport")
