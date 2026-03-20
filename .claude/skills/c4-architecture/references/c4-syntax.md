# Mermaid C4 Syntax Reference

Complete reference for creating C4 architecture diagrams using Mermaid's C4 syntax.

---

## Table of Contents

1. [C4Context Diagram](#c4context-diagram)
2. [C4Container Diagram](#c4container-diagram)
3. [C4Component Diagram](#c4component-diagram)
4. [C4Deployment Diagram](#c4deployment-diagram)
5. [C4Dynamic Diagram](#c4dynamic-diagram)
6. [Complete Keyword Reference](#complete-keyword-reference)
7. [Relationships](#relationships)
8. [Boundaries](#boundaries)
9. [Styling and Theming](#styling-and-theming)
10. [Full Examples](#full-examples)

---

## C4Context Diagram

The highest-level diagram showing the system in the context of its users and other systems.

### Diagram Declaration

```
C4Context
```

### Elements

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `Person(alias, label, ?description)` | alias, label, description | A human user of the system |
| `Person_Ext(alias, label, ?description)` | alias, label, description | An external person outside the system boundary |
| `System(alias, label, ?description)` | alias, label, description | The software system being described |
| `System_Ext(alias, label, ?description)` | alias, label, description | An external software system |
| `SystemDb(alias, label, ?description)` | alias, label, description | A system represented as a database |
| `SystemDb_Ext(alias, label, ?description)` | alias, label, description | An external system represented as a database |
| `SystemQueue(alias, label, ?description)` | alias, label, description | A system represented as a message queue |
| `SystemQueue_Ext(alias, label, ?description)` | alias, label, description | An external system represented as a message queue |

### Example

```mermaid
C4Context
    title System Context Diagram for Internet Banking System

    Person(customer, "Banking Customer", "A customer of the bank with personal accounts")
    Person_Ext(support, "Customer Service Staff", "Handles customer inquiries")

    System(bankingSystem, "Internet Banking System", "Allows customers to view balances and make payments")
    System_Ext(emailSystem, "E-mail System", "Microsoft Exchange e-mail system")
    SystemDb_Ext(mainframe, "Mainframe Banking System", "Stores core banking information")
    SystemQueue_Ext(eventBus, "Event Bus", "Publishes domain events")

    Rel(customer, bankingSystem, "Views balances, makes payments")
    Rel(bankingSystem, emailSystem, "Sends e-mails using", "SMTP")
    Rel(bankingSystem, mainframe, "Gets account info from", "XML/HTTPS")
    Rel(emailSystem, customer, "Sends e-mails to")
    Rel(support, bankingSystem, "Manages customer accounts")
    Rel(bankingSystem, eventBus, "Publishes events to", "AMQP")
```

---

## C4Container Diagram

Zooms into a single system to show the high-level containers (applications, data stores, etc.).

### Diagram Declaration

```
C4Container
```

### Elements

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `Container(alias, label, ?technology, ?description)` | alias, label, tech, description | An application or data store within the system |
| `Container_Ext(alias, label, ?technology, ?description)` | alias, label, tech, description | An external container |
| `ContainerDb(alias, label, ?technology, ?description)` | alias, label, tech, description | A database container |
| `ContainerDb_Ext(alias, label, ?technology, ?description)` | alias, label, tech, description | An external database container |
| `ContainerQueue(alias, label, ?technology, ?description)` | alias, label, tech, description | A message queue container |
| `ContainerQueue_Ext(alias, label, ?technology, ?description)` | alias, label, tech, description | An external message queue container |

### Example

```mermaid
C4Container
    title Container Diagram for Internet Banking System

    Person(customer, "Banking Customer", "A customer of the bank")
    System_Ext(emailSystem, "E-mail System", "Microsoft Exchange")
    System_Ext(mainframe, "Mainframe Banking System", "Core banking")

    Container_Boundary(bankingSystem, "Internet Banking System") {
        Container(webApp, "Web Application", "Java, Spring MVC", "Delivers the static content and the single-page application")
        Container(spa, "Single-Page Application", "JavaScript, Angular", "Provides banking functionality via the browser")
        Container(mobileApp, "Mobile App", "Kotlin, Swift", "Provides banking functionality via mobile device")
        Container(apiGateway, "API Gateway", "Java, Spring Cloud Gateway", "Routes and rate-limits API requests")
        Container(apiApp, "API Application", "Java, Spring Boot", "Provides banking functionality via JSON/HTTPS API")
        ContainerDb(database, "Database", "PostgreSQL", "Stores user data, accounts, transactions")
        ContainerQueue(messageQueue, "Message Queue", "RabbitMQ", "Handles async processing")
    }

    Rel(customer, webApp, "Visits", "HTTPS")
    Rel(customer, spa, "Uses", "HTTPS")
    Rel(customer, mobileApp, "Uses")
    Rel(webApp, spa, "Delivers")
    Rel(spa, apiGateway, "Makes API calls to", "JSON/HTTPS")
    Rel(mobileApp, apiGateway, "Makes API calls to", "JSON/HTTPS")
    Rel(apiGateway, apiApp, "Routes requests to", "JSON/HTTPS")
    Rel(apiApp, database, "Reads from and writes to", "SQL/TCP")
    Rel(apiApp, mainframe, "Gets account info from", "XML/HTTPS")
    Rel(apiApp, messageQueue, "Publishes messages to", "AMQP")
    Rel(messageQueue, emailSystem, "Triggers email via")
```

---

## C4Component Diagram

Zooms into a single container to show the components (modules, classes, services) inside it.

### Diagram Declaration

```
C4Component
```

### Elements

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `Component(alias, label, ?technology, ?description)` | alias, label, tech, description | A component within a container |
| `Component_Ext(alias, label, ?technology, ?description)` | alias, label, tech, description | An external component |
| `ComponentDb(alias, label, ?technology, ?description)` | alias, label, tech, description | A component represented as a database |
| `ComponentDb_Ext(alias, label, ?technology, ?description)` | alias, label, tech, description | An external database component |
| `ComponentQueue(alias, label, ?technology, ?description)` | alias, label, tech, description | A component represented as a message queue |
| `ComponentQueue_Ext(alias, label, ?technology, ?description)` | alias, label, tech, description | An external message queue component |

### Example

```mermaid
C4Component
    title Component Diagram for API Application

    Container_Ext(spa, "Single-Page Application", "JavaScript, Angular", "The main UI")
    ContainerDb(database, "Database", "PostgreSQL", "Stores user data")
    System_Ext(mainframe, "Mainframe Banking System", "Core banking")

    Container_Boundary(apiApp, "API Application") {
        Component(authController, "Auth Controller", "Spring REST Controller", "Handles authentication and authorization")
        Component(accountController, "Account Controller", "Spring REST Controller", "Provides account information")
        Component(paymentController, "Payment Controller", "Spring REST Controller", "Handles payment processing")
        Component(authService, "Auth Service", "Spring Bean", "Manages user authentication logic")
        Component(accountService, "Account Service", "Spring Bean", "Business logic for accounts")
        Component(paymentService, "Payment Service", "Spring Bean", "Business logic for payments")
        ComponentDb(accountRepo, "Account Repository", "Spring Data JPA", "Data access for accounts")
        Component(mainframeAdapter, "Mainframe Adapter", "Spring Bean", "Adapts mainframe XML to domain objects")
    }

    Rel(spa, authController, "Authenticates via", "JSON/HTTPS")
    Rel(spa, accountController, "Gets account data from", "JSON/HTTPS")
    Rel(spa, paymentController, "Submits payments to", "JSON/HTTPS")
    Rel(authController, authService, "Uses")
    Rel(accountController, accountService, "Uses")
    Rel(paymentController, paymentService, "Uses")
    Rel(accountService, accountRepo, "Uses")
    Rel(accountService, mainframeAdapter, "Uses")
    Rel(accountRepo, database, "Reads from and writes to", "SQL/TCP")
    Rel(mainframeAdapter, mainframe, "Makes API calls to", "XML/HTTPS")
```

---

## C4Deployment Diagram

Shows how containers are mapped to infrastructure (servers, cloud services, containers).

### Diagram Declaration

```
C4Deployment
```

### Elements

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `Deployment_Node(alias, label, ?type, ?description)` | alias, label, type, description | An infrastructure node (server, VM, container runtime, etc.) |
| `Node(alias, label, ?type, ?description)` | alias, label, type, description | Alias for Deployment_Node |
| `Node_L(alias, label, ?type, ?description)` | alias, label, type, description | Left-aligned node |
| `Node_R(alias, label, ?type, ?description)` | alias, label, type, description | Right-aligned node |

Deployment diagrams also use Container elements (`Container`, `ContainerDb`, `ContainerQueue`) placed inside `Deployment_Node` blocks to show what runs where.

### Example

```mermaid
C4Deployment
    title Deployment Diagram for Internet Banking System

    Deployment_Node(userDevice, "Customer's Device", "Desktop or Mobile") {
        Deployment_Node(browser, "Web Browser", "Chrome, Firefox, Safari") {
            Container(spa, "Single-Page Application", "JavaScript, Angular", "Provides banking functionality")
        }
    }

    Deployment_Node(aws, "AWS", "Amazon Web Services") {
        Deployment_Node(region, "us-east-1", "AWS Region") {
            Deployment_Node(alb, "ALB", "Application Load Balancer") {
                Container(lb, "Load Balancer", "AWS ALB", "Distributes incoming traffic")
            }
            Deployment_Node(eks, "EKS Cluster", "Kubernetes") {
                Deployment_Node(webPod, "Web Pod", "Docker") {
                    Container(webApp, "Web Application", "Java, Spring MVC", "Delivers static content")
                }
                Deployment_Node(apiPod, "API Pod x3", "Docker") {
                    Container(apiApp, "API Application", "Java, Spring Boot", "Provides banking API")
                }
            }
            Deployment_Node(rds, "RDS", "AWS Managed Database") {
                ContainerDb(database, "Database", "PostgreSQL 15", "Stores user and account data")
            }
            Deployment_Node(elasticache, "ElastiCache", "AWS Managed Cache") {
                ContainerDb(cache, "Session Cache", "Redis 7", "Stores session data")
            }
        }
    }

    Rel(spa, lb, "Makes API calls to", "HTTPS")
    Rel(lb, webApp, "Forwards to", "HTTPS")
    Rel(lb, apiApp, "Forwards to", "HTTPS")
    Rel(webApp, spa, "Delivers to browser")
    Rel(apiApp, database, "Reads/writes", "SQL/TCP")
    Rel(apiApp, cache, "Reads/writes", "TCP")
```

---

## C4Dynamic Diagram

Shows how elements interact at runtime with numbered, ordered relationships.

### Diagram Declaration

```
C4Dynamic
```

### Relationships in Dynamic Diagrams

Dynamic diagrams use the same elements as other C4 diagrams but relationships are rendered with sequence numbers to show the order of interactions.

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `Rel(from, to, label, ?technology)` | from, to, label, tech | A numbered relationship (auto-increments) |

### Example

```mermaid
C4Dynamic
    title Dynamic Diagram - Customer Makes a Payment

    Person(customer, "Banking Customer", "A customer of the bank")

    Container_Boundary(bankingSystem, "Internet Banking System") {
        Container(spa, "SPA", "Angular", "Single-page application")
        Container(apiGateway, "API Gateway", "Spring Cloud Gateway", "API routing")
        Container(paymentService, "Payment Service", "Spring Boot", "Payment processing")
        Container(accountService, "Account Service", "Spring Boot", "Account management")
        ContainerDb(database, "Database", "PostgreSQL", "Stores transactions")
        ContainerQueue(queue, "Message Queue", "RabbitMQ", "Async processing")
    }

    System_Ext(paymentProvider, "Payment Provider", "External payment network")

    Rel(customer, spa, "Submits payment form")
    Rel(spa, apiGateway, "POST /api/payments", "JSON/HTTPS")
    Rel(apiGateway, paymentService, "Routes payment request", "JSON/HTTPS")
    Rel(paymentService, accountService, "Validates account balance", "gRPC")
    Rel(paymentService, database, "Stores payment record", "SQL")
    Rel(paymentService, paymentProvider, "Submits payment", "HTTPS")
    Rel(paymentService, queue, "Publishes PaymentCompleted event", "AMQP")
    Rel(queue, accountService, "Consumes event, updates balance", "AMQP")
```

---

## Complete Keyword Reference

### Diagram Types

| Keyword | Description |
|---------|-------------|
| `C4Context` | Level 1: System Context diagram |
| `C4Container` | Level 2: Container diagram |
| `C4Component` | Level 3: Component diagram |
| `C4Deployment` | Deployment diagram |
| `C4Dynamic` | Dynamic/runtime interaction diagram |

### Person Elements

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `Person(alias, label, ?descr)` | alias, label, description | Internal person/user |
| `Person_Ext(alias, label, ?descr)` | alias, label, description | External person/user |

### System Elements

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `System(alias, label, ?descr)` | alias, label, description | Internal software system |
| `System_Ext(alias, label, ?descr)` | alias, label, description | External software system |
| `SystemDb(alias, label, ?descr)` | alias, label, description | Internal system as database |
| `SystemDb_Ext(alias, label, ?descr)` | alias, label, description | External system as database |
| `SystemQueue(alias, label, ?descr)` | alias, label, description | Internal system as queue |
| `SystemQueue_Ext(alias, label, ?descr)` | alias, label, description | External system as queue |

### Container Elements

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `Container(alias, label, ?techn, ?descr)` | alias, label, technology, description | Application, service, or data store |
| `Container_Ext(alias, label, ?techn, ?descr)` | alias, label, technology, description | External container |
| `ContainerDb(alias, label, ?techn, ?descr)` | alias, label, technology, description | Database container |
| `ContainerDb_Ext(alias, label, ?techn, ?descr)` | alias, label, technology, description | External database container |
| `ContainerQueue(alias, label, ?techn, ?descr)` | alias, label, technology, description | Message queue container |
| `ContainerQueue_Ext(alias, label, ?techn, ?descr)` | alias, label, technology, description | External message queue container |

### Component Elements

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `Component(alias, label, ?techn, ?descr)` | alias, label, technology, description | Component within a container |
| `Component_Ext(alias, label, ?techn, ?descr)` | alias, label, technology, description | External component |
| `ComponentDb(alias, label, ?techn, ?descr)` | alias, label, technology, description | Database component |
| `ComponentDb_Ext(alias, label, ?techn, ?descr)` | alias, label, technology, description | External database component |
| `ComponentQueue(alias, label, ?techn, ?descr)` | alias, label, technology, description | Message queue component |
| `ComponentQueue_Ext(alias, label, ?techn, ?descr)` | alias, label, technology, description | External message queue component |

### Deployment Elements

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `Deployment_Node(alias, label, ?type, ?descr)` | alias, label, type, description | Infrastructure node |
| `Node(alias, label, ?type, ?descr)` | alias, label, type, description | Alias for Deployment_Node |
| `Node_L(alias, label, ?type, ?descr)` | alias, label, type, description | Left-aligned deployment node |
| `Node_R(alias, label, ?type, ?descr)` | alias, label, type, description | Right-aligned deployment node |

### Boundaries

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `Boundary(alias, label, ?type)` | alias, label, type | Generic grouping boundary |
| `Enterprise_Boundary(alias, label)` | alias, label | Enterprise-level boundary |
| `System_Boundary(alias, label)` | alias, label | System-level boundary |
| `Container_Boundary(alias, label)` | alias, label | Container-level boundary |

All boundaries use block syntax with curly braces:
```
Boundary(alias, "Label") {
    ...elements...
}
```

---

## Relationships

### Relationship Keywords

| Keyword | Parameters | Description |
|---------|-----------|-------------|
| `Rel(from, to, label, ?techn)` | from alias, to alias, label, technology | Generic relationship |
| `Rel_U(from, to, label, ?techn)` | from, to, label, technology | Relationship with upward direction hint |
| `Rel_D(from, to, label, ?techn)` | from, to, label, technology | Relationship with downward direction hint |
| `Rel_L(from, to, label, ?techn)` | from, to, label, technology | Relationship with leftward direction hint |
| `Rel_R(from, to, label, ?techn)` | from, to, label, technology | Relationship with rightward direction hint |
| `Rel_Back(from, to, label, ?techn)` | from, to, label, technology | Return/callback relationship |
| `BiRel(from, to, label, ?techn)` | from, to, label, technology | Bidirectional relationship |

### Direction Aliases

| Keyword | Alias For | Direction |
|---------|-----------|-----------|
| `Rel_Up` | `Rel_U` | Upward |
| `Rel_Down` | `Rel_D` | Downward |
| `Rel_Left` | `Rel_L` | Leftward |
| `Rel_Right` | `Rel_R` | Rightward |

### Relationship Examples

```mermaid
C4Context
    Person(user, "User")
    System(systemA, "System A")
    System(systemB, "System B")
    SystemDb(db, "Database")

    Rel(user, systemA, "Uses")
    Rel(systemA, systemB, "Calls", "JSON/HTTPS")
    Rel_D(systemA, db, "Reads/writes", "SQL")
    BiRel(systemA, systemB, "Exchanges data", "gRPC")
    Rel_Back(systemB, user, "Sends notifications to")
```

---

## Boundaries

Boundaries group related elements together visually. They use block syntax with curly braces.

### Boundary Types

```mermaid
C4Context
    Enterprise_Boundary(enterprise, "Acme Corporation") {
        System_Boundary(internalSystems, "Internal Systems") {
            System(systemA, "System A", "Core business system")
            System(systemB, "System B", "Supporting system")
        }
        Boundary(teamBoundary, "Team X Ownership", "team") {
            System(systemC, "System C", "Team X's service")
        }
    }
    System_Ext(external, "External System", "Third-party service")

    Rel(systemA, systemB, "Uses")
    Rel(systemA, external, "Integrates with")
    Rel(systemC, systemA, "Depends on")
```

### Nesting Rules

- Boundaries can be nested inside other boundaries.
- Elements can only appear inside one boundary.
- Relationships can cross boundary lines.
- Keep nesting to a maximum of 3 levels for readability.

---

## Styling and Theming

### Title

```
title My Diagram Title
```

Place `title` immediately after the diagram type declaration.

### UpdateElementStyle

Customize the appearance of individual elements.

```
UpdateElementStyle(alias, $bgColor="color", $fontColor="color", $borderColor="color", $shadowing="true/false", $shape="shape")
```

| Parameter | Values | Description |
|-----------|--------|-------------|
| `$bgColor` | Hex color (e.g., `#438DD5`) | Background color |
| `$fontColor` | Hex color (e.g., `#FFFFFF`) | Text color |
| `$borderColor` | Hex color (e.g., `#2E6295`) | Border color |
| `$shadowing` | `"true"` or `"false"` | Whether to show shadow |
| `$shape` | `RoundedBoxShape`, `EightSidedShape`, `HexagonShape` | Element shape |
| `$sprite` | Sprite name | Icon/sprite to display |
| `$legendSprite` | Sprite name | Icon for legend |

### UpdateRelStyle

Customize the appearance of relationships.

```
UpdateRelStyle(from, to, $textColor="color", $lineColor="color", $offsetX="num", $offsetY="num")
```

| Parameter | Values | Description |
|-----------|--------|-------------|
| `$textColor` | Hex color | Color of the label text |
| `$lineColor` | Hex color | Color of the relationship line |
| `$offsetX` | Number | Horizontal offset for the label |
| `$offsetY` | Number | Vertical offset for the label |

### UpdateLayoutConfig

Configure the overall diagram layout.

```
UpdateLayoutConfig($c4ShapeInRow="num", $c4BoundaryInRow="num")
```

| Parameter | Values | Description |
|-----------|--------|-------------|
| `$c4ShapeInRow` | Number (default: 4) | Max elements per row |
| `$c4BoundaryInRow` | Number (default: 2) | Max boundaries per row |

### Styling Example

```mermaid
C4Context
    title Styled System Context Diagram

    Person(user, "User", "End user of the system")
    System(core, "Core System", "Main application")
    System_Ext(external, "External API", "Third-party service")
    SystemDb(db, "Database", "Primary data store")

    Rel(user, core, "Uses", "HTTPS")
    Rel(core, external, "Calls", "REST/HTTPS")
    Rel(core, db, "Reads/writes", "SQL")

    UpdateElementStyle(core, $bgColor="#1168BD", $fontColor="#FFFFFF", $borderColor="#0B4884")
    UpdateElementStyle(external, $bgColor="#999999", $fontColor="#FFFFFF")
    UpdateElementStyle(db, $bgColor="#438DD5", $fontColor="#FFFFFF", $shape="EightSidedShape")

    UpdateRelStyle(user, core, $textColor="#1168BD", $lineColor="#1168BD")
    UpdateRelStyle(core, external, $textColor="#999999", $lineColor="#999999")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

---

## Full Examples

### E-Commerce Platform - Context Diagram

```mermaid
C4Context
    title System Context Diagram - E-Commerce Platform

    Person(shopper, "Online Shopper", "Browses products and makes purchases")
    Person(admin, "Store Admin", "Manages products, orders, and inventory")
    Person_Ext(deliveryDriver, "Delivery Driver", "Delivers orders to customers")

    System(ecommerce, "E-Commerce Platform", "Allows customers to browse and purchase products online")

    System_Ext(paymentGateway, "Payment Gateway", "Stripe - Processes credit card payments")
    System_Ext(shippingProvider, "Shipping Provider", "FedEx API - Provides shipping rates and tracking")
    SystemDb_Ext(analyticsSystem, "Analytics Platform", "Google Analytics - Tracks user behavior")
    SystemQueue_Ext(notificationService, "Notification Service", "Twilio - Sends SMS notifications")

    Rel(shopper, ecommerce, "Browses, searches, and purchases products", "HTTPS")
    Rel(admin, ecommerce, "Manages catalog and orders", "HTTPS")
    Rel(ecommerce, paymentGateway, "Processes payments via", "HTTPS")
    Rel(ecommerce, shippingProvider, "Gets rates, creates labels via", "REST/HTTPS")
    Rel(ecommerce, analyticsSystem, "Sends tracking events to", "HTTPS")
    Rel(ecommerce, notificationService, "Sends order updates via", "HTTPS")
    Rel(notificationService, shopper, "Sends SMS to")
    Rel(notificationService, deliveryDriver, "Sends delivery alerts to")
```

### E-Commerce Platform - Container Diagram

```mermaid
C4Container
    title Container Diagram - E-Commerce Platform

    Person(shopper, "Online Shopper", "Browses and purchases products")
    System_Ext(paymentGateway, "Payment Gateway", "Stripe")
    System_Ext(shippingProvider, "Shipping Provider", "FedEx")

    Container_Boundary(ecommerce, "E-Commerce Platform") {
        Container(webApp, "Web Application", "Next.js, React", "Server-rendered storefront")
        Container(adminPanel, "Admin Dashboard", "React, Vite", "Product and order management UI")
        Container(apiGateway, "API Gateway", "Kong", "Request routing, rate limiting, auth")
        Container(catalogService, "Catalog Service", "Node.js, Express", "Product catalog management")
        Container(orderService, "Order Service", "Node.js, Express", "Order processing and fulfillment")
        Container(cartService, "Cart Service", "Node.js, Express", "Shopping cart management")
        Container(userService, "User Service", "Node.js, Express", "User accounts and authentication")
        ContainerDb(catalogDb, "Catalog DB", "PostgreSQL", "Products, categories, inventory")
        ContainerDb(orderDb, "Order DB", "PostgreSQL", "Orders, payments, shipments")
        ContainerDb(userDb, "User DB", "PostgreSQL", "User accounts, preferences")
        ContainerDb(cartCache, "Cart Cache", "Redis", "Shopping cart session data")
        ContainerQueue(eventBus, "Event Bus", "RabbitMQ", "Domain events and async processing")
    }

    Rel(shopper, webApp, "Browses products", "HTTPS")
    Rel(webApp, apiGateway, "Makes API calls", "JSON/HTTPS")
    Rel(adminPanel, apiGateway, "Manages catalog/orders", "JSON/HTTPS")
    Rel(apiGateway, catalogService, "Routes to", "JSON/HTTPS")
    Rel(apiGateway, orderService, "Routes to", "JSON/HTTPS")
    Rel(apiGateway, cartService, "Routes to", "JSON/HTTPS")
    Rel(apiGateway, userService, "Routes to", "JSON/HTTPS")
    Rel(catalogService, catalogDb, "Reads/writes", "SQL")
    Rel(orderService, orderDb, "Reads/writes", "SQL")
    Rel(userService, userDb, "Reads/writes", "SQL")
    Rel(cartService, cartCache, "Reads/writes", "Redis protocol")
    Rel(orderService, eventBus, "Publishes OrderCreated", "AMQP")
    Rel(eventBus, catalogService, "Consumes InventoryReserved", "AMQP")
    Rel(orderService, paymentGateway, "Processes payments", "HTTPS")
    Rel(orderService, shippingProvider, "Creates shipments", "HTTPS")
```

### SaaS Platform - Deployment Diagram

```mermaid
C4Deployment
    title Deployment Diagram - SaaS Platform on AWS

    Deployment_Node(cdn, "CloudFront CDN", "AWS CloudFront") {
        Container(staticAssets, "Static Assets", "React SPA", "JavaScript bundle and static files")
    }

    Deployment_Node(aws, "AWS Account", "Production") {
        Deployment_Node(vpc, "VPC", "10.0.0.0/16") {
            Deployment_Node(publicSubnet, "Public Subnet", "10.0.1.0/24") {
                Deployment_Node(alb, "ALB", "Application Load Balancer") {
                    Container(loadBalancer, "Load Balancer", "AWS ALB", "TLS termination, routing")
                }
            }
            Deployment_Node(privateSubnet, "Private Subnet", "10.0.2.0/24") {
                Deployment_Node(ecs, "ECS Cluster", "AWS Fargate") {
                    Deployment_Node(apiTask, "API Tasks x3", "Docker") {
                        Container(apiService, "API Service", "Node.js", "REST API")
                    }
                    Deployment_Node(workerTask, "Worker Tasks x2", "Docker") {
                        Container(workerService, "Worker Service", "Node.js", "Background job processor")
                    }
                }
            }
            Deployment_Node(dataSubnet, "Data Subnet", "10.0.3.0/24") {
                Deployment_Node(rds, "RDS Multi-AZ", "AWS RDS") {
                    ContainerDb(primaryDb, "Primary DB", "PostgreSQL 15", "Application data")
                }
                Deployment_Node(redis, "ElastiCache", "AWS ElastiCache") {
                    ContainerDb(cacheCluster, "Cache Cluster", "Redis 7", "Session and query cache")
                }
            }
        }
    }

    Rel(staticAssets, loadBalancer, "API requests", "HTTPS")
    Rel(loadBalancer, apiService, "Forwards", "HTTP")
    Rel(apiService, primaryDb, "Reads/writes", "SQL/TLS")
    Rel(apiService, cacheCluster, "Caches", "Redis/TLS")
    Rel(workerService, primaryDb, "Reads/writes", "SQL/TLS")
```

---

## Parameter Rules

1. **alias** - Must be a valid identifier (letters, numbers, underscores). No spaces or special characters. Used to reference the element in relationships.
2. **label** - Human-readable name displayed on the diagram. Enclosed in double quotes.
3. **technology** - Optional. The technology stack. Enclosed in double quotes. Only available on Container and Component elements.
4. **description** - Optional. A brief description of the element's purpose. Enclosed in double quotes.
5. Parameters prefixed with `?` in the reference tables are optional.
6. All string parameters must be enclosed in double quotes.
7. Commas separate parameters within the parentheses.

## Tips

- Always declare the diagram type first (`C4Context`, `C4Container`, etc.).
- Place `title` on the line immediately after the diagram type.
- Define all elements before defining relationships.
- Use `_Ext` suffix variants for elements outside the system boundary.
- Use descriptive relationship labels that explain *what* data flows, not just "calls" or "uses".
- Include the technology/protocol in relationship labels when it adds clarity.
- Keep diagrams focused on one level of abstraction at a time.
- Use boundaries to group logically related elements.
