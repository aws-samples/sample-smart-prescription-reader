/**
  * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
  * SPDX-License-Identifier: MIT
  *
  * Licensed under the MIT License. See the LICENSE accompanying this file
  * for the specific language governing permissions and limitations under
  * the License.
 */

import FileUpload from '@cloudscape-design/components/file-upload';
import FormField from '@cloudscape-design/components/form-field';
import { useState } from 'react';

type ImageError = string | null;

export interface ImageUploaderProps {
  value: File[];
  setValue: (value: File[]) => void;
}

const maxImages = 1;
const ImageUploader: React.FC<ImageUploaderProps> = (
  props: ImageUploaderProps,
) => {
  const { value, setValue } = props;
  const [errorList, setErrorList] = useState<ImageError[]>([]);
  const [error, setError] = useState<string | undefined>();

  const validateImage = (file: File): ImageError => {
    const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      return 'The image must be in JPG, PNG, GIF, or WebP format';
    }
    return null;
  };

  return (
    <FormField
      label="Upload Prescription Image"
      description="A clear photo or scanned image of your prescription"
      errorText={error}
    >
      <FileUpload
        onChange={({ detail }) => {
          if (detail.value.length > maxImages) {
            setError(`Please provide only one image`);
            return;
          } else if (detail.value.length === 0) {
            setError('Please provide an image');
          } else {
            setError(undefined);
          }
          setValue(detail.value);
          setErrorList(detail.value.map(validateImage));
        }}
        value={value}
        i18nStrings={{
          uploadButtonText: (e) => (e ? 'Choose images' : 'Choose image'),
          dropzoneText: (e) =>
            e ? 'Drop images to upload' : 'Drop image to upload',
          removeFileAriaLabel: (e) => `Remove image ${e + 1}`,
          limitShowFewer: 'Show fewer images',
          limitShowMore: 'Show more images',
          errorIconAriaLabel: 'Error',
        }}
        multiple={false}
        accept="image/png,image/jpeg,image/gif,image/webp"
        fileErrors={errorList}
        showFileLastModified
        showFileSize
        showFileThumbnail
        constraintText="Supported image formats are JPEG, PNG, GIF, and WebP."
      />
    </FormField>
  );
};

export default ImageUploader;
