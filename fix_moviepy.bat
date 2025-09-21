@echo off
echo 🔧 Corrigindo MoviePy...
cd /d C:\dev\video-cutter-v8
call venv\Scripts\activate
pip uninstall moviepy -y
pip install moviepy==1.0.3
python -c "import moviepy.editor; print('MoviePy OK!')"
echo ✅ MoviePy corrigido!
pause
