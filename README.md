# polybin 🧬

> Smash formats together. Break assumptions. Build valid chaos. 

“Why yes, that is an icon that plays video and extracts as a PowerPoint.”

## 📦 What is this?

**polybin** is a file format combiner.  
It creates single files that are valid in multiple formats at the same time.  
Not "sort of valid". Not "renamed". *Actually valid.*

| You give it...             | It builds...                         |
|---------------------------|--------------------------------------|
| `icon.ico + video.mp4`    | A valid `.ico` **and** a valid `.mp4` |
| `icon.ico + file.zip`     | A valid `.ico` **and** a valid `.zip` |
| `video.mp4 + file.zip`    | A valid `.mp4` **and** a valid `.zip` |
| `icon.ico + mp4 + zip`    | All 3 formats in one file            |

It works with real-world apps:
- 📂 Windows Explorer: shows icon
- 🎥 Windows Media Player: plays video
- 🗂️ `unzip`, PowerPoint, Android: reads ZIP contents

No shell scripts. No renaming. No MIME guessing. Just **legit files that lie**.

## ⚙️ How It Works

### 🔁 File Formats = Predictable Structures

Every file format starts and ends in known ways:
- `.ico` starts with a 6-byte header + directory
- `.mp4` starts with an `ftyp` box
- `.zip` ends with a central directory and signature
- `.pptx`, `.apk`, `.jar` = ZIP

**polybin** uses that knowledge to surgically position headers and bodies so that:
- Every parser finds what it needs  
- Offsets are realigned, patched, and respected
- You get a valid file in all formats, with no corruption
  
### 📐 Precise Offsets Matter

Every format has quirks:
- `MP4` needs `ftyp` early and `moov` + `mdat` aligned
- `ZIP` needs correct file pointer tables at the end
- `ICO` pointers must match embedded image sizes

**polybin** reads, modifies, and patches offsets so each format thinks it's alone.

## ✅ Supported Combinations

| Format 1 | Format 2 | Format 3 | Result                    |
|----------|----------|----------|---------------------------|
| ICO      | MP4      | -        | 🖼️ Plays video, shows icon |
| ICO      | ZIP      | -        | 🖼️ Unzips, shows icon      |
| MP4      | ZIP      | -        | 🎥 Opens in video player + unzip |
| ICO      | MP4      | ZIP      | 🧨 Works in all three      |
| PPTX     | ICO      | -        | 💼 + 🖼️ works in PowerPoint |

## 🔍 Install

```bash
pip install polybin
```

(or install from source if you're a dev:)
```bash
git clone https://github.com/viodoescyber/polybin
cd polybin
pip install .
```

## 🚀 Quickstart

```bash
polybin out --ico icon.ico --mp4 video.mp4 --zip slides.pptx
```

Then:
- `mv out something.ico` → see icon
- `mv out smoething.mp4` → watch video
- `mv out something.zip` → unzip slides
  
All the same file.