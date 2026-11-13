"""Układ slajdów decku. Kolejność = kolejność w `SLIDES`; każda funkcja ma podpis
`slide_NN_nazwa(prs, t, assets)`, gdzie `t` to słownik treści z content_<lang>.json."""

from .architecture import (
    slide_04_architecture, slide_05_decisions, slide_06_rag, slide_07_tools, slide_08_omnichannel,
)
from .opening import slide_01_title, slide_02_problem, slide_03_persona
from .operations import (
    slide_09_demo, slide_10_security, slide_11_multihotel, slide_12_costs, slide_13_roadmap, slide_14_qa,
)

SLIDES = [
    slide_01_title,
    slide_02_problem,
    slide_03_persona,
    slide_04_architecture,
    slide_05_decisions,
    slide_06_rag,
    slide_07_tools,
    slide_08_omnichannel,
    slide_09_demo,
    slide_10_security,
    slide_11_multihotel,
    slide_12_costs,
    slide_13_roadmap,
    slide_14_qa,
]

__all__ = ["SLIDES"]
