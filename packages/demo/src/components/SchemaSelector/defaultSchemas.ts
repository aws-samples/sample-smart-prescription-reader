/**
 * Copyright Amazon.com, Inc. and its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License. See the LICENSE accompanying this file
 * for the specific language governing permissions and limitations under
 * the License.
 */

export const defaultSchemaName = 'Standard';
export const defaultSchemas = Object.freeze({
  [defaultSchemaName]: JSON.stringify({
    type: 'object',
    required: ['prescriber', 'patient', 'date', 'medications'],
    properties: {
      prescriber: {
        type: 'string',
        description: "Doctor's name",
      },
      patient: {
        type: 'string',
        description: "Patient's name",
      },
      date: {
        type: 'string',
        description: 'Prescription date',
      },
      medications: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            medication: {
              type: 'string',
              description: 'Name of the medication',
            },
            dosage: {
              type: 'string',
              description: 'Prescribed dosage',
            },
          },
        },
      },
    },
  }),
  Compounded: JSON.stringify({
    $schema: 'http://json-schema.org/draft-07/schema#',
    type: 'object',
    required: ['prescriptionIngredients', 'date'],
    properties: {
      patientName: {
        type: 'string',
        description: "patient's full name",
      },
      patientAge: {
        type: 'string',
        description: "patient's age in years",
      },
      prescriptionIngredients: {
        type: 'array',
        description: 'List of medications/compounds and their amounts',
        items: {
          type: 'object',
          required: ['ingredientName', 'amount'],
          properties: {
            ingredientName: {
              type: 'string',
              description: 'Name of the medication or compound',
            },
            amount: {
              type: 'string',
              description:
                'Concentration or amount of the ingredient in percentage, weight, or volume',
            },
          },
        },
      },
      prescriptionInstructions: {
        type: 'string',
        description: 'Instructions on how to use the medication',
      },
      date: {
        type: 'string',
        description:
          'The date the prescription was written in YYYY-MM-DD format',
      },
    },
  }),
});
