# Future Enhancements

This project is currently stable as a modernization proof-of-concept. Future improvements can make it more scalable, enterprise-ready, and easier to integrate into real modernization programs.

## 1. Expand HLASM Coverage

Extend support for additional HLASM instructions, macros, addressing modes, packed decimal variations, and VSAM/file-processing patterns.

## 2. Strengthen ML Risk Integration

Integrate the saved Week 1 ML model more deeply into the Week 2 dashboard by showing model confidence, top risk factors, and SHAP-based explanations for each module.

## 3. Improve Test Automation

Use CFG, PDG, and AI recommendations to generate stronger test coverage, including branch tests, packed decimal boundary tests, file I/O tests, and field-impact regression tests.

## 4. Extend CI/CD Validation

The project already includes a GitHub Actions CI pipeline. Future work can extend it with code quality checks, test coverage reporting, deployment checks, and release artifacts.

## 5. Enhance Dashboard Experience

Improve the dashboard with dependency graphs, field-impact visualizations, risk trend charts, report export, and reviewer approval notes.

## 6. Prepare for Enterprise Deployment

Package the platform for easier enterprise review using Docker, internal Streamlit hosting, cloud deployment, or a FastAPI service layer.

## Known Current Limitation

The AUTHDEC approval behavior is documented as a source-program issue. The Java generator should not silently change business behavior. The correct modernization approach is to review or fix the source logic before production migration sign-off.