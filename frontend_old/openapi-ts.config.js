/** @type {import('@hey-api/openapi-ts').UserConfig} */
module.exports = {
  input: 'openapi.json',
  output: 'client',
  plugins: ['@hey-api/client-axios'],
  typescript: {
    targetFiles: [
      {name: 'types.gen.ts', exportType: 'types'},
      {name: 'schemas.gen.ts', exportType: 'schemas'},
      {name: 'sdk.gen.ts', exportType: 'sdk'}
    ],
    indentation: 2,
    typeOverrides: {
      // Ensure sentence_id is always treated as a number
      'FootageChoice.sentence_id': {
        type: 'number'
      }
    }
  }
};
