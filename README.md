### AI-Powered Legacy Software Intelligence & Modernization Platform
# 2-Week Sprint Plan
Week 1: "Which HLASM modules are risky to modernize?"
Week 2: "How do we modernize them safely and verify the translated behavior?"

**Scope:**  ML-based legacy code risk prediction, HLASM-to-Java modernization, behavioral validation, and AI-assisted modernization reporting
**Duration:** 2 Weeks
**Project Type:** Enterprise Legacy Modernization Platform
________________________________________

## 1. Problem Definition

Many enterprises still depend on legacy mainframe systems written in HLASM, COBOL, PL/I, and other older technologies. These systems are business-critical, but modernization is difficult because the code often contains complex branching, interlinked modules, packed decimal operations, external calls, file handling, and limited documentation.
Before converting legacy code into a modern language, organizations need to understand:

•	Which modules are risky to modernize?
•	Why are those modules risky?
•	Can the business logic be preserved after translation?
•	What modernization steps should engineers follow?

This project builds an integrated platform that uses Machine Learning to predict modernization risk and AI to assist with HLASM-to-Java modernization and engineering recommendations.

________________________________________

## 2. Project Objective

The objective is to build a platform that performs two major functions:

# 1. ML-Based Legacy Code Risk Intelligence

This component analyses legacy HLASM modules and predicts modernization risk using machine learning.
Rather than relying only on module size, the model learns from multiple software engineering characteristics, including:
•	Lines of Code (LOC) 
•	Branch Instruction Count 
•	Called Module Count 
•	Calling Module Count 
•	File I/O Operations 
•	Database Access Operations 
•	Macro Call Count 
•	Packed Decimal Instruction Count 
•	Historical Defect Count 
•	Change Count (Last 12 Months) 
•	Comment Ratio 
•	Unsupported Instruction Count 
**Output**
•	 Modernization Risk Level: Low / Medium / High
•	 Prediction Confidence Score
•	 Top Risk Factors
•	 Feature Importance Explanation
•	 SHAP-based Sample Prediction Explanation
**Important**
The model does not classify risk based only on Lines of Code.
For example:
•	A 6,000-line reporting module can still be Low Risk if it has simple logic, few dependencies, low defect history, and good documentation. 
•	A 400-line authorization module can be High Risk if it contains deep branching, unsupported instructions, frequent changes, and complex dependencies. 

________________________________________

# 2. AI-Powered HLASM-to-Java Modernization

This component analyzes HLASM modules, translates supported logic into Java, validates behavior, and generates modernization recommendations.

It performs:
•	HLASM parsing
•	Intermediate representation creation
•	Java code generation
•	Behavioral validation
•	AI-assisted explanation
•	Modernization report generation

# Output:

Generated Java Code
Behavior Match Score
Translation Summary
Modernization Recommendations
Estimated Migration Effort
________________________________________

## 3. System Architecture

Legacy HLASM / Legacy Code
        |
        v
Static Feature Extraction
        |
        v
ML Risk Prediction Engine
        |
        v
Risk Score + Top Risk Factors
        |
        v
HLASM Parser + Java Generator
        |
        v
Behavioral Validation Engine
        |
        v
AI Modernization Intelligence Layer
        |
        v
Final Modernization Report / Dashboard

The ML model predicts how risky the module is.
The AI modernization layer explains why it is risky, validates translated behavior, and recommends how to modernize it safely.
________________________________________

## 4. Two-Week Sprint Plan

# Week 1: ML-Based Legacy Code Risk Prediction
**Goal**
Develop an ML pipeline that predicts modernization risk for legacy HLASM software modules.

# 1A.	Enterprise Dataset Design
Develop a realistic enterprise banking dataset where each record represents one HLASM module.
**Example columns:**
application_name
business_process
module_name
module_role
lines_of_code
branch_instruction_count
called_module_count
calling_module_count
file_io_count
database_access_count
macro_call_count
packed_decimal_instruction_count
historical_defect_count
change_count_last_12_months
comment_ratio
unsupported_instruction_count


**Target variable**
risk_level
Low
Medium
High

________________________________________

# 1B.	Data Preparation

Perform data preprocessing before model training.
Activities include:
•	Feature selection 
•	Categorical feature encoding (One-Hot Encoding) 
•	Numerical feature preparation 
•	Train/Test split 
•	ML pipeline construction using Scikit-learn 

________________________________________

# 1C.	 Model Development

