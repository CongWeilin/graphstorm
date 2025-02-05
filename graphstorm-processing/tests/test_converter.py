"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License").
You may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import pytest

from graphstorm_processing.config.config_conversion import (
    GConstructConfigConverter,
)


@pytest.fixture(name="converter")
def fixture_create_converter() -> GConstructConfigConverter:
    """Creates a new converter object for each test."""
    yield GConstructConfigConverter()


@pytest.fixture(name="node_dict")
def create_node_dict() -> dict:
    """Creates a node dictionary for each test."""
    text_input: dict[str, list[dict]] = {"nodes": [{}]}
    # nodes only with required elements
    text_input["nodes"][0] = {
        "node_type": "author",
        "format": {"name": "parquet", "separator": ","},
        "files": "/tmp/acm_raw/nodes/author.parquet",
        "node_id_col": "node_id",
    }
    return text_input


@pytest.mark.parametrize("wildcard", ["*", "?"])
def test_try_read_file_with_wildcard(
    converter: GConstructConfigConverter, node_dict: dict, wildcard
):
    """We don't currently support wildcards in filenames, so should error out."""
    node_dict["nodes"][0]["files"] = f"/tmp/acm_raw/nodes/author{wildcard}.parquet"

    with pytest.raises(ValueError):
        _ = converter.convert_nodes(node_dict["nodes"])


def test_try_read_unsupported_feature(converter: GConstructConfigConverter, node_dict: dict):
    """We currently only support no-op features, so should error out otherwise."""
    node_dict["nodes"][0]["features"] = [
        {
            "feature_col": ["citation_time"],
            "feature_name": "feat",
            "transform": {"name": "max_min_norm"},
        }
    ]

    with pytest.raises(ValueError):
        _ = converter.convert_nodes(node_dict["nodes"])


def test_read_node_gconstruct(converter: GConstructConfigConverter, node_dict: dict):
    """Multiple test cases for GConstruct node conversion"""
    # test case with only necessary components
    node_config = converter.convert_nodes(node_dict["nodes"])[0]
    assert len(converter.convert_nodes(node_dict["nodes"])) == 1
    assert node_config.node_type == "author"
    assert node_config.file_format == "parquet"
    assert node_config.files == ["/tmp/acm_raw/nodes/author.parquet"]
    assert node_config.separator == ","
    assert node_config.column == "node_id"
    assert node_config.features is None
    assert node_config.labels is None

    node_dict["nodes"].append(
        {
            "node_type": "paper",
            "format": {"name": "parquet"},
            "files": ["/tmp/acm_raw/nodes/paper.parquet"],
            "node_id_col": "node_id",
            "features": [{"feature_col": ["citation_time"], "feature_name": "feat"}],
            "labels": [
                {"label_col": "label", "task_type": "classification", "split_pct": [0.8, 0.1, 0.1]}
            ],
        }
    )

    # nodes with all elements
    # [self.type, self.format, self.files, self.separator, self.column, self.features, self.labels]
    node_config = converter.convert_nodes(node_dict["nodes"])[1]
    assert len(converter.convert_nodes(node_dict["nodes"])) == 2
    assert node_config.node_type == "paper"
    assert node_config.file_format == "parquet"
    assert node_config.files == ["/tmp/acm_raw/nodes/paper.parquet"]
    assert node_config.separator is None
    assert node_config.column == "node_id"
    assert node_config.features == [
        {"column": "citation_time", "transform": {"name": "no-op"}, "name": "feat"}
    ]
    assert node_config.labels == [
        {
            "column": "label",
            "type": "classification",
            "split_rate": {"train": 0.8, "val": 0.1, "test": 0.1},
        }
    ]


