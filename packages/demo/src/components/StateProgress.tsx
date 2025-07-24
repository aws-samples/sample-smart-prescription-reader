/**
 * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License. See the LICENSE accompanying this file
 * for the specific language governing permissions and limitations under
 * the License.
 */

import {
  JobStateEnum,
  ModelUsage,
} from ':smart-prescription-reader/models-graphql';
import { StateLogEntry } from '../hooks/usePrescriptionExtraction';
import {
  Badge,
  Container,
  Popover,
  Steps,
} from '@cloudscape-design/components';

const stateToDisplayHeader = (state: JobStateEnum) => {
  switch (state.toUpperCase()) {
    case 'TRANSCRIBE':
      return 'Transcribe Prescription';
    case 'EXTRACT':
      return 'Extract Prescription Data';
    case 'JUDGE':
      return 'Evaluate Extraction';
    case 'CORRECT':
      return 'Improve Extraction';
    default:
      return 'Unknown';
  }
};

const scoreToDisplayDetails = (score: string) => {
  switch (score.toUpperCase()) {
    case 'POOR':
      return <Badge color={'red'}>Poor</Badge>;
    case 'FAIR':
      return <Badge color={'grey'}>Fair</Badge>;
    case 'GOOD':
      return <Badge color={'blue'}>Good</Badge>;
    case 'EXCELLENT':
      return <Badge color={'green'}>Excellent</Badge>;
    default:
      return 'Unknown';
  }
};

/**
 * UsageDatail component takes in usage as ModelUsage and JSX child components.
 * If usage is undefined, it will render the child components.
 * If usage is defined, it will render the child components wrapped in a Popover with the usage data.
 * @param usage - ModelUsage
 * @param children - JSX child components
 * @returns JSX.Element
 */
const UsageDetail = ({
  usage,
  children,
}: {
  usage?: ModelUsage;
  children: React.ReactNode;
}) => {
  if (usage) {
    return (
      <Popover
        dismissButton={false}
        content={
          <div>
            <p>Input Tokens: {usage.inputTokens}</p>
            {!!usage.outputTokens && <p>Output Tokens: {usage.outputTokens}</p>}
            {!!usage.cacheReadInputTokens && (
              <p>Cached Input Tokens: {usage.cacheReadInputTokens}</p>
            )}
          </div>
        }
      >
        {children}
      </Popover>
    );
  } else {
    return <>{children}</>;
  }
};

const StateProgress = (props: { stateLog: StateLogEntry[] }) => {
  return (
    <Container header={<h3>Prescription Extraction Progress</h3>}>
      <Steps
        steps={props.stateLog.map((entry) => {
          return {
            header: (
              <UsageDetail usage={entry.usage}>
                {stateToDisplayHeader(entry.state)}
              </UsageDetail>
            ),
            status: entry.status,
            details: entry.score
              ? scoreToDisplayDetails(entry.score)
              : undefined,
          };
        })}
      />
    </Container>
  );
};

export default StateProgress;
