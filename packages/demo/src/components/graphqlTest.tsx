/**
 * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License. See the LICENSE accompanying this file
 * for the specific language governing permissions and limitations under
 * the License.
 */

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { GetJobStatusDocument } from ':smart-prescription-reader/models-graphql';
import { useGraphqlClient } from '../hooks/useGraphqlClient';

const GraphqlTest: React.FC = () => {
  const graphqlClient = useGraphqlClient();
  const jobId = '6465bb62-3b4d-4b68-ae2a-1468056474bb';

  const result = useQuery({
    queryKey: ['getJobStatus', jobId],
    queryFn: () =>
      graphqlClient(GetJobStatusDocument, {
        jobId: jobId,
      }),
    refetchInterval: 5000,
  });
  return (
    <div>
      <h1>Graphql Test</h1>
      {result.data && result.data.getJobStatus.status}
    </div>
  );
};
export default GraphqlTest;