def test_read_edge_gconstruct(converter: GConstructConfigConverter):
    """Multiple test cases for GConstruct edges conversion"""
    text_input: dict[str, list[dict]] = {"edges": [{}]}
    # nodes only with required elements
    text_input["edges"][0] = {
        "relation": ["author", "writing", "paper"],
        "format": {"name": "parquet"},
        "files": "/tmp/acm_raw/edges/author_writing_paper.parquet",
        "source_id_col": "~from",
        "dest_id_col": "~to",
    }
    # Test with only required attributes
    # [self.source_col, self.source_type, self.dest_col, self.dest_type,
    #  self.format, self.files, self.separator, self.relation, self.features, self.labels]
    edge_config = converter.convert_edges(text_input["edges"])[0]
    assert len(converter.convert_edges(text_input["edges"])) == 1
    assert edge_config.source_col == "~from"
    assert edge_config.source_type == "author"
    assert edge_config.dest_col == "~to"
    assert edge_config.dest_type == "paper"
    assert edge_config.file_format == "parquet"
    assert edge_config.files == ["/tmp/acm_raw/edges/author_writing_paper.parquet"]
    assert edge_config.separator is None
    assert edge_config.relation == "writing"
    assert edge_config.features is None
    assert edge_config.labels is None

    # Test with all attributes available
    text_input["edges"].append(
        {
            "relation": ["author", "writing", "paper"],
            "format": {"name": "parquet"},
            "files": ["/tmp/acm_raw/edges/author_writing_paper.parquet"],
            "source_id_col": "~from",
            "dest_id_col": "~to",
            "features": [{"feature_col": ["author"], "feature_name": "feat"}],
            "labels": [
                {
                    "label_col": "edge_col",
                    "task_type": "classification",
                    "split_pct": [0.8, 0.2, 0.0],
                },
                {
                    "label_col": "edge_col2",
                    "task_type": "classification",
                    "split_pct": [0.9, 0.1, 0.0],
                },
            ],
        }
    )

    edge_config = converter.convert_edges(text_input["edges"])[1]
    assert len(converter.convert_edges(text_input["edges"])) == 2
    assert edge_config.source_col == "~from"
    assert edge_config.source_type == "author"
    assert edge_config.dest_col == "~to"
    assert edge_config.dest_type == "paper"
    assert edge_config.file_format == "parquet"
    assert edge_config.files == ["/tmp/acm_raw/edges/author_writing_paper.parquet"]
    assert edge_config.separator is None
    assert edge_config.relation == "writing"
    assert edge_config.features == [
        {"column": "author", "transform": {"name": "no-op"}, "name": "feat"}
    ]
    assert edge_config.labels == [
        {
            "column": "edge_col",
            "type": "classification",
            "split_rate": {"train": 0.8, "val": 0.2, "test": 0.0},
        },
        {
            "column": "edge_col2",
            "type": "classification",
            "split_rate": {"train": 0.9, "val": 0.1, "test": 0.0},
        },
    ]


def test_convert_gsprocessing(converter: GConstructConfigConverter):
    """Multiple test cases for end2end GConstruct-to-GSProcessing conversion"""
    # test empty
    assert converter.convert_to_gsprocessing({}) == {
        "version": "gsprocessing-v1.0",
        "graph": {"nodes": [], "edges": []},
    }

    gcons_conf = {}
    gcons_conf["nodes"] = [
        {
            "node_type": "paper",
            "format": {"name": "parquet"},
            "files": ["/tmp/acm_raw/nodes/paper.parquet"],
            "separator": ",",
            "node_id_col": "node_id",
            "features": [{"feature_col": ["citation_time"], "feature_name": "feat"}],
            "labels": [
                {"label_col": "label", "task_type": "classification", "split_pct": [0.8, 0.1, 0.1]}
            ],
        }
    ]
    gcons_conf["edges"] = [
        {
            "relation": ["author", "writing", "paper"],
            "format": {"name": "parquet"},
            "files": ["/tmp/acm_raw/edges/author_writing_paper.parquet"],
            "source_id_col": "~from",
            "dest_id_col": "~to",
            "features": [{"feature_col": ["author"], "feature_name": "feat"}],
            "labels": [
                {
                    "label_col": "edge_col",
                    "task_type": "classification",
                    "split_pct": [0.8, 0.2, 0.0],
                },
                {
                    "label_col": "edge_col2",
                    "task_type": "classification",
                    "split_pct": [0.9, 0.1, 0.0],
                },
            ],
        }
    ]

    assert len(converter.convert_to_gsprocessing(gcons_conf)["graph"]["nodes"]) == 1
    nodes_output = converter.convert_to_gsprocessing(gcons_conf)["graph"]["nodes"][0]
    assert nodes_output["data"]["format"] == "parquet"
    assert nodes_output["data"]["files"] == ["/tmp/acm_raw/nodes/paper.parquet"]
    assert nodes_output["type"] == "paper"
    assert nodes_output["column"] == "node_id"
    assert nodes_output["features"] == [
        {"column": "citation_time", "transform": {"name": "no-op"}, "name": "feat"}
    ]
    assert nodes_output["labels"] == [
        {
            "column": "label",
            "type": "classification",
            "split_rate": {"train": 0.8, "val": 0.1, "test": 0.1},
        }
    ]

    assert len(converter.convert_to_gsprocessing(gcons_conf)["graph"]["edges"]) == 1
    edges_output = converter.convert_to_gsprocessing(gcons_conf)["graph"]["edges"][0]
    assert edges_output["data"]["format"] == "parquet"
    assert edges_output["data"]["files"] == ["/tmp/acm_raw/edges/author_writing_paper.parquet"]
    assert edges_output["source"] == {"column": "~from", "type": "author"}
    assert edges_output["dest"] == {"column": "~to", "type": "paper"}
    assert edges_output["relation"] == {"type": "writing"}
    assert edges_output["features"] == [
        {"column": "author", "transform": {"name": "no-op"}, "name": "feat"}
    ]
    assert edges_output["labels"] == [
        {
            "column": "edge_col",
            "type": "classification",
            "split_rate": {"train": 0.8, "val": 0.2, "test": 0.0},
        },
        {
            "column": "edge_col2",
            "type": "classification",
            "split_rate": {"train": 0.9, "val": 0.1, "test": 0.0},
        },
    ]
