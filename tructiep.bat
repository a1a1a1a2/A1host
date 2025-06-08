


@echo off
title 🔴 YouTube Livestream GUI
cd /d "D:\truc tiep"   :: 👉 Thay đường dẫn nếu cần

echo ===============================================
echo 🚀 Đang khởi chạy giao diện Livestream YouTube...
echo ===============================================

REM Kiểm tra file Python có tồn tại không
if not exist "livestream_gui.py" (
    echo ❌ Không tìm thấy file livestream_gui.py!
    pause
    exit /b
)

REM Kiểm tra Python đã cài chưa
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Bạn chưa cài Python hoặc chưa thêm vào PATH!
    pause
    exit /b
)

REM Chạy giao diện
python livestream_gui.py

pause
