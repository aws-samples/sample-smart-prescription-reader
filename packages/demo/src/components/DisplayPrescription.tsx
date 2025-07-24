/**
 * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License. See the LICENSE accompanying this file
 * for the specific language governing permissions and limitations under
 * the License.
 */

import { Container } from '@cloudscape-design/components';

export interface DisplayPrescriptionProps {
  imageFile: File;
}

const DisplayPrescription = (props: DisplayPrescriptionProps) => {
  return (
    <Container>
      <img
        src={URL.createObjectURL(props.imageFile as Blob)}
        alt="prescription image"
        style={{ maxWidth: '100%' }}
      />
    </Container>
  );
};

export default DisplayPrescription;
