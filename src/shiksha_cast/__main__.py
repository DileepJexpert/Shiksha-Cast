from __future__ import annotations

import sys


if len(sys.argv) > 1 and sys.argv[1] in {"asset-check", "asset-plan"}:
    command = sys.argv.pop(1)
    if command == "asset-check":
        from shiksha_cast.asset_library import asset_check_main

        asset_check_main()
    else:
        from shiksha_cast.asset_library import asset_plan_main

        asset_plan_main()
else:
    from shiksha_cast.cli import main

    main()
