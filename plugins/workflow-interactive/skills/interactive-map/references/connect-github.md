# Connect GitHub to your workflow map

You do this once. It lets your map page pull, commit, and push to your fleet
repository (`cms-f26-fleet-<your GitHub login>`) without the terminal.

1. In Claude (the desktop app or claude.ai), open **Settings**, then
   **Connectors**.
2. Find **GitHub** and choose **Connect**.
3. Sign in to GitHub if asked, and allow Claude access. The course
   organization has already approved Claude, so your fleet repository is
   available once you allow it for your own account.
4. In your Week 10 project's chat in Cowork, open the tools menu and check
   that GitHub is on for this chat.
5. Ask Claude to make your map again, or to republish it, so the page is
   published with GitHub connected. The toolbar then shows **Pull**,
   **Commit**, and **Push**.

If Push says the repository has newer commits, press **Pull** first, as you
would with `git pull`. If a push fails with a message about access, tell an
instructor; the page keeps your commit until it goes through.

You can skip this. Without GitHub the page still saves itself when you press
**Save**, and you commit and push `workflow/<id>/` from the terminal as
usual.
