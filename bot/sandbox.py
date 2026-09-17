"""
اجرای کد هر کاربر داخل یک یوزر لینوکسی جداگانه‌ی خودش (نه Docker-in-Docker، چون روی
Railway در دسترس نیست) — هر کاربر هوم و پرمیشن‌های خودشو داره، بدون sudo/root،
ولی هیچ محدودیت مصنوعی روی زبان یا نصب پکیج (pip/npm داخل هوم خودش) نداره.
"""
import asyncio
import os
import pwd
import shlex
import subprocess
from . import config

_created_users: set[str] = set()


def _username_for(user_id: int) -> str:
    return f"sb{user_id}"


def _ensure_os_user(user_id: int) -> str:
    username = _username_for(user_id)
    if username in _created_users:
        return username
    try:
        pwd.getpwnam(username)
    except KeyError:
        home = os.path.join(config.SANDBOX_ROOT, username)
        subprocess.run(
            ["useradd", "-m", "-d", home, "-s", "/bin/bash", username],
            check=True, capture_output=True,
        )
        subprocess.run(["chown", "-R", f"{username}:{username}", home], check=True)
    _created_users.add(username)
    return username


def workspace_path(user_id: int) -> str:
    username = _username_for(user_id)
    return os.path.join(config.SANDBOX_ROOT, username)


async def run_code(user_id: int, language: str, code: str, timeout: int | None = None) -> dict:
    """
    اجرای کد کاربر داخل هوم خودش. خروجی: {"stdout": str, "stderr": str, "exit_code": int}
    """
    username = _ensure_os_user(user_id)
    home = workspace_path(user_id)
    timeout = timeout or config.CODE_EXEC_TIMEOUT_SECONDS

    ext_map = {"python": "py", "python3": "py", "javascript": "js", "node": "js",
               "bash": "sh", "shell": "sh", "sh": "sh"}
    run_map = {
        "python": "python3", "python3": "python3",
        "javascript": "node", "node": "node",
        "bash": "bash", "shell": "bash", "sh": "bash",
    }

    lang = language.lower().strip()
    ext = ext_map.get(lang, "txt")
    runner = run_map.get(lang)

    filename = f"snippet_{os.urandom(4).hex()}.{ext}"
    filepath = os.path.join(home, filename)
    with open(filepath, "w") as f:
        f.write(code)
    subprocess.run(["chown", f"{username}:{username}", filepath], check=False)

    if runner is None:
        # زبان ناشناخته -> کد رو به‌عنوان دستور شل مستقیم اجرا کن
        command = code
    else:
        command = f"{runner} {shlex.quote(filename)}"

    # اجرای دستور به‌عنوان یوزر خودش، داخل هوم خودش، با محدودیت زمانی و حافظه‌ی منطقی
    # (برای جلوگیری از crash کل هاست، نه محدود کردن قابلیت‌های کاربر)
    wrapped = (
        f"cd {shlex.quote(home)} && "
        f"ulimit -v 4000000; ulimit -t {timeout}; "
        f"{command}"
    )
    full_cmd = ["su", "-", username, "-c", wrapped]

    try:
        proc = await asyncio.create_subprocess_exec(
            *full_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout + 10)
        except asyncio.TimeoutError:
            proc.kill()
            return {"stdout": "", "stderr": "⏱️ اجرای کد بیش از حد طول کشید و متوقف شد.", "exit_code": -1}

        return {
            "stdout": stdout.decode(errors="replace")[-4000:],
            "stderr": stderr.decode(errors="replace")[-2000:],
            "exit_code": proc.returncode,
        }
    finally:
        try:
            os.remove(filepath)
        except OSError:
            pass


async def install_package(user_id: int, manager: str, package: str) -> dict:
    """نصب پکیج داخل هوم کاربر (pip --user یا npm install لوکال) — بدون نیاز به root."""
    username = _ensure_os_user(user_id)
    home = workspace_path(user_id)

    if manager == "pip":
        cmd = f"pip install --user {shlex.quote(package)}"
    elif manager == "npm":
        cmd = f"npm install {shlex.quote(package)}"
    else:
        return {"stdout": "", "stderr": f"مدیر پکیج پشتیبانی‌نشده: {manager}", "exit_code": -1}

    full_cmd = ["su", "-", username, "-c", f"cd {shlex.quote(home)} && {cmd}"]
    proc = await asyncio.create_subprocess_exec(
        *full_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
    return {
        "stdout": stdout.decode(errors="replace")[-3000:],
        "stderr": stderr.decode(errors="replace")[-1500:],
        "exit_code": proc.returncode,
    }
