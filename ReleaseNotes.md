### **Conversational AI Evaluation Tool - Version 2.0**

#### **Description**:

Version 2.0 is a major usability and operations release focused on complete dockerisation, unified UI access, and centralized documentation. This version brings the full application stack (including CLI workflows) into a Docker-first model, introduces single-port access through NGINX, and strengthens the end-to-end TDMS + Dashboard experience with clear, production-ready run guidance.

#### **New Features**
- **Full Dockerisation (Including CLI Workflows)**

    Version 2.0 dockerises the complete runtime path, including importer, testcase execution, analysis, and report generation through containerized CLI operations. This ensures consistent execution environments across machines and simplifies onboarding for both UI users and CLI operators.

- **Single-Port NGINX Gateway**

    The platform now supports a unified gateway model with NGINX as the single public entrypoint. Users can access Dashboard UI, TDMS UI, API routes, auth routes, and Selenium live view from one externally exposed port, improving deployment simplicity and operational clarity.

- **Integrated TDMS + Dashboard Experience**

    TDMS and the Test Case Execution Dashboard are now documented and operated as a cohesive workflow. This improves continuity from test-data preparation to run execution, analysis, and reporting within a single integrated operational model.

- **Full Functional Dashboard Flow (Execution + Analysis)**

    The Dashboard workflow is now documented and presented as a full lifecycle experience, including execution monitoring, analysis steps, and report-oriented outcome review. This closes the previous operational gap where analysis handling was not clearly represented as part of the primary UI-driven flow.

- **Refactored Docker Run Documentation (UI and CLI)**

    Docker operational guides were split and refined into dedicated UI and CLI runbooks. Commands, service names, routes, and configuration references were updated to align with the current stack and reduce ambiguity during setup and day-to-day operations.

- **Centralized Documentation Website**

    Documentation is now consolidated and easier to navigate from a single source of truth, with complete setup, run, architecture, and user-manual coverage available in one place via the documentation portal.

- **Web Application**

    The platform's web application layer has been modernized to improve performance, accessibility, and maintainability. Deprecated CPGRAMS integration has been removed, and enhanced UI components with streamlined workflows provide a better user experience across all modules. A new Farmer Chatbot integration enables agricultural query support and domain-specific conversation workflows.
