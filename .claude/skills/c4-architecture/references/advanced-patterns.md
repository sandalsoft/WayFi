# Advanced C4 Architecture Patterns

Reusable C4 patterns for common architectural styles, each with a complete Mermaid C4 diagram example.

---

## Table of Contents

1. [Microservices Architecture](#1-microservices-architecture)
2. [Event-Driven Architecture](#2-event-driven-architecture)
3. [API Gateway Pattern](#3-api-gateway-pattern)
4. [Database per Service Pattern](#4-database-per-service-pattern)
5. [CQRS / Event Sourcing Pattern](#5-cqrs--event-sourcing-pattern)
6. [Multi-Region Deployment](#6-multi-region-deployment)
7. [CI/CD Pipeline Visualization](#7-cicd-pipeline-visualization)
8. [Cross-Cutting Concerns](#8-cross-cutting-concerns)
9. [Backend for Frontend (BFF) Pattern](#9-backend-for-frontend-bff-pattern)
10. [Saga / Choreography Pattern](#10-saga--choreography-pattern)

---

## 1. Microservices Architecture

A system decomposed into independently deployable services, each owning its own data and communicating through well-defined APIs or messaging.

### Context Diagram

```mermaid
C4Context
    title Microservices E-Commerce Platform - System Context

    Person(customer, "Customer", "Browses and purchases products online")
    Person(seller, "Seller", "Lists products and manages inventory")
    Person(csAgent, "CS Agent", "Handles customer support tickets")

    System(ecommerce, "E-Commerce Platform", "Cloud-native microservices platform for online retail")

    System_Ext(stripe, "Stripe", "Payment processing")
    System_Ext(sendgrid, "SendGrid", "Transactional email")
    System_Ext(twilio, "Twilio", "SMS notifications")
    System_Ext(fedex, "FedEx API", "Shipping rates and tracking")
    System_Ext(algolia, "Algolia", "Product search indexing")

    Rel(customer, ecommerce, "Browses products, places orders", "HTTPS")
    Rel(seller, ecommerce, "Manages listings and inventory", "HTTPS")
    Rel(csAgent, ecommerce, "Resolves support tickets", "HTTPS")
    Rel(ecommerce, stripe, "Processes payments", "REST/HTTPS")
    Rel(ecommerce, sendgrid, "Sends order confirmations", "REST/HTTPS")
    Rel(ecommerce, twilio, "Sends shipping alerts", "REST/HTTPS")
    Rel(ecommerce, fedex, "Gets shipping rates and labels", "REST/HTTPS")
    Rel(ecommerce, algolia, "Syncs product catalog for search", "REST/HTTPS")
```

### Container Diagram

```mermaid
C4Container
    title Microservices E-Commerce Platform - Container Diagram

    Person(customer, "Customer", "Shops online")

    Container_Boundary(platform, "E-Commerce Platform") {
        Container(webApp, "Web Storefront", "React, Next.js", "Server-rendered shopping experience")
        Container(mobileApp, "Mobile App", "React Native", "iOS and Android shopping app")
        Container(gateway, "API Gateway", "Kong", "Request routing, auth, rate limiting")

        Container(catalogService, "Catalog Service", "Go", "Product catalog and search")
        Container(orderService, "Order Service", "Java, Spring Boot", "Order lifecycle management")
        Container(paymentService, "Payment Service", "Java, Spring Boot", "Payment processing and refunds")
        Container(userService, "User Service", "Node.js, Express", "User accounts and authentication")
        Container(inventoryService, "Inventory Service", "Go", "Stock tracking and reservation")
        Container(shippingService, "Shipping Service", "Python, FastAPI", "Shipping rate calculation and label generation")
        Container(notificationService, "Notification Service", "Node.js", "Email, SMS, and push notifications")

        ContainerDb(catalogDb, "Catalog DB", "PostgreSQL", "Products, categories")
        ContainerDb(orderDb, "Order DB", "PostgreSQL", "Orders, line items")
        ContainerDb(userDb, "User DB", "PostgreSQL", "Accounts, preferences")
        ContainerDb(inventoryDb, "Inventory DB", "PostgreSQL", "Stock levels")
        ContainerDb(searchIndex, "Search Index", "Elasticsearch", "Product search index")
        ContainerDb(cache, "Cache", "Redis", "Session and catalog cache")
        ContainerQueue(eventBus, "Event Bus", "Apache Kafka", "Domain events across services")
    }

    System_Ext(stripe, "Stripe", "Payment processing")
    System_Ext(fedex, "FedEx", "Shipping")

    Rel(customer, webApp, "Browses and purchases", "HTTPS")
    Rel(customer, mobileApp, "Browses and purchases")
    Rel(webApp, gateway, "API requests", "JSON/HTTPS")
    Rel(mobileApp, gateway, "API requests", "JSON/HTTPS")
    Rel(gateway, catalogService, "Routes", "gRPC")
    Rel(gateway, orderService, "Routes", "gRPC")
    Rel(gateway, userService, "Routes", "gRPC")
    Rel(catalogService, catalogDb, "Reads/writes", "SQL")
    Rel(catalogService, searchIndex, "Indexes products", "REST")
    Rel(catalogService, cache, "Caches product data", "Redis")
    Rel(orderService, orderDb, "Stores orders", "SQL")
    Rel(orderService, eventBus, "Publishes OrderCreated, OrderPaid", "Kafka")
    Rel(userService, userDb, "Stores accounts", "SQL")
    Rel(inventoryService, inventoryDb, "Tracks stock", "SQL")
    Rel(eventBus, inventoryService, "Delivers OrderCreated for stock reservation", "Kafka")
    Rel(eventBus, shippingService, "Delivers OrderPaid for fulfillment", "Kafka")
    Rel(eventBus, notificationService, "Delivers events for notifications", "Kafka")
    Rel(paymentService, stripe, "Charges cards", "HTTPS")
    Rel(shippingService, fedex, "Creates labels", "HTTPS")
```

### Key Characteristics

- Each service owns its own database (no shared databases)
- Services communicate via API Gateway (synchronous) and Event Bus (asynchronous)
- Independent deployment and scaling per service
- Technology diversity allowed (Go, Java, Node.js, Python)

---

## 2. Event-Driven Architecture

An architecture where components communicate primarily through events, enabling loose coupling, high scalability, and real-time responsiveness.

### Container Diagram

```mermaid
C4Container
    title Event-Driven Architecture - IoT Telemetry Platform

    Person(operator, "Plant Operator", "Monitors equipment and responds to alerts")

    Container_Boundary(platform, "IoT Telemetry Platform") {
        Container(dashboard, "Operations Dashboard", "React, WebSocket", "Real-time equipment monitoring")
        Container(ingestApi, "Ingestion API", "Go", "Receives telemetry data from devices at high throughput")
        Container(streamProcessor, "Stream Processor", "Apache Flink", "Real-time aggregation, anomaly detection, windowed analytics")
        Container(alertEngine, "Alert Engine", "Python, FastAPI", "Evaluates rules and triggers alerts")
        Container(historicalService, "Historical Service", "Java, Spring Boot", "Serves historical queries and trend analysis")
        Container(deviceRegistry, "Device Registry", "Node.js, Express", "Manages device metadata and configuration")

        ContainerQueue(eventStream, "Event Stream", "Apache Kafka", "Ordered, partitioned telemetry event log")
        ContainerQueue(alertTopic, "Alert Topic", "Apache Kafka", "Alert events for downstream consumers")
        ContainerDb(timeseriesDb, "Time Series DB", "TimescaleDB", "Compressed telemetry history")
        ContainerDb(stateStore, "State Store", "Redis", "Current device state and session data")
        ContainerDb(deviceDb, "Device DB", "PostgreSQL", "Device metadata and configurations")
    }

    System_Ext(pagerDuty, "PagerDuty", "Incident management")
    System_Ext(devices, "IoT Devices", "Sensors and PLCs on factory floor")

    Rel(devices, ingestApi, "Sends telemetry data", "MQTT/HTTPS")
    Rel(ingestApi, eventStream, "Publishes raw telemetry events", "Kafka")
    Rel(eventStream, streamProcessor, "Consumes telemetry events", "Kafka")
    Rel(streamProcessor, stateStore, "Updates current device state", "Redis")
    Rel(streamProcessor, timeseriesDb, "Writes aggregated metrics", "SQL")
    Rel(streamProcessor, alertTopic, "Publishes anomaly alerts", "Kafka")
    Rel(alertTopic, alertEngine, "Consumes alert events", "Kafka")
    Rel(alertEngine, pagerDuty, "Triggers incidents", "REST/HTTPS")
    Rel(operator, dashboard, "Monitors equipment", "HTTPS/WSS")
    Rel(dashboard, historicalService, "Queries historical data", "JSON/HTTPS")
    Rel(dashboard, stateStore, "Subscribes to live updates", "WebSocket/Redis Pub/Sub")
    Rel(historicalService, timeseriesDb, "Reads time series data", "SQL")
    Rel(deviceRegistry, deviceDb, "Manages device records", "SQL")
```

### Key Characteristics

- Events as the primary communication mechanism
- Stream processing for real-time analytics and anomaly detection
- Event log (Kafka) as the system of record for raw data
- Multiple consumers can independently process the same event stream
- Separation of real-time (stream) and historical (batch) query paths

---

## 3. API Gateway Pattern

A centralized entry point that handles cross-cutting concerns like authentication, rate limiting, request routing, and protocol translation.

### Container Diagram

```mermaid
C4Container
    title API Gateway Pattern - Multi-Client Platform

    Person(webUser, "Web User", "Uses browser-based application")
    Person(mobileUser, "Mobile User", "Uses iOS/Android app")
    Person_Ext(partner, "Partner Developer", "Integrates via public API")

    Container_Boundary(platform, "Platform") {
        Container(webApp, "Web Application", "React", "Single-page application")
        Container(mobileApp, "Mobile App", "React Native", "Cross-platform mobile app")

        Container(gateway, "API Gateway", "Kong", "Central entry point for all API traffic")
        Container(authService, "Auth Service", "Node.js, Express", "OAuth2/OIDC token issuance and validation")
        Container(rateLimiter, "Rate Limiter", "Redis-backed", "Per-client request throttling")

        Container(userService, "User Service", "Go", "User management and profiles")
        Container(productService, "Product Service", "Java, Spring Boot", "Product catalog management")
        Container(orderService, "Order Service", "Java, Spring Boot", "Order lifecycle")
        Container(searchService, "Search Service", "Python, FastAPI", "Full-text product search")

        ContainerDb(userDb, "User DB", "PostgreSQL", "User data")
        ContainerDb(productDb, "Product DB", "PostgreSQL", "Product catalog")
        ContainerDb(orderDb, "Order DB", "PostgreSQL", "Orders")
        ContainerDb(searchIndex, "Search Index", "Elasticsearch", "Product search index")
        ContainerDb(rateLimitStore, "Rate Limit Store", "Redis", "Request counters and sliding windows")
    }

    Rel(webUser, webApp, "Uses", "HTTPS")
    Rel(mobileUser, mobileApp, "Uses")
    Rel(webApp, gateway, "All API calls", "JSON/HTTPS")
    Rel(mobileApp, gateway, "All API calls", "JSON/HTTPS")
    Rel(partner, gateway, "Public API calls", "JSON/HTTPS")

    Rel(gateway, authService, "Validates JWT tokens", "gRPC")
    Rel(gateway, rateLimiter, "Checks rate limits", "gRPC")
    Rel(rateLimiter, rateLimitStore, "Reads/updates counters", "Redis")

    Rel(gateway, userService, "Routes /users/**", "gRPC")
    Rel(gateway, productService, "Routes /products/**", "gRPC")
    Rel(gateway, orderService, "Routes /orders/**", "gRPC")
    Rel(gateway, searchService, "Routes /search/**", "gRPC")

    Rel(userService, userDb, "Reads/writes", "SQL")
    Rel(productService, productDb, "Reads/writes", "SQL")
    Rel(orderService, orderDb, "Reads/writes", "SQL")
    Rel(searchService, searchIndex, "Queries", "REST")
```

### Dynamic Diagram - Request Flow Through Gateway

```mermaid
C4Dynamic
    title API Gateway Request Flow - Authenticated Product Search

    Person(user, "Mobile User")
    Container(mobileApp, "Mobile App", "React Native")
    Container(gateway, "API Gateway", "Kong")
    Container(authService, "Auth Service", "Node.js")
    Container(rateLimiter, "Rate Limiter", "Redis-backed")
    Container(searchService, "Search Service", "Python, FastAPI")
    ContainerDb(searchIndex, "Search Index", "Elasticsearch")

    Rel(user, mobileApp, "Searches for 'wireless headphones'")
    Rel(mobileApp, gateway, "GET /api/search?q=wireless+headphones", "JSON/HTTPS")
    Rel(gateway, authService, "Validates Bearer token", "gRPC")
    Rel(gateway, rateLimiter, "Checks client rate limit", "gRPC")
    Rel(gateway, searchService, "Forwards search request", "gRPC")
    Rel(searchService, searchIndex, "Queries products index", "REST")
    Rel(searchService, gateway, "Returns ranked results", "gRPC")
    Rel(gateway, mobileApp, "Returns JSON search results", "HTTPS")
```

### Key Characteristics

- Single entry point for all clients (web, mobile, third-party)
- Authentication and authorization enforced at the gateway
- Rate limiting protects backend services from abuse
- Protocol translation (HTTPS to gRPC) at the gateway
- Backend services are not directly exposed to the internet

---

## 4. Database per Service Pattern

Each microservice owns its private database, ensuring data encapsulation and independent schema evolution. Services share data through APIs and events, never through direct database access.

### Container Diagram

```mermaid
C4Container
    title Database per Service - Healthcare Platform

    Person(patient, "Patient", "Manages health records and appointments")
    Person(doctor, "Doctor", "Views patient records and manages care")

    Container_Boundary(platform, "Healthcare Platform") {
        Container(gateway, "API Gateway", "Kong", "Routing, auth, audit logging")

        Container(patientService, "Patient Service", "Java, Spring Boot", "Patient registration, demographics, insurance")
        ContainerDb(patientDb, "Patient DB", "PostgreSQL", "Patient demographics and insurance")

        Container(appointmentService, "Appointment Service", "Node.js, Express", "Scheduling and calendar management")
        ContainerDb(appointmentDb, "Appointment DB", "PostgreSQL", "Appointments, availability slots")

        Container(recordsService, "Medical Records Service", "Java, Spring Boot", "Clinical notes, lab results, prescriptions")
        ContainerDb(recordsDb, "Records DB", "MongoDB", "Semi-structured clinical documents")

        Container(billingService, "Billing Service", "Python, FastAPI", "Claims, invoices, payments")
        ContainerDb(billingDb, "Billing DB", "PostgreSQL", "Financial transactions and claims")

        Container(notificationService, "Notification Service", "Node.js", "Patient and provider notifications")
        ContainerDb(notificationDb, "Notification DB", "DynamoDB", "Notification history and preferences")

        ContainerQueue(eventBus, "Event Bus", "Apache Kafka", "Domain events for cross-service data sync")
    }

    Rel(patient, gateway, "Books appointments, views records", "HTTPS")
    Rel(doctor, gateway, "Manages patients and care plans", "HTTPS")

    Rel(gateway, patientService, "Routes patient requests", "gRPC")
    Rel(gateway, appointmentService, "Routes scheduling requests", "gRPC")
    Rel(gateway, recordsService, "Routes clinical requests", "gRPC")
    Rel(gateway, billingService, "Routes billing requests", "gRPC")

    Rel(patientService, patientDb, "Reads/writes patient data", "SQL")
    Rel(appointmentService, appointmentDb, "Reads/writes appointments", "SQL")
    Rel(recordsService, recordsDb, "Reads/writes clinical documents", "MongoDB Wire")
    Rel(billingService, billingDb, "Reads/writes financial data", "SQL")
    Rel(notificationService, notificationDb, "Reads/writes notification history", "DynamoDB SDK")

    Rel(patientService, eventBus, "Publishes PatientRegistered, PatientUpdated", "Kafka")
    Rel(appointmentService, eventBus, "Publishes AppointmentBooked, AppointmentCancelled", "Kafka")
    Rel(recordsService, eventBus, "Publishes LabResultAvailable", "Kafka")
    Rel(billingService, eventBus, "Publishes ClaimSubmitted, PaymentReceived", "Kafka")
    Rel(eventBus, notificationService, "Delivers events for notifications", "Kafka")
    Rel(eventBus, billingService, "Delivers AppointmentBooked for invoicing", "Kafka")
```

### Key Characteristics

- Each service has its own private database -- no other service accesses it directly
- Polyglot persistence: PostgreSQL for relational data, MongoDB for documents, DynamoDB for key-value
- Data consistency across services is eventual, achieved through domain events
- Schema changes in one service do not impact other services
- The event bus enables data synchronization without tight coupling

---

## 5. CQRS / Event Sourcing Pattern

Command Query Responsibility Segregation separates read and write models. Event Sourcing persists state as an append-only log of domain events rather than mutable rows.

### Container Diagram

```mermaid
C4Container
    title CQRS + Event Sourcing - Financial Trading Platform

    Person(trader, "Trader", "Submits and monitors trades")
    Person(riskManager, "Risk Manager", "Monitors portfolio risk in real time")

    Container_Boundary(platform, "Trading Platform") {
        Container(tradingUI, "Trading UI", "React, WebSocket", "Real-time trading interface")
        Container(riskDashboard, "Risk Dashboard", "React, D3.js", "Risk analytics and reporting")

        Container(commandApi, "Command API", "Java, Spring Boot", "Accepts write commands: place order, cancel order")
        Container(commandHandler, "Command Handler", "Java", "Validates and processes commands, emits domain events")
        Container(eventStore, "Event Store", "EventStoreDB", "Append-only log of all domain events")

        Container(projectionEngine, "Projection Engine", "Java", "Builds read models from event stream")

        ContainerDb(orderReadModel, "Order Read Model", "PostgreSQL", "Denormalized view of current order state")
        ContainerDb(portfolioReadModel, "Portfolio Read Model", "PostgreSQL", "Aggregated portfolio positions and P&L")
        ContainerDb(tradeHistoryModel, "Trade History Model", "ClickHouse", "Time-series trade analytics")

        Container(queryApi, "Query API", "Node.js, Express", "Serves read requests from optimized read models")

        ContainerQueue(eventBus, "Event Bus", "Apache Kafka", "Distributes domain events to projections and external consumers")
    }

    System_Ext(exchange, "Stock Exchange", "NYSE, NASDAQ order routing")
    System_Ext(marketData, "Market Data Feed", "Real-time price quotes")

    Rel(trader, tradingUI, "Places and monitors orders", "HTTPS/WSS")
    Rel(riskManager, riskDashboard, "Monitors risk metrics", "HTTPS/WSS")

    Rel(tradingUI, commandApi, "Submits order commands", "JSON/HTTPS")
    Rel(commandApi, commandHandler, "Dispatches validated commands")
    Rel(commandHandler, eventStore, "Appends domain events", "gRPC")
    Rel(commandHandler, exchange, "Routes orders to exchange", "FIX protocol")
    Rel(eventStore, eventBus, "Publishes persisted events", "Kafka")

    Rel(eventBus, projectionEngine, "Delivers events for projection", "Kafka")
    Rel(projectionEngine, orderReadModel, "Updates order projections", "SQL")
    Rel(projectionEngine, portfolioReadModel, "Updates portfolio projections", "SQL")
    Rel(projectionEngine, tradeHistoryModel, "Writes trade analytics", "SQL")

    Rel(tradingUI, queryApi, "Queries order status and positions", "JSON/HTTPS")
    Rel(riskDashboard, queryApi, "Queries risk metrics and P&L", "JSON/HTTPS")
    Rel(queryApi, orderReadModel, "Reads order data", "SQL")
    Rel(queryApi, portfolioReadModel, "Reads portfolio data", "SQL")
    Rel(queryApi, tradeHistoryModel, "Reads trade history", "SQL")

    Rel(marketData, eventBus, "Publishes price updates", "Kafka")
```

### Key Characteristics

- **Command side:** Validates business rules, emits events, writes to event store
- **Query side:** Multiple denormalized read models optimized for specific queries
- **Event Store:** The single source of truth -- an append-only log of all state changes
- **Projections:** Rebuild read models by replaying events from the event store
- **Separate scaling:** Read and write sides scale independently
- **Audit trail:** Complete history of every state change, useful for financial compliance

---

## 6. Multi-Region Deployment

Deploying the same system across multiple geographic regions for latency reduction, disaster recovery, and data sovereignty compliance.

### Deployment Diagram

```mermaid
C4Deployment
    title Multi-Region Deployment - Global SaaS Platform

    Deployment_Node(globalEdge, "Cloudflare", "Global CDN and DNS") {
        Container(cdn, "CDN", "Cloudflare CDN", "Static assets, geo-routing, DDoS protection")
    }

    Deployment_Node(usRegion, "AWS us-east-1", "Primary Region - US") {
        Deployment_Node(usEks, "EKS Cluster", "Kubernetes 1.28") {
            Deployment_Node(usApiPods, "API Pods x6", "Auto-scaling 3-12") {
                Container(usApi, "API Service", "Node.js, Express", "Handles US traffic")
            }
            Deployment_Node(usWorkerPods, "Worker Pods x3", "Auto-scaling 2-6") {
                Container(usWorker, "Worker Service", "Node.js", "Background job processing")
            }
        }
        Deployment_Node(usRds, "RDS", "Multi-AZ, db.r6g.2xlarge") {
            ContainerDb(usPrimary, "Primary DB", "PostgreSQL 15", "Read-write primary, US data")
        }
        Deployment_Node(usRedis, "ElastiCache", "Cluster mode, 3 shards") {
            ContainerDb(usCache, "Cache", "Redis 7", "Session and query cache")
        }
    }

    Deployment_Node(euRegion, "AWS eu-west-1", "Secondary Region - EU") {
        Deployment_Node(euEks, "EKS Cluster", "Kubernetes 1.28") {
            Deployment_Node(euApiPods, "API Pods x4", "Auto-scaling 2-8") {
                Container(euApi, "API Service", "Node.js, Express", "Handles EU traffic, GDPR compliance")
            }
            Deployment_Node(euWorkerPods, "Worker Pods x2", "Auto-scaling 1-4") {
                Container(euWorker, "Worker Service", "Node.js", "Background job processing")
            }
        }
        Deployment_Node(euRds, "RDS", "Multi-AZ, db.r6g.xlarge") {
            ContainerDb(euPrimary, "EU Primary DB", "PostgreSQL 15", "EU user data for GDPR compliance")
        }
        Deployment_Node(euRedis, "ElastiCache", "Cluster mode, 2 shards") {
            ContainerDb(euCache, "Cache", "Redis 7", "Session and query cache")
        }
    }

    Deployment_Node(apRegion, "AWS ap-southeast-1", "Tertiary Region - APAC") {
        Deployment_Node(apEks, "EKS Cluster", "Kubernetes 1.28") {
            Deployment_Node(apApiPods, "API Pods x3", "Auto-scaling 2-6") {
                Container(apApi, "API Service", "Node.js, Express", "Handles APAC traffic")
            }
        }
        Deployment_Node(apRds, "RDS Read Replica", "db.r6g.large") {
            ContainerDb(apReadReplica, "Read Replica", "PostgreSQL 15", "Read-only replica of US primary")
        }
    }

    Rel(cdn, usApi, "Routes US traffic", "HTTPS")
    Rel(cdn, euApi, "Routes EU traffic", "HTTPS")
    Rel(cdn, apApi, "Routes APAC traffic", "HTTPS")
    Rel(usApi, usPrimary, "Reads/writes", "SQL/TLS")
    Rel(usApi, usCache, "Caches", "Redis/TLS")
    Rel(euApi, euPrimary, "Reads/writes EU data", "SQL/TLS")
    Rel(euApi, euCache, "Caches", "Redis/TLS")
    Rel(apApi, apReadReplica, "Reads", "SQL/TLS")
    Rel(usPrimary, apReadReplica, "Replicates to", "PostgreSQL streaming")
```

### Key Characteristics

- **Geo-routing** at the CDN/DNS layer directs traffic to the nearest region
- **Data sovereignty:** EU data stays in the EU region for GDPR compliance
- **Read replicas** in secondary regions reduce read latency
- **Active-active** in US and EU; **read-only** in APAC
- **Independent scaling** per region based on traffic patterns
- **Failover:** CDN can redirect traffic if a region goes down

---

## 7. CI/CD Pipeline Visualization

Visualizing the continuous integration and deployment pipeline as a C4 Context or Container diagram to show how code flows from commit to production.

### Context Diagram

```mermaid
C4Context
    title CI/CD Pipeline - System Context

    Person(developer, "Developer", "Writes code and opens pull requests")
    Person(reviewer, "Code Reviewer", "Reviews and approves pull requests")

    System(cicd, "CI/CD Pipeline", "Automated build, test, and deployment system")

    System_Ext(github, "GitHub", "Source code hosting and pull requests")
    System_Ext(sonarqube, "SonarQube", "Static code analysis and quality gates")
    System_Ext(artifactory, "Artifactory", "Docker image and artifact registry")
    System_Ext(kubernetes, "Kubernetes Clusters", "Production and staging environments")
    System_Ext(slack, "Slack", "Team notifications and alerts")
    System_Ext(datadog, "Datadog", "Deployment monitoring and rollback triggers")

    Rel(developer, github, "Pushes commits and opens PRs")
    Rel(reviewer, github, "Reviews and approves PRs")
    Rel(github, cicd, "Triggers pipeline via webhook", "HTTPS")
    Rel(cicd, sonarqube, "Sends code for analysis", "REST/HTTPS")
    Rel(cicd, artifactory, "Publishes Docker images", "HTTPS")
    Rel(cicd, kubernetes, "Deploys containers", "kubectl/HTTPS")
    Rel(cicd, slack, "Sends build/deploy notifications", "Webhook")
    Rel(cicd, datadog, "Reports deployment markers", "REST/HTTPS")
    Rel(datadog, cicd, "Triggers rollback on error spike", "Webhook")
```

### Container Diagram

```mermaid
C4Container
    title CI/CD Pipeline - Container Diagram

    Person(developer, "Developer")
    System_Ext(github, "GitHub", "Source code")

    Container_Boundary(pipeline, "CI/CD Pipeline") {
        Container(webhookReceiver, "Webhook Receiver", "Node.js", "Receives GitHub webhook events")
        Container(buildOrchestrator, "Build Orchestrator", "GitHub Actions", "Coordinates pipeline stages")
        Container(testRunner, "Test Runner", "Docker", "Runs unit, integration, and E2E tests")
        Container(securityScanner, "Security Scanner", "Trivy, Snyk", "Container and dependency vulnerability scanning")
        Container(imageBuilder, "Image Builder", "Docker, Kaniko", "Builds and tags container images")
        Container(deployController, "Deploy Controller", "ArgoCD", "GitOps-based deployment to Kubernetes")
        Container(smokeTests, "Smoke Tests", "Playwright", "Post-deployment health and smoke tests")
        Container(rollbackController, "Rollback Controller", "Custom Go", "Automated rollback on failure")

        ContainerDb(pipelineDb, "Pipeline State", "PostgreSQL", "Build history, metrics, audit log")
        ContainerDb(artifactStore, "Artifact Store", "S3", "Build artifacts and test reports")
    }

    System_Ext(registry, "Container Registry", "ECR")
    System_Ext(k8sStaging, "Staging Cluster", "EKS")
    System_Ext(k8sProd, "Production Cluster", "EKS")
    System_Ext(slack, "Slack", "Notifications")

    Rel(developer, github, "Pushes code")
    Rel(github, webhookReceiver, "Sends push/PR events", "Webhook/HTTPS")
    Rel(webhookReceiver, buildOrchestrator, "Triggers pipeline run")
    Rel(buildOrchestrator, testRunner, "Runs test suite")
    Rel(buildOrchestrator, securityScanner, "Scans for vulnerabilities")
    Rel(buildOrchestrator, imageBuilder, "Builds container image")
    Rel(imageBuilder, registry, "Pushes tagged image", "HTTPS")
    Rel(buildOrchestrator, deployController, "Triggers deployment")
    Rel(deployController, k8sStaging, "Deploys to staging", "kubectl")
    Rel(buildOrchestrator, smokeTests, "Runs post-deploy checks")
    Rel(smokeTests, k8sStaging, "Tests staging endpoints", "HTTPS")
    Rel(deployController, k8sProd, "Promotes to production", "kubectl")
    Rel(smokeTests, k8sProd, "Tests production endpoints", "HTTPS")
    Rel(rollbackController, k8sProd, "Rolls back on failure", "kubectl")
    Rel(buildOrchestrator, pipelineDb, "Stores build records", "SQL")
    Rel(testRunner, artifactStore, "Uploads test reports", "S3 SDK")
    Rel(buildOrchestrator, slack, "Sends status notifications", "Webhook")
```

### Key Characteristics

- **Pipeline as code:** Pipeline definition lives in the repository
- **Security scanning** as a mandatory pipeline stage (shift-left security)
- **Progressive deployment:** Staging validation before production
- **Automated rollback** on post-deployment failure
- **Audit trail** of all builds, tests, and deployments
- **GitOps:** Desired state in Git, ArgoCD reconciles the cluster

---

## 8. Cross-Cutting Concerns

Patterns for handling concerns that span multiple services: authentication, authorization, logging, monitoring, tracing, and service mesh.

### Container Diagram

```mermaid
C4Container
    title Cross-Cutting Concerns - Platform Infrastructure

    Person(user, "User", "Accesses platform services")
    Person(sre, "SRE Engineer", "Monitors and manages platform health")

    Container_Boundary(platform, "Platform") {
        Container(gateway, "API Gateway", "Kong", "Entry point with auth, rate limiting, request logging")

        Container(serviceA, "Order Service", "Java, Spring Boot", "Order management")
        Container(serviceB, "Catalog Service", "Go", "Product catalog")
        Container(serviceC, "User Service", "Node.js, Express", "User management")
    }

    Container_Boundary(crossCutting, "Cross-Cutting Infrastructure") {
        Container(authServer, "Auth Server", "Keycloak", "OAuth2/OIDC identity provider, SSO, MFA")
        Container(serviceMesh, "Service Mesh", "Istio", "mTLS, traffic management, circuit breaking, retries")
        Container(logAggregator, "Log Aggregator", "Fluentd + Loki", "Collects and indexes structured logs from all services")
        Container(tracingCollector, "Distributed Tracing", "Jaeger", "Collects and visualizes request traces across services")
        Container(metricsCollector, "Metrics Collector", "Prometheus", "Scrapes and stores service metrics")
        Container(alertManager, "Alert Manager", "Prometheus Alertmanager", "Evaluates alert rules and routes notifications")
        Container(dashboard, "Observability Dashboard", "Grafana", "Unified view of logs, metrics, and traces")
        Container(secretManager, "Secret Manager", "HashiCorp Vault", "Manages secrets, certificates, and encryption keys")
        Container(configServer, "Config Server", "Consul", "Centralized service configuration and feature flags")
    }

    System_Ext(pagerDuty, "PagerDuty", "Incident management")
    System_Ext(slack, "Slack", "Team notifications")

    Rel(user, gateway, "All requests", "HTTPS")
    Rel(gateway, authServer, "Validates tokens", "OIDC")
    Rel(gateway, serviceA, "Routes via mesh", "mTLS")
    Rel(gateway, serviceB, "Routes via mesh", "mTLS")
    Rel(gateway, serviceC, "Routes via mesh", "mTLS")

    Rel(serviceA, serviceMesh, "Traffic routed through sidecar proxy", "mTLS")
    Rel(serviceB, serviceMesh, "Traffic routed through sidecar proxy", "mTLS")
    Rel(serviceC, serviceMesh, "Traffic routed through sidecar proxy", "mTLS")

    Rel(serviceA, logAggregator, "Ships structured logs", "Fluentd")
    Rel(serviceB, logAggregator, "Ships structured logs", "Fluentd")
    Rel(serviceC, logAggregator, "Ships structured logs", "Fluentd")

    Rel(serviceA, tracingCollector, "Sends trace spans", "OpenTelemetry")
    Rel(serviceB, tracingCollector, "Sends trace spans", "OpenTelemetry")
    Rel(serviceC, tracingCollector, "Sends trace spans", "OpenTelemetry")

    Rel(metricsCollector, serviceA, "Scrapes /metrics endpoint", "HTTP")
    Rel(metricsCollector, serviceB, "Scrapes /metrics endpoint", "HTTP")
    Rel(metricsCollector, serviceC, "Scrapes /metrics endpoint", "HTTP")

    Rel(metricsCollector, alertManager, "Fires alert rules", "HTTP")
    Rel(alertManager, pagerDuty, "Routes critical alerts", "Webhook")
    Rel(alertManager, slack, "Sends warning notifications", "Webhook")

    Rel(sre, dashboard, "Monitors platform health", "HTTPS")
    Rel(dashboard, logAggregator, "Queries logs", "LogQL")
    Rel(dashboard, metricsCollector, "Queries metrics", "PromQL")
    Rel(dashboard, tracingCollector, "Queries traces", "REST")

    Rel(serviceA, secretManager, "Fetches secrets at startup", "HTTPS")
    Rel(serviceB, secretManager, "Fetches secrets at startup", "HTTPS")
    Rel(serviceC, secretManager, "Fetches secrets at startup", "HTTPS")

    Rel(serviceA, configServer, "Reads configuration", "HTTP")
    Rel(serviceB, configServer, "Reads configuration", "HTTP")
    Rel(serviceC, configServer, "Reads configuration", "HTTP")
```

### Key Characteristics

- **Authentication/Authorization:** Centralized at the API Gateway and Auth Server; services trust validated tokens
- **Service Mesh:** mTLS between all services, circuit breaking, retries, traffic splitting
- **Observability triad:** Logs (Loki), Metrics (Prometheus), Traces (Jaeger) unified in Grafana
- **Secret management:** No hardcoded secrets; Vault provides dynamic secrets and certificate rotation
- **Configuration management:** Centralized config with Consul; feature flags for progressive rollouts
- **Alerting chain:** Prometheus rules trigger Alertmanager which routes to PagerDuty/Slack based on severity

---

## 9. Backend for Frontend (BFF) Pattern

A dedicated backend service tailored to each frontend client, aggregating and transforming data from multiple downstream services.

### Container Diagram

```mermaid
C4Container
    title Backend for Frontend (BFF) Pattern - Media Streaming Platform

    Person(webUser, "Web User", "Streams content in browser")
    Person(mobileUser, "Mobile User", "Streams on phone/tablet")
    Person(tvUser, "Smart TV User", "Streams on television")

    Container_Boundary(platform, "Streaming Platform") {
        Container(webApp, "Web Application", "React", "Feature-rich browsing and playback")
        Container(mobileApp, "Mobile App", "React Native", "Optimized for mobile data and battery")
        Container(tvApp, "TV App", "Android TV SDK", "10-foot UI, remote-control navigation")

        Container(webBff, "Web BFF", "Node.js, Express", "Aggregates data for web client: full catalog, social features, recommendations")
        Container(mobileBff, "Mobile BFF", "Node.js, Express", "Optimized payloads for mobile: compressed images, offline support, reduced data")
        Container(tvBff, "TV BFF", "Node.js, Express", "Simplified data for TV: large artwork, curated rows, minimal navigation depth")

        Container(catalogService, "Catalog Service", "Java, Spring Boot", "Content metadata, genres, ratings")
        Container(streamingService, "Streaming Service", "Go", "Adaptive bitrate video delivery")
        Container(recommendationService, "Recommendation Service", "Python, FastAPI", "ML-powered personalized recommendations")
        Container(userService, "User Service", "Node.js, Express", "Profiles, watchlists, preferences")
        Container(socialService, "Social Service", "Node.js, Express", "Reviews, ratings, friend activity")

        ContainerDb(catalogDb, "Catalog DB", "PostgreSQL", "Content metadata")
        ContainerDb(userDb, "User DB", "PostgreSQL", "User profiles and preferences")
        ContainerDb(recommendationCache, "Recommendation Cache", "Redis", "Pre-computed recommendations")
    }

    System_Ext(cdnProvider, "CDN", "CloudFront - Video segment delivery")

    Rel(webUser, webApp, "Browses and streams", "HTTPS")
    Rel(mobileUser, mobileApp, "Browses and streams")
    Rel(tvUser, tvApp, "Browses and streams")

    Rel(webApp, webBff, "API requests", "JSON/HTTPS")
    Rel(mobileApp, mobileBff, "API requests", "JSON/HTTPS")
    Rel(tvApp, tvBff, "API requests", "JSON/HTTPS")

    Rel(webBff, catalogService, "Fetches full catalog data", "gRPC")
    Rel(webBff, recommendationService, "Gets personalized lists", "gRPC")
    Rel(webBff, userService, "Gets user profile", "gRPC")
    Rel(webBff, socialService, "Gets friend activity and reviews", "gRPC")

    Rel(mobileBff, catalogService, "Fetches condensed catalog data", "gRPC")
    Rel(mobileBff, recommendationService, "Gets top-N recommendations", "gRPC")
    Rel(mobileBff, userService, "Gets user profile", "gRPC")

    Rel(tvBff, catalogService, "Fetches curated catalog rows", "gRPC")
    Rel(tvBff, recommendationService, "Gets featured recommendations", "gRPC")

    Rel(catalogService, catalogDb, "Reads metadata", "SQL")
    Rel(userService, userDb, "Reads/writes profiles", "SQL")
    Rel(recommendationService, recommendationCache, "Reads cached recommendations", "Redis")
    Rel(streamingService, cdnProvider, "Serves video segments via", "HTTPS")
```

### Key Characteristics

- **One BFF per client type:** Web, Mobile, and TV each have a dedicated backend
- **Tailored responses:** Mobile BFF sends compressed images and smaller payloads; TV BFF sends large artwork and simplified navigation
- **Aggregation layer:** BFFs combine data from multiple downstream services into client-optimal responses
- **Independent evolution:** Web BFF can add social features without affecting mobile or TV clients
- **Downstream services remain generic:** Catalog, User, and Recommendation services serve all BFFs with the same API

---

## 10. Saga / Choreography Pattern

Managing distributed transactions across multiple services using a choreography-based saga where each service reacts to events and publishes its own events, with compensating actions for failure scenarios.

### Container Diagram

```mermaid
C4Container
    title Saga Pattern (Choreography) - Travel Booking Platform

    Person(traveler, "Traveler", "Books travel packages")

    Container_Boundary(platform, "Travel Booking Platform") {
        Container(bookingUI, "Booking UI", "React", "Multi-step booking wizard")
        Container(gateway, "API Gateway", "Kong", "Routes and authenticates requests")

        Container(bookingService, "Booking Service", "Java, Spring Boot", "Orchestrates booking saga lifecycle")
        Container(flightService, "Flight Service", "Java, Spring Boot", "Reserves and confirms flight seats")
        Container(hotelService, "Hotel Service", "Go", "Reserves and confirms hotel rooms")
        Container(carService, "Car Rental Service", "Node.js, Express", "Reserves and confirms rental cars")
        Container(paymentService, "Payment Service", "Java, Spring Boot", "Processes payments and refunds")

        ContainerDb(bookingDb, "Booking DB", "PostgreSQL", "Saga state and booking records")
        ContainerDb(flightDb, "Flight DB", "PostgreSQL", "Flight inventory and reservations")
        ContainerDb(hotelDb, "Hotel DB", "PostgreSQL", "Room inventory and reservations")
        ContainerDb(carDb, "Car DB", "PostgreSQL", "Vehicle inventory and reservations")
        ContainerDb(paymentDb, "Payment DB", "PostgreSQL", "Payment transactions and refunds")

        ContainerQueue(eventBus, "Event Bus", "Apache Kafka", "Saga events: commands, confirmations, compensations")
    }

    System_Ext(stripe, "Stripe", "Payment processing")

    Rel(traveler, bookingUI, "Creates travel booking", "HTTPS")
    Rel(bookingUI, gateway, "Submits booking request", "JSON/HTTPS")
    Rel(gateway, bookingService, "Routes booking", "gRPC")

    Rel(bookingService, bookingDb, "Stores saga state", "SQL")
    Rel(bookingService, eventBus, "Publishes BookingRequested", "Kafka")

    Rel(eventBus, flightService, "Delivers BookingRequested", "Kafka")
    Rel(flightService, flightDb, "Reserves seats", "SQL")
    Rel(flightService, eventBus, "Publishes FlightReserved or FlightReservationFailed", "Kafka")

    Rel(eventBus, hotelService, "Delivers FlightReserved", "Kafka")
    Rel(hotelService, hotelDb, "Reserves rooms", "SQL")
    Rel(hotelService, eventBus, "Publishes HotelReserved or HotelReservationFailed", "Kafka")

    Rel(eventBus, carService, "Delivers HotelReserved", "Kafka")
    Rel(carService, carDb, "Reserves vehicle", "SQL")
    Rel(carService, eventBus, "Publishes CarReserved or CarReservationFailed", "Kafka")

    Rel(eventBus, paymentService, "Delivers CarReserved", "Kafka")
    Rel(paymentService, paymentDb, "Records payment", "SQL")
    Rel(paymentService, stripe, "Charges customer", "HTTPS")
    Rel(paymentService, eventBus, "Publishes PaymentCompleted or PaymentFailed", "Kafka")

    Rel(eventBus, bookingService, "Delivers saga completion/failure events", "Kafka")
```

### Dynamic Diagram - Happy Path

```mermaid
C4Dynamic
    title Saga Happy Path - Travel Booking

    Container(bookingService, "Booking Service", "Java, Spring Boot")
    ContainerQueue(eventBus, "Event Bus", "Apache Kafka")
    Container(flightService, "Flight Service", "Java, Spring Boot")
    Container(hotelService, "Hotel Service", "Go")
    Container(carService, "Car Rental Service", "Node.js")
    Container(paymentService, "Payment Service", "Java, Spring Boot")

    Rel(bookingService, eventBus, "1. Publishes BookingRequested")
    Rel(eventBus, flightService, "2. Delivers BookingRequested")
    Rel(flightService, eventBus, "3. Publishes FlightReserved")
    Rel(eventBus, hotelService, "4. Delivers FlightReserved")
    Rel(hotelService, eventBus, "5. Publishes HotelReserved")
    Rel(eventBus, carService, "6. Delivers HotelReserved")
    Rel(carService, eventBus, "7. Publishes CarReserved")
    Rel(eventBus, paymentService, "8. Delivers CarReserved")
    Rel(paymentService, eventBus, "9. Publishes PaymentCompleted")
    Rel(eventBus, bookingService, "10. Delivers PaymentCompleted, saga complete")
```

### Dynamic Diagram - Compensation Path

```mermaid
C4Dynamic
    title Saga Compensation - Hotel Reservation Fails

    Container(bookingService, "Booking Service", "Java, Spring Boot")
    ContainerQueue(eventBus, "Event Bus", "Apache Kafka")
    Container(flightService, "Flight Service", "Java, Spring Boot")
    Container(hotelService, "Hotel Service", "Go")

    Rel(bookingService, eventBus, "1. Publishes BookingRequested")
    Rel(eventBus, flightService, "2. Delivers BookingRequested")
    Rel(flightService, eventBus, "3. Publishes FlightReserved (seats held)")
    Rel(eventBus, hotelService, "4. Delivers FlightReserved")
    Rel(hotelService, eventBus, "5. Publishes HotelReservationFailed (no rooms)")
    Rel(eventBus, flightService, "6. Delivers HotelReservationFailed (compensate)")
    Rel(flightService, eventBus, "7. Publishes FlightReservationCancelled (seats released)")
    Rel(eventBus, bookingService, "8. Delivers failure, saga rolled back")
```

### Key Characteristics

- **No distributed transactions:** Each service manages its own local transaction
- **Event choreography:** Services react to events and emit their own events
- **Compensating actions:** When a step fails, previous steps are undone via compensation events
- **Saga state tracking:** The Booking Service maintains the saga state machine
- **Eventually consistent:** The system reaches consistency through the completion of all saga steps
- **Idempotency required:** Every event handler must be idempotent to handle retries safely

---

## Pattern Selection Guide

| Pattern | Best For | Trade-offs |
|---------|----------|------------|
| **Microservices** | Large teams, complex domains, independent scaling | Operational complexity, distributed data management |
| **Event-Driven** | Real-time processing, high throughput, loose coupling | Event ordering, eventual consistency, debugging difficulty |
| **API Gateway** | Multiple client types, centralized security, rate limiting | Single point of failure, potential bottleneck |
| **Database per Service** | Independent deployments, polyglot persistence | Cross-service queries are hard, data duplication |
| **CQRS/Event Sourcing** | High-read/low-write ratios, audit requirements, complex domains | Increased complexity, eventual consistency in reads |
| **Multi-Region** | Global user base, low latency, regulatory compliance | Data replication lag, operational cost, conflict resolution |
| **CI/CD Pipeline** | Frequent releases, quality gates, compliance auditing | Pipeline maintenance, flaky tests, long feedback loops |
| **Cross-Cutting Concerns** | Platform teams, consistent observability, security | Infrastructure overhead, configuration complexity |
| **BFF** | Multiple client types with different needs | More services to maintain, potential code duplication |
| **Saga/Choreography** | Distributed transactions, multi-service workflows | Complex failure handling, debugging difficulty |
