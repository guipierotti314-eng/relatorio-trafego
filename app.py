"""Aplicativo Streamlit do dashboard de Tráfego pago."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import (
    BASE_EXCEL_PATH,
    RESULT_CATEGORY_OPTIONS,
    SHOW_TECHNICAL_DETAILS,
    THEME_COLORS,
)
from src.comparisons import previous_period
from src.data_loader import get_file_signature, load_excel_base
from src.exports import to_csv_bytes, to_xlsx_bytes
from src.filters import (
    apply_dimension_filters,
    available_date_range,
    default_latest_month_range,
    dimension_options,
    filter_by_period,
)
from src.formatters import format_date_range_br
from src.normalization import NormalizationResult
from src.state import (
    clear_advanced_filters,
    initialize_filter_state,
    persist_filter_state,
    render_multi_checkbox_group,
    render_single_checkbox_group,
)
from src.validators import WorkbookValidationError
from src.views import overview


def _toggle_theme() -> None:
    current = st.session_state.get("theme_mode", "light")
    st.session_state["theme_mode"] = "dark" if current == "light" else "light"


def load_css(theme: str) -> None:
    colors = THEME_COLORS[theme]
    variables = ";".join(f"--{name.replace('_', '-')}: {value}" for name, value in colors.items())
    css_path = Path(__file__).parent / "assets" / "styles.css"
    css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
    st.markdown(f"<style>:root {{{variables};}}\n{css}</style>", unsafe_allow_html=True)


def advanced_filters(all_data: pd.DataFrame, period_data: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Renderiza grupos estáveis; opções não dependem do período selecionado."""
    initialize_filter_state()
    with st.sidebar.expander("Filtros avançados", expanded=True):
        brands = render_multi_checkbox_group("Marca", "brands", dimension_options(all_data, "marca"))
        platforms = render_multi_checkbox_group(
            "Plataforma", "platforms", dimension_options(all_data, "plataforma")
        )
        segments = render_multi_checkbox_group(
            "Categoria da campanha", "segments", ("0 km", "Seminovos")
        )
        actions = render_multi_checkbox_group(
            "Tipo de ação", "actions", ("Evento", "Regular")
        )
        result = render_single_checkbox_group(
            "Tipo de resultado", "result", RESULT_CATEGORY_OPTIONS
        )
        st.button(
            "Limpar filtros avançados",
            on_click=clear_advanced_filters,
            use_container_width=True,
        )
    persist_filter_state()
    filtered = apply_dimension_filters(
        period_data,
        platforms=platforms,
        brands=brands,
        campaign_segments=segments,
        action_types=actions,
        result_category=result,
    )
    return filtered, result


def render_filtered_downloads(data: pd.DataFrame) -> None:
    if data.empty:
        return
    with st.expander("Baixar dados filtrados"):
        st.caption(f"{len(data):,.0f} registros no recorte atual".replace(",", "."))
        csv_col, xlsx_col, _ = st.columns([1, 1, 3])
        csv_col.download_button(
            "CSV", to_csv_bytes(data), "dados_filtrados.csv", "text/csv", key="filtered_csv"
        )
        xlsx_col.download_button(
            "XLSX", to_xlsx_bytes(data, "dados_filtrados"), "dados_filtrados.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="filtered_xlsx",
        )


def _period_input(
    data: pd.DataFrame,
    file_signature: tuple[int, int],
) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    bounds, default = available_date_range(data), default_latest_month_range(data)
    if bounds is None or default is None:
        return None
    if st.session_state.get("period_file_signature") != file_signature:
        st.session_state["selected_period"] = (default.start.date(), default.end.date())
        st.session_state["period_file_signature"] = file_signature
    selected = st.sidebar.date_input(
        "Período", min_value=bounds.start.date(), max_value=bounds.end.date(),
        key="selected_period", format="DD/MM/YYYY",
    )
    if not isinstance(selected, (tuple, list)) or len(selected) != 2:
        st.sidebar.info("Selecione as datas inicial e final.")
        return None
    return pd.Timestamp(selected[0]), pd.Timestamp(selected[1])


def main() -> None:
    st.set_page_config(page_title="Dashboard de Tráfego pago", page_icon="📊", layout="wide")
    st.session_state.setdefault("theme_mode", "light")
    initialize_filter_state()
    load_css(str(st.session_state["theme_mode"]))
    st.sidebar.markdown("<div class='brand-mark'>TRÁFEGO <span>PAGO</span></div>", unsafe_allow_html=True)
    theme_label = "🌙 Modo escuro" if st.session_state["theme_mode"] == "light" else "☀️ Modo claro"
    st.sidebar.button(theme_label, on_click=_toggle_theme, use_container_width=True, key="theme_toggle")
    st.title("Dashboard de Tráfego pago")
    st.caption("Meta Ads e Google Ads em uma visão simples e comparável")
    try:
        file_signature = get_file_signature(BASE_EXCEL_PATH)
        result: NormalizationResult = load_excel_base(str(BASE_EXCEL_PATH), file_signature)
    except (FileNotFoundError, WorkbookValidationError, PermissionError, OSError) as exc:
        st.warning("Não há dados disponíveis nesse período.")
        if SHOW_TECHNICAL_DETAILS:
            with st.expander("Detalhes técnicos"):
                st.code(str(exc))
        return
    except Exception:
        st.warning("Não há dados disponíveis nesse período.")
        if SHOW_TECHNICAL_DETAILS:
            with st.expander("Detalhes técnicos"):
                st.code("Falha inesperada durante o carregamento da base.")
        return

    valid_data = result.data.loc[result.data["registro_valido"]].copy()
    selected_period = _period_input(valid_data, file_signature)
    if selected_period is None:
        return
    start, end = selected_period
    period_data = filter_by_period(valid_data, start, end)
    current, result_filter = advanced_filters(valid_data, period_data)

    comparison = previous_period(start, end, "Semana")
    previous_data = filter_by_period(valid_data, comparison.start, comparison.end)
    prior = apply_dimension_filters(
        previous_data,
        platforms=tuple(st.session_state["filter_platforms"]),
        brands=tuple(st.session_state["filter_brands"]),
        campaign_segments=tuple(st.session_state["filter_segments"]),
        action_types=tuple(st.session_state["filter_actions"]),
        result_category=result_filter,
    )

    st.markdown(
        "<div class='period-banner'>"
        f"<div><small>PERÍODO ANALISADO</small><b>{format_date_range_br(start, end)}</b></div>"
        f"<div><small>PERÍODO ANTERIOR</small><span>{format_date_range_br(comparison.start, comparison.end)}</span></div>"
        "</div>",
        unsafe_allow_html=True,
    )
    if comparison.adjusted:
        st.caption("A comparação foi ajustada para o último dia válido do mês anterior.")
    st.caption(
        "Intervalos agregados são incluídos integralmente quando intersectam o período; não há rateio proporcional."
    )

    overview.render(
        current,
        prior,
        result_filter,
        tuple(st.session_state["filter_brands"]),
        start,
        end,
        comparison.start,
        comparison.end,
    )
    render_filtered_downloads(current)


if __name__ == "__main__":
    main()
