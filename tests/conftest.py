from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def valid_frames() -> dict[str, pd.DataFrame]:
    meta = pd.DataFrame(
        {
            "Nome da Página": ["Marca A"],
            "Nome da campanha": ["Campanha FLN"],
            "Tipo de resultado": ["Conversas"],
            "Resultados": ["10"],
            "Alcance": ["1.738"],
            "Impressões": ["2.000"],
            "Custo por resultado": ["20,00"],
            "Cliques (todos)": ["50"],
            "Valor usado (BRL)": ["200,00"],
            "Início dos relatórios": ["01/05/2024"],
            "Término dos relatórios": ["08/05/2024"],
            "Semana": ["1 a 8"],
        }
    )
    google = pd.DataFrame(
        {
            "Marca": ["Marca B"],
            "Campanha": ["Pesquisa BRQ"],
            "Tipo de campanha": ["Pesquisa"],
            "Cliques": ["100"],
            "Impr.": ["5.000"],
            "Custo": ["200,00"],
            "CPC": ["2,00"],
            "Início": ["01/05/2024"],
            "Fim": ["08/05/2024"],
            "Semana": ["1 a 8"],
        }
    )
    return {"dados-face": meta, "dados-google": google}

