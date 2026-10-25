"""Check that the Instagram secrets work, without posting anything.

Reads IG_USER_ID and IG_ACCESS_TOKEN from the environment (GitHub secrets),
asks Instagram which account the token belongs to, and checks that the token
is allowed to publish. Never prints the token.

    python3 scripts/check_connection.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from publish import ApiError, call  # noqa: E402


def main():
    user = os.environ.get("IG_USER_ID", "").strip()
    token = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    missing = [n for n, v in (("IG_USER_ID", user), ("IG_ACCESS_TOKEN", token)) if not v]
    if missing:
        print("Missing secret(s): " + ", ".join(missing)
              + ". Add them under Settings > Secrets and variables > Actions > Secrets.")
        return 1

    ok = True
    try:
        me = call("GET", "me", {"fields": "user_id,username", "access_token": token})
        print(f"Token works: it belongs to @{me.get('username')} (user ID {me.get('user_id')}).")
        if str(me.get("user_id")) != user:
            ok = False
            print(f"Problem: IG_USER_ID is {user}, but the token's account ID is {me.get('user_id')}. "
                  "Set IG_USER_ID to the token's account ID.")
    except (ApiError, OSError) as e:
        print("Problem: Instagram did not accept the token. It may have been copied incompletely, "
              "or expired. Generate a new one in the Meta app and update IG_ACCESS_TOKEN.\n" + str(e))
        return 1

    try:
        lim = call("GET", f"{user}/content_publishing_limit",
                   {"fields": "quota_usage,config", "access_token": token})
        data = (lim.get("data") or [{}])[0]
        total = (data.get("config") or {}).get("quota_total", "?")
        print(f"Publishing allowed: {data.get('quota_usage', 0)} of {total} posts used in the last 24 hours.")
    except (ApiError, OSError) as e:
        ok = False
        print("Problem: the token cannot publish. In the Meta app, add the "
              "instagram_business_content_publish permission, then generate a new token.\n" + str(e))

    print("All good." if ok else "Not ready yet: see the problem above.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
