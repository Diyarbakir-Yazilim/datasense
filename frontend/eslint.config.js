import js from "@eslint/js";

export default [
  js.configs.recommended,
  {
    ignores: ["dist/**", "node_modules/**"]
  },
  {
    files: ["**/*.{js,jsx}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parserOptions: {
        ecmaFeatures: { jsx: true }
      },
      globals: {
        window: "readonly",
        document: "readonly",
        console: "readonly",
        module: "readonly",
        process: "readonly",
        FormData: "readonly",
        setInterval: "readonly",
        clearInterval: "readonly",
        setTimeout: "readonly"
      }
    },
    rules: {
      "no-unused-vars": "warn",
      "react/prop-types": "off"
    }
  }
];
