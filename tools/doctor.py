#!/usr/bin/env python3
import argparse
import json
import sys

import _sslib
import validate_campaign
import validate_repo


def main() -> int:
    parser = argparse.ArgumentParser(description="Run repo/campaign diagnostics.")
    parser.add_argument("--campaign", help="Campaign slug under campaigns/")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    repo_errors = validate_repo.collect_errors()
    repo_ok = not repo_errors

    campaign_payload = None
    if args.campaign:
        manifest = _sslib.load_manifest()
        result = validate_campaign.validate_campaign(args.campaign, manifest)
        campaign_payload = {
            "campaign": args.campaign,
            "ok": result.ok(),
            "errors": result.errors,
            "warnings": result.warnings,
        }

    payload = {
        "repo": {
            "ok": repo_ok,
            "errors": repo_errors,
        },
        "campaign": campaign_payload,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0 if repo_ok and (campaign_payload is None or campaign_payload["ok"]) else 1

    if repo_ok:
        print("repo: ok")
    else:
        print("repo: error")
        for err in repo_errors:
            print(f"error: {err}", file=sys.stderr)

    if campaign_payload:
        if campaign_payload["ok"]:
            print(f"campaign {args.campaign}: ok")
        else:
            print(f"campaign {args.campaign}: error")
        for warn in campaign_payload["warnings"]:
            print(f"warning: {warn}", file=sys.stderr)
        for err in campaign_payload["errors"]:
            print(f"error: {err}", file=sys.stderr)

    ok = repo_ok and (campaign_payload is None or campaign_payload["ok"])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
