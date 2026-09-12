from __future__ import annotations

from typing import TypedDict

from langgraph.graph import StateGraph, END

from predictive_utils import predict_upcoming_issues


class PredictiveState(TypedDict):
    complaints: list[dict]
    location: str | None
    months_ahead: int
    top_n: int
    predictions: list[dict]


def forecast_node(state: PredictiveState) -> PredictiveState:
    state["predictions"] = predict_upcoming_issues(
        state["complaints"],
        location=state["location"],
        months_ahead=state["months_ahead"],
        top_n=state["top_n"],
    )
    return state


def build_predictive_graph():
    graph = StateGraph(PredictiveState)
    graph.add_node("forecast_node", forecast_node)
    graph.set_entry_point("forecast_node")
    graph.add_edge("forecast_node", END)
    return graph.compile()


predictive_graph = build_predictive_graph()


def run_predictive_pipeline(complaints: list[dict], location: str | None = None, months_ahead: int = 2, top_n: int = 5):
    state: PredictiveState = {
        "complaints": complaints,
        "location": location,
        "months_ahead": months_ahead,
        "top_n": top_n,
        "predictions": [],
    }
    return predictive_graph.invoke(state)
