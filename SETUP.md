# Setting up Orthodox Daily's Instagram automation

This is a one-time setup, about 30–45 minutes. After it, your only daily job is to look at one pull request and tap Merge.

## How it works

1. **Every night**, the *Fetch calendar days* workflow (GitHub Actions) saves the next 8 days of calendar data from Orthocal, the same source and settings as orthodoxdaily.net (New Calendar, Slavic, Septuagint and World English Bible), into `days/`.
2. **Every morning just before 9 am Pacific**, a scheduled task in Claude follows [AUTOMATION.md](AUTOMATION.md): it writes the day's texts, renders the Story, carousel and Reel in your fonts and colours, and opens a pull request named "Posts for …" with a preview.
3. **You review it** in the GitHub app or website. Merge it to publish. Close it to skip the day.
4. **Merging publishes**: the *Publish approved posts* workflow puts the images and video online with GitHub Pages (Instagram needs a public address to fetch them from), then posts them through Instagram's official API.

Nothing is ever posted without your merge.

## Step 1: Merge the setup pull request

On GitHub, open the pull request "Set up the daily Instagram automation", read it, and click **Merge pull request**.

## Step 2: Switch on GitHub Pages

Repository **Settings → Pages → Build and deployment → Source: GitHub Actions**. Nothing else to fill in.

## Step 3: Fetch the calendar data once

**Actions → Fetch calendar days → Run workflow**. After a minute, a `days/` folder appears with the next 8 days. From now on it runs every night by itself.

## Step 4: Make your Instagram a professional account

In the Instagram app: **Settings → Account type and tools → Switch to professional account → Creator** (or Business). The API only publishes for professional accounts.

## Step 5: Create the Meta app and get a token

Meta's screens change often, so follow the labels rather than exact positions.

1. Go to **developers.facebook.com**, log in, and choose **My Apps → Create app**.
2. Pick the use case for managing messaging and content on Instagram (the "Instagram API" product with Instagram login). Name it "Orthodox Daily Publisher".
3. In the app, open **Instagram → API setup with Instagram login**.
4. Under **Generate access tokens**, click **Add account** and log in with @orthodoxdaily. Allow the permissions it asks for. Publishing needs `instagram_business_basic` and `instagram_business_content_publish`.
5. Click **Generate token** next to the account. Copy the token (it starts with `IG`). This is a long-lived token, valid for 60 days.
6. Copy the **Instagram user ID** shown next to the account (a long number).

Your app stays in development mode; you are its administrator and publish only to your own account.

Keep the token private: don't paste it into chats, emails or files.

## Step 6: Store the token in GitHub

Repository **Settings → Secrets and variables → Actions**.

- **Secrets → New repository secret**: `IG_ACCESS_TOKEN` = the token; `IG_USER_ID` = the user ID.
- **Variables → New repository variable**: `PUBLISH_ENABLED` = `false` for now.

## Step 7: Test, then switch publishing on

1. The next morning's pull request arrives at 9 am. Merge it with `PUBLISH_ENABLED` still `false`: the workflow puts the media online and does a dry run, listing what it *would* post. Open **Actions → Publish approved posts** to read it.
2. When you're happy, change `PUBLISH_ENABLED` to `true`. From then on, merging publishes.
3. If a day ever fails, open the failed workflow run in Actions to see why, fix the cause, and use **Run workflow** on *Publish approved posts* with that date. Items that already went out are never posted twice.

## Step 8 (optional): Keep the token fresh automatically

Instagram tokens expire after 60 days. The *Refresh Instagram token* workflow renews it on the 1st of every month, but storing the new token needs permission:

1. GitHub **Settings (your profile) → Developer settings → Fine-grained tokens → Generate new token**.
2. Repository access: only `orthodox-daily-social`. Permissions: **Secrets: Read and write**. Expiration: a year.
3. Save it in this repository as the secret `SECRETS_ADMIN_TOKEN`.

Without it, repeat Step 5.5 and Step 6 every 60 days.

## Your daily routine

- Around 9 am, open the "Posts for …" pull request (the GitHub app notifies you).
- Look at the preview and captions.
- To change a caption: **Files changed → posts/<date>/post.json → ⋯ → Edit file**, change the text, commit to the same branch.
- **Merge** to publish, or **Close** to skip the day.

## Things you can change

| What | Where |
| --- | --- |
| Which psalm on Wednesdays | `psalm-plan.json`: add a date, or reorder the rotation |
| What each weekday posts, tone, caption rules | `AUTOMATION.md` |
| Calendar, tradition, translation | `config.json` |
| Fonts | `fonts/` (Crimson Text and Geist, SIL Open Font License) |
| Designs | `social/templates.py` |

## Not automated yet

- **Story link stickers**: the API can't add them, so Stories say "link in bio".
- **Voice and music on Reels**: Reels are published silent for now. The next step is adding the Kokoro voice-over and a quiet music bed to the workflow. Until then, on Reel days you can close the pull request and post that Reel yourself with music.
