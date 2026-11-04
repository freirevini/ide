#!/usr/bin/env python3
"""api_surface.py - prints which Streamlit APIs and parameters exist in the INSTALLED version.

Run with the project's interpreter (read-only, installs nothing):
    .venv/bin/python path/to/api_surface.py            all checks
    .venv/bin/python path/to/api_surface.py pills html  only these names

Use before writing code for a pinned Streamlit (1.38-1.40) so no API from a newer release slips in.
"""
import inspect
import sys

import streamlit as st

CHECKS = {
    # name: parameters that newer examples often pass
    "pills": ["required", "width"],
    "segmented_control": ["required", "width"],
    "container": ["key", "horizontal", "gap", "width"],
    "columns": ["vertical_alignment", "border"],
    "html": ["unsafe_allow_javascript", "width"],
    "page_link": ["query_params", "width"],
    "navigation": ["position", "expanded"],
    "dataframe": ["on_select", "selection_mode", "row_height", "width", "placeholder"],
    "plotly_chart": ["width", "height", "config", "on_select"],
    "button": ["width", "icon", "type"],
    "download_button": ["width", "on_click", "icon"],
    "chat_input": ["accept_file", "file_type", "max_chars"],
    "dialog": ["width", "dismissible", "on_dismiss"],
    "popover": ["width", "use_container_width"],
    "file_uploader": ["accept_multiple_files", "max_upload_size"],
    "pagination": [],
    "login": [],
    "logout": [],
    "user": [],
    "badge": [],
    "space": [],
    "audio_input": [],
    "feedback": [],
    "fragment": ["run_every"],
}


def params(obj):
    try:
        return set(inspect.signature(obj).parameters)
    except (TypeError, ValueError):
        return None


def main(names):
    print(f"streamlit {st.__version__}")
    for name in names or CHECKS:
        obj = getattr(st, name, None)
        if obj is None:
            print(f"  MISSING  st.{name}")
            continue
        have = params(obj)
        wanted = CHECKS.get(name, [])
        if have is None:
            print(f"  ok       st.{name} ({type(obj).__name__})")
            continue
        missing = [p for p in wanted if p not in have]
        tail = f"  (no: {', '.join(missing)})" if missing else ""
        print(f"  ok       st.{name}{tail}")
    print("  st.context:", [a for a in dir(st.context) if not a.startswith("_")])
    import streamlit.column_config as cc
    print("  column_config:", [a for a in dir(cc) if a.endswith("Column")])
    import streamlit.components as comp
    print("  components:", [a for a in dir(comp) if a.startswith("v")])
    from streamlit import config
    config.get_option("theme.base")  # loads the option registry
    print("  theme options:", sorted(k for k in config._config_options if k.startswith("theme")))


if __name__ == "__main__":
    main(sys.argv[1:])
