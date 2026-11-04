---
name: streamlit-legacy-140
description: Write, port and review Streamlit apps pinned to 1.38-1.40 (corporate images, frameworks that cap Streamlit) - what exists and what does not in 1.40.2, the replacement for each newer API (theme, JavaScript, pagination, ButtonColumn, horizontal containers, page_link query params, required pills), config.toml limits, 1.40 runtime pitfalls, and a script that checks the installed API surface. Use instead of developing-with-streamlit (which needs >=1.57) whenever requirements pin streamlit below 1.41, when porting code written for a newer Streamlit down to 1.40, or when the user says "Streamlit 1.40", "versão homologada do Streamlit", "não existe na 1.40", "portar para Streamlit antigo", "TypeError unexpected keyword argument" on a Streamlit call.
metadata:
  version: "1.0.0"
---

# Streamlit 1.38-1.40 (legacy pin)

Most Streamlit examples online, in docs and in model memory target recent releases. On a pinned 1.38-1.40 they fail with `TypeError: ... got an unexpected keyword argument` or `AttributeError: module 'streamlit' has no attribute ...`, or they silently do nothing. This skill keeps code inside the installed API.

`developing-with-streamlit` needs Streamlit >= 1.57. Do not load it for these projects.

## Step 1 - Confirm the version, then the surface

1. Read the pin: `requirements*.txt`, `pyproject.toml`, lock file. Exact pin (`==1.40.2`) is the target. A range means the lowest allowed version is the target.
2. Run the checker with the project's interpreter. It only reads and installs nothing:

```bash
.venv/bin/python <skills>/streamlit-legacy-140/scripts/api_surface.py            # full report
.venv/bin/python <skills>/streamlit-legacy-140/scripts/api_surface.py pills html  # selected calls
```

3. Any API not in the report does not exist for this project. Never add `try/except AttributeError` to call a newer API "if available". That forks behavior between environments.

Verified on 1.40.2 with Python 3.11. The 1.38 and 1.39 releases have less: `st.pills` and `st.segmented_control` first appear in 1.40. Run the checker on the real pin.

## Step 2 - Missing in 1.40.2 and the replacement

Put every replacement behind one function in a single compatibility module, for example `core/compat.py`. Pages call the function, never the replacement directly. Raising the pin then changes one file.

| Newer API | In 1.40 | Replacement |
|---|---|---|
| `st.context.theme`, `[theme.light]`/`[theme.dark]`/`[theme.sidebar]`, `fontFaces` | `st.context` has only `headers`, `cookies`. Theme keys are only `base`, `primaryColor`, `backgroundColor`, `secondaryBackgroundColor`, `textColor`, `font` | Light theme in `[theme]`; dark via CSS variables; detect the applied theme with a small `components.v1` probe that reports back |
| `st.html(..., unsafe_allow_javascript=True)` | `st.html(body)` only; scripts do not run | `components.v1.html("<script>...</script>", height=0)`; it runs in a same-origin iframe and reaches the page through `window.parent` |
| `st.components.v2` | only `components.v1` | `components.v1.declare_component` with a versioned local folder |
| `st.pagination` | missing | Previous/Next buttons plus "Page X of Y", page in `session_state`, clamped when filters shrink the data |
| `column_config.ButtonColumn` | missing | `st.dataframe(on_select="rerun", selection_mode="single-row")` plus one `st.button` for the selected row |
| `st.container(horizontal=True, gap=...)` | `container(height, border, key)` only | `st.columns(spec, gap=..., vertical_alignment=...)` |
| `st.page_link(..., query_params=...)` | missing parameter | `st.button` that stores the target in `session_state` and calls `st.switch_page` |
| `required=True` on `pills`/`segmented_control` | missing | `on_change` callback that restores the previous value when the user unselects |
| `width="stretch"` / `width=` on widgets | missing | `use_container_width=True` |
| `st.plotly_chart(height=..., width=..., config=...)` | missing parameters | `fig.update_layout(height=...)`, `use_container_width=True` |
| `st.chat_input(accept_file=...)` | missing | separate `st.file_uploader` |
| `st.dialog(dismissible=, on_dismiss=)` | `title`, `width` only | handle closing with state inside the dialog |
| `st.login`, `st.logout`, `st.user` | missing | identity from the proxy: `st.context.headers` |
| `st.badge`, `st.space` | missing | `st.html` with own CSS class; `st.write("")` or CSS margin |
| `st.experimental_*` | present but deprecated | do not use; stable names exist for dialog, fragment, audio_input, query params |

## Step 3 - CSS and DOM

- Select only stable hooks: the `st-key-<key>` class that keyed containers and widgets receive, and `data-testid`. Never `st-emotion-cache-*`: those classes change on every release.
- Own classes get a project prefix. Colors come from CSS variables, not literals scattered in Python.
- `st.markdown(unsafe_allow_html=True)` and `st.html` take HTML. Escape every value that came from an API or user before interpolating (`html.escape`). Injection through a "label" or "currency" field is a real finding in review.

## Step 4 - Runtime pitfalls seen on 1.40

- **`st.rerun()` in the middle of a page** stops the script. Widgets below are not rendered, and their state is dropped because a widget missing from a run loses its state. Pattern: pages set a flag; the entry script calls `st.rerun()` once at the very end.
- **First session after server start shows "Page not found"** for a direct URL such as `/report`. The page still renders under the modal. Cause: the first session resolves the URL before `st.navigation` has ever run in the process. Fixed upstream later. Workaround: detect it before `st.navigation` and close the modal by script when the address is a real page.
- **`server.enableCORS = false` is overridden** to `true` while `enableXsrfProtection` stays true. Streamlit prints a warning at start. Decide both together and record the choice.
- **Theme is unknown on the first run** of a session until a probe answers. Default to light and accept one extra rerun.
- **`st.cache_data` returns shared data.** Never cache anything user-specific. Copy mutable results before editing them.

## Step 5 - Porting code from a newer Streamlit

1. List every `st.` call and its keyword arguments in the source.
2. Run the checker for those names. Mark each call as exists, missing parameter, or missing API.
3. Map each failure to the table in Step 2 and implement it once in the compatibility module.
4. Run the app headless. Check the server log for `TypeError` and `AttributeError`, then open each page.
5. Record each fidelity loss, such as a dark theme that only reaches own blocks or pills replacing clickable HTML, as a known difference for the user.

## Testing

- `streamlit.testing.v1.AppTest` exists in 1.40: `AppTest.from_file("app.py").run()`, then assert on `at.exception`, widgets and markdown.
- Test the compatibility module with plain pytest by faking `st.session_state` where possible.
- JavaScript in `components.v1` does not run under `AppTest`. Cover it with a headless browser check (`webapp-testing`, `e2e-testing`).

## Done means

- Checker run on the project interpreter, output quoted for the calls touched.
- No call or keyword argument outside the installed surface; `grep -rn "st-emotion-cache\|unsafe_allow_javascript\|st.experimental_" src` is empty.
- App started headless with no exception in the log, every page opened.
