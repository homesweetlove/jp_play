"""JP Play - 일본(및 모든 국가) 앱 APK 다운로드 & 폰 설치 도구.

- 검색: Google Play 웹을 일본 지역(gl=JP)으로 열어 패키지 ID 확인
- 다운로드: apkeep (EFF 오픈소스) 사용, APKPure(로그인 불필요) 또는 Google Play
- 설치: adb 로 USB 연결된 폰에 설치 (.apk / .xapk / split apk / OBB 지원)
"""
import json
import os
import re
import shutil
import subprocess
import threading
import urllib.parse
import urllib.request
import webbrowser
import zipfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

BASE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(BASE, "tools")
DOWNLOADS = os.path.join(BASE, "downloads")
CONFIG = os.path.join(BASE, "config.json")

APKEEP_URL = "https://github.com/EFForg/apkeep/releases/latest/download/apkeep-x86_64-pc-windows-msvc.exe"
PLATFORM_TOOLS_URL = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"

APKEEP = os.path.join(TOOLS, "apkeep.exe")
ADB = os.path.join(TOOLS, "platform-tools", "adb.exe")

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def load_config():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_config(cfg):
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def parse_package_id(text):
    """패키지 ID 또는 Play 스토어 URL 에서 ID 추출."""
    text = text.strip()
    if "id=" in text:
        q = urllib.parse.urlparse(text).query
        ids = urllib.parse.parse_qs(q).get("id")
        if ids:
            return ids[0]
    m = re.fullmatch(r"[A-Za-z][\w]*(\.[A-Za-z0-9_]+)+", text)
    return m.group(0) if m else None


def download_file(url, dest, log):
    log(f"다운로드 중: {url}")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    with urllib.request.urlopen(url) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f)
    os.replace(tmp, dest)


def ensure_apkeep(log):
    if not os.path.exists(APKEEP):
        download_file(APKEEP_URL, APKEEP, log)
    return APKEEP


def ensure_adb(log):
    if os.path.exists(ADB):
        return ADB
    system_adb = shutil.which("adb")
    if system_adb:
        return system_adb
    zpath = os.path.join(TOOLS, "platform-tools.zip")
    download_file(PLATFORM_TOOLS_URL, zpath, log)
    with zipfile.ZipFile(zpath) as z:
        z.extractall(TOOLS)
    os.remove(zpath)
    return ADB


def run(cmd, log):
    log("> " + " ".join(f'"{c}"' if " " in c else c for c in cmd))
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding="utf-8", errors="replace",
                         creationflags=NO_WINDOW)
    out = []
    for line in p.stdout:
        line = line.rstrip()
        out.append(line)
        if line:
            log(line)
    p.wait()
    return p.returncode, "\n".join(out)


