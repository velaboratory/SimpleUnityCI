nssm install SimpleUnityCI "C:\git_repo\SimpleUnityCI\env\Scripts\python.exe" main.py
nssm set SimpleUnityCI AppDirectory "C:\git_repo\SimpleUnityCI"
nssm set SimpleUnityCI Description "Simple Unity CI FastAPI Server"