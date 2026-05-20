@echo off
:: AI & Data Daily Report — 작업 스케줄러 실행 파일
cd /d "%~dp0.."
python scripts\ingest_and_send.py
