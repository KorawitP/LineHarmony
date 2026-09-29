@echo off
chcp 65001 >nul
echo ========================================
echo GUI Layout Demo Launcher
echo ========================================
echo.

REM ตรวจสอบว่ามี uv ติดตั้งหรือไม่
where uv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] uv ไม่ได้ติดตั้งในระบบ
    echo กรุณาติดตั้ง uv ก่อนใช้งาน: https://docs.astral.sh/uv/getting-started/installation/
    echo.
    pause
    exit /b 1
)

echo [1/3] ตรวจสอบ virtual environment...
if not exist ".venv" (
    echo Virtual environment ยังไม่มี กำลังสร้าง...
    uv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] ไม่สามารถสร้าง virtual environment ได้
        pause
        exit /b 1
    )
    echo ✓ สร้าง virtual environment สำเร็จ
) else (
    echo ✓ พบ virtual environment แล้ว
)
echo.

echo [2/3] ตรวจสอบและติดตั้ง dependencies...
uv pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] ไม่สามารถติดตั้ง dependencies ได้
    pause
    exit /b 1
)
echo ✓ ติดตั้ง dependencies สำเร็จ
echo.

echo [3/3] กำลังเปิดโปรแกรม GUI Layout Demo...
echo.
uv run python examples\gui_layout_demo.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] เกิดข้อผิดพลาดในการรันโปรแกรม
    pause
    exit /b 1
)

echo.
echo ========================================
echo โปรแกรมทำงานเสร็จสิ้น
echo ========================================
pause
