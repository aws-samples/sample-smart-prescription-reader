#!/usr/bin/env bash
# Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.


set -e

# must be run from project root
if [ ! -f "pnpm-lock.yaml" ]; then
    echo "Must be run from project root"
    exit 1
fi

# takes one argument, the output pdf filename
if [ $# -ne 1 ]; then
    echo "Usage: $0 <output.pdf>"
    exit 1
fi
# validate that output is pdf
if [[ $1 != *.pdf ]]; then
    echo "Output must be a pdf file"
    exit 1
fi

export MERMAID_FILTER_FORMAT=pdf

pandoc --metadata title="Smart Prescription Reader" \
  --pdf-engine=xelatex \
  -V geometry:margin=1in -V colorlinks=true -V linkcolor=blue -V toccolor=gray -V urlcolor=blue \
  -F mermaid-filter -f markdown-implicit_figures -f markdown+rebase_relative_paths --file-scope \
  --number-sections --toc --toc-depth=2 -s \
  README.md \
  documentation/technical_approach.md documentation/architecture.md documentation/improvements.md documentation/security.md \
  packages/demo/README.md \
  -o $1