Train and compare multiple machine learning models:
•	Logistic Regression (Baseline) 
•	Decision Tree 
•	Random Forest 
•	• XGBoost Classifier
Perform hyperparameter tuning using:
•	GridSearchCV 
•	5-Fold Cross Validation 
Select the Final model as the production model.

________________________________________
## 1D.   Model Evaluation

Evaluate each model using:
•	Accuracy 
•	Precision 
•	Recall 
•	F1-Score 
•	Confusion Matrix 
•	Cross-Validation Accuracy 
Compare baseline and tuned models to select the most reliable model.
________________________________________


# 1E.	Explainability

Interpret model predictions using:
• Feature Importance Ranking
• SHAP-based sample prediction explanation
____________________________________


**Week 1 Deliverables**
•	Enterprise Banking HLASM Risk Dataset 
•	Data Dictionary 
•	Data Preprocessing Pipeline 
•	Trained ML Models 
•	Hyperparameter Tuning Results 
•	Model Evaluation Report 
•	Feature Importance Analysis 
•	Sample Modernization Risk Predictions 
•	Saved Model Artifacts for Week 2 Integration 

________________________________________

## Week 2: AI-Powered Legacy Software Modernization Platform
**Goal**
Integrate the ML risk engine with the HLASM-to-Java modernization system and generate engineering-level modernization reports.

Main Activities

# 2A.	HLASM Parser
Parse HLASM source code and identify:
•	Labels
•	Opcodes
•	Operands
•	Branch instructions
•	External calls
•	Data declarations
•	Packed decimal operations
•	File/VSAM operations
Output:
Structured representation of the HLASM module
________________________________________

# 2B.	Intermediate Representation and Java Generation

Convert parsed HLASM logic into a language-neutral structure, then generate readable Java code.
Example:
HLASM packed decimal comparison
        ↓
Intermediate business rule
        ↓
Java BigDecimal comparison
________________________________________

# 2C.	Behavioral Validation

Run test cases against the generated Java logic to verify that the business behavior matches the original HLASM logic.
Example:
Total Test Cases: 25
Passed: 23
Failed: 2
Behavior Match Score: 92%
________________________________________

# 2D.	AI Modernization Intelligence Layer

Use the ML prediction, extracted features, SHAP explanation, generated Java, and validation result to create a modernization report.
Example output:
Module: LIMITCHK.ASM

ML Risk Prediction:
Medium Risk, 78% confidence

Behavior Validation:
92% behavior match

Primary Risk Factors:
- Packed decimal comparison
- Shared transaction structure
- Error code dependency
- Limited comments

Recommended Actions:
1. Add boundary test cases.
2. Review packed decimal rounding behavior.
3. Convert error codes into typed Java responses.
4. Isolate validation logic into a Java service class.

# Estimated Migration Effort:
Medium

**Week 2 Deliverables**
•	HLASM parser
•	Java generation engine
•	Behavioral validation engine
•	AI modernization report generator
•	API or dashboard interface
•	Final modernization report sample
________________________________________

# 2E. Final Platform Deliverables
At the end of the sprint, the platform should include:
•	ML-based modernization risk predictor
•	Realistic legacy code risk dataset
•	Feature extraction pipeline
•	HLASM-to-Java modernization engine
•	Behavioral validation system
•	AI modernization recommendation engine
•	Final modernization report
•	Technical documentation
________________________________________

## 5. Conclusion

The project is not just a translator and not just an ML model. It is an integrated modernization platform that predicts risk, modernizes code, validates behavior, and provides engineering guidance.

### Power shall commands:
python tests/test_scanner.py    -- to get list of called modules (asm_scanner.py)
python tests/test_cfg_builder.py -- to get CFG of all 11 modules with branches(cfg_builder.py)
python tests/test_pdg_builder.py--pdg_builder.py
python validator/impact_analyzer.py
python validator/documentation_generator.py
python validator/instruction_translator_updated_v3.py
python validator\java_generator_updated_v4_local_io.py
## To verify synatx errors
cd generated_java
javac *.java
###
cd ..
python tests/asm_runtime_tests.py    (only when instruction updates in symantic and translator)
python validator/behavior_comparator.py
python validator/modernization_dashboard.py
streamlit run dashboard/app.py


ai_llm_integration_details.json     -> proves OpenAI/LLM integration details
ai_modernization_report.md          -> final AI-generated modernization report
behavior_comparison_report.md       -> behavior validation summary
behavior_comparison_results.json    -> machine-readable validation result
generated_behavior_report.md        -> static/generated behavior documentation
known_hlasm_issues.md               -> documents AUTHDEC source issue
project_analysis_report.md          -> static analysis / module analysis report