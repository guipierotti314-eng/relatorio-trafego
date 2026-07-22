"""Estado persistente e sincronização dos filtros por checkbox."""

from __future__ import annotations

from collections.abc import MutableMapping, Sequence
from hashlib import sha1
import json
from typing import Any

import streamlit as st


FILTER_DEFAULTS: dict[str, Any] = {
    "filter_brands": [],
    "filter_platforms": [],
    "filter_segments": [],
    "filter_actions": [],
    "filter_result": "Todos",
}


def initialize_filter_state(
    state: MutableMapping[str, Any] | None = None,
    query_params: MutableMapping[str, Any] | None = None,
) -> None:
    target = st.session_state if state is None else state
    params = st.query_params if state is None and query_params is None else (query_params or {})
    for key, default in FILTER_DEFAULTS.items():
        if key not in target:
            restored: Any = None
            raw = params.get(key)
            if raw is not None:
                try:
                    restored = json.loads(str(raw))
                except (TypeError, ValueError, json.JSONDecodeError):
                    restored = None
            valid = isinstance(restored, list) if isinstance(default, list) else isinstance(restored, str)
            target[key] = restored if valid else (default.copy() if isinstance(default, list) else default)


def persist_filter_state(
    state: MutableMapping[str, Any] | None = None,
    query_params: MutableMapping[str, Any] | None = None,
) -> None:
    source = st.session_state if state is None else state
    target = st.query_params if query_params is None else query_params
    for key in FILTER_DEFAULTS:
        serialized = json.dumps(source.get(key, FILTER_DEFAULTS[key]), ensure_ascii=False)
        if target.get(key) != serialized:
            target[key] = serialized


def option_widget_key(group: str, option: str) -> str:
    token = sha1(option.encode("utf-8")).hexdigest()[:10]
    return f"filter_{group}_option_{token}"


def sync_multi_group(
    state: MutableMapping[str, Any],
    selection_key: str,
    all_key: str,
    options: Sequence[str],
    changed_key: str,
) -> None:
    pairs = [(option, option_widget_key(selection_key, option)) for option in options]
    if changed_key == all_key and bool(state.get(all_key)):
        for _, key in pairs:
            state[key] = False
        state[selection_key] = []
        return
    selected = [option for option, key in pairs if bool(state.get(key))]
    if selected:
        state[all_key] = False
        state[selection_key] = selected
    else:
        state[all_key] = True
        state[selection_key] = []


def sync_single_group(
    state: MutableMapping[str, Any],
    selection_key: str,
    all_key: str,
    options: Sequence[str],
    changed_key: str,
) -> None:
    if changed_key == all_key:
        state[selection_key] = "Todos"
    else:
        chosen = next(
            (option for option in options if option_widget_key(selection_key, option) == changed_key),
            None,
        )
        state[selection_key] = chosen if chosen and bool(state.get(changed_key)) else "Todos"
    selected = state[selection_key]
    state[all_key] = selected == "Todos"
    for option in options:
        state[option_widget_key(selection_key, option)] = option == selected


def _multi_callback(selection_key: str, all_key: str, options: tuple[str, ...], changed_key: str) -> None:
    sync_multi_group(st.session_state, selection_key, all_key, options, changed_key)


def _single_callback(selection_key: str, all_key: str, options: tuple[str, ...], changed_key: str) -> None:
    sync_single_group(st.session_state, selection_key, all_key, options, changed_key)


def render_multi_checkbox_group(label: str, group: str, options: Sequence[str]) -> tuple[str, ...]:
    selection_key = f"filter_{group}"
    all_key = f"filter_{group}_all"
    selected = list(st.session_state.get(selection_key, []))
    visible_options = tuple(dict.fromkeys([*options, *selected]))
    st.markdown(f"<div class='filter-group-title'>{label}</div>", unsafe_allow_html=True)
    st.session_state.setdefault(all_key, not selected)
    st.checkbox(
        "Todos", key=all_key, on_change=_multi_callback,
        args=(selection_key, all_key, visible_options, all_key),
    )
    for option in visible_options:
        widget_key = option_widget_key(selection_key, option)
        st.session_state.setdefault(widget_key, option in selected)
        st.checkbox(
            option, key=widget_key, on_change=_multi_callback,
            args=(selection_key, all_key, visible_options, widget_key),
        )
    return tuple(st.session_state.get(selection_key, []))


def render_single_checkbox_group(label: str, group: str, options: Sequence[str]) -> str:
    selection_key = f"filter_{group}"
    all_key = f"filter_{group}_all"
    selected = str(st.session_state.get(selection_key, "Todos"))
    st.markdown(f"<div class='filter-group-title'>{label}</div>", unsafe_allow_html=True)
    st.session_state.setdefault(all_key, selected == "Todos")
    st.checkbox(
        "Todos", key=all_key, on_change=_single_callback,
        args=(selection_key, all_key, tuple(options), all_key),
    )
    for option in options:
        widget_key = option_widget_key(selection_key, option)
        st.session_state.setdefault(widget_key, option == selected)
        st.checkbox(
            option, key=widget_key, on_change=_single_callback,
            args=(selection_key, all_key, tuple(options), widget_key),
        )
    return str(st.session_state.get(selection_key, "Todos"))


def clear_advanced_filters(state: MutableMapping[str, Any] | None = None) -> None:
    target = st.session_state if state is None else state
    for key, default in FILTER_DEFAULTS.items():
        target[key] = default.copy() if isinstance(default, list) else default
    for key in list(target):
        if key.startswith("filter_") and "_option_" in key:
            target[key] = False
        elif key.endswith("_all") and key.startswith("filter_"):
            target[key] = True
