"""Unit tests for the specification parser in the attack tree analyzer."""


from app.model import parse_spec, SpecError


def test_parse_yaml_simple():
    """A minimal YAML spec with one root and one leaf parses correctly."""
    yaml_text = """
id: root
label: Top event
type: OR
children: [leaf]
nodes:
  - id: leaf
    label: Leaf
    type: LEAF
    prob: 0.4
    impact: 1.0
"""
    spec = parse_spec(yaml_text, "yaml")
    assert spec["root"] == "root"
    assert set(spec["nodes"].keys()) == {"root", "leaf"}
    assert spec["nodes"]["leaf"]["prob"] == 0.4


def test_parse_json():
    """JSON input is supported."""
    json_text = {
        "id": "r",
        "label": "Top",
        "type": "AND",
        "children": ["a", "b"],
        "nodes": [
            {"id": "a", "label": "A", "type": "LEAF", "prob": 0.3, "impact": 5},
            {"id": "b", "label": "B", "type": "LEAF", "prob": 0.2, "impact": 3},
        ],
    }
    import json
    spec = parse_spec(json.dumps(json_text), "json")
    assert spec["nodes"]["a"]["impact"] == 5


def test_parse_xml():
    """XML input is supported and normalised."""
    xml_text = """
<spec>
  <id>top</id>
  <label>Test</label>
  <type>OR</type>
  <children>
    <child>a</child>
    <child>b</child>
  </children>
  <nodes>
    <node>
      <id>a</id>
      <label>A</label>
      <type>LEAF</type>
      <prob>0.2</prob>
      <impact>1</impact>
    </node>
    <node>
      <id>b</id>
      <label>B</label>
      <type>LEAF</type>
      <prob>0.1</prob>
      <impact>2</impact>
    </node>
  </nodes>
</spec>
"""
    spec = parse_spec(xml_text, "xml")
    assert spec["root"] == "top"
    assert set(spec["nodes"].keys()) == {"top", "a", "b"}


def test_invalid_missing_child():
    """Referencing a non‑existent child should raise SpecError."""
    yaml_text = """
id: r
label: Top
type: AND
children: [x]
nodes:
  - id: a
    label: A
    type: LEAF
    prob: 0.1
    impact: 1
"""
    raised = False
    try:
        parse_spec(yaml_text, "yaml")
    except SpecError:
        raised = True
    assert raised, "SpecError not raised for missing child"
