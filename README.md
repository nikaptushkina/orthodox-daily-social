# Orthodox Daily · Instagram

Daily Instagram posts and Stories for [orthodoxdaily.net](https://orthodoxdaily.net): drafted automatically every morning, published only when you approve.

- **[SETUP.md](SETUP.md)**: the one-time setup and your daily routine. Start here.
- **[AUTOMATION.md](AUTOMATION.md)**: exactly what the morning task does each day.

| Folder | What's in it |
| --- | --- |
| `days/` | Calendar data, saved nightly from Orthocal |
| `posts/<date>/` | Each day's texts (`content.json`), rendered media, what to publish (`post.json`) and what was published |
| `social/` | Templates and renderer (`python3 -m social.build <date>`) |
| `scripts/` | Fetching calendar data and publishing to Instagram |
| `fonts/`, `assets/` | Crimson Text and Geist (SIL Open Font License), the cross logo, the LXX2012 Psalter (public domain, downloaded on the first run) |
| `.github/workflows/` | Nightly data fetch, publishing approved posts at their posting times, monthly token refresh |
