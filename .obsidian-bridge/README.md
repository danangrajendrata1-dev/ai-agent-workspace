# Obsidian Bridge Lokal

Bridge ini hanya untuk workflow lokal:

- Ambil konteks `git` dan log test dari workspace saat ini.
- Kirim ringkasan ke Ollama lokal di `http://localhost:11434/api/chat`.
- Append hasilnya ke vault Obsidian, tanpa overwrite file yang sudah ada.

## Setup

1. Set environment variable `OBSIDIAN_VAULT_PATH` ke root vault Obsidian.
2. Jalankan Ollama lokal.
3. Pakai model default `qwen2.5:3b` atau override lewat argumen `--model`.

Contoh:

```powershell
$env:OBSIDIAN_VAULT_PATH = "C:\Path\To\ObsidianVault"
python scripts/obsidian_level3_ollama.py --project "Personal AI Agent Workspace" --title "Ollama Obsidian Bridge Test" --status PASS --model qwen2.5:3b
```

Dengan test log opsional:

```powershell
python scripts/obsidian_level3_ollama.py --project "Personal AI Agent Workspace" --title "Backend Test Summary" --status PASS --test-log .obsidian-bridge/logs/latest-test.log --model qwen2.5:3b
```

## Output note

Note ditulis ke:

```text
Projects/<project name>/AI_SUMMARIES.md
```

## Aturan aman

- Tidak memanggil API AI eksternal.
- Tidak membaca atau menampilkan isi `.env`.
- Tidak menyimpan secret, token, password, cookie, atau credential.
- Hanya append note baru.

## Runtime files

Folder `.obsidian-bridge/logs/` diabaikan oleh Git untuk artefak lokal.
