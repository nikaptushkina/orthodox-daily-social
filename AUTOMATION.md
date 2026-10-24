# The daily procedure (for the morning task)

This file is the instruction set the 9 am scheduled task follows. A person can follow it too.
Everything happens in this repository; nothing is posted until the day's pull request is merged.

## 0. Setup

```
git clone https://github.com/nikaptushkina/orthodox-daily-social
cd orthodox-daily-social
```

- `D` = today's date in America/Los_Angeles, as `YYYY-MM-DD`. The weekday is D's weekday.
- If a branch named `posts/D` already exists (`git ls-remote origin posts/D` prints a line), stop: today is already drafted.
- Read `config.json` (calendar, tradition, translations) and `days/D.json` (today's calendar data, saved overnight by the "Fetch calendar days" workflow). Also read the following days in `days/` when the weekday needs them.
- If `days/D.json` is missing, stop and report: "Calendar data for D is missing. Run the Fetch calendar days workflow in the Actions tab."

## 1. Decide what to post

Every day: the **Story**. Plus, by weekday:

| Weekday | Feed post (`feed.kind`) | Reel (`reel`) |
| --- | --- | --- |
| Sunday | `week_ahead`: today to Saturday | none |
| Monday | `saint`: today's principal saint | none |
| Tuesday | `word`: today's Gospel (the Epistle if there is no Gospel) | none |
| Wednesday | none | Psalm from `psalm-plan.json` (the date's entry, else rotation entry `(ISO week number) mod length`) |
| Thursday | `saint`: today's principal saint | none |
| Friday | `feast`: the most significant feast in the coming 8 days (Great Feasts first, then feasts of the Theotokos, the Cross, apostles and great saints); if none, today's principal commemoration | none |
| Saturday | none | Vespers readings if `days/D.json` has readings whose `source` is `Vespers`; otherwise today's Gospel |

On a Great Feast (or Pascha), make the feed post a `feast` explainer for that feast, whatever the weekday.

## 2. Write `posts/D/content.json`

Write only text here. Scripture is never typed: `reading.index` points into `days/D.json` `readings`, and psalms come from `assets/psalms.json`, word for word.

```json
{
  "date": "D",
  "story": {
    "date_line": "Saturday · October 24",
    "title": "Demetrius Saturday",
    "subtitle": "A memorial Saturday: we pray for the departed",
    "week_line": "Saturday of the 21st week after Pentecost",
    "commemorating": "Martyr Arethas and Companions",
    "fasting": "No fast",
    "readings": [
      {"label": "Readings of the day", "refs": ["2 Corinthians 3:12–18", "Luke 7:1–10"]},
      {"label": "For the departed", "refs": ["1 Thessalonians 4:13–17", "John 5:24–30"]}
    ],
    "accent": "ordinary"
  },
  "feed": { "kind": "...", "caption": "...", "...": "fields below" },
  "reel": { "...": "fields below", "caption": "..." }
}
```

**Story** (every day), from `days/D.json`:
- `title`: the feast or principal commemoration, in plain words (from `titles[0]`, `summary_title`, `feasts`, `saints`). `subtitle`: one short line saying what the day is, if useful. `week_line`: the liturgical week (`titles[1]` when it reads like "Saturday of the 21st week after Pentecost").
- `commemorating`: one or two saints, the most important first. `fasting`: from `fast_level_desc` and `fast_exception_desc`, written simply ("No fast", "Fast day", "Fish allowed", "Wine and oil allowed", "Strict fast").
- `readings`: the day's Epistle and Gospel as "Book C:V–V" (en dash), then a second group for extra readings with their `description` as the label ("For the departed", "For the saint"). At most two groups.

**Feed kinds** (every carousel also needs `caption` and `accent`):
- `week_ahead`: `range_line` ("October 25 – 31"), `rows` (up to 7: `day` "Sun 25", `title` the main commemoration, `fast` short text, `fast_kind` one of `none` `fast` `fish` `dairy`), optional `banner` (the week's main event), and `end` (`kicker`, `title`, `date`, optional `second` (the Old Calendar date when it helps), `line`, `accent`): the coming feast or fast, or "Have a blessed week".
- `saint`: `name`, `subtitle` (title and place), `dates` ("Oct 26 New Calendar · Nov 8 Old Calendar"), `heading` ("Who he was" / "Who she was" / "Who they were"), `life` (two short paragraphs, 25–45 words each, from the day's `stories` and well-established tradition only), `intercession` ("Holy Great-martyr Demetrios, pray to God for us.").
- `word`: `reading` (`{"index": N}`), `book_intro` ("The Gospel according to", "The Epistle of St Paul to the", "The Acts of the"), `book_title` ("Luke", "Romans", "Apostles"), `ref_line` ("Chapter 7, verses 1–10"), `context` ("Gospel for Tuesday, October 27"), `translation` ("World English Bible"). Pages are built automatically.
- `feast`: `kicker` ("Great Feast", "Feast"), `name`, `subtitle`, `dates`, `meaning` (exactly three sentences of 20–30 words), `kept` (three rows labelled `Fasting`, `Services`, `Hymns`, one sentence each).

**Reel**:
- Psalm (Wednesday): `{"kind":"psalm","mood":"dawn","psalm":{"name":"Psalm 102","from":1,"to":5},"title":{"kicker":"A psalm to pray · Wednesday","title":"Psalm 102","subtitle":"Bless the Lord, O my soul"},"end":{"quote":"a short line from the psalm, word for word"},"footer":"orthodoxdaily.net · Septuagint"}`
- Gospel or Vespers (Saturday): `{"kind":"gospel","mood":"dawn","reading":{"index":N},"title":{"kicker":"The Gospel · Saturday, October 24","title":"Luke 7:1–10","subtitle":"a short theme"},"end":{"quote":"one line from the reading, word for word"},"footer":"orthodoxdaily.net · World English Bible"}`. For Vespers readings use `"mood":"vespers"`, the kicker "Vespers · Saturday evening", and the Septuagint footer for Old Testament readings. When there are several Vespers readings, use the first.
- `title.title` must fit on one line: shorten long titles ("Wisdom 3:1–9"). Add `"size": 140` to `title` for titles over 12 characters.

**Accents**: `feast` (Feasts of the Lord, Nativity, Pascha), `theotokos`, `martyr`, `lent` (Great Lent, Holy Week), `pentecost`, `ordinary` (ordinary days, memorial Saturdays). One per post.

**Voice** (see the design system): calm, reverent, plain. Liturgically exact; always name the calendar ("New Calendar"). Fasting stated simply with no rules lectures. Never polemical. No emoji.

**Captions**: first line under 125 characters and says what the post is; two to four short paragraphs; end with "Full day at the link in our bio." and three to five hashtags from #OrthodoxChristian #OrthodoxChurch #SaintOfTheDay #GospelOfTheDay #DailyPrayer #Psalms #Scripture #OrthodoxFeasts. Quote Scripture only word for word from the reading.

Never invent facts. If a saint's life or a feast's practice is uncertain, say less.

## 3. Build and check

```
python3 -m social.build D
```

This renders `posts/D/` (JPEGs, `reel.mp4`, `reel-cover.jpg`, `post.json`, `preview.jpg`). A Reel takes a few minutes.

Then **look at every image** (open each JPEG, and `preview.jpg`). Fix and rebuild if text is cut off, a name is wrong, a line is awkwardly broken, or the calendar label is missing. Make sure `post.json` lists the expected items.

## 4. Open the pull request

```
git checkout -b posts/D
git add posts/D
git commit -m "Posts for <Weekday>, <Month> <day>"
git push -u origin posts/D
```

Open a pull request into `main` titled "Posts for <Weekday>, <Month> <day>" with GitHub's REST API (GraphQL, and so `gh pr create`, may not be available):

```
gh api repos/nikaptushkina/orthodox-daily-social/pulls -f base=main -f head=posts/D -f title="Posts for ..." -f body="$(cat body.md)"
```

Use this body:

- `![preview](https://raw.githubusercontent.com/nikaptushkina/orthodox-daily-social/posts/D/posts/D/preview.jpg)`
- What is in it (Story, carousel or Reel) and today's commemoration in one line.
- Each caption in a quote block.
- "Merge to publish. To change a caption, edit `posts/D/post.json` in this pull request before merging. To skip today, close the pull request."

Finish with one line for the person: the pull request link and what it contains.
