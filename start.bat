call env\Scripts\activate.bat
call python -m uvicorn main:app --host 0.0.0.0 --port 8064 --workers 10