# Hosted fictional demo

The container starts one generated vault, the existing write-enabled portal
on 127.0.0.1:8765, and a password front door on Render's PORT. Each start
creates a new fictional history. A restart or redeploy discards the meeting
edits. The image includes the committed canvas assets.

## Render service

Use a Docker web service from the private Chassis repository, select this
draft's branch and use the repository root as the build context. Set the
Dockerfile path to `deploy/Dockerfile`. Use manual deployment of the reviewed
commit, one fixed instance, ephemeral storage and the default TCP health
check. The public listener opens after the loopback portal confirms writes
are enabled. Keep autoscaling and automatic deploys off during the meeting.

Set `DEMO_PASSWORD` as a secret in Render. The browser username is `demo`.
Render supplies `PORT` and `RENDER_EXTERNAL_URL`. If Joe uses a custom domain,
set `PUBLIC_ORIGIN` to its exact HTTPS origin, without a trailing slash.
Advertise only the configured origin privately to Joe. Chassis generates the
viewer, editor and chief credentials afresh. The front door passes the
browser's CSRF token and fetch metadata through to the unchanged portal.

The meeting commands below require **Shell on the running web instance**.
Render offers that shell on paid web compute, starting at $7/month prorated.
Paid web compute stays awake while idle. Free sleeps after 15 idle minutes,
loses local edits when it spins down, and has no live shell. Joe's hosting
exception covers the fictional vault. The repo separately excludes paid
infrastructure. A paid service requires a spending decision before creation.
[Render shell support](https://render.com/docs/ssh) ·
[Free service behavior](https://render.com/docs/free) ·
[Compute pricing](https://render.com/pricing)

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

Start with a fresh instance. In a separate browser session, enter a wrong
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

The CI rehearsal runs the Docker image behind a local TLS terminator with two
Chromium processes. The hosted checks above exercise the actual Render edge.
