#!/usr/bin/env bash

set -e
set -x

# Create the client directory
mkdir -p frontend/client

# Generate OpenAPI schema from FastAPI app
cd backend
python3 -c "import app.main; import json; print(json.dumps(app.main.app.openapi()))" > ../openapi.json
cd ..

# Move to frontend directory
mv openapi.json frontend/
cd frontend

# Install the OpenAPI generator and other necessary dependencies
npm install --save-dev @hey-api/openapi-ts @hey-api/client-axios --legacy-peer-deps
npm install --save axios --legacy-peer-deps

# Create a config file for openapi-ts
cat > openapi-ts.config.js << 'EOL'
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
EOL

# Generate the API client
npx @hey-api/openapi-ts

# Clean up
echo "API client generated successfully"
echo "Usage:"
echo "import { createClient } from './client';" 
echo "const apiClient = createClient({ baseUrl: 'http://localhost:8000' });"
