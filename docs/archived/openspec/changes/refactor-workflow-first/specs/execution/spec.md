## ADDED Requirements

### Requirement: Atomic Actions
The system SHALL implement atomic Action classes, containing only minimal interaction units.

#### Scenario: Action boundary enforcement
- **WHEN** implementing Action classes
- **THEN** Actions SHALL be limited to four operations: open_page, click, input, wait_for

#### Scenario: Business logic prohibition
- **WHEN** Actions are executing
- **THEN** they SHALL NOT contain business logic or flow control logic

### Requirement: Action Implementation
The system SHALL provide concrete Action class implementations, supporting basic browser interactions.

#### Scenario: OpenPage execution
- **WHEN** executing OpenPageAction
- **THEN** it SHALL navigate to the specified URL and wait for page load completion

#### Scenario: Click execution
- **WHEN** executing ClickAction
- **THEN** it SHALL locate and click the element with the specified selector

#### Scenario: Input execution
- **WHEN** executing InputAction
- **THEN** it SHALL input text content into the specified input field

#### Scenario: WaitFor execution
- **WHEN** executing WaitForAction
- **THEN** it SHALL wait for the specified condition to be met or timeout

### Requirement: Execution Context
The system SHALL maintain accurate execution state during execution.

#### Scenario: Step tracking
- **WHEN** executing each Action
- **THEN** Context SHALL update the current_step field

#### Scenario: URL tracking
- **WHEN** page navigation occurs
- **THEN** Context SHALL update the current_url field