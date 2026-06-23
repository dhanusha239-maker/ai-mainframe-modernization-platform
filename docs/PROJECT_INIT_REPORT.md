# Legacy Assembler Modernization Intelligence Platform
## Project Initiation Report and 10-Day Plan

## Project Scope

This project focuses specifically on HLASM / IBM Mainframe Assembler modernization.

The objective is to build a modernization intelligence platform that can analyze assembler programs, extract control flow, data flow, parameter flow, VSAM/file usage, packed decimal behavior, and generate Java modernization candidates with testing and validation support.

This project does not target COBOL, PL/I, Natural, RPG, or other legacy languages.

---

## Project Vision

HLASM applications often contain critical business logic, packed decimal calculations, register-based parameter passing, VSAM file processing, PS/PDS source structures, and low-level control-flow behavior.

The goal of this project is to create a framework that can understand these assembler programs deeply enough to support:

- Documentation generation
- Impact analysis
- Java conversion candidates
- Testing pipeline creation
- ML-based behavioral validation

---
HLASM
 ↓
Analysis
 ↓
Behavior Extraction
 ↓
Documentation
 ↓
Full Java Replacement Candidate
 ↓
Testing
 ↓
ML Validation
---

## Core Capabilities

### 1. Source Intake Layer

The system should read assembler source from:

- Local `.asm` / `.asm.txt` files
- PS-style sequential source exports
- PDS-style member folders
- Future mainframe dataset exports

Deliverables:

- PS/PDS source reader
- Module inventory
- Member discovery

---

### 2. Assembler Intelligence Layer

The system should analyze:

- CSECT modules
- Labels
- Branches
- BAL/BALR/BAS/BASR calls
- DS/DC declarations
- Parameter blocks
- Register usage
- Return codes
- Packed decimal instructions
- VSAM ACB/RPL/GET/PUT/MODCB behavior

Deliverables:

- ASM Scanner
- CFG Builder
- PDG Builder
- VSAM/RPL Analyzer
- Packed Decimal Utility

---

### 3. Dependency and Impact Layer

The system should identify:

- Which modules call each other
- Which fields are read
- Which fields are written
- Which modules are impacted if a field changes
- Which record buffers are populated or written out
- Which modules contain modernization warnings

Deliverables:

- Impact Analyzer
- Behavior Reporter
- Project Documentation Generator

---

### 4. Java Modernization Layer

The system should generate Java conversion candidates from assembler analysis.

Java output should include:

- Java context/data classes
- Module classes
- Execute methods
- Return code handling
- Field access logic
- Packed decimal-safe calculations
- File processing placeholders

Deliverables:

- Java Generator
- Java model classes
- Java service classes

---

### 5. Testing and Validation Layer

Testing is a core part of the project.

The system should support:

- Unit test generation
- Input/output test case generation
- Regression testing
- HLASM vs Java behavior comparison
- Return code comparison
- Field value comparison
- Packed decimal calculation validation
- File output comparison

Deliverables:

- Test data generator
- Java unit tests
- Behavioral comparison engine
- Validation report

---

### 6. ML-Based Behavioral Validation Layer

The ML validation layer should compare legacy behavior and Java behavior using extracted execution features.

Possible features:

- Return code
- Error code
- Authorization status
- Updated business fields
- Execution path
- Module sequence
- File operation type
- Packed decimal output value
- Validation status

Example validation features:

```text
RC
ERRCODE
AUTHSTAT
TXAMT
TXFEE
MODULE_PATH
OUTPUT_RECORD_HASH
```

Deliverables:

- Behavioral feature extractor
- Similarity scoring
- Drift detection
- Confidence score

---

# 10-Day Implementation Plan

## Day 1 – HLASM Source Intake and Repository Discovery

Objectives:

- Read assembler source files
- Support PS-style sequential files
- Support PDS-style member folders
- Discover modules automatically

Deliverables:

- PS/PDS source reader
- Module inventory
- Source loading framework

---

## Day 2 – Assembler Scanner and Call Graph

Objectives:

- Identify CSECT modules
- Detect BAL/BALR/BAS/BASR calls
- Build module call graph

Deliverables:

- ASM scanner
- Call graph report

---

## Day 3 – Control Flow Graph

Objectives:

- Track branches
- Track labels
- Track fall-through paths
- Identify execution blocks

Deliverables:

- CFG builder
- Control flow report

---

## Day 4 – Data and Layout Discovery

Objectives:

- Parse DS/DC declarations
- Discover record layouts
- Build field offset maps
- Identify packed decimal fields

Deliverables:

- Symbol table
- Field offset map
- Packed decimal field inventory

---

## Day 5 – Program Dependency Graph

Objectives:

- Track reads and writes
- Resolve register-based operands
- Resolve parameter blocks
- Track return codes and conditions

Deliverables:

- PDG builder
- Read/write summary
- Condition summary
- Return code summary

---

## Day 6 – VSAM, PS/PDS, and Record Buffer Intelligence

Objectives:

- Analyze ACB/RPL
- Track GET/PUT/MODCB behavior
- Identify record buffers
- Support PS/PDS file reading utilities

Deliverables:

- VSAM/RPL analyzer
- Record buffer effects
- PS/PDS source utilities

---

## Day 7 – Packed Decimal Conversion and Arithmetic Support

Objectives:

- Decode packed decimal values
- Encode decimal values to COMP-3/packed format
- Support packed arithmetic validation
- Prepare Java BigDecimal mapping

Deliverables:

- Packed decimal utility
- Packed value test cases
- Java BigDecimal conversion strategy

---

## Day 8 – Impact Analysis and Documentation Generation

Objectives:

- Generate impact reports
- Generate behavior reports
- Generate project analysis documentation

Deliverables:

- Impact analyzer
- Behavior reporter
- Documentation generator

---

## Day 9 – Java Generator and Testing Pipeline

Objectives:

- Generate Java class skeletons
- Generate Java business logic candidates
- Generate test cases
- Compare expected outputs

Deliverables:

- Java generator
- Test harness
- Regression test report

---

## Day 10 – ML-Based Behavioral Validation and Final Demonstration

Objectives:

- Extract behavioral features
- Compare HLASM and Java outputs
- Generate similarity scores
- Create final modernization report

Deliverables:

- ML feature extractor
- Behavioral comparison report
- Final project demo package

---

# Expected Final Outcome

The platform will support a full HLASM modernization workflow:

```text
HLASM Source
    ↓
PS/PDS Source Reader
    ↓
ASM Scanner
    ↓
CFG Builder
    ↓
PDG Builder
    ↓
VSAM + Packed Decimal Analyzer
    ↓
Impact Analysis
    ↓
Documentation Generator
    ↓
Java Generator
    ↓
Testing Pipeline
    ↓
ML-Based Behavioral Validation
```

The final system will help teams understand assembler applications, identify modernization risks, generate Java candidates, and validate behavior before replacement.

# Project Challenges

Modernizing HLASM applications is significantly more complex than translating syntax from one language to another. Business behavior is often distributed across multiple modules, parameter blocks, VSAM record structures, packed decimal calculations, and register-based control flow.

Key challenges include resolving dynamic parameter passing, accurately interpreting packed decimal arithmetic, understanding file and record-buffer interactions, preserving return-code behavior, and generating Java code that remains functionally equivalent to the original assembler implementation. The platform addresses these challenges through dependency analysis, behavioral extraction, automated testing, and ML-based validation techniques.

Another challenge is achieving full Java replacement rather than generating simple code skeletons. The modernization engine must produce compilable Java candidates that preserve business rules, calculations, execution paths, and file-processing behavior while clearly identifying any instructions that require manual review.
