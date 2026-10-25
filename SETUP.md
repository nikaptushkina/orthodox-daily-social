# Setting up Orthodox Daily's Instagram automation

This is a one-time setup, about 30–45 minutes. After it, your only daily job is to look at one pull request and tap Merge.

## How it works

1. **Every night**, the *Fetch calendar days* workflow (GitHub Actions) saves the next 8 days of calendar data from Orthocal, the same source and settings as orthodoxdaily.net (New Calendar, Slavic, Septuagint and World English Bible), into `days/`. On its first run it also downloads the public-domain LXX2012 Psalter (all 151 psalms) for the Wednesday Reels.
2. **Every morning just before 9 am Pacific**, a scheduled task in Claude follows [AUTOMATION.md](AUTOMATION.md): it writes the day's texts, renders the Story, carousel and Reel in your fonts and colours, and opens a pull request named "Posts for …" with a preview.
3. **You review it** in the GitHub app or website. Merge it to approve. Close it to skip the day.
4. **Approved posts go out on schedule**: the *Publish approved posts* workflow puts the images and video online with GitHub Pages (Instagram needs a public address to fetch them from), posts the Story right away, and posts the feed post at that weekday's posting time (see *Posting times* below) through Instagram's official API. If you approve after the posting time, it goes out right away.

Nothing is ever posted without your merge.

## Step 1: Merge the setup pull request

On GitHub, open the pull request "Set up the daily Instagram automation", read it, and click **Merge pull request**.

## Step 2: Switch on GitHub Pages

Repository **Settings → Pages → Build and deployment → Source: GitHub Actions**. Nothing else to fill in.

## Step 3: Fetch the calendar data once

**Actions → Fetch calendar days → Run workflow**. After a minute, a `days/` folder appears with the next 8 days, and `assets/psalter-lxx2012.json` with the Psalter. From now on it runs every night by itself.

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
2. When you're happy, change `PUBLISH_ENABLED` to `true`. From then on, merging approves: the Story posts right away and the feed post at its posting time.
3. If a day ever fails, open the failed workflow run in Actions to see why, fix the cause, and use **Run workflow** on *Publish approved posts* with that date. That posts the day's remaining items immediately, whatever the time. Items that already went out are never posted twice.

## Step 7b: Music for the Reels

Reels are read aloud by Kokoro (Michael, at 0.9) with music underneath. The music is a licensed Pixabay track, so it lives in a private repo, `orthodox-daily-assets`, rather than in this public one.

1. Create the private repo `orthodox-daily-assets` (no README) and put the track at `music/the-mountain-quiet-documentary.mp3`.
2. Create a fine-grained personal access token at https://github.com/settings/personal-access-tokens/new: name `orthodox-daily music`, the longest expiration offered, **Only select repositories** → `orthodox-daily-assets`, **Contents: Read-only**.
3. Save it in this repo as the secret `ASSETS_TOKEN`.

Without it, Reels still get the voice, with no music. If the token expires, make a new one the same way and replace the secret.

On Reel days (Wednesday and Saturday) the morning pull request opens as a **draft**. About 15 minutes later the *Add voice and music to the Reel* workflow adds the finished video, comments with a link to watch it, and marks the pull request ready to merge.

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
- **Merge** to approve, or **Close** to skip the day. Approve before the posting time and the feed post waits for it; a day not approved by midnight is not posted.

## Saint icons

The nightly fetch asks orthodoxdaily.net's own icon lookup (Wikipedia and Wikimedia Commons, freely licensed images only) for every saint in the coming days, and saves what it finds in `assets/icons/`. On Monday and Thursday the saint's icon goes in the arch on the first slide, with its credit underneath.

When the lookup has no confident match, the cross is shown instead and the morning pull request opens as a **draft** that says "Icon needed". To add one, reply on the pull request with

```
icon: https://link-to-the-image.jpg
credit: Icon: Wikimedia Commons · Public domain
```

or paste the image into a comment that has the word "icon" in it (the credit line is optional). A workflow downloads it, rebuilds the slides, comments with the new preview and marks the pull request ready. Only your own comments are acted on.

## Posting times

Set in `config.json` under `posting_times`, in Pacific time:

| Day | Feed post | Time |
|---|---|---|
| Monday | Saint carousel | 2:00 pm |
| Tuesday | Word for the day | 1:00 pm |
| Wednesday | Psalm Reel | 12:00 noon |
| Thursday | Saint carousel | 12:00 noon |
| Friday | Feast explainer | 11:00 am |
| Saturday | Vespers readings Reel | 4:00 pm |
| Sunday | The week ahead | 1:00 pm |

The Story goes out as soon as you approve, so the day's calendar is up all day. To change a time, edit the value (24-hour, e.g. `"17:30"`). Posts can land up to about 15–30 minutes after the time, because GitHub's scheduled checks run every 15 minutes and are sometimes delayed.

## Things you can change

| What | Where |
| --- | --- |
| Which psalm on Wednesdays | `psalm-plan.json`: the rotation goes through the whole Psalter, Psalm 1 to 151, one each Wednesday, splitting long psalms into parts. Pin a psalm to a date under `dates` |
| What each weekday posts, tone, caption rules | `AUTOMATION.md` |
| Calendar, tradition, translation | `config.json` |
| Fonts | `fonts/` (Crimson Text and Geist, SIL Open Font License) |
| Designs | `social/templates.py` |

## Not automated yet

- **Story link stickers**: the API can't add them, so Stories say "link in bio".
- **Reel voice and music**: in `config.json` under `reel_audio`. `voice` is any Kokoro voice (`am_michael`, `bm_george`, `af_heart`, ...), `speed` 1.0 is normal, `music_lufs` sets how loud the music is (−20 is louder, −28 quieter). To change the track, add an mp3 to the private `orthodox-daily-assets` repo and point `music` at it.
