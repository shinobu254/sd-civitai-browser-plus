import neko

if not neko.is_installed("send2trash"):
    neko.run_pip("install send2trash", "requirements for CivitAI Browser")
if not neko.is_installed("ZipUnicode"):
    neko.run_pip("install ZipUnicode", "requirements for CivitAI Browser")