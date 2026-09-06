import re
from pathlib import Path
from xml.etree import ElementTree

import yaml
from openapi_spec_validator import validate

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_openapi_contract_is_valid() -> None:
    contract_path = REPOSITORY_ROOT / "contracts/openapi/order-service.yaml"
    contract = yaml.safe_load(contract_path.read_text())

    validate(contract)
    assert "/api/v1/orders" in contract["paths"]


def test_asyncapi_contract_has_required_structure() -> None:
    contract_path = REPOSITORY_ROOT / "contracts/asyncapi/order-events.yaml"
    contract = yaml.safe_load(contract_path.read_text())

    assert contract["asyncapi"] == "3.1.0"
    assert contract["channels"]["orderCreated"]["address"] == "order.created.v1"
    payload = contract["components"]["schemas"]["OrderCreatedPayload"]
    assert "customerName" not in payload["properties"]
    assert "customerPhone" not in payload["properties"]
    assert "address" not in payload["properties"]


def test_bpmn_and_svg_files_are_xml() -> None:
    files = list((REPOSITORY_ROOT / "docs").rglob("*.bpmn"))
    files.extend((REPOSITORY_ROOT / "docs").rglob("*.svg"))

    assert files
    for path in files:
        ElementTree.parse(path)


def test_local_markdown_links_exist() -> None:
    link_pattern = re.compile(r"\]\(([^)]+)\)")
    missing: list[str] = []

    for markdown_path in REPOSITORY_ROOT.rglob("*.md"):
        for link in link_pattern.findall(markdown_path.read_text()):
            if link.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = link.split("#", maxsplit=1)[0]
            if not target:
                continue
            resolved = (markdown_path.parent / target).resolve()
            if not resolved.exists():
                missing.append(f"{markdown_path.relative_to(REPOSITORY_ROOT)}: {link}")

    assert not missing, "Missing local links:\n" + "\n".join(missing)
