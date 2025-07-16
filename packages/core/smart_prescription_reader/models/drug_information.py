# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.

from pydantic import BaseModel, Field


class DrugInformation(BaseModel):
    """Model representing drug information from the repository.

    This model contains essential information about medications including
    the drug name, active ingredient, strength, and form. It is used for
    providing context to the extraction model to improve medication name
    recognition and correction.

    Attributes:
        drug_name: Name of the drug
        active_ingredient: Active ingredient(s) in the drug
        strength: Strength/dosage of the drug
        form: Form of the drug (tablet, capsule, etc.)
    """

    drug_name: str = Field(description="Name of the drug")
    active_ingredient: str = Field(description="Active ingredient(s) in the drug")
    strength: str = Field(description="Strength/dosage of the drug")
    form: str = Field(description="Form of the drug (tablet, capsule, etc.)")
