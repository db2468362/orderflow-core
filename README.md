# orderflow-core

`orderflow-core` is the core foundational library for the **OrderFlow** microservice ecosystem. It enforces Clean Architecture principles, unified error handling, and standard response formats across all backend services.

---

## Features

- **Domain-Driven Exception Hierarchy**: Pure Python domain exceptions decoupled from HTTP infrastructure.
- **Automated FastAPI Exception Handler**: Maps domain exception categories into proper HTTP status codes (`404 Not Found`, `409 Conflict`, `400 Bad Request`).
- **Consistent API Error Responses**: Guarantees a standardized JSON structure for all application errors across all microservices.

---