# Hosted fictional demo

The container serves one fictional vault from `/var/data/current`. The portal
listens on 127.0.0.1:8765 behind a password front door on Render's PORT.
The first start seeds the empty disk. Subsequent starts reopen that Git
checkout, keeping the board edits, versions, layout and history.

## Render service

Use a Docker web service from the private Chassis repository, select this
draft's branch and use the repository root as the build context. Set the
Dockerfile path to `deploy/Dockerfile`. Use manual deployment of the reviewed
commit, one fixed instance, one persistent disk and the default TCP health
check. The public listener opens after the loopback portal confirms writes
are enabled. Keep autoscaling and automatic deploys off throughout the sandbox window.

Set `DEMO_PASSWORD` as a secret in Render. The browser username is `demo`.
Render supplies `PORT` and `RENDER_EXTERNAL_URL`. If Joe uses a custom domain,
set `PUBLIC_ORIGIN` to its exact HTTPS origin, without a trailing slash.
Advertise only the configured origin privately to Joe. Startup issues viewer
and editor credentials for the current process. The front door passes the
browser's CSRF token and fetch metadata through to the unchanged portal.

The meeting commands below require **Shell on the running web instance**.
Render offers that shell on paid web compute, starting at $7/month prorated.
Paid web compute stays awake while idle. Free sleeps after 15 idle minutes,
loses local edits when it spins down, and has no live shell. Joe approved one Starter instance for this fictional sandbox through
December 1, 2026.
[Render shell support](https://render.com/docs/ssh) ·
[Free service behavior](https://render.com/docs/free) ·
[Compute pricing](https://render.com/pricing)

### Disk and first cutover

The proposed 1 GB disk adds **$0.25 per month** to Starter. Joe's Starter
approval through December 1 covers compute. Wait for his disk approval before
attaching storage. Use the existing sandbox's **Disks** page, name the disk
`chassis-vault`, and mount it at **`/var/data`**. This image requires that
mount and write access for its `demo` user. [Render pricing](https://render.com/pricing)
· [Persistent disks](https://render.com/docs/disks)

Adding the disk triggers a deploy. The currently hosted build keeps its vault
on ephemeral storage. Before cutover, preserve its complete fictional checkout
off-instance, including hidden files, and verify its Git HEAD against the live
checkout. Follow the `/run/chassis-demo/current` link to the actual directory
when copying. A blank disk starts at the fictional baseline. Plan any restore
before serving writes from the new disk. Disk-backed deploys briefly interrupt
the single instance.

## Joe's reset procedure

1. When ready to discard sandbox edits and history, open **Shell** on the
   running disk-backed instance and run `touch /var/data/current/.chassis/reset-on-next-start`.
   The current board stays available until the next start. To cancel before
   then, remove that marker with `rm /var/data/current/.chassis/reset-on-next-start`.
2. Choose **Manual Deploy** > **Restart service**. Startup replaces the marked
   vault with fresh fictional records and consumes the request.
3. Open Acme D2C and confirm **Acme D2C: launch review 1** is back at version 1.
   Cedar Rentals' second launch review should be **planned**. In Shell, run
   `/app/.venv/bin/python /app/deploy/meeting.py history` and confirm the
   fictional baseline is the only commit.

Once the disk-backed build is live, tell Andy, “Your edits survive restarts
and redeploys. Joe can deliberately reset the sandbox to its sample board.”

## Joe's meeting commands

Open the web service in the Render dashboard and select **Shell** on its
running instance. The commands below resolve the same vault as both browsers.
An ephemeral shell or one-off job has a different filesystem.

1. Open the same Acme D2C venture in two independent browsers. In the first,
   rename **Acme D2C: launch review 1** and save once. Watch the second browser
   pick up that exact title without reloading.
2. For Homer's turn, open Cedar Rentals. Run the first command below once.
   It reads the current version of **Cedar Rentals: launch review 2**, sets
   it to done and records Homer's next step through the Chassis CLI. It
   prints the record ID, new version and commit. Repeating a successful
   command leaves the Git history intact. A version conflict stops the write.
3. Run the second command to show the three latest vault commits with
   author, email and changed paths. On a fresh run with one browser save,
   expect chief-of-staff, canvas-editor and the fictional baseline in order.
   The baseline lists all seeded files.

```sh
/app/.venv/bin/python /app/deploy/meeting.py chief-write
/app/.venv/bin/python /app/deploy/meeting.py history
```

## Acceptance on the Render address

Start with a known fictional baseline. In a separate browser session, enter a wrong
password and verify a 401 on the session request. Carry out the two-browser
edit above. In the live shell, verify one editor commit and its single path:

```sh
git -C /run/chassis-demo/current log --author='canvas-editor@chassis.local' --format='%h %an <%ae>' --name-only
git -C /run/chassis-demo/current rev-parse HEAD
```

Send a PATCH to the same visible record using the valid demo login, current
version and session CSRF, with an Origin from a different site and
Sec-Fetch-Site set to cross-site. Expect 403 and the same vault HEAD. Keep
credentials out of command history, URLs and logs. Then run Joe's two
commands. Record the deployed commit, actual compute plan, idle behavior
and results in the checkpoint. Keep the service address in Joe's chat.

The CI rehearsal uses a named Docker volume and two Chromium processes behind
local TLS. It checks Acme's saved title, version and commit after restart,
reuses the volume in a replacement container, then exercises Joe's reset.
