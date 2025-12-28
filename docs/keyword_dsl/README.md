# Keyword DSL

- Each file contains one or more CASE blocks
- Only keyword lines are allowed (STEP/ASSERT/VAR/TAGS/USE_LOCATORS)
- No selectors or timeouts in DSL

Example:

CASE "DEMO"
  TAGS ["example"]
  USE_LOCATORS "demo"
  STEP open url="https://example.com"
  STEP click target="nav.ai_create"
  ASSERT text_contains target="toast" text="success"
END
