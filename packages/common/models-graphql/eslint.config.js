import prettierConfig from 'eslint-config-prettier';
import prettierPlugin from 'eslint-plugin-prettier';
import graphqlPlugin from '@graphql-eslint/eslint-plugin';

export default [
  prettierConfig,
  {
    plugins: {
      prettier: { rules: prettierPlugin.rules },
    },
  },
  {
    files: ['src/**/*.graphql'],
    languageOptions: {
      parser: graphqlPlugin.parser,
    },
    plugins: {
      '@graphql-eslint': graphqlPlugin,
    },
    rules: {
      'prettier/prettier': 'error',
    },
  },
];