def install_package(adb, path, log):
    """.apk / .xapk / .apks / .apkm 를 폰에 설치."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".apk":
        code, _ = run([adb, "install", "-r", path], log)
        return code == 0

    if ext not in (".xapk", ".apks", ".apkm", ".zip"):
        log(f"지원하지 않는 형식: {path}")
        return False

    workdir = os.path.join(DOWNLOADS, "_extract", os.path.splitext(os.path.basename(path))[0])
    shutil.rmtree(workdir, ignore_errors=True)
    with zipfile.ZipFile(path) as z:
        z.extractall(workdir)

    apks = []
    for root, _, files in os.walk(workdir):
        apks += [os.path.join(root, f) for f in files if f.lower().endswith(".apk")]
    if not apks:
        log("압축 안에 APK 가 없습니다.")
        return False

    if len(apks) == 1:
        code, _ = run([adb, "install", "-r", apks[0]], log)
    else:
        code, _ = run([adb, "install-multiple", "-r"] + apks, log)
    if code != 0:
        return False

    # XAPK 의 OBB(추가 데이터) 복사
    manifest = os.path.join(workdir, "manifest.json")
    if os.path.exists(manifest):
        with open(manifest, encoding="utf-8") as f:
            info = json.load(f)
        for exp in info.get("expansions", []):
            src = os.path.join(workdir, exp["file"])
            dst = "/sdcard/" + exp["install_path"]
            run([adb, "shell", "mkdir", "-p", os.path.dirname(dst).replace("\\", "/")], log)
            run([adb, "push", src, dst], log)
    return True


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("JP Play - 해외 앱 다운로더")
        self.geometry("760x600")
        self.cfg = load_config()
        os.makedirs(DOWNLOADS, exist_ok=True)

        pad = {"padx": 8, "pady": 4}

        # 1. 검색
        f1 = ttk.LabelFrame(self, text="1. 앱 찾기 (Google Play 일본판)")
        f1.pack(fill="x", **pad)
        self.query = tk.StringVar()
        ttk.Entry(f1, textvariable=self.query).pack(side="left", fill="x", expand=True, padx=6, pady=6)
        self.country = tk.StringVar(value=self.cfg.get("country", "JP"))
        ttk.Combobox(f1, textvariable=self.country, width=5,
                     values=["JP", "US", "KR", "CN", "TW", "HK", "GB", "DE", "FR"]).pack(side="left")
        ttk.Button(f1, text="웹에서 검색", command=self.search).pack(side="left", padx=6)

        # 2. 다운로드
        f2 = ttk.LabelFrame(self, text="2. 다운로드 (패키지 ID 또는 Play 스토어 링크)")
        f2.pack(fill="x", **pad)
        self.pkg = tk.StringVar()
        ttk.Entry(f2, textvariable=self.pkg).grid(row=0, column=0, columnspan=3, sticky="ew", padx=6, pady=6)
        f2.columnconfigure(0, weight=1)

        self.source = tk.StringVar(value=self.cfg.get("source", "apk-pure"))
        ttk.Radiobutton(f2, text="APKPure (로그인 불필요)", value="apk-pure",
                        variable=self.source, command=self.toggle_google).grid(row=1, column=0, sticky="w", padx=6)
        ttk.Radiobutton(f2, text="Google Play (계정 필요)", value="google-play",
                        variable=self.source, command=self.toggle_google).grid(row=1, column=1, sticky="w")
        ttk.Button(f2, text="다운로드", command=self.download).grid(row=1, column=2, padx=6)

        self.gframe = ttk.Frame(f2)
        self.gframe.grid(row=2, column=0, columnspan=3, sticky="ew", padx=6)
        ttk.Label(self.gframe, text="이메일").grid(row=0, column=0, sticky="w")
        self.email = tk.StringVar(value=self.cfg.get("email", ""))
        ttk.Entry(self.gframe, textvariable=self.email, width=40).grid(row=0, column=1, sticky="w")
        ttk.Label(self.gframe, text="AAS 토큰").grid(row=1, column=0, sticky="w")
        self.token = tk.StringVar(value=self.cfg.get("aas_token", ""))
        ttk.Entry(self.gframe, textvariable=self.token, width=40, show="*").grid(row=1, column=1, sticky="w")
        ttk.Label(self.gframe, text="※ README 의 토큰 발급 방법 참고").grid(row=2, column=1, sticky="w")
        self.toggle_google()

        # 3. 설치
        f3 = ttk.LabelFrame(self, text="3. 폰에 설치 (USB 디버깅 켜고 연결)")
        f3.pack(fill="x", **pad)
        ttk.Button(f3, text="연결된 기기 확인", command=self.devices).pack(side="left", padx=6, pady=6)
        ttk.Button(f3, text="파일 선택해서 설치", command=self.install_pick).pack(side="left", padx=6)
        ttk.Button(f3, text="다운로드 폴더 열기", command=lambda: os.startfile(DOWNLOADS)).pack(side="left", padx=6)
        self.auto_install = tk.BooleanVar(value=self.cfg.get("auto_install", False))
        ttk.Checkbutton(f3, text="다운로드 후 자동 설치", variable=self.auto_install).pack(side="left", padx=6)

        # 로그
        self.logbox = tk.Text(self, height=18, wrap="word")
        self.logbox.pack(fill="both", expand=True, **pad)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---- helpers ----
    def log(self, msg):
        self.after(0, lambda: (self.logbox.insert("end", msg + "\n"), self.logbox.see("end")))

    def bg(self, fn):
        def wrap():
            try:
                fn()
            except Exception as e:  # noqa: BLE001 - GUI 에 오류 표시
                self.log(f"오류: {e}")
        threading.Thread(target=wrap, daemon=True).start()

    def toggle_google(self):
        if self.source.get() == "google-play":
            self.gframe.grid()
        else:
            self.gframe.grid_remove()

    def on_close(self):
        self.cfg.update(country=self.country.get(), source=self.source.get(),
                        email=self.email.get(), aas_token=self.token.get(),
                        auto_install=self.auto_install.get())
        save_config(self.cfg)
        self.destroy()

    # ---- actions ----
    def search(self):
        q = self.query.get().strip()
        gl = self.country.get().strip() or "JP"
        hl = {"JP": "ja", "KR": "ko", "CN": "zh", "TW": "zh-TW", "HK": "zh-HK"}.get(gl, "en")
        if q:
            url = ("https://play.google.com/store/search?"
                   + urllib.parse.urlencode({"q": q, "c": "apps", "gl": gl, "hl": hl}))
        else:
            url = f"https://play.google.com/store/apps?gl={gl}&hl={hl}"
        webbrowser.open(url)
        self.log("브라우저에서 앱을 찾은 뒤, 주소창 링크(…?id=패키지명)를 2번 칸에 붙여넣으세요.")

    def download(self):
        pkg = parse_package_id(self.pkg.get())
        if not pkg:
            messagebox.showerror("JP Play", "패키지 ID 또는 Play 스토어 링크를 입력하세요.\n예) jp.ne.paypay.android.app")
            return
        source = self.source.get()

        def job():
            apkeep = ensure_apkeep(self.log)
            cmd = [apkeep, "-a", pkg, "-d", source]
            if source == "google-play":
                if not self.email.get() or not self.token.get():
                    self.log("Google Play 는 이메일과 AAS 토큰이 필요합니다.")
                    return
                cmd += ["-e", self.email.get(), "-t", self.token.get(), "--accept-tos",
                        "-o", "split_apk=true,include_additional_files=true"]
            before = set(os.listdir(DOWNLOADS))
            code, out = run(cmd + [DOWNLOADS], self.log)
            new = sorted(set(os.listdir(DOWNLOADS)) - before - {"_extract"})
            if code != 0 or not new:
                self.log("다운로드 실패. 다른 소스를 선택하거나 패키지 ID 를 확인하세요.")
                return
            self.log(f"완료: {', '.join(new)}")
            if self.auto_install.get():
                self.install_paths([os.path.join(DOWNLOADS, n) for n in new])

        self.bg(job)

    def install_paths(self, paths):
        adb = ensure_adb(self.log)
        for p in paths:
            if os.path.isdir(p):  # google-play split_apk 는 폴더로 저장됨
                apks = [os.path.join(p, f) for f in os.listdir(p) if f.lower().endswith(".apk")]
                ok = run([adb, "install-multiple", "-r"] + apks, self.log)[0] == 0 if apks else False
            else:
                ok = install_package(adb, p, self.log)
            self.log(("설치 성공: " if ok else "설치 실패: ") + os.path.basename(p))

    def install_pick(self):
        paths = filedialog.askopenfilenames(
            initialdir=DOWNLOADS, title="설치할 파일",
            filetypes=[("Android 패키지", "*.apk *.xapk *.apks *.apkm"), ("모든 파일", "*.*")])
        if paths:
            self.bg(lambda: self.install_paths(list(paths)))

    def devices(self):
        self.bg(lambda: run([ensure_adb(self.log), "devices", "-l"], self.log))


if __name__ == "__main__":
    App().mainloop()
