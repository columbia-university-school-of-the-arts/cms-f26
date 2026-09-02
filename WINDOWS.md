# Windows: set up WSL first

**Not yet tested end to end.** This is written from the documentation and will
be walked on a real machine before the first session. If a step here does not
match what you see, that is worth telling us — you will not be the only one.

## Why WSL

On native Windows, `git` and the GitHub CLI both demand administrator rights.
If your laptop is your own you may have them; if it is a college loaner you
probably do not, and no script can grant them.

WSL — Windows Subsystem for Linux — gives you a real Linux inside Windows,
where **you are the administrator of your own machine**. `sudo apt install`
just works. The wall disappears.

It only stands in one place: installing WSL itself.

## 1. Install WSL

Open **PowerShell** — press Start, type `PowerShell`, press return — and run:

```powershell
wsl --install
```

Then **restart your computer**. When it comes back, Ubuntu opens and asks you
to choose a username and a password.

**Choose a password you can retype**, because you will. It is not your Windows
password and not your GitHub password; it belongs to your Linux only. Nothing
appears on screen while you type it — that is normal and is not a broken
keyboard.

**If `wsl --install` says you need administrator rights**, stop there and tell
us before the first session rather than fighting it. Two other routes exist —
installing *Windows Subsystem for Linux* from the Microsoft Store, which
sometimes works without elevation, or the native Windows path without WSL at
all — and which one you need depends on your Windows version. That is a
five-minute conversation and an hour of frustration if you skip it.

## 2. Open your Linux

Press Start, type `Ubuntu`, press return. That window is your WSL terminal, and
it is where everything below happens.

**PowerShell is not WSL.** They look similar and behave differently, and running
the wrong commands in the wrong window is the most common way this goes sideways.
If your prompt ends in `$` you are in WSL; if it looks like `PS C:\>` you are in
PowerShell.

## 3. Get the setup script and run it

Download **`setup-wsl.sh`** from **Files** on the course Canvas site. It lands
in your Windows Downloads folder, which WSL can see:

```bash
bash /mnt/c/Users/YOUR-WINDOWS-USERNAME/Downloads/setup-wsl.sh
```

Replace `YOUR-WINDOWS-USERNAME` with your actual Windows account name. If you
do not know it, run `ls /mnt/c/Users/` and look for the one that is yours.

Read it first if you like — this prints every command and runs none of them:

```bash
bash /mnt/c/Users/YOUR-WINDOWS-USERNAME/Downloads/setup-wsl.sh --dry-run
```

It installs git, the GitHub CLI, ffmpeg, and Claude Code, and asks for your
Ubuntu password when it needs `sudo`.

## 4. Sign in

```bash
gh auth login
gh auth setup-git
```

Choose **HTTPS**, and authenticate in the browser when it offers. WSL will open
your Windows browser to do it — that is expected, not a mistake.

The second command is what lets `git push` work later without asking you for a
password every time.

## 5. Check it worked

```bash
git --version && gh --version && ffmpeg -version | head -1 && claude --version
```

Four answers means you are ready.

---

## One thing we are still working out

Your work will live in two places, and we have not yet settled how they meet.

**Claude Desktop and Cowork run on Windows.** The course reader — the folder of
readings you build in the first session — will be a Windows folder.

**Your code and your repository live inside WSL**, because that is where git and
Claude Code are.

Windows and WSL can each see the other's files. From WSL, your Windows drive is
under `/mnt/c/`. From Windows, your Linux files are at `\\wsl$\Ubuntu\home\`.
Whether Cowork will happily point at a folder across that boundary is exactly
the kind of thing that works in principle and surprises you in practice, so we
are testing it rather than assuming.

**For the first session this does not matter.** Cowork work happens on the
Windows side and the terminal work happens on the WSL side, and they do not
need to meet until Week 2. If you are on Windows, mention it in the room and we
will make sure you are not the person who finds out the hard way.
