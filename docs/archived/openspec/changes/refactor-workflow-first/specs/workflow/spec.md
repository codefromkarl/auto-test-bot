## ADDED Requirements

### Requirement: Workflow Definition and Parsing
The system SHALL support workflow definition and parsing based on YAML Workflow DSL v1 format.

#### Scenario: Valid workflow loading
- **WHEN** a configuration file compliant with DSL v1 format is provided
- **THEN** the system SHALL successfully parse and create a Workflow object

#### Scenario: Linear execution constraint
- **WHEN** a Workflow contains multiple Phases and Steps
- **THEN** the system SHALL execute strictly in the defined order, without supporting parallel or branching

### Requirement: Phase as Mental Model
The system SHALL use Phase as an abstraction for user mental model phases, with each phase containing an ordered set of Actions.

#### Scenario: Phase boundary
- **WHEN** execution enters a new Phase
- **THEN** the system SHALL update the current_phase field in Context

### Requirement: Workflow Orchestration
The system SHALL provide WorkflowExecutor as the highest-level execution engine.

#### Scenario: Execution start
- **WHEN** Workflow execution is started
- **THEN** Executor SHALL execute following the Phase→Step→Action hierarchy

#### Scenario: Error handling
- **WHEN** an error occurs during execution
- **THEN** Executor SHALL stop execution and generate an explainable failure report