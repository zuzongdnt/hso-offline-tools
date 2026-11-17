"""Build a self-extracting PC release with a newly initialized database."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import time
from zipfile import ZipFile


def seed_database(root, source, password, admin_password):
    bin_dir = root / "runtime/mariadb/bin"
    database = root / "database"
    port = 33329
    with socket.socket() as port_check:
        port_check.bind(("127.0.0.1", port))
    init = subprocess.run(
        [bin_dir / "mariadb-install-db.exe", f"--datadir={database}", f"--port={port}",
         f"--password={admin_password}"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if init.returncode:
        raise RuntimeError("Could not initialize the fresh MariaDB seed")
    server_ini = root.parent / "seed-server.ini"
    server_ini.write_text(
        f"[mysqld]\nbasedir={bin_dir.parent.as_posix()}\ndatadir={database.as_posix()}\n"
        f"port={port}\nbind-address=127.0.0.1\nskip-name-resolve\n", encoding="utf-8",
    )
    build_client = root.parent / "seed-client.ini"
    client_settings = f"[client]\nhost=127.0.0.1\nuser=root\npassword={admin_password}\nprotocol=tcp\n"
    build_client.write_text(client_settings + f"port={port}\n", encoding="utf-8")
    (root / "database-client.ini").write_text(client_settings + "port=33317\n", encoding="utf-8")
    proc = subprocess.Popen(
        [bin_dir / "mariadbd.exe", f"--defaults-file={server_ini}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW,
    )
    client = [bin_dir / "mariadb.exe", f"--defaults-file={build_client}", "-N", "-B",
              "--default-character-set=utf8mb4"]

    def sql(query, schema=None, check=True):
        return subprocess.run(
            client + ([schema] if schema else []), input=query, capture_output=True, check=check,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

    try:
        for _ in range(80):
            if proc.poll() is not None:
                raise RuntimeError("Fresh database exited during initialization")
            if sql(b"SELECT 1;", check=False).returncode == 0:
                break
            time.sleep(0.25)
        else:
            raise RuntimeError("Fresh database did not start")
        schema = "hso_zuzong_offline"
        sql(f"CREATE DATABASE {schema} CHARACTER SET utf8mb3; "
            f"CREATE USER 'hso_local'@'127.0.0.1' IDENTIFIED BY '{password}'; "
            f"GRANT ALL ON {schema}.* TO 'hso_local'@'127.0.0.1';".encode())
        for filename in ("fresh-schema.sql", "support-boss.sql"):
            sql((source / "server" / filename).read_bytes(), schema)
        counts = sql(b"SELECT (SELECT COUNT(*) FROM account), "
                     b"(SELECT COUNT(*) FROM player WHERE id >= 0), "
                     b"(SELECT COUNT(*) FROM player WHERE id < 0), "
                     b"(SELECT COUNT(*) FROM clan), (SELECT COUNT(*) FROM wedding);", schema)
        if counts.stdout.strip() != b"0\t0\t1\t0\t0":
            raise RuntimeError("The PC installer database is not an empty player seed")
    finally:
        if proc.poll() is None:
            subprocess.run(
                [bin_dir / "mariadb-admin.exe", f"--defaults-file={build_client}", "shutdown"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW, check=True,
            )
            proc.wait(20)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "update", "stage", "out", "rar"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    source, update, stage, out, rar = (
        item.resolve() for item in (args.source, args.update, args.stage, args.out, args.rar)
    )
    if stage.exists() or out.exists():
        parser.error("Use new paths for staging and output")
    with ZipFile(update) as patch:
        if patch.testzip() is not None:
            raise ValueError("Invalid PC update")
        manifest = json.loads(patch.read("files.json"))
        root = stage / f"HSO_Offline_PC_{manifest['version']}"
        root.mkdir(parents=True)
        shutil.copytree(source / "runtime", root / "runtime")
        shutil.copytree(source / "client/hso_v403_Data", root / "client/hso_v403_Data",
                        ignore=shutil.ignore_patterns("output_log.txt"))
        shutil.copy2(source / "client/hso_v403.exe", root / "client/hso_v403.exe")
        for folder in ("icon", "mapnew", "msg", "npc", "part_char"):
            shutil.copytree(source / "server/data" / folder, root / "server/data" / folder)
        for filename in ("BAT_DAU.ps1", "CHOI_OFFLINE.cmd", "CHOI_OFFLINE.ps1", "TAT_OFFLINE.cmd", "TAT_SERVER.ps1"):
            shutil.copy2(source / filename, root / filename)
        launcher = root / "BAT_DAU.ps1"
        content = launcher.read_text(encoding="utf-8-sig")
        old_limit = "$i -lt 60; $i++"
        if content.count(old_limit) != 1:
            raise ValueError("Unexpected launcher startup wait")
        launcher.write_text(content.replace(old_limit, "$i -lt 480; $i++"), encoding="utf-8-sig")
        for entry in manifest["files"]:
            relative = entry["path"]
            destination = (root / relative).resolve()
            if not destination.is_relative_to(root):
                raise ValueError("Unexpected path in PC update")
            data = patch.read("payload/" + relative)
            if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise ValueError(f"PC update file failed verification: {relative}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
    if b"TikTok @thinhdzuong" not in (root / "server/data/offline-tools.html").read_bytes():
        raise ValueError("Missing contact details in the PC package")
    (root / "logs").mkdir()
    password, admin_password = secrets.token_hex(16), secrets.token_hex(24)
    config = (source / "server/hso.conf").read_text(encoding="utf-8-sig")
    config = re.sub(r"(?m)^mysql-password:[^\r\n]*", "mysql-password: " + password, config)
    (root / "server/hso.conf").write_text(config, encoding="utf-8")
    seed_database(root, source, password, admin_password)
    subprocess.run(
        [rar, "a", "-r", "-m3", "-sfxDefault.SFX", out, root.name],
        cwd=stage, check=True,
    )
    subprocess.run([rar, "t", "-inul", out], check=True)
    print(out)


if __name__ == "__main__":
    main()
