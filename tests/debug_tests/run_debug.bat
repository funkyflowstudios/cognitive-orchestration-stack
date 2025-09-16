@echo off
cd /d "D:\Projektit\agent_stack"
python debug_imports.py > debug_output.txt 2>&1
echo Debug completed, check debug_output.txt
