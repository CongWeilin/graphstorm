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
from typing import List, Optional

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, FloatType, NumericType

from graphstorm_processing.constants import SPECIAL_CHARACTERS
from .base_dist_transformation import DistributedTransformation


class NoopTransformation(DistributedTransformation):
    """A no-op transformation that parses data as floats or lists of floats
    and forwards the result withouth any processing.

    For CSV input that contains numerical array rows that use a separator character,
    this transformation splits the values into a vector of floats, e.g. "1|2|3"
    becomes a vector [1.0, 2.0, 3.0].

    Parameters
    ----------
    cols : List[str]
        The list of columns to parse as floats or lists of float
    separator : Optional[str], optional
        Optional separator to use to split the string, by default None
    """

    def __init__(self, cols: List[str], separator: Optional[str] = None) -> None:
        super().__init__(cols)
        # TODO: Support multiple cols?

        self.separator = separator
        # Spark's split function uses a regexp so we need to
        # escape special chars to be used as separators
        if self.separator in SPECIAL_CHARACTERS:
            self.separator = f"\\{self.separator}"

    def apply(self, input_df: DataFrame) -> DataFrame:
        """
        Applies the transformation to the input DataFrame.
        The returned dataframe will only contain the columns specified during
        initialization of the transformation.
        """

        # If the incoming DataFrame has numerical array rows, just return it.
        col_datatype = input_df.schema[self.cols[0]].dataType
        if col_datatype.typeName() == "array":
            assert isinstance(col_datatype, ArrayType)
            if not isinstance(col_datatype.elementType, NumericType):
                raise ValueError(
                    f"Unsupported array type {col_datatype.elementType} "
                    f"for column {self.cols[0]}"
                )
            return input_df

        def str_list_to_float_vec(string_list: Optional[List[str]]) -> Optional[List[float]]:
            if string_list:
                return [float(x) for x in string_list]
            return None

        strvec_to_float_vec_udf = F.udf(
            str_list_to_float_vec, ArrayType(FloatType(), containsNull=False)
        )

        if self.separator:
            # Split up string into vector of floats
            input_df = input_df.select(
                [
                    strvec_to_float_vec_udf(F.split(F.col(column), self.separator)).alias(column)
                    for column in self.cols
                ]
            )
            return input_df
        else:
            return input_df.select(
                [F.col(column).cast(FloatType()).alias(column) for column in self.cols]
            )

    @staticmethod
    def get_transformation_name() -> str:
        """
        Get the name of the transformation
        """
        return "NoopTransformation"
