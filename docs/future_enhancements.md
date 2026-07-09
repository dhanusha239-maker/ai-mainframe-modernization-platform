# Future Enhancements

This project is production-ready as a modernization proof-of-concept. The following items can be added in future iterations.

## 1. Expanded HLASM Instruction Coverage

Add support for more HLASM instructions, macros, addressing modes, packed decimal variants, and VSAM patterns.

## 2. Stronger Week 1 ML Integration

Integrate the saved Week 1 ML model directly into the Week 2 dashboard.

Planned improvements:
- Load trained ML model artifact
- Show risk prediction confidence
- Show SHAP explanation per module
- Compare static risk score with ML-predicted risk

## 3. Automated Test Generation

Use CFG, PDG, and AI recommendations to generate test case templates.

Planned improvements:
- Branch coverage tests
- Packed decimal boundary tests
- File I/O batch tests
- Field impact regression tests

## 4. CI/CD Pipeline

Add automated checks for every commit.

Expected CI steps:
- Python syntax check
- Scanner / CFG / PDG tests
- Java generation
- Java compilation
- Behavior comparison
- AI report generation in offline mode

## 5. Dashboard Enhancements

Improve dashboard visualization.

Planned improvements:
- Module dependency graph
- Field impact graph
- Risk trend charts
- Export AI report as PDF
- Reviewer notes and approval workflow

## 6. Enterprise Deployment

Package the platform for demo or internal review.

Possible options:
- Docker container
- Internal Streamlit server
- Azure App Service
- AWS EC2 / ECS
- GitHub Actions deployment

## Known Current Limitation

AUTHDEC approval behavior is documented as a source-program issue. The Java generator should not silently change business behavior. The correct modernization process is to review or fix the source logic before production migration sign-off.
