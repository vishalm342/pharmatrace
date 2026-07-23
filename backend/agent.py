import os
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from opentelemetry import trace
from backend.tools import lookup_drug, check_interaction as fda_check

llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))

@tool
def drug_lookup(drug_name: str) -> str:
    """Look up drug warnings and known interactions from FDA database."""
    return str(lookup_drug(drug_name))

@tool
def interaction_check(drug_a_and_b: str) -> str:
    """Check adverse event reports for two drugs used together. Input format: 'drugA,drugB'"""
    parts = drug_a_and_b.split(",")
    drug_a, drug_b = parts[0].strip(), parts[1].strip()
    return str(fda_check(drug_a, drug_b))

tools = [drug_lookup, interaction_check]
tool_map = {t.name: t for t in tools}
llm_with_tools = llm.bind_tools(tools)
tracer = trace.get_tracer("pharmatrace.agent")

async def run_agent(drug_a: str, drug_b: str) -> str:
    with tracer.start_as_current_span("llm-agent-run") as span:
        span.set_attribute("drug.a", drug_a)
        span.set_attribute("drug.b", drug_b)

        msgs = [
            SystemMessage(content="You are a clinical pharmacology assistant. Use tools to check drug warnings and interactions, then give a structured safety analysis with risk level (LOW/MODERATE/HIGH)."),
            HumanMessage(content=f"What are the risks of taking {drug_a} and {drug_b} together? Check both drugs individually then their interaction.")
        ]

        response = llm_with_tools.invoke(msgs)
        msgs.append(response)

        while response.tool_calls:
            for tc in response.tool_calls:
                selected = tool_map.get(tc["name"])
                output = selected.invoke(tc["args"])
                span.set_attribute(f"tool.{tc['name']}.called", True)
                msgs.append(ToolMessage(content=str(output), tool_call_id=tc["id"]))
            response = llm_with_tools.invoke(msgs)
            msgs.append(response)

        span.set_attribute("agent.response_length", len(response.content))
        return response.